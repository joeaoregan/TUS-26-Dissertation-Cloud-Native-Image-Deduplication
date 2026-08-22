# Robustness Transform Dataset Generator

This directory contains base images and a script to generate transformed variants for robustness testing.

## Structure

- `base/`  
  Original source images (input set).
- `generate_transforms.py`  
  Bulk transform generator script.
- `transform_manifest.csv`  
  Auto-generated mapping of source image -> transformed output + transform parameters.
- `brightness_*`, `contrast_*`, `jpeg_q*`, `resize_*`, etc.  
  Auto-generated output folders.

## Purpose

The generated dataset is used to evaluate duplicate-detection robustness under photometric, geometric, compression, and format transformations.

## Prerequisites

Install Pillow:

```bash
pip install pillow
```

## Run

From repository root:

```bash
python data/robustness/generate_transforms.py
```

## Generated transform families

- Brightness (`0.85`, `1.15`)
- Contrast (`0.85`, `1.15`)
- Colour shift (`R+20`, `G+20`, `B+20`)
- JPEG recompression (`Q=90`, `75`, `60`)
- Resize (`0.75`, `0.50`)
- Centre crop (`0.90`, `0.75`)
- Rotation (`+2°`, `-2°`)
- PNG conversion

## Reproducibility notes

- Keep `base/` unchanged once experiments begin.
- Use `transform_manifest.csv` as the authoritative record of transformation provenance.
- If transform parameters are changed, regenerate outputs and archive previous manifest versions.