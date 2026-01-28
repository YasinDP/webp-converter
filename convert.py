#!/usr/bin/env python3
"""
WebP Converter - Convert SVG and images to WebP format offline.

Supports: PNG, JPG, JPEG, GIF, BMP, TIFF, ICO, SVG
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
from io import BytesIO
from typing import Optional, Tuple, List

# Fix Cairo library path on macOS (Homebrew)
def _setup_cairo_path():
    """Set up library path for Cairo on macOS."""
    if sys.platform == 'darwin':
        try:
            result = subprocess.run(
                ['brew', '--prefix', 'cairo'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                cairo_lib = Path(result.stdout.strip()) / 'lib'
                if cairo_lib.exists():
                    # Set for ctypes to find the library
                    os.environ['DYLD_LIBRARY_PATH'] = str(cairo_lib) + ':' + os.environ.get('DYLD_LIBRARY_PATH', '')
                    # Also try to help cffi find it
                    import ctypes.util
                    if not ctypes.util.find_library('cairo'):
                        # Directly load the library
                        try:
                            import ctypes
                            ctypes.CDLL(str(cairo_lib / 'libcairo.2.dylib'))
                        except OSError:
                            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

_setup_cairo_path()

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

try:
    import cairosvg
    SVG_SUPPORT = True
except (ImportError, OSError) as e:
    SVG_SUPPORT = False
    if 'cairo' in str(e).lower():
        print("Warning: Cairo library not found. SVG conversion disabled.")
        print("To enable SVG support on macOS, run: brew install cairo")
    else:
        print("Warning: CairoSVG not installed. SVG conversion disabled.")
        print("To enable SVG support, run: pip install CairoSVG")

SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.ico'}
if SVG_SUPPORT:
    SUPPORTED_FORMATS.add('.svg')


def convert_svg_to_webp(svg_path: Path, output_path: Path, quality: int, scale: float = 1.0) -> bool:
    """Convert SVG to WebP."""
    if not SVG_SUPPORT:
        print(f"  ✗ SVG support not available: {svg_path.name}")
        return False
    
    try:
        # Convert SVG to PNG in memory
        png_data = cairosvg.svg2png(url=str(svg_path), scale=scale)
        
        # Open PNG from memory and convert to WebP
        img = Image.open(BytesIO(png_data))
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Keep alpha channel
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
        
        img.save(output_path, 'WEBP', quality=quality, method=6)
        return True
    except Exception as e:
        print(f"  ✗ Failed to convert {svg_path.name}: {e}")
        return False


def convert_image_to_webp(image_path: Path, output_path: Path, quality: int) -> bool:
    """Convert raster image to WebP."""
    try:
        img = Image.open(image_path)
        
        # Handle different modes
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Keep alpha channel for transparent images
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
        
        # Save as WebP
        img.save(output_path, 'WEBP', quality=quality, method=6)
        return True
    except Exception as e:
        print(f"  ✗ Failed to convert {image_path.name}: {e}")
        return False


def get_output_path(input_path: Path, output_dir: Optional[Path], keep_structure: bool, base_input: Optional[Path]) -> Path:
    """Determine the output path for a converted file."""
    if output_dir:
        if keep_structure and base_input:
            # Maintain relative directory structure
            relative = input_path.parent.relative_to(base_input)
            out_dir = output_dir / relative
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = output_dir
        return out_dir / f"{input_path.stem}.webp"
    else:
        return input_path.with_suffix('.webp')


def process_file(file_path: Path, output_dir: Optional[Path], quality: int, 
                 scale: float, keep_structure: bool, base_input: Optional[Path],
                 delete_on_success: bool = False) -> Tuple[bool, str]:
    """Process a single file."""
    suffix = file_path.suffix.lower()
    
    if suffix not in SUPPORTED_FORMATS:
        return False, f"  ⊘ Skipped (unsupported): {file_path.name}"
    
    output_path = get_output_path(file_path, output_dir, keep_structure, base_input)
    
    # Skip if output already exists and is newer
    if output_path.exists() and output_path.stat().st_mtime > file_path.stat().st_mtime:
        return True, f"  ○ Already converted: {file_path.name}"
    
    if suffix == '.svg':
        success = convert_svg_to_webp(file_path, output_path, quality, scale)
    else:
        success = convert_image_to_webp(file_path, output_path, quality)
    
    if success:
        # Calculate size reduction
        original_size = file_path.stat().st_size
        new_size = output_path.stat().st_size
        reduction = ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0
        
        size_info = f"({format_size(original_size)} → {format_size(new_size)}, {reduction:+.1f}%)"
        
        # Delete original file on success if requested
        if delete_on_success:
            try:
                file_path.unlink()
                return True, f"  ✓ Converted & removed: {file_path.name} → {output_path.name} {size_info}"
            except Exception as e:
                return True, f"  ✓ Converted: {file_path.name} → {output_path.name} {size_info} (could not delete: {e})"
        
        return True, f"  ✓ Converted: {file_path.name} → {output_path.name} {size_info}"
    
    return False, ""


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def find_images(path: Path, recursive: bool) -> List[Path]:
    """Find all supported image files in a path."""
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_FORMATS else []
    
    images = []
    pattern = '**/*' if recursive else '*'
    
    for ext in SUPPORTED_FORMATS:
        images.extend(path.glob(f"{pattern}{ext}"))
        images.extend(path.glob(f"{pattern}{ext.upper()}"))
    
    return sorted(set(images))


def get_script_dir() -> Path:
    """Get the directory where this script is located."""
    return Path(__file__).parent.resolve()


def main():
    # Default input/output directories relative to script location
    script_dir = get_script_dir()
    default_input = script_dir / 'input'
    default_output = script_dir / 'output'
    
    parser = argparse.ArgumentParser(
        description='Convert images and SVGs to WebP format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s                               Convert from ./input to ./output (auto-delete on success)
  %(prog)s image.png                     Convert single image
  %(prog)s logo.svg                      Convert SVG file
  %(prog)s ./images/                     Convert all images in directory
  %(prog)s ./images/ -r                  Convert recursively
  %(prog)s ./images/ -o ./webp/          Output to specific directory
  %(prog)s ./images/ -q 90               Set quality to 90%%
  %(prog)s logo.svg --scale 2            Convert SVG at 2x resolution

Default mode (no arguments):
  - Reads from: {default_input}
  - Outputs to: {default_output}
  - Successfully converted images are removed from input folder
  - Images remaining in input folder = failed conversions
        """
    )
    
    parser.add_argument('input', type=Path, nargs='?', default=None,
                        help='Input file or directory (default: ./input)')
    parser.add_argument('-o', '--output', type=Path, default=None,
                        help='Output directory (default: same as input, or ./output in default mode)')
    parser.add_argument('-q', '--quality', type=int, default=80,
                        help='WebP quality 1-100 (default: 80)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process directories recursively')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='Scale factor for SVG conversion (default: 1.0)')
    parser.add_argument('--keep-structure', action='store_true',
                        help='Maintain directory structure in output')
    parser.add_argument('--no-delete', action='store_true',
                        help='Do not delete source files after successful conversion (default mode only)')
    
    args = parser.parse_args()
    
    # Determine if using default mode (no input specified)
    default_mode = args.input is None
    
    if default_mode:
        args.input = default_input
        if args.output is None:
            args.output = default_output
        delete_on_success = not args.no_delete
        print("🔄 Running in default mode")
        print(f"   Input:  {args.input}")
        print(f"   Output: {args.output}")
        if delete_on_success:
            print("   ⚠️  Source files will be deleted after successful conversion")
        print()
    else:
        delete_on_success = False
    
    # Validate input
    if not args.input.exists():
        print(f"Error: Input path does not exist: {args.input}")
        if default_mode:
            print(f"       Create the input directory and add images to convert.")
        sys.exit(1)
    
    # Validate quality
    if not 1 <= args.quality <= 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Create output directory if specified
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
    
    # Find images
    images = find_images(args.input, args.recursive)
    
    if not images:
        print("No supported images found.")
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
        if default_mode:
            print(f"\nPlace images in: {args.input}")
        sys.exit(0)
    
    print(f"Found {len(images)} image(s) to convert")
    print(f"Quality: {args.quality}%")
    if args.scale != 1.0:
        print(f"SVG Scale: {args.scale}x")
    print("-" * 50)
    
    # Process images
    base_input = args.input if args.input.is_dir() else args.input.parent
    success_count = 0
    fail_count = 0
    
    for image in images:
        success, message = process_file(
            image, args.output, args.quality, 
            args.scale, args.keep_structure, base_input,
            delete_on_success=delete_on_success
        )
        if message:
            print(message)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print("-" * 50)
    print(f"Done! Converted: {success_count}, Failed: {fail_count}")
    
    if default_mode and fail_count > 0:
        print(f"\n⚠️  {fail_count} file(s) remain in input folder (conversion failed)")


if __name__ == '__main__':
    main()
