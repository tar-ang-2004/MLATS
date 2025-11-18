
from __future__ import annotations

import argparse
import io
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from PIL import Image

try:
    import filetype
except Exception:
    filetype = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def detect_image_extension_from_bytes(b: bytes) -> str:
    """Return a file extension (without dot) guessed from bytes, or 'bin'."""
    # Try Pillow first (more robust and available in requirements)
    try:
        img = Image.open(io.BytesIO(b))
        fmt = getattr(img, "format", None)
        if fmt:
            ext = fmt.lower()
            if ext == "jpeg":
                return "jpg"
            return ext
    except Exception:
        pass

    # Fallback to filetype package if available
    if filetype is not None:
        kind = filetype.guess(b)
        if kind is not None:
            return kind.extension

    return "bin"


def save_bytes(data: bytes, out_path: Path) -> Path:
    ensure_dir(out_path.parent)
    ext = detect_image_extension_from_bytes(data)
    if ext == "bin":
        fname = out_path.with_suffix(".bin")
    else:
        fname = out_path.with_suffix(f".{ext}")
    with open(fname, "wb") as f:
        f.write(data)
    return fname


def save_array_as_image(arr: np.ndarray, out_path: Path) -> Optional[Path]:
    """Try to save a numeric array as an image. Returns path or None if not suitable."""
    arr = np.asarray(arr)
    if arr.size == 0:
        return None

    # If 1D, can't easily form an image — save as .npy instead
    if arr.ndim == 1:
        np.save(out_path.with_suffix(".npy"), arr)
        return out_path.with_suffix(".npy")

    # If values are floats in range 0-1, scale up
    if np.issubdtype(arr.dtype, np.floating):
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)

    if arr.ndim == 2:
        pil = Image.fromarray(arr)
        ensure_dir(out_path.parent)
        path = out_path.with_suffix(".png")
        pil.save(path)
        return path

    if arr.ndim == 3:
        # Expect HxWxC where C is 1,3,4
        c = arr.shape[2]
        if c in (1, 3, 4):
            pil = Image.fromarray(arr.astype(np.uint8))
            ensure_dir(out_path.parent)
            path = out_path.with_suffix(".png")
            pil.save(path)
            return path

    # Otherwise fallback to saving numpy file
    np.save(out_path.with_suffix(".npy"), arr)
    return out_path.with_suffix(".npy")


def process_parquet_file(parquet_path: Path, out_base: Path) -> None:
    logger.info("Processing %s", parquet_path)
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        logger.error("Failed to read %s: %s", parquet_path, e)
        return

    file_stem = parquet_path.stem
    out_dir = out_base / file_stem
    ensure_dir(out_dir)

    summary_rows = []

    for idx, row in df.iterrows():
        # Keep a per-row subdir
        row_subdir = out_dir / f"row_{idx}"
        ensure_dir(row_subdir)

        for col in df.columns:
            val = row[col]
            saved = None
            try:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    # skip
                    continue

                # bytes-like
                if isinstance(val, (bytes, bytearray)):
                    out_path = row_subdir / f"{col}"
                    saved = save_bytes(bytes(val), out_path)

                # numpy array
                elif isinstance(val, np.ndarray):
                    out_path = row_subdir / f"{col}"
                    saved = save_array_as_image(val, out_path)

                # list/tuple of numbers -> try convert to array
                elif isinstance(val, (list, tuple)):
                    try:
                        arr = np.asarray(val)
                        out_path = row_subdir / f"{col}"
                        saved = save_array_as_image(arr, out_path)
                    except Exception:
                        # dump to .txt
                        p = row_subdir / f"{col}.txt"
                        p.write_text(str(val), encoding="utf-8")
                        saved = p

                # pandas-supported binary types (like memoryview)
                elif hasattr(val, "tobytes") and not isinstance(val, str):
                    try:
                        b = val.tobytes()
                        out_path = row_subdir / f"{col}"
                        saved = save_bytes(b, out_path)
                    except Exception:
                        # fallback to string
                        p = row_subdir / f"{col}.txt"
                        p.write_text(str(val), encoding="utf-8")
                        saved = p

                # strings / scalars: save to text file (small)
                else:
                    p = row_subdir / f"{col}.txt"
                    try:
                        p.write_text(str(val), encoding="utf-8")
                        saved = p
                    except Exception:
                        # last resort: repr
                        p.write_text(repr(val), encoding="utf-8")
                        saved = p

            except Exception as e:
                logger.debug("Failed to save column %s in row %s: %s", col, idx, e)

            summary_rows.append({
                "parquet": parquet_path.name,
                "row_index": idx,
                "column": col,
                "saved_path": str(saved) if saved is not None else "",
            })

    # write summary CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = out_dir / f"{file_stem}_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    logger.info("Wrote summary %s", summary_csv)


def process_input_dirs(input_dirs: list[str], out_dir: Path) -> None:
    cwd = Path('.').resolve()
    seen: set[Path] = set()

    for d in input_dirs:
        p = Path(d)
        candidates = []

        if p.exists():
            # If p is a single parquet file
            if p.is_file() and p.suffix == ".parquet":
                candidates.append(p)
            # If p is a directory, take its parquet files
            elif p.is_dir():
                candidates.extend(sorted(p.glob("*.parquet")))
        else:
            # Try common patterns at repo root (train-*.parquet, test-*.parquet)
            candidates.extend(sorted(cwd.glob(f"{d}-*.parquet")))
            candidates.extend(sorted(cwd.glob(f"{d}*.parquet")))
            # If explicitly asked for '.', include all parquet files in cwd
            if d in (".", "./"):
                candidates.extend(sorted(cwd.glob("*.parquet")))

        for parquet in candidates:
            try:
                parquet = parquet.resolve()
            except Exception:
                continue
            if parquet in seen:
                continue
            seen.add(parquet)

            # determine dataset folder name (prefer train/test by filename)
            name = "root"
            lname = parquet.name.lower()
            if lname.startswith("train"):
                name = "train"
            elif lname.startswith("test"):
                name = "test"
            else:
                # fallback to parent folder name if not root
                if parquet.parent != cwd:
                    name = parquet.parent.name

            out_base = out_dir / name
            ensure_dir(out_base)
            process_parquet_file(parquet, out_base)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Extract files from parquet datasets")
    ap.add_argument("--input-dirs", nargs="+", default=["train", "test"],
                    help="One or more input directories containing .parquet files (default: train test)")
    ap.add_argument("--out-dir", default="extracted",
                    help="Base output directory (default: extracted)")
    ap.add_argument("--verbose", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    process_input_dirs(args.input_dirs, out_dir)
    logger.info("Done. Extracted content is under %s", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
