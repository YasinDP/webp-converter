# WebP Converter

A simple offline tool to convert SVG and images to WebP format.

## Supported Formats

- **Raster Images**: PNG, JPG, JPEG, GIF, BMP, TIFF, ICO
- **Vector Images**: SVG

## Installation

```bash
# Navigate to the converter directory
cd webp-converter

# Install dependencies
pip3 install -r requirements.txt
```

### macOS Note

CairoSVG requires Cairo to be installed for SVG support:

```bash
brew install cairo
```

## Usage

Use the `./webp` wrapper script (recommended) or call `python3 convert.py` directly.

### Default Mode (Recommended)

Simply run without arguments to use the built-in `input` and `output` folders:

```bash
./webp
```

**How it works:**
1. Place images in the `input/` folder
2. Run `./webp`
3. Converted WebP files appear in `output/`
4. Successfully converted images are **automatically removed** from `input/`
5. Any images remaining in `input/` = failed conversions

```bash
# To keep source files (don't delete after conversion)
./webp --no-delete
```

### Manual Conversion

```bash
# Convert a single image
./webp image.png

# Convert an SVG
./webp logo.svg

# Convert all images in a directory
./webp ./images/
```

### Advanced Options

```bash
# Recursive directory conversion
./webp ./images/ -r

# Specify output directory
./webp ./images/ -o ./webp/

# Set quality (1-100, default: 80)
./webp ./images/ -q 90

# Scale SVG (2x resolution)
./webp logo.svg --scale 2

# Keep directory structure in output
./webp ./images/ -r -o ./output/ --keep-structure
```

### All Options

| Option | Description |
|--------|-------------|
| `input` | Input file or directory (optional, defaults to `./input`) |
| `-o, --output` | Output directory (default: same as input, or `./output` in default mode) |
| `-q, --quality` | WebP quality 1-100 (default: 80) |
| `-r, --recursive` | Process directories recursively |
| `-s, --scale` | Scale factor for SVG conversion (default: 1.0) |
| `--keep-structure` | Maintain directory structure in output |
| `--no-delete` | Don't delete source files after conversion (default mode only) |

## Examples

```bash
# Convert all PNGs in current folder to WebP
./webp . 

# Convert with high quality
./webp photo.jpg -q 95

# Batch convert a website's images
./webp ./assets/images/ -r -o ./assets/webp/ --keep-structure

# Create retina-ready WebP from SVG
./webp icon.svg --scale 2 -o ./icons/
```

## Output

The converter provides detailed output:

**Default mode (auto-delete enabled):**
```
🔄 Running in default mode
   Input:  /path/to/webp-converter/input
   Output: /path/to/webp-converter/output
   ⚠️  Source files will be deleted after successful conversion

Found 3 image(s) to convert
Quality: 80%
--------------------------------------------------
  ✓ Converted & removed: logo.png → logo.webp (45.2KB → 12.1KB, -73.2%)
  ✓ Converted & removed: hero.svg → hero.webp (8.3KB → 15.4KB, +85.5%)
  ✗ Failed to convert broken.png: cannot identify image file
--------------------------------------------------
Done! Converted: 2, Failed: 1

⚠️  1 file(s) remain in input folder (conversion failed)
```

**Manual mode:**
```
Found 2 image(s) to convert
Quality: 80%
--------------------------------------------------
  ✓ Converted: photo.jpg → photo.webp (1.2MB → 89.5KB, -92.5%)
  ○ Already converted: icon.png
--------------------------------------------------
Done! Converted: 2, Failed: 0
```

## Tips

- **Quality**: For photos, 75-85 works well. For graphics/icons, try 85-95.
- **SVG Scaling**: Use `--scale 2` for retina displays.
- **Batch Processing**: Use `-r` to process all subdirectories at once.
