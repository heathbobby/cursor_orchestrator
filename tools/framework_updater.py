from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class UpdateReport:
    success: bool
    message: str
    source_dir: Path
    dest_dir: Path
    dry_run: bool
    files_considered: int
    files_changed: int
    actions: list[str]
    report_path: Path | None = None


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_item(src: Path, dst: Path) -> None:
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _parse_source_arg(source_arg: str) -> dict[str, str]:
    """
    Support:
      - local path: C:/path/to/repo
      - git URL: https://github.com/org/repo.git@main
    """
    source_arg = (source_arg or "").strip()
    if not source_arg:
        return {}
    if "://" in source_arg:
        if "@" in source_arg:
            repo, ref = source_arg.rsplit("@", 1)
            return {"type": "git", "repo": repo, "ref": ref}
        return {"type": "git", "repo": source_arg, "ref": "main"}
    return {"type": "local", "path": source_arg}


def update_framework(
    *,
    repo_root: Path,
    config: dict[str, Any] | None,
    source_arg: str | None = None,
    dry_run: bool = False,
) -> UpdateReport:
    """
    Update the installed `orchestration-framework/` folder in a bootstrapped project.

    Minimal payload policy:
      only copies files listed in `updates.payload` (defaults to minimal runtime payload).
    """
    config = config or {}
    orch = config.get("orchestration") or {}
    updates = config.get("updates") or {}

    dest_dir = repo_root / (orch.get("framework_dir") or "orchestration-framework")
    if not dest_dir.exists():
        return UpdateReport(
            False,
            f"Framework install dir not found: {dest_dir}",
            source_dir=dest_dir,
            dest_dir=dest_dir,
            dry_run=dry_run,
            files_considered=0,
            files_changed=0,
            actions=[],
        )

    # Resolve source spec
    source_spec: dict[str, Any] = {}
    if source_arg:
        source_spec = _parse_source_arg(source_arg)
    if not source_spec:
        source_spec = updates.get("source") or {}

    if not source_spec:
        return UpdateReport(
            False,
            "No update source provided. Pass a source arg or set `updates.source` in config.",
            source_dir=dest_dir,
            dest_dir=dest_dir,
            dry_run=dry_run,
            files_considered=0,
            files_changed=0,
            actions=[],
        )

    payload = updates.get("payload") or [
        "bootstrap.py",
        "cli.py",
        "requirements.txt",
        "config.yaml.example",
        "templates",
        "tools",
    ]

    now = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    actions: list[str] = []

    # Acquire source_dir
    tmpdir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if source_spec.get("type") == "git":
            repo = source_spec.get("repo")
            ref = source_spec.get("ref") or "main"
            if not repo:
                raise RuntimeError("updates.source.repo is required for git source")
            tmpdir = tempfile.TemporaryDirectory(prefix="orchestration-framework-update-")
            clone_dir = Path(tmpdir.name)
            # non-interactive shallow clone
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, repo, str(clone_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            source_dir = clone_dir
        elif source_spec.get("type") == "local":
            p = source_spec.get("path")
            if not p:
                raise RuntimeError("updates.source.path is required for local source")
            source_dir = Path(p).expanduser().resolve()
        else:
            raise RuntimeError(f"Unknown updates.source.type: {source_spec.get('type')}")

        # Determine if source is a framework repo root or already points at an install dir.
        # If it contains `tools/` and `bootstrap.py`, treat it as root.
        # If it contains `orchestration-framework/`, treat that as the framework folder root.
        if (source_dir / "orchestration-framework").exists():
            # allow passing a monorepo root that contains an installed folder
            source_dir = source_dir / "orchestration-framework"

        # Compute diffs + apply payload copies.
        files_considered = 0
        files_changed = 0

        def _hash_tree(p: Path) -> dict[str, str]:
            out: dict[str, str] = {}
            if p.is_file():
                out[p.name] = _sha256(p)
                return out
            if not p.exists():
                return out
            for f in _iter_files(p):
                out[str(f.relative_to(p)).replace("\\", "/")] = _sha256(f)
            return out

        for item in payload:
            src_item = source_dir / item
            dst_item = dest_dir / item
            if not src_item.exists():
                actions.append(f"SKIP missing in source: {item}")
                continue

            src_hashes = _hash_tree(src_item)
            dst_hashes = _hash_tree(dst_item)
            files_considered += max(len(src_hashes), len(dst_hashes), 1)
            changed = src_hashes != dst_hashes
            if changed:
                files_changed += 1
                actions.append(f"UPDATE {item}")
            else:
                actions.append(f"OK {item} (no change)")

            if (not dry_run) and changed:
                _copy_item(src_item, dst_item)

        # Write a report under runtime (ignored by git), but still useful for humans.
        report_path: Path | None = None
        runtime_dir = repo_root / ".orchestration" / "runtime" / "updates"
        if not dry_run:
            runtime_dir.mkdir(parents=True, exist_ok=True)
            report_path = runtime_dir / f"framework_update_{now}.md"
            report_path.write_text(
                "\n".join(
                    [
                        "# Framework Update Report",
                        "",
                        f"- **Timestamp**: {now}Z",
                        f"- **Source**: `{str(source_spec)}`",
                        f"- **Source dir**: `{source_dir.as_posix()}`",
                        f"- **Dest dir**: `{dest_dir.as_posix()}`",
                        f"- **Dry-run**: {dry_run}",
                        f"- **Payload items**: {len(payload)}",
                        "",
                        "## Actions",
                        *[f"- {a}" for a in actions],
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

        return UpdateReport(
            True,
            "Framework update complete" + (" (dry-run)" if dry_run else ""),
            source_dir=source_dir,
            dest_dir=dest_dir,
            dry_run=dry_run,
            files_considered=files_considered,
            files_changed=files_changed,
            actions=actions,
            report_path=report_path,
        )
    except subprocess.CalledProcessError as e:
        return UpdateReport(
            False,
            f"Framework update failed (git): {e.stderr or e.stdout or str(e)}",
            source_dir=dest_dir,
            dest_dir=dest_dir,
            dry_run=dry_run,
            files_considered=0,
            files_changed=0,
            actions=actions,
        )
    except Exception as e:
        return UpdateReport(
            False,
            f"Framework update failed: {e}",
            source_dir=dest_dir,
            dest_dir=dest_dir,
            dry_run=dry_run,
            files_considered=0,
            files_changed=0,
            actions=actions,
        )
    finally:
        if tmpdir is not None:
            try:
                tmpdir.cleanup()
            except Exception:
                pass

