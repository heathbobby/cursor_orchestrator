from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StatusRenderResult:
    success: bool
    message: str
    markdown_path: Path
    html_path: Path


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_status(
    *,
    repo_root: Path,
    config: dict[str, Any] | None,
    iteration: str | None = None,
    dry_run: bool = False,
) -> StatusRenderResult:
    config = config or {}
    orchestration_cfg = config.get("orchestration") or {}
    coordination_cfg = config.get("coordination") or {}
    commands_cfg = config.get("commands") or {}
    status_cfg = config.get("status") or {}

    agent_sync_dir = repo_root / (coordination_cfg.get("agent_sync_dir") or ".orchestration/runtime/agent-sync")
    iterations_dir = repo_root / (orchestration_cfg.get("iterations_dir") or ".orchestration/runtime/iterations")
    tasks_dir = repo_root / (commands_cfg.get("task_cards_dir") or ".orchestration/runtime/agent-sync/tasks")
    status_dir = repo_root / (status_cfg.get("status_dir") or ".orchestration/runtime/status")

    now = datetime.utcnow().isoformat() + "Z"

    # Determine which iterations to report
    iter_dirs: list[Path] = []
    if iteration:
        p = iterations_dir / iteration
        if p.exists():
            iter_dirs = [p]
    else:
        if iterations_dir.exists():
            iter_dirs = [p for p in sorted(iterations_dir.iterdir()) if p.is_dir()]

    # Memo scan
    try:
        from .memo_scanner import MemoScanner
    except ImportError:
        from memo_scanner import MemoScanner
    memos = MemoScanner(agent_sync_dir).scan_all()

    def _count(pred) -> int:
        return sum(1 for m in memos if pred(m))

    counts = {
        "draft": _count(lambda m: m.is_draft),
        "ready_to_consume": _count(lambda m: m.is_ready_to_consume),
        "ready_to_merge": _count(lambda m: m.is_ready_to_merge),
        "blocked": _count(lambda m: m.is_blocked),
        "total": len(memos),
    }

    # Task indices
    idx_files = sorted(tasks_dir.glob("*_INDEX.md")) if tasks_dir.exists() else []
    latest_idx = idx_files[-1] if idx_files else None

    md = []
    md.append("# Orchestration Status\n")
    md.append(f"- **Generated at**: {now}")
    md.append(f"- **Repo root**: `{repo_root.as_posix()}`\n")

    md.append("## Memo status\n")
    md.append(f"- **total**: {counts['total']}")
    md.append(f"- **draft**: {counts['draft']}")
    md.append(f"- **ready-to-consume**: {counts['ready_to_consume']}")
    md.append(f"- **ready-to-merge**: {counts['ready_to_merge']}")
    md.append(f"- **blocked**: {counts['blocked']}\n")

    md.append("## Iterations\n")
    if not iter_dirs:
        md.append("- (none found)\n")
    else:
        for it in iter_dirs[-20:]:
            md.append(f"- `{it.name}`")
        md.append("")

    md.append("## Tasks\n")
    md.append(f"- **tasks_dir**: `{tasks_dir.as_posix()}`")
    md.append(f"- **index_files**: {len(idx_files)}")
    if latest_idx:
        md.append(f"- **latest_index**: `{latest_idx.name}`")
    md.append("")

    md.append("## Recent memos\n")
    for m in sorted(memos, key=lambda x: (x.date or datetime.min), reverse=True)[:10]:
        md.append(f"- `{m.path.name}` — `{m.status}`")
    md.append("")

    md_text = "\n".join(md) + "\n"

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Orchestration Status</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }}
    pre {{ background: #0b1020; color: #e6edf3; padding: 16px; border-radius: 8px; overflow-x: auto; }}
    h1 {{ margin-bottom: 8px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>Orchestration Status</h1>
  <div class="meta">Generated at { _html_escape(now) }</div>
  <pre>{_html_escape(md_text)}</pre>
</body>
</html>
"""

    md_path = status_dir / ("STATUS.md" if not iteration else f"STATUS_{iteration}.md")
    html_path = status_dir / ("STATUS.html" if not iteration else f"STATUS_{iteration}.html")

    if not dry_run:
        status_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_text, encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")

    return StatusRenderResult(True, "Status rendered" + (" (dry-run)" if dry_run else ""), md_path, html_path)

