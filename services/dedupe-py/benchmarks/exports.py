from pathlib import Path

DATA_ROOT = Path("data").resolve()


def short_path(p: str) -> str:
    x = Path(p).resolve()
    try:
        return x.relative_to(DATA_ROOT).as_posix()  # e.g. dedupe_test_100/img1.jpg
    except ValueError:
        return x.name  # fallback: filename only


def export_stage1_groups(stage1_result: dict, limit: int) -> list[dict]:
    groups = []
    for digest, paths in stage1_result.items():
        if len(paths) > 1:
            groups.append(
                {
                    "sha256": digest,
                    "files": [short_path(str(p)) for p in paths],
                    "group_size": len(paths),
                    "redundant_files": len(paths) - 1,
                }
            )
    groups.sort(key=lambda g: g["group_size"], reverse=True)
    return groups[:limit]


def export_stage2_candidates(candidates: list[tuple], limit: int) -> list[dict]:
    out = []
    for p1, p2, distance in candidates[:limit]:
        a = short_path(str(p1))
        b = short_path(str(p2))
        out.append(
            {
                "file_a": a,
                "file_b": b,
                "phash_distance": int(distance),
            }
        )
    return out


def export_stage3_verified(verified: list[tuple], limit: int) -> list[dict]:
    out = []
    for p1, p2, score in verified[:limit]:
        out.append(
            {
                "file_a": short_path(str(p1)),
                "file_b": short_path(str(p2)),
                "ssim_score": round(float(score), 6),
            }
        )
    return out
