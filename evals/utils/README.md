# Evals Utils

Utility scripts used to validate datasets and support evaluation runs.

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

```text
ILSVRC2012_val_00000001.JPEG
ILSVRC2012_val_00000002.JPEG
...
```

---

## Usage

Run from repository root:

```bash
python evals/utils/check_dataset_file_numbering.py
```

### Useful options

- `--dir` dataset directory to scan
- `--prefix` filename prefix before numeric part
- `--ext` filename extension
- `--start` expected first number
- `--width` zero-padding width for numeric section
- `--case-insensitive-ext` allow extension case-insensitive matching

### Examples

Default check (`data/base`, ImageNet-style naming):

```bash
python evals/utils/check_dataset_file_numbering.py
```

Custom directory:

```bash
python evals/utils/check_dataset_file_numbering.py --dir data/base
```

Case-insensitive extension matching (e.g. `.JPEG`, `.jpeg`, `.Jpeg`):

```bash
python evals/utils/check_dataset_file_numbering.py --case-insensitive-ext
```

Different extension/padding/start:

```bash
python evals/utils/check_dataset_file_numbering.py \
  --dir data/base \
  --prefix ILSVRC2012_val_ \
  --ext .jpg \
  --start 1 \
  --width 8 \
  --case-insensitive-ext
```

---

## Exit codes

- `0` = OK (numbering is consecutive for matched files)
- `1` = numbering issues found (missing/duplicate/out-of-range)
- `2` = directory not found
- `3` = no files matched configured pattern

---

## Notes

- Non-matching files are reported separately and are not used for sequence checks.
- This tool is read-only (no file modifications).