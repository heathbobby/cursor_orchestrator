#!/usr/bin/env python3
"""
Cursor CLI launcher helpers.

This framework's "most innovative" loop is that an orchestrator agent running inside
Cursor can drive multi-step orchestration by executing CLI commands (including the
Cursor CLI) from a terminal.

We keep this best-effort and configurable because Cursor CLI behavior differs by OS
and installation method.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class CursorLaunchResult:
    success: bool
    command: list[str]
    error: Optional[str] = None
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


def _stringify_cmd(parts: list[Any]) -> list[str]:
    return [str(p) for p in parts if p is not None and str(p) != ""]


def windows_path_to_wsl(path: str) -> str:
    """
    Convert a Windows path like `C:\\Users\\me\\proj` to `/mnt/c/Users/me/proj`.
    Best-effort; if it doesn't look like a drive path, returns input unchanged.
    """
    s = str(path)
    if len(s) >= 3 and s[1] == ":" and (s[2] == "\\" or s[2] == "/"):
        drive = s[0].lower()
        rest = s[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return s


def _bash_heredoc_substitution(content: str, marker: str = "PROMPT") -> str:
    """
    Render `content` into a bash command substitution using a single-quoted heredoc.
    This preserves newlines without requiring escaping.
    """
    body = content if content.endswith("\n") else (content + "\n")
    return f"$(cat <<'{marker}'\n{body}{marker}\n)"


def build_agent_command(prompt: str, config: dict[str, Any]) -> list[str]:
    """
    Build a Cursor CLI `agent` command in non-interactive "print" mode.

    Based on Cursor CLI docs: https://cursor.com/docs/cli/overview

    Config keys (all optional):
      cursor:
        agent_command: "agent"
        agent_runner_prefix: ["wsl", "-d", "Ubuntu", "--"]  # for Windows→WSL
        agent_model: "gpt-5"
        agent_output_format: "text"
        agent_extra_args: []
    """
    cursor_cfg = (config or {}).get("cursor") or {}

    agent_command = cursor_cfg.get("agent_command") or "agent"
    runner_prefix = cursor_cfg.get("agent_runner_prefix") or []
    model = cursor_cfg.get("agent_model")
    output_format = cursor_cfg.get("agent_output_format") or "text"
    extra_args = cursor_cfg.get("agent_extra_args") or []

    cmd: list[Any] = []
    cmd.extend(runner_prefix if isinstance(runner_prefix, list) else [runner_prefix])
    cmd.extend([agent_command, *extra_args, "-p", prompt])

    if model:
        cmd.extend(["--model", model])
    if output_format:
        cmd.extend(["--output-format", output_format])

    return _stringify_cmd(cmd)


def build_agent_command_bash(prompt: str, config: dict[str, Any]) -> str:
    """
    Build a bash-friendly command string for Cursor CLI `agent`.

    Uses a heredoc-based command substitution for `-p` to safely include newlines.
    This is intended for copy/paste into shells (especially WSL).
    """
    cursor_cfg = (config or {}).get("cursor") or {}

    agent_command = cursor_cfg.get("agent_command") or "agent"
    runner_prefix = cursor_cfg.get("agent_runner_prefix") or []
    model = cursor_cfg.get("agent_model")
    output_format = cursor_cfg.get("agent_output_format") or "text"
    extra_args = cursor_cfg.get("agent_extra_args") or []

    prefix = " ".join(_stringify_cmd(runner_prefix if isinstance(runner_prefix, list) else [runner_prefix]))
    p = _bash_heredoc_substitution(prompt, marker="PROMPT")

    parts: list[str] = []
    if prefix:
        parts.append(prefix)
    parts.append(str(agent_command))
    parts.extend([str(x) for x in extra_args])
    parts.extend(["-p", p])
    if model:
        parts.extend(["--model", str(model)])
    if output_format:
        parts.extend(["--output-format", str(output_format)])

    return " ".join(parts)


def run_agent(prompt: str, config: dict[str, Any], cwd: Optional[Path] = None) -> CursorLaunchResult:
    """Best-effort run of Cursor CLI `agent` in the current environment."""
    cmd = build_agent_command(prompt, config)
    try:
        res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False, capture_output=True, text=True)
        ok = res.returncode == 0
        return CursorLaunchResult(
            success=ok,
            command=cmd,
            returncode=res.returncode,
            stdout=res.stdout,
            stderr=res.stderr,
        )
    except Exception as e:
        return CursorLaunchResult(success=False, command=cmd, error=str(e), returncode=None)


def open_in_cursor(path: Path, config: dict[str, Any]) -> CursorLaunchResult:
    """
    Open a file/folder path in Cursor using a CLI command.

    Config keys (all optional):
      cursor:
        cli_command: "cursor"          # executable name/path
        open_args: ["--reuse-window"]  # extra args before the path
    """
    cursor_cfg = (config or {}).get("cursor") or {}
    cli_command = cursor_cfg.get("cli_command") or "cursor"
    open_args = cursor_cfg.get("open_args") or []

    cmd = _stringify_cmd([cli_command, *open_args, str(Path(path))])

    try:
        subprocess.run(cmd, check=False, capture_output=True, text=True)
        return CursorLaunchResult(success=True, command=cmd)
    except Exception as e:
        return CursorLaunchResult(success=False, command=cmd, error=str(e))

