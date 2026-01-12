from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DerivedRolesResult:
    derived: dict[str, Any]
    derived_path: Path
    cursor_rule_path: Path | None


def _has_any(haystack: list[str], needles: list[str]) -> bool:
    s = set(haystack or [])
    return any(n in s for n in needles)


def derive_roles_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    languages = profile.get("languages") or []
    node = profile.get("node") or {}
    framework_hints = node.get("framework_hints") or []
    containerization = profile.get("containerization") or []
    ci = profile.get("ci") or []

    roles: list[dict[str, Any]] = []

    def add(role: str, why: str) -> None:
        roles.append({"role": role, "why": why})

    # Baseline roles that are almost always useful.
    add("backend_developer", "Core implementation work (APIs, services, scripts).")
    add("qa_engineer", "Tests, validation, reproduction steps, and quality gates.")
    add("tech_writer", "Docs, runbooks, and user-facing guidance.")

    # Frontend specialization if we see typical frontend frameworks.
    if _has_any(framework_hints, ["react", "next", "vue", "svelte"]):
        add("frontend_developer", f"UI work detected via Node framework hints: {', '.join(sorted(framework_hints))}.")

    # Infra/SRE specialization if we see containerization/CI.
    if containerization or ci:
        add("sre", "CI/containerization signals detected; ops/runbooks and pipeline support are likely needed.")

    # Slightly different emphasis for pure Python repos.
    if languages == ["python"]:
        add("python_backend_developer", "Python-only repo detected; specialization can improve speed and correctness.")

    # Deduplicate by role name, preserving first rationale.
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for r in roles:
        if r["role"] in seen:
            continue
        seen.add(r["role"])
        deduped.append(r)

    return {
        "generated_at": profile.get("generated_at"),
        "languages": languages,
        "node_framework_hints": framework_hints,
        "containerization": containerization,
        "ci": ci,
        "recommended_roles": deduped,
        "notes": [
            "This is a recommendation only. Wire these roles into your workflows under `.orchestration/config/workflows/`.",
            "Keep role-specific Cursor rules small and focused; avoid duplicating large framework docs into the target repo.",
        ],
    }


def _render_cursor_rule(derived: dict[str, Any]) -> str:
    roles = derived.get("recommended_roles") or []
    lines: list[str] = []
    lines.append("---")
    lines.append("description: Derived recommended agent roles for this project")
    lines.append("---\n")
    lines.append("## Recommended agent roles (derived)\n")
    lines.append("These roles were derived from a lightweight project scan.\n")
    for r in roles:
        lines.append(f"- **{r.get('role')}**: {r.get('why')}")
    lines.append("")
    lines.append("If you adopt these roles, ensure your workflows reference them and your worktree naming matches role.")
    return "\n".join(lines) + "\n"


def write_derived_roles(
    repo_root: Path,
    derived: dict[str, Any],
    config: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> DerivedRolesResult:
    config = config or {}
    config_dir = repo_root / ".orchestration" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    derived_path = config_dir / "derived_roles.yaml"
    cursor_rule_path: Path | None = None

    if not dry_run:
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError(f"PyYAML is required to write derived_roles.yaml: {e}")
        derived_path.write_text(yaml.safe_dump(derived, sort_keys=False), encoding="utf-8")

        cursor_cfg = config.get("cursor") or {}
        if bool(cursor_cfg.get("enabled")):
            rules_dir = repo_root / (cursor_cfg.get("rules_dir") or ".cursor/rules")
            rules_dir.mkdir(parents=True, exist_ok=True)
            cursor_rule_path = rules_dir / "30-derived-roles.mdc"
            cursor_rule_path.write_text(_render_cursor_rule(derived), encoding="utf-8")

    return DerivedRolesResult(derived=derived, derived_path=derived_path, cursor_rule_path=cursor_rule_path)

