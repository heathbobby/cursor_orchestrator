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
    0) Prefer "installed framework" markers (bootstrapped projects may not be git repos)
    1) Try `git rev-parse --show-toplevel`
    2) Fallback: walk parents looking for a `.git/` directory
    3) Fallback: return `start` (or cwd) as-is
    """
    start_path = Path(start) if start else Path.cwd()

    # Prefer "installed framework" markers. This is important for scenarios like:
    # - running tests from within a mono-repo or nested folder that itself contains a `.git/`
    # - bootstrapped target projects that are not yet initialized as git repos
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        # Bootstrapped project root marker
        if (parent / "orchestration-framework" / "cli.py").exists():
            return parent
        if (parent / ".orchestration" / "config" / "framework.yaml").exists():
            return parent
        # Standalone framework repo marker
        if (parent / "cli.py").exists() and (parent / "tools").exists() and (parent / "bootstrap.py").exists():
            return parent

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
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent

    return start_path.resolve()

