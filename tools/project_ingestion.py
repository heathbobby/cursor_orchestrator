from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IngestionResult:
    profile: dict[str, Any]
    profile_path: Path
    context_md: str
    context_path: Path


def _read_text_if_exists(path: Path, limit: int = 200_000) -> str | None:
    try:
        if not path.exists() or not path.is_file():
            return None
        data = path.read_text(encoding="utf-8", errors="replace")
        if len(data) > limit:
            return data[:limit] + "\n\n[TRUNCATED]\n"
        return data
    except Exception:
        return None


def _detect_from_package_json(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"present": False}
    raw = _read_text_if_exists(path)
    if not raw:
        return out
    try:
        pkg = json.loads(raw)
    except Exception:
        return {"present": True, "parse_error": True}

    deps = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        if isinstance(pkg.get(k), dict):
            deps.update(pkg.get(k) or {})

    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    out = {
        "present": True,
        "name": pkg.get("name"),
        "type": pkg.get("type"),
        "scripts": scripts,
        "deps": sorted(list(deps.keys()))[:200],  # cap for readability
    }

    # Light framework hints
    hints = []
    for fw in ("next", "react", "vue", "svelte", "express", "nestjs", "fastify", "electron"):
        if fw in deps:
            hints.append(fw)
    if hints:
        out["framework_hints"] = sorted(hints)

    return out


def build_project_profile(repo_root: Path, scope: Path | None = None) -> dict[str, Any]:
    """
    Lightweight, dependency-free project scan that produces a small YAML profile.
    Keep it fast: we only look for common "signal files".
    """
    scope = (scope or repo_root).resolve()
    root = repo_root.resolve()

    # Signal files (repo root first)
    signals = {
        "package_json": root / "package.json",
        "requirements_txt": root / "requirements.txt",
        "pyproject_toml": root / "pyproject.toml",
        "poetry_lock": root / "poetry.lock",
        "pipfile": root / "Pipfile",
        "go_mod": root / "go.mod",
        "cargo_toml": root / "Cargo.toml",
        "pom_xml": root / "pom.xml",
        "build_gradle": root / "build.gradle",
        "makefile": root / "Makefile",
        "dockerfile": root / "Dockerfile",
        "compose": root / "docker-compose.yml",
        "github_workflows": root / ".github" / "workflows",
    }

    present = {k: str(p.relative_to(root)) for k, p in signals.items() if p.exists()}

    languages: list[str] = []
    if signals["package_json"].exists():
        languages.append("javascript/typescript")
    if signals["requirements_txt"].exists() or signals["pyproject_toml"].exists() or signals["pipfile"].exists():
        languages.append("python")
    if signals["go_mod"].exists():
        languages.append("go")
    if signals["cargo_toml"].exists():
        languages.append("rust")
    if signals["pom_xml"].exists() or signals["build_gradle"].exists():
        languages.append("java")

    package_managers: list[str] = []
    if signals["package_json"].exists():
        if (root / "pnpm-lock.yaml").exists():
            package_managers.append("pnpm")
        elif (root / "yarn.lock").exists():
            package_managers.append("yarn")
        elif (root / "package-lock.json").exists():
            package_managers.append("npm")
        else:
            package_managers.append("npm (unknown lockfile)")
    if signals["pyproject_toml"].exists():
        if signals["poetry_lock"].exists():
            package_managers.append("poetry")
        else:
            package_managers.append("python (pyproject)")
    if signals["requirements_txt"].exists():
        package_managers.append("pip")

    ci: list[str] = []
    if signals["github_workflows"].exists() and signals["github_workflows"].is_dir():
        ci.append("github-actions")

    containerization: list[str] = []
    if signals["dockerfile"].exists():
        containerization.append("docker")
    if signals["compose"].exists():
        containerization.append("docker-compose")

    node = _detect_from_package_json(signals["package_json"])

    suggested_commands: dict[str, str] = {}
    if node.get("present") and isinstance(node.get("scripts"), dict):
        scripts = node["scripts"]
        for k in ("test", "lint", "build", "dev", "start"):
            if k in scripts:
                suggested_commands[k] = f"npm run {k}"
    # Python heuristics
    req = _read_text_if_exists(signals["requirements_txt"]) or ""
    if "pytest" in req.lower():
        suggested_commands.setdefault("test", "pytest")
    if "ruff" in req.lower():
        suggested_commands.setdefault("lint", "ruff check .")

    profile: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "repo_root": str(root),
        "scope": str(scope),
        "signals_present": present,
        "languages": sorted(set(languages)),
        "package_managers": sorted(set(package_managers)),
        "ci": sorted(set(ci)),
        "containerization": sorted(set(containerization)),
        "node": node,
        "suggested_commands": suggested_commands,
    }

    return profile


def build_project_context_md(profile: dict[str, Any]) -> str:
    languages = profile.get("languages") or []
    package_managers = profile.get("package_managers") or []
    ci = profile.get("ci") or []
    containerization = profile.get("containerization") or []
    cmds = profile.get("suggested_commands") or {}
    signals = profile.get("signals_present") or {}

    lines = []
    lines.append("# Project Context (Generated)\n")
    lines.append("This file is generated by `/orchestrator::ingest_project`.\n")
    lines.append("## What this repo looks like\n")
    lines.append(f"- **Languages**: {', '.join(languages) if languages else 'unknown'}")
    lines.append(f"- **Package managers**: {', '.join(package_managers) if package_managers else 'unknown'}")
    lines.append(f"- **CI**: {', '.join(ci) if ci else 'none detected'}")
    lines.append(f"- **Containerization**: {', '.join(containerization) if containerization else 'none detected'}\n")

    if signals:
        lines.append("## Signal files detected\n")
        for k, v in sorted(signals.items()):
            lines.append(f"- **{k}**: `{v}`")
        lines.append("")

    if cmds:
        lines.append("## Suggested commands\n")
        for k, v in sorted(cmds.items()):
            lines.append(f"- **{k}**: `{v}`")
        lines.append("")

    lines.append("## Orchestration locations\n")
    lines.append("- **Config (commit)**: `.orchestration/config/`")
    lines.append("- **Runtime (do not commit)**: `.orchestration/runtime/`")
    lines.append("- **Cursor agent config (commit)**: `.cursor/`\n")

    lines.append("## Agent operating notes\n")
    lines.append("- Prefer isolated worktrees/branches per agent when running in parallel.")
    lines.append("- Post `ready-to-consume` memos in `.orchestration/runtime/agent-sync/` for integration.")
    return "\n".join(lines) + "\n"


def ingest_project(
    repo_root: Path,
    config: dict[str, Any] | None = None,
    path: str | None = None,
    dry_run: bool = False,
) -> IngestionResult:
    config = config or {}
    orch = (config.get("orchestration") or {})
    config_dir = repo_root / ".orchestration" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    scope = (repo_root / path).resolve() if path else None
    profile = build_project_profile(repo_root, scope=scope)
    context_md = build_project_context_md(profile)

    profile_path = config_dir / "project_profile.yaml"
    context_path = config_dir / "PROJECT_CONTEXT.md"

    if not dry_run:
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError(f"PyYAML is required to write project_profile.yaml: {e}")
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        context_path.write_text(context_md, encoding="utf-8")

    return IngestionResult(
        profile=profile,
        profile_path=profile_path,
        context_md=context_md,
        context_path=context_path,
    )

