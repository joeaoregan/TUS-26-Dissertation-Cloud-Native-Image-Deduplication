from pathlib import Path

import pytest

from benchmarks.tools.path_safety import resolve_within


def test_resolve_within_allows_relative_path(tmp_path: Path):
    result = resolve_within(tmp_path, "benchmarks/results.json")
    expected = (tmp_path / "benchmarks" / "results.json").resolve()
    assert result == expected


def test_resolve_within_allows_absolute_path_inside_base(tmp_path: Path):
    inside = (tmp_path / "data" / "input").resolve()
    result = resolve_within(tmp_path, str(inside))
    assert result == inside


def test_resolve_within_blocks_parent_traversal(tmp_path: Path):
    with pytest.raises(ValueError, match="Path escapes allowed directory"):
        resolve_within(tmp_path, "../../evil.json")


def test_resolve_within_blocks_absolute_path_outside_base(tmp_path: Path):
    if Path("/").exists():
        outside = Path("/tmp/evil.json")
    else:
        outside = Path("C:/evil.json")

    outside = outside.resolve()
    if outside == tmp_path.resolve() or tmp_path.resolve() in outside.parents:
        pytest.skip("Could not construct an outside path on this platform")

    with pytest.raises(ValueError, match="Path escapes allowed directory"):
        resolve_within(tmp_path, str(outside))


def test_resolve_within_allows_base_dir_itself(tmp_path: Path):
    result = resolve_within(tmp_path, ".")
    assert result == tmp_path.resolve()
