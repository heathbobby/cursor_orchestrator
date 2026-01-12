from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ArchiveResult:
    success: bool
    message: str
    archive_dir: Path | None = None
    moved: list[str] | None = None
    skipped: list[str] | None = None


def _extract_task_files_from_index(index_text: str) -> list[str]:
    """
    Extract linked task card filenames from an index markdown.
    Matches the same style as `launch_agents`: ](FILENAME.md)
    """
    out: list[str] = []
    for m in re.finditer(r"\]\(([^)]+\.md)\)", index_text):
        fname = m.group(1).strip()
        if fname.endswith("_INDEX.md"):
            continue
        out.append(fname)
    # preserve order but dedupe
    seen: set[str] = set()
    deduped: list[str] = []
    for f in out:
        if f in seen:
            continue
        seen.add(f)
        deduped.append(f)
    return deduped


def archive_iteration_tasks(
    *,
    tasks_dir: Path,
    iteration: str,
    archive_root: Path | None = None,
    dry_run: bool = False,
    index_path: Path | None = None,
    card_paths: Iterable[Path] | None = None,
) -> ArchiveResult:
    """
    Move the latest index + its referenced task cards into a timestamped archive folder.

    Defaults:
      archive_root = <tasks_dir>/_archive/<iteration>/<YYYYMMDD-HHMMSS>/
    """
    tasks_dir = Path(tasks_dir)
    if not tasks_dir.exists():
        return ArchiveResult(False, f"Tasks dir not found: {tasks_dir}")

    # Resolve index path (prefer caller-provided, else latest match)
    if index_path is None:
        index_candidates = sorted(tasks_dir.glob(f"*_{iteration}_INDEX.md"))
        if not index_candidates:
            return ArchiveResult(False, f"No task index found for iteration '{iteration}' in {tasks_dir}")
        index_path = index_candidates[-1]

    if not index_path.exists():
        return ArchiveResult(False, f"Index not found: {index_path}")

    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    index_task_files = _extract_task_files_from_index(index_text)

    # Prefer caller-provided card paths (already resolved), else resolve from index links.
    resolved_cards: list[Path] = []
    if card_paths is not None:
        for p in card_paths:
            if Path(p).exists():
                resolved_cards.append(Path(p))
    else:
        for fname in index_task_files:
            p = tasks_dir / fname
            if p.exists():
                resolved_cards.append(p)

    # Determine archive destination
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if archive_root is None:
        archive_root = tasks_dir / "_archive" / iteration / stamp
    else:
        archive_root = Path(archive_root) / iteration / stamp

    to_move: list[Path] = [index_path, *resolved_cards]
    moved: list[str] = []
    skipped: list[str] = []

    if not dry_run:
        archive_root.mkdir(parents=True, exist_ok=True)

    for src in to_move:
        if not src.exists():
            skipped.append(str(src))
            continue
        dst = archive_root / src.name
        if dry_run:
            moved.append(f"{src} -> {dst}")
            continue
        # Avoid overwriting; if exists, suffix with incremental counter.
        if dst.exists():
            base = dst.stem
            ext = dst.suffix
            i = 1
            while True:
                candidate = archive_root / f"{base}.{i}{ext}"
                if not candidate.exists():
                    dst = candidate
                    break
                i += 1
        shutil.move(str(src), str(dst))
        moved.append(f"{src} -> {dst}")

    return ArchiveResult(
        True,
        f"Archived {len(to_move)} file(s) for iteration '{iteration}'" + (" (dry-run)" if dry_run else ""),
        archive_dir=archive_root,
        moved=moved,
        skipped=skipped,
    )

