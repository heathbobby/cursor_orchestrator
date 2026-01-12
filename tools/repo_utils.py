#!/usr/bin/env python3
"""
Repository utilities for the Generic Orchestration Framework.

These helpers make the CLI usable from any working directory by
deriving a stable repo root.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """
    Find the git repository root.

    Strategy:
    1) Try `git rev-parse --show-toplevel`
    2) Fallback: walk parents looking for a `.git/` directory
    3) Fallback: return `start` (or cwd) as-is
    """
    start_path = Path(start) if start else Path.cwd()

    # Try git plumbing first (most reliable).
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start_path,
            check=True,
            capture_output=True,
            text=True,
        )
        top = result.stdout.strip()
        if top:
            return Path(top)
    except Exception:
        pass

    # Fallback: detect `.git` by walking upward.
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent

    return start_path.resolve()

