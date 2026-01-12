from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class KnowledgeUpdateResult:
    success: bool
    message: str
    knowledge_dir: Path
    written: list[str]


def _read_text(path: Path, max_chars: int = 200_000) -> str | None:
    try:
        if not path.exists() or not path.is_file():
            return None
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + "\n\n[TRUNCATED]\n"
        return text
    except Exception:
        return None


def _safe_dump_yaml(data: dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore
    except Exception:
        # Fallback: crude repr (still readable, but not ideal)
        return repr(data) + "\n"
    return yaml.safe_dump(data, sort_keys=False)


def update_knowledge_base(
    *,
    repo_root: Path,
    config: dict[str, Any] | None = None,
    iteration: str | None = None,
    dry_run: bool = False,
) -> KnowledgeUpdateResult:
    """
    Generate / refresh a lightweight, human-readable knowledgebase for the project.

    Writes to `.orchestration/knowledge/` by default (commit-able).
    """
    config = config or {}
    knowledge_cfg = config.get("knowledge") or {}
    orchestration_cfg = config.get("orchestration") or {}
    coordination_cfg = config.get("coordination") or {}

    knowledge_dir = repo_root / (knowledge_cfg.get("knowledge_dir") or ".orchestration/knowledge")
    kb_iters_dir = repo_root / (knowledge_cfg.get("iterations_dir") or ".orchestration/knowledge/iterations")
    agent_sync_dir = repo_root / (coordination_cfg.get("agent_sync_dir") or ".orchestration/runtime/agent-sync")
    iterations_dir = repo_root / (orchestration_cfg.get("iterations_dir") or ".orchestration/runtime/iterations")

    written: list[str] = []
    now = datetime.utcnow().isoformat() + "Z"

    # Build memo summary using MemoScanner
    try:
        from .memo_scanner import MemoScanner
    except ImportError:
        from memo_scanner import MemoScanner
    scanner = MemoScanner(agent_sync_dir)
    memos = scanner.scan_all()

    counts = {"draft": 0, "ready-to-consume": 0, "ready-to-merge": 0, "blocked": 0, "other": 0}
    for m in memos:
        s = (m.status or "").lower()
        if "ready-to-consume" in s:
            counts["ready-to-consume"] += 1
        elif "ready-to-merge" in s:
            counts["ready-to-merge"] += 1
        elif "blocked" in s:
            counts["blocked"] += 1
        elif "draft" in s:
            counts["draft"] += 1
        else:
            counts["other"] += 1

    readme = []
    readme.append("# Knowledgebase\n")
    readme.append("This folder is generated/maintained by `/orchestrator::update_knowledge`.\n")
    readme.append(f"- **Last updated**: {now}\n")
    readme.append("## What’s in here\n")
    readme.append("- `memos_summary.md`: current coordination memo status rollup")
    readme.append("- `iterations/`: generated iteration summaries (one file per iteration)\n")
    readme.append("## Source of truth\n")
    readme.append("- Runtime: `.orchestration/runtime/`")
    readme.append("- Config: `.orchestration/config/`")
    readme.append("- Cursor agent setup: `.cursor/`\n")

    memos_md = []
    memos_md.append("# Memo Summary\n")
    memos_md.append(f"- **Generated at**: {now}")
    memos_md.append(f"- **Agent sync dir**: `{agent_sync_dir.as_posix()}`\n")
    memos_md.append("## Status counts\n")
    for k in ("draft", "ready-to-consume", "ready-to-merge", "blocked", "other"):
        memos_md.append(f"- **{k}**: {counts[k]}")
    memos_md.append("\n## Recent memos\n")
    for m in sorted(memos, key=lambda x: (x.date or datetime.min), reverse=True)[:30]:
        memos_md.append(f"- `{m.path.name}` — **status**: `{m.status}`" + (f", **branch**: `{m.branch}`" if m.branch else ""))

    # Iteration summaries
    target_iterations: list[Path] = []
    if iteration:
        p = iterations_dir / iteration
        if p.exists():
            target_iterations = [p]
    else:
        if iterations_dir.exists():
            target_iterations = [p for p in sorted(iterations_dir.iterdir()) if p.is_dir()]

    iter_summaries: dict[str, str] = {}
    for it_dir in target_iterations:
        it_name = it_dir.name
        ctx_md = _read_text(it_dir / "CONTEXT.md") or ""
        crit_md = _read_text(it_dir / "COMPLETION_CRITERIA.md") or ""
        summary = []
        summary.append(f"# Iteration Summary: {it_name}\n")
        summary.append(f"- **Generated at**: {now}")
        summary.append(f"- **Iteration dir**: `{it_dir.as_posix()}`\n")
        if ctx_md:
            summary.append("## Context (excerpt)\n")
            summary.append(ctx_md[:4000] + ("\n\n[TRUNCATED]\n" if len(ctx_md) > 4000 else ""))
        if crit_md:
            summary.append("\n## Completion Criteria (excerpt)\n")
            summary.append(crit_md[:4000] + ("\n\n[TRUNCATED]\n" if len(crit_md) > 4000 else ""))
        iter_summaries[it_name] = "\n".join(summary) + "\n"

    if not dry_run:
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        kb_iters_dir.mkdir(parents=True, exist_ok=True)

        (knowledge_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
        written.append(str((knowledge_dir / "README.md").relative_to(repo_root)))

        (knowledge_dir / "memos_summary.md").write_text("\n".join(memos_md) + "\n", encoding="utf-8")
        written.append(str((knowledge_dir / "memos_summary.md").relative_to(repo_root)))

        for it_name, content in iter_summaries.items():
            out_path = kb_iters_dir / f"{it_name}.md"
            out_path.write_text(content, encoding="utf-8")
            written.append(str(out_path.relative_to(repo_root)))

        # Snapshot key config signals into knowledgebase for convenience (optional).
        cfg_dir = repo_root / ".orchestration" / "config"
        for p in ("project_profile.yaml", "derived_roles.yaml", "framework.yaml"):
            src = cfg_dir / p
            if src.exists():
                kb_copy = knowledge_dir / f"config_snapshot_{p}"
                kb_copy.write_text(_read_text(src) or "", encoding="utf-8")
                written.append(str(kb_copy.relative_to(repo_root)))

    return KnowledgeUpdateResult(
        success=True,
        message="Knowledgebase updated" + (" (dry-run)" if dry_run else ""),
        knowledge_dir=knowledge_dir,
        written=written,
    )

