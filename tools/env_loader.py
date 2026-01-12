from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DotenvLoadResult:
    loaded: bool
    path: Path
    keys_set: list[str]


def load_dotenv(path: Path, *, override: bool = False) -> DotenvLoadResult:
    """
    Minimal `.env` loader (stdlib-only).

    Supports lines like:
      KEY=value
      KEY="value"
      export KEY=value
    Ignores blank lines and comments starting with '#'.

    Notes:
    - Does NOT try to fully emulate python-dotenv.
    - Does NOT override existing environment variables unless override=True.
    """
    path = Path(path)
    if not path.exists() or not path.is_file():
        return DotenvLoadResult(loaded=False, path=path, keys_set=[])

    keys_set: list[str] = []
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if not key:
                continue
            # Strip quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if (not override) and (key in os.environ):
                continue
            os.environ[key] = val
            keys_set.append(key)
    except Exception:
        return DotenvLoadResult(loaded=False, path=path, keys_set=[])

    return DotenvLoadResult(loaded=True, path=path, keys_set=keys_set)


def find_dotenv(start: Path, *, filename: str = ".env", max_depth: int = 8) -> Path | None:
    """
    Walk upward from `start` looking for a dotenv file.

    This is useful in test/mono-repo layouts where the "project root" (repo_root)
    may not be where the operator placed `.env`.
    """
    start = Path(start).resolve()
    current = start
    for _ in range(max_depth + 1):
        candidate = current / filename
        if candidate.exists() and candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def load_dotenv_searching_parents(start: Path, *, filename: str = ".env", max_depth: int = 8, override: bool = False) -> DotenvLoadResult:
    """
    Find and load a dotenv file by searching upward from `start`.
    """
    found = find_dotenv(start, filename=filename, max_depth=max_depth)
    if not found:
        return DotenvLoadResult(loaded=False, path=Path(start).resolve() / filename, keys_set=[])
    return load_dotenv(found, override=override)

