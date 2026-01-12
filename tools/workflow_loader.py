#!/usr/bin/env python3
"""
Workflow loading and normalization.

We support two on-disk formats:
1) Catalog-style:
   workflow:
     name: ...
     phases: ...
2) Simple config style:
   name: ...
   phases: ...

This module normalizes both into:
{
  "name": str,
  "description": str|None,
  "phases": [
     {"id": str, "name": str|None, "iterations": [ ... ] }
  ]
}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_workflow_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError(
            f"PyYAML is required to load workflow YAML ({path}). "
            f"Install dependencies (e.g. `pip install -r requirements.txt`). Error: {e}"
        )

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Workflow file must be a YAML mapping/object: {path}")

    # Accept both formats: top-level "workflow:" or direct.
    wf = data.get("workflow") if "workflow" in data else data
    if not isinstance(wf, dict):
        raise ValueError(f"Workflow file has invalid structure (expected mapping): {path}")

    name = wf.get("name") or wf.get("id") or path.stem
    phases = wf.get("phases") or []
    if not isinstance(phases, list):
        raise ValueError(f"Workflow phases must be a list: {path}")

    normalized_phases: list[dict[str, Any]] = []
    for p in phases:
        if not isinstance(p, dict):
            continue
        phase_id = p.get("id") or p.get("phase") or p.get("name")
        iterations = p.get("iterations") or []
        if not isinstance(iterations, list):
            iterations = []
        normalized_phases.append(
            {
                "id": str(phase_id) if phase_id else "phase",
                "name": p.get("name"),
                "description": p.get("description") or p.get("goal"),
                "iterations": iterations,
            }
        )

    return {
        "name": name,
        "description": wf.get("description"),
        "phases": normalized_phases,
        "_path": str(path),
    }


def find_iteration(workflow: dict[str, Any], phase_id: str, iteration_id: str) -> dict[str, Any]:
    """Find a specific iteration config by phase id + iteration id/name."""
    for p in workflow.get("phases", []):
        if str(p.get("id")) != phase_id:
            continue
        for it in p.get("iterations", []):
            if not isinstance(it, dict):
                continue
            it_id = it.get("id") or it.get("name")
            if str(it_id) == iteration_id:
                return it
    raise KeyError(f"Iteration not found: phase={phase_id}, iteration={iteration_id}")

