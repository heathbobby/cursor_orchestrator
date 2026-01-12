from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    success: bool
    message: str
    output_path: Path
    suggestions: list[str]


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


def _latest_index_for_iteration(tasks_dir: Path, iteration: str) -> Path | None:
    cands = sorted(tasks_dir.glob(f"*_{iteration}_INDEX.md"))
    return cands[-1] if cands else None


def evaluate_iteration(
    *,
    repo_root: Path,
    config: dict[str, Any] | None,
    iteration: str,
    dry_run: bool = False,
) -> EvaluationResult:
    """
    Heuristic evaluation that produces prompt/rules improvement suggestions.

    Output is written under `.orchestration/knowledge/evaluations/` (commit-able).
    """
    config = config or {}
    orchestration_cfg = config.get("orchestration") or {}
    commands_cfg = config.get("commands") or {}
    knowledge_cfg = config.get("knowledge") or {}
    coordination_cfg = config.get("coordination") or {}

    iterations_dir = repo_root / (orchestration_cfg.get("iterations_dir") or ".orchestration/runtime/iterations")
    it_dir = iterations_dir / iteration

    tasks_dir = repo_root / (commands_cfg.get("task_cards_dir") or ".orchestration/runtime/agent-sync/tasks")
    agent_sync_dir = repo_root / (coordination_cfg.get("agent_sync_dir") or ".orchestration/runtime/agent-sync")

    evals_dir = repo_root / (knowledge_cfg.get("evaluations_dir") or ".orchestration/knowledge/evaluations")
    evals_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_path = evals_dir / f"{iteration}_{stamp}.md"

    suggestions: list[str] = []

    ctx = _read_text(it_dir / "CONTEXT.md") or ""
    crit = _read_text(it_dir / "COMPLETION_CRITERIA.md") or ""

    if not it_dir.exists():
        suggestions.append("Iteration directory not found; ensure `/orchestrator::start_workflow` ran successfully.")
    if not ctx:
        suggestions.append("Missing or empty `CONTEXT.md`; improve workflow scaffold generation for this iteration.")
    if not crit:
        suggestions.append("Missing or empty `COMPLETION_CRITERIA.md`; add explicit completion criteria to workflow YAML.")

    idx = _latest_index_for_iteration(tasks_dir, iteration)
    if not idx:
        suggestions.append("No task index found for iteration; confirm task generation succeeded and `commands.task_cards_dir` is correct.")
    else:
        idx_text = _read_text(idx) or ""
        # Count task links
        links = re.findall(r"\]\(([^)]+\.md)\)", idx_text)
        task_links = [l for l in links if not l.endswith("_INDEX.md")]
        if len(task_links) == 0:
            suggestions.append("Task index has no linked task cards; task index formatting may need adjustment.")

        # Quick quality checks on task cards
        missing_sections = 0
        for fname in task_links[:30]:
            card_path = tasks_dir / fname
            card = _read_text(card_path) or ""
            if not card:
                missing_sections += 1
                continue
            for must in ("- **Role**:", "- **Work Item**:", "## Steps", "## Deliverables", "## Command to Start"):
                if must not in card:
                    missing_sections += 1
                    break
        if missing_sections:
            suggestions.append("Some task cards are missing expected sections; consider tightening task card template and validation.")

    # Memo hygiene checks
    try:
        from .memo_scanner import MemoScanner
    except ImportError:
        from memo_scanner import MemoScanner
    memos = MemoScanner(agent_sync_dir).scan_all()
    iteration_related = [m for m in memos if iteration in m.path.name or iteration in (_read_text(m.path) or "")]
    if not iteration_related:
        suggestions.append("No iteration-related memos detected; consider ensuring dispatch memo includes the iteration name and that agents post completion memos.")

    # Prompt/rules suggestions (concrete)
    concrete = []
    concrete.append("## Suggested Cursor rule updates\n")
    concrete.append("Consider adding (or updating) a Cursor rule that reinforces:\n")
    concrete.append("- Always post `ready-to-consume` memos with Branch+SHA")
    concrete.append("- Use `/orchestrator::archive_tasks(<iteration>)` after successful convergence to keep tasks clean")
    concrete.append("- Prefer worktrees for parallel roles\n")

    report = []
    report.append(f"# Iteration Evaluation: {iteration}\n")
    report.append(f"- **Generated at**: {datetime.utcnow().isoformat()}Z")
    report.append(f"- **Iteration dir**: `{it_dir.as_posix()}`")
    report.append(f"- **Tasks dir**: `{tasks_dir.as_posix()}`")
    report.append(f"- **Agent sync dir**: `{agent_sync_dir.as_posix()}`\n")

    report.append("## Findings\n")
    if suggestions:
        for s in suggestions:
            report.append(f"- {s}")
    else:
        report.append("- No obvious issues detected by heuristics.\n")

    report.append("\n## Context (excerpt)\n")
    report.append((ctx[:2000] + ("\n\n[TRUNCATED]\n" if len(ctx) > 2000 else "")) or "_No CONTEXT.md found._")

    report.append("\n## Completion Criteria (excerpt)\n")
    report.append((crit[:2000] + ("\n\n[TRUNCATED]\n" if len(crit) > 2000 else "")) or "_No COMPLETION_CRITERIA.md found._")

    report.append("\n" + "\n".join(concrete))

    if not dry_run:
        out_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    return EvaluationResult(
        success=True,
        message="Iteration evaluation generated" + (" (dry-run)" if dry_run else ""),
        output_path=out_path,
        suggestions=suggestions,
    )

