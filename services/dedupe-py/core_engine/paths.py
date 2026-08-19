from __future__ import annotations

import os
from pathlib import Path


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def get_repo_root() -> Path:
    """
    Assumes this file is at: services/dedupe-py/core_engine/paths.py
    repo root => parents[3]
    """
    return Path(__file__).resolve().parents[3]


def get_data_root() -> Path:
    """
    Runtime data root:
    1) DATA_ROOT env (if set)
    2) /app/data (container default)
    3) <repo>/data (local default)
    """
    env = os.getenv("DATA_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    candidates = [
        Path("/app/data"),
        get_repo_root() / "data",
    ]
    found = _first_existing(candidates)
    return found if found else candidates[-1]


def get_test_data_dir() -> Path:
    """
    Test data root:
    1) TEST_DATA_DIR env (if set)
    2) DATA_ROOT env (if set)
    3) /app/data
    4) <repo>/data
    """
    test_env = os.getenv("TEST_DATA_DIR")
    if test_env:
        return Path(test_env).expanduser().resolve()

    data_env = os.getenv("DATA_ROOT")
    if data_env:
        return Path(data_env).expanduser().resolve()

    candidates = [
        Path("/app/data"),
        get_repo_root() / "data",
    ]
    found = _first_existing(candidates)
    return found if found else candidates[-1]
