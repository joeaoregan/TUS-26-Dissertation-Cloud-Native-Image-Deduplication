# Evals Utils

Utility scripts and supporting assets used to prepare datasets and run evaluation prerequisites in a reproducible way.

## Contents

- `check_dataset_file_numbering.py`
- `robustness/`
  - `base/` (source images)
  - `generate_transforms.py`
  - `transform_manifest.csv` (generated)
  - transform output folders (generated, e.g. `brightness_*`, `contrast_*`, `jpeg_q*`, `resize_*`, etc.)

---

## `check_dataset_file_numbering.py`

Checks that files in a dataset directory are consecutively numbered based on a configurable filename pattern.

### Default behaviour

By default, the script validates files in:

- `data/base`

Using pattern components:

- prefix: `ILSVRC2012_val_`
- numeric width: `8`
- extension: `.JPEG`
- start index: `1`

So expected names look like:

`ILSVRC2012_val_00000001.JPEG`
`ILSVRC2012_val_00000002.JPEG`
`...`

### Usage

Run from repository root:

`python evals/utils/check_dataset_file_numbering.py`

### Useful options

- `--dir` dataset directory to scan
- `--prefix` filename prefix before numeric part
- `--ext` filename extension
- `--start` expected first number
- `--width` zero-padding width for numeric section
- `--case-insensitive-ext` allow extension case-insensitive matching

### Examples

Default check (`data/base`, ImageNet-style naming):

`python evals/utils/check_dataset_file_numbering.py`

Custom directory:

`python evals/utils/check_dataset_file_numbering.py --dir data/base`

Case-insensitive extension matching (e.g. `.JPEG`, `.jpeg`, `.Jpeg`):

`python evals/utils/check_dataset_file_numbering.py --case-insensitive-ext`

Different extension/padding/start:

`python evals/utils/check_dataset_file_numbering.py --dir data/base --prefix ILSVRC2012_val_ --ext .jpg --start 1 --width 8 --case-insensitive-ext`

### Exit codes

- `0` = OK (numbering is consecutive for matched files)
- `1` = numbering issues found (missing/duplicate/out-of-range)
- `2` = directory not found
- `3` = no files matched configured pattern

### Notes

- Non-matching files are reported separately and are not used for sequence checks.
- This tool is read-only (no file modifications).

---

## Robustness transform dataset generator (`robustness/`)

This directory contains base images and a script to generate transformed variants for robustness testing.

### Structure

- `robustness/base/`  
  Original source images (input set).
- `robustness/generate_transforms.py`  
  Bulk transform generator script.
- `robustness/transform_manifest.csv`  
  Auto-generated mapping of source image -> transformed output + transform parameters.
- `robustness/brightness_*`, `robustness/contrast_*`, `robustness/jpeg_q*`, `robustness/resize_*`, etc.  
  Auto-generated output folders.

### Purpose

The generated dataset is used to evaluate duplicate-detection robustness under photometric, geometric, compression, and format transformations.

### Prerequisites

Install Pillow:

`pip install pillow`

### Run

From repository root:

`python evals/utils/robustness/generate_transforms.py`

### Generated transform families

- Brightness (`0.85`, `1.15`)
- Contrast (`0.85`, `1.15`)
- Colour shift (`R+20`, `G+20`, `B+20`)
- JPEG recompression (`Q=90`, `75`, `60`)
- Resize (`0.75`, `0.50`)
- Centre crop (`0.90`, `0.75`)
- Rotation (`+2°`, `-2°`)
- PNG conversion

### Reproducibility notes

- Keep `robustness/base/` unchanged once experiments begin.
- Use `robustness/transform_manifest.csv` as the authoritative record of transformation provenance.
- If transform parameters are changed, regenerate outputs and archive previous manifest versions.