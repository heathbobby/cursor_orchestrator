from __future__ import annotations

import json
import os
import re
from pathlib import PurePosixPath
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

TEMPLATE_VERSION = "3"

@dataclass(frozen=True)
class SyncResult:
    success: bool
    message: str
    dry_run: bool
    repo: str
    state: str
    dest_dir: Path
    fetched: int
    written: int
    updated: int
    skipped: int
    errors: list[str]


def _slugify(text: str, max_len: int = 60) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        return "issue"
    return s[:max_len].strip("-")


def _read_text(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _github_request(url: str, token: str | None = None) -> dict[str, Any] | list[Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "orchestration-framework",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # nosec - controlled URL + read-only
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        # Include response body for debugging (GitHub returns JSON with message + status).
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        raise RuntimeError(f"HTTP {getattr(e, 'code', '?')} {getattr(e, 'reason', '')}: {raw}".strip()) from e


def _issues_url(api_base: str, repo: str, state: str, per_page: int, page: int) -> str:
    owner, name = repo.split("/", 1)
    qs = urllib.parse.urlencode({"state": state, "per_page": str(per_page), "page": str(page)})
    return f"{api_base.rstrip('/')}/repos/{owner}/{name}/issues?{qs}"


def _render_work_item(issue: dict[str, Any], repo: str) -> str:
    number = issue.get("number")
    title = issue.get("title") or ""
    state = issue.get("state") or ""
    html_url = issue.get("html_url") or ""
    created_at = issue.get("created_at") or ""
    updated_at = issue.get("updated_at") or ""
    labels = issue.get("labels") or []
    label_names = []
    for l in labels:
        if isinstance(l, dict) and l.get("name"):
            label_names.append(str(l["name"]))
    assignees = issue.get("assignees") or []
    assignee_logins = []
    for a in assignees:
        if isinstance(a, dict) and a.get("login"):
            assignee_logins.append(str(a["login"]))
    body = issue.get("body") or ""
    synced_at = datetime.utcnow().isoformat() + "Z"

    lines = []
    lines.append(f"# GH-{number}: {title}\n")
    lines.append(f"- **Source**: GitHub Issues")
    lines.append(f"- **Repo**: `{repo}`")
    lines.append(f"- **Issue**: `{number}`")
    lines.append(f"- **Work Item ID**: `GH-{number}`")
    lines.append(f"- **State**: `{state}`")
    if label_names:
        lines.append(f"- **Labels**: {', '.join(f'`{n}`' for n in sorted(label_names))}")
    if assignee_logins:
        lines.append(f"- **Assignees**: {', '.join(f'`{a}`' for a in sorted(assignee_logins))}")
    if created_at:
        lines.append(f"- **Created**: `{created_at}`")
    if updated_at:
        lines.append(f"- **Updated**: `{updated_at}`")
    lines.append(f"- **Synced At**: `{synced_at}`")
    lines.append(f"- **Template Version**: `{TEMPLATE_VERSION}`")
    if html_url:
        lines.append(f"- **URL**: `{html_url}`")
    lines.append("")
    lines.append("## Objective\n")
    lines.append("Implement this work item according to the project’s conventions.\n")
    lines.append("## Project Agent Guidance (detected)\n")
    lines.append("- (This section is auto-filled when `AGENTS.md` / context docs exist in the repo.)\n")
    lines.append("## Source Issue Body\n")
    lines.append(body if body.strip() else "_(no description provided)_")
    lines.append("")
    lines.append("## Deliverables\n")
    lines.append("- (Fill in expected deliverables for this issue)")
    lines.append("")
    lines.append("## Suggested Commands (from ingestion)\n")
    lines.append("- (This section is auto-filled when `.orchestration/config/project_profile.yaml` exists.)\n")
    lines.append("## Notes for Agents\n")
    lines.append("- If the issue is ambiguous, ask clarifying questions in an `agent-sync` memo.")
    lines.append("- When complete, commit work on your branch/worktree and post a `ready-to-consume` memo with Branch+SHA.")
    return "\n".join(lines) + "\n"


def _load_project_profile(repo_root: Path) -> dict[str, Any]:
    profile_path = repo_root / ".orchestration" / "config" / "project_profile.yaml"
    if not profile_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        return {}
    try:
        data = yaml.safe_load(profile_path.read_text(encoding="utf-8", errors="replace")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _discover_guidance_paths(repo_root: Path) -> list[str]:
    """
    Return repo-relative paths to key agent guidance documents, if present.
    """
    candidates = [
        "AGENTS.md",
        "AGENT.md",
        "CONTRIBUTING.md",
        ".orchestration/config/PROJECT_CONTEXT.md",
        ".orchestration/runtime/agent-sync/COMMAND_SHORTHAND.md",
        ".orchestration/runtime/agent-sync/COMMUNICATION_CONVENTIONS.md",
        ".cursor/agent.md",
    ]
    found: list[str] = []
    for rel in candidates:
        if (repo_root / rel).exists():
            found.append(rel)

    # Also add a nested AGENTS.md if it exists (common for monorepos).
    nested = repo_root / "saasgen-consolidated" / "AGENTS.md"
    if nested.exists():
        found.append("saasgen-consolidated/AGENTS.md")

    # Dedup preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in found:
        p2 = str(PurePosixPath(p))
        if p2 in seen:
            continue
        seen.add(p2)
        out.append(p2)
    return out


def _fill_template_sections(repo_root: Path, content: str) -> str:
    """
    Replace placeholder sections with repo-specific hints (best-effort).
    """
    profile = _load_project_profile(repo_root)
    guidance = _discover_guidance_paths(repo_root)

    # Compute "project root" hint based on detected package.json location, if nested.
    signals = profile.get("signals_present") if isinstance(profile.get("signals_present"), dict) else {}
    pkg = signals.get("package_json") if isinstance(signals, dict) else None
    root_hint = None
    if isinstance(pkg, str) and pkg:
        p = PurePosixPath(pkg.replace("\\", "/"))
        if p.name == "package.json" and len(p.parts) > 1:
            root_hint = str(p.parent)

    # Suggested commands
    cmds = profile.get("suggested_commands") if isinstance(profile.get("suggested_commands"), dict) else {}
    cmd_lines: list[str] = []
    if root_hint:
        cmd_lines.append(f"- **Working directory**: `cd {root_hint}`")
    if isinstance(cmds, dict) and cmds:
        cmd_lines.append("- **Common commands**:")
        for k, v in sorted(cmds.items()):
            cmd_lines.append(f"  - **{k}**: `{v}`")
    if not cmd_lines:
        cmd_lines.append("- (No suggested commands available yet. Run `/orchestrator::ingest_project`.)")

    # Guidance section
    guide_lines: list[str] = []
    if guidance:
        guide_lines.append("- **Read first**:")
        for p in guidance:
            guide_lines.append(f"  - `{p}`")
    else:
        guide_lines.append("- (No guidance files detected. Add `AGENTS.md` or `.cursor/agent.md`.)")

    content = content.replace(
        "## Project Agent Guidance (detected)\n\n- (This section is auto-filled when `AGENTS.md` / context docs exist in the repo.)\n",
        "## Project Agent Guidance (detected)\n\n" + "\n".join(guide_lines) + "\n",
    )

    content = content.replace(
        "## Suggested Commands (from ingestion)\n\n- (This section is auto-filled when `.orchestration/config/project_profile.yaml` exists.)\n",
        "## Suggested Commands (from ingestion)\n\n" + "\n".join(cmd_lines) + "\n",
    )

    return content


def sync_github_issues(
    *,
    repo_root: Path,
    repo: str,
    state: str,
    dest_dir: Path,
    api_base: str = "https://api.github.com",
    token_env_var: str = "GITHUB_TOKEN",
    per_page: int = 100,
    max_issues: int = 200,
    include_pull_requests: bool = False,
    dry_run: bool = False,
) -> SyncResult:
    errors: list[str] = []
    fetched = 0
    written = 0
    updated = 0
    skipped = 0

    if "/" not in repo:
        return SyncResult(False, f"Invalid repo '{repo}'. Expected 'owner/name'.", dry_run, repo, state, dest_dir, 0, 0, 0, 0, [f"invalid repo: {repo}"])

    if state not in ("open", "closed", "all"):
        return SyncResult(False, f"Invalid state '{state}'. Expected open|closed|all.", dry_run, repo, state, dest_dir, 0, 0, 0, 0, [f"invalid state: {state}"])

    if dry_run:
        # No network; deterministic.
        dest_dir.mkdir(parents=True, exist_ok=True)
        sample_url = _issues_url(api_base, repo, state, per_page, 1)
        return SyncResult(
            True,
            f"[DRY RUN] Would fetch issues from {sample_url} and write to {dest_dir}",
            dry_run,
            repo,
            state,
            dest_dir,
            fetched=0,
            written=0,
            updated=0,
            skipped=0,
            errors=[],
        )

    token = os.getenv(token_env_var)

    # Fetch with pagination
    page = 1
    issues: list[dict[str, Any]] = []
    while True:
        url = _issues_url(api_base, repo, state, per_page, page)
        try:
            data = _github_request(url, token=token)
        except Exception as e:
            hint = ""
            msg = str(e)
            # GitHub uses 404 to hide private repos from unauthenticated callers.
            if ("HTTP 404" in msg) and (not token):
                hint = f" (hint: repo may be private; set {token_env_var} with access)"
            errors.append(f"fetch failed: {e}{hint}")
            break
        if not isinstance(data, list):
            errors.append("unexpected response (not a list)")
            break
        if not data:
            break
        for item in data:
            if not isinstance(item, dict):
                continue
            if (not include_pull_requests) and ("pull_request" in item):
                continue
            issues.append(item)
            if len(issues) >= max_issues:
                break
        if len(issues) >= max_issues:
            break
        page += 1

    fetched = len(issues)

    # Write work items
    dest_dir.mkdir(parents=True, exist_ok=True)
    for issue in issues:
        number = issue.get("number")
        title = issue.get("title") or ""
        updated_at = issue.get("updated_at") or ""
        slug = _slugify(title)
        fname = f"GH-{number}-{slug}.md" if number else f"GH-unknown-{slug}.md"
        path = dest_dir / fname

        content = _fill_template_sections(repo_root, _render_work_item(issue, repo))

        existing = _read_text(path)
        if existing is None:
            _write_text(path, content)
            written += 1
            continue

        # Fast skip if already has this updated_at marker.
        if updated_at and (f"- **Updated**: `{updated_at}`" in existing) and (f"- **Template Version**: `{TEMPLATE_VERSION}`" in existing):
            skipped += 1
            continue

        if existing != content:
            _write_text(path, content)
            updated += 1
        else:
            skipped += 1

    ok = len(errors) == 0
    msg = f"Synced {fetched} issue(s): {written} new, {updated} updated, {skipped} unchanged"
    if not token:
        msg += f" (unauthenticated; set {token_env_var} to increase rate limits)"

    return SyncResult(ok, msg, dry_run, repo, state, dest_dir, fetched, written, updated, skipped, errors)

