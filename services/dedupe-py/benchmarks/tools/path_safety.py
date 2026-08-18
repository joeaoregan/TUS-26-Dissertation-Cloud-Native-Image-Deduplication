from pathlib import Path


def resolve_within(base_dir: Path, user_input: str) -> Path:
    base = base_dir.resolve()
    target = Path(user_input)

    if not target.is_absolute():
        target = (base / target).resolve()
    else:
        target = target.resolve()

    if target != base and base not in target.parents:
        raise ValueError(f"Path escapes allowed directory: {user_input}")

    return target
