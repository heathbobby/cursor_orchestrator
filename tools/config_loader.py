#!/usr/bin/env python3
"""
Configuration loading for the Generic Orchestration Framework.

We intentionally keep this lightweight: a single YAML file is loaded (if present),
otherwise sane defaults are used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def default_config() -> dict[str, Any]:
    """Return a minimal default configuration."""
    return {
        "project": {"name": "GenericProject", "trunk_branch": "main"},
        "coordination": {"agent_sync_dir": ".orchestration/runtime/agent-sync"},
        "worktrees": {"enabled": True, "location": None, "branch_prefix": "feat"},
        "orchestration": {
            "workflows_dir": ".orchestration/config/workflows",
            "iterations_dir": ".orchestration/runtime/iterations",
            "work_items_dir": "work_items",
            "framework_dir": "orchestration-framework",
            "allow_auto_apply_ready": False,
        },
        "integration": {"target_branch_pattern": "integration/{date}", "auto_merge_to_trunk": False},
        "commands": {
            "task_cards_dir": ".orchestration/runtime/agent-sync/tasks",
            "task_archive_dir": ".orchestration/runtime/agent-sync/tasks/_archive",
        },
        "knowledge": {
            "knowledge_dir": ".orchestration/knowledge",
            "evaluations_dir": ".orchestration/knowledge/evaluations",
            "iterations_dir": ".orchestration/knowledge/iterations",
        },
        "status": {
            "status_dir": ".orchestration/runtime/status",
        },
        "cursor": {
            "enabled": False,
            "auto_open_worktrees": False,
            "cli_command": "cursor",
            "open_args": [],
            # Cursor CLI (terminal agent) integration. See: https://cursor.com/docs/cli/overview
            "agent_command": "agent",
            "agent_runner_prefix": [],
            "agent_model": None,
            "agent_output_format": "text",
            "agent_extra_args": [],
            "agent_max_parallel": 1,
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base (override wins)."""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def find_config_path(repo_root: Path) -> Path | None:
    """
    Find a config file.

    Order matters:
    1) <repo_root>/orchestration-framework/config.yaml  (installed into another project)
    2) <repo_root>/config.yaml                          (standalone repo)
    """
    candidates = [
        repo_root / ".orchestration" / "config" / "framework.yaml",
        repo_root / ".orchestration" / "config" / "config.yaml",
        repo_root / "orchestration-framework" / "config.yaml",
        repo_root / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_config(repo_root: Path) -> dict[str, Any]:
    """
    Load YAML config if present, else return defaults.

    Requires PyYAML at runtime if a YAML file exists.
    """
    cfg = default_config()

    path = find_config_path(repo_root)
    if not path:
        return cfg

    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError(
            f"Config file exists at {path} but PyYAML is not installed. "
            f"Install dependencies (e.g. `pip install -r requirements.txt`). Error: {e}"
        )

    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config at {path} must be a YAML mapping/object.")

    cfg = _deep_merge(cfg, loaded)
    cfg["_config_path"] = str(path)
    return cfg

