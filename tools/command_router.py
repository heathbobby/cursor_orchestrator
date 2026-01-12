#!/usr/bin/env python3
"""
Command router and handler registry for Generic Orchestration Framework.

Routes parsed commands to appropriate handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

try:
    from .command_parser import ParsedCommand
except ImportError:
    from command_parser import ParsedCommand


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Optional[Any] = None
    
    def __str__(self) -> str:
        status = "OK" if self.success else "ERR"
        return f"[{status}] {self.message}"


# Type alias for command handler functions
CommandHandler = Callable[[ParsedCommand, dict], CommandResult]


class CommandRouter:
    """Routes commands to appropriate handlers."""
    
    def __init__(self):
        """Initialize router with empty handler registry."""
        self._handlers: dict[str, dict[str, CommandHandler]] = {
            'orchestrator': {},
            'integrator': {},
            'role': {},  # Generic role commands
        }
    
    def register(
        self,
        role: str,
        command: str,
        handler: CommandHandler
    ) -> None:
        """
        Register a command handler.
        
        Args:
            role: Role name ('orchestrator', 'integrator', or 'role' for generic)
            command: Command name
            handler: Handler function
        """
        if role not in self._handlers:
            self._handlers[role] = {}
        
        self._handlers[role][command] = handler
    
    def route(
        self,
        cmd: ParsedCommand,
        context: Optional[dict] = None
    ) -> CommandResult:
        """
        Route command to appropriate handler.
        
        Args:
            cmd: Parsed command
            context: Optional context dictionary (config, paths, etc.)
            
        Returns:
            CommandResult with execution status
        """
        context = context or {}
        
        # Determine handler category
        if cmd.is_orchestrator:
            category = 'orchestrator'
        elif cmd.is_integrator:
            category = 'integrator'
        else:
            category = 'role'
        
        # Find handler
        handlers = self._handlers.get(category, {})
        handler = handlers.get(cmd.command)
        
        if not handler:
            return CommandResult(
                success=False,
                message=f"No handler registered for {category}::{cmd.command}"
            )
        
        # Execute handler
        try:
            return handler(cmd, context)
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Handler error: {str(e)}"
            )
    
    def list_commands(self, role: Optional[str] = None) -> dict[str, list[str]]:
        """
        List registered commands.
        
        Args:
            role: Optional role to filter by
            
        Returns:
            Dictionary mapping roles to command lists
        """
        if role:
            return {role: list(self._handlers.get(role, {}).keys())}
        
        return {
            role: list(commands.keys())
            for role, commands in self._handlers.items()
        }


# Global router instance
_global_router: Optional[CommandRouter] = None


def get_router() -> CommandRouter:
    """Get or create global command router."""
    global _global_router
    if _global_router is None:
        _global_router = CommandRouter()
    return _global_router


def register_handler(
    role: str,
    command: str
) -> Callable[[CommandHandler], CommandHandler]:
    """
    Decorator to register a command handler.
    
    Usage:
        @register_handler('orchestrator', 'start_workflow')
        def handle_start_workflow(cmd: ParsedCommand, ctx: dict) -> CommandResult:
            # ... implementation
            return CommandResult(success=True, message="Workflow started")
    """
    def decorator(func: CommandHandler) -> CommandHandler:
        router = get_router()
        router.register(role, command, func)
        return func
    return decorator


def execute_command(
    cmd: ParsedCommand,
    context: Optional[dict] = None
) -> CommandResult:
    """
    Execute a parsed command using the global router.
    
    Args:
        cmd: Parsed command
        context: Optional context dictionary
        
    Returns:
        CommandResult with execution status
    """
    router = get_router()
    return router.route(cmd, context)


# Handlers

@register_handler('orchestrator', 'start_workflow')
def handle_start_workflow(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::start_workflow(workflow, phase, iteration).
    """
    from datetime import date
    from pathlib import Path

    try:
        from .task_cards import generate_task_cards
        from .workflow_loader import load_workflow_yaml, find_iteration
        from .worktree_manager import WorktreeManager
    except ImportError:
        from task_cards import generate_task_cards
        from workflow_loader import load_workflow_yaml, find_iteration
        from worktree_manager import WorktreeManager

    workflow_name, phase_id, iteration_id = cmd.args

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}

    coordination = config.get("coordination") or {}
    orchestration = config.get("orchestration") or {}
    worktrees_cfg = config.get("worktrees") or {}
    commands_cfg = config.get("commands") or {}
    project_cfg = config.get("project") or {}

    agent_sync_dir = repo_root / coordination.get("agent_sync_dir", "agent-sync")
    workflows_dir = repo_root / orchestration.get("workflows_dir", "workflows")
    iterations_dir = repo_root / orchestration.get("iterations_dir", "iterations")

    agent_sync_dir.mkdir(parents=True, exist_ok=True)
    workflows_dir.mkdir(parents=True, exist_ok=True)
    iterations_dir.mkdir(parents=True, exist_ok=True)

    # Resolve workflow path
    if workflow_name.endswith((".yml", ".yaml")):
        workflow_path = (repo_root / workflow_name).resolve() if not Path(workflow_name).is_absolute() else Path(workflow_name)
    else:
        workflow_path = workflows_dir / f"{workflow_name}.yaml"
        if not workflow_path.exists():
            # Allow passing a filename without extension as a fallback
            alt = workflows_dir / workflow_name
            if alt.exists():
                workflow_path = alt

    if not workflow_path.exists():
        return CommandResult(
            success=False,
            message=f"Workflow config not found: {workflow_path}",
            data={"workflow": workflow_name, "searched": str(workflow_path)},
        )

    workflow = load_workflow_yaml(workflow_path)
    iteration_cfg = find_iteration(workflow, phase_id, iteration_id)

    # Ensure the iteration config has what task generation expects.
    iteration_config = {
        "name": iteration_id,
        "goal": iteration_cfg.get("goal") or iteration_cfg.get("description") or "",
        "agents": iteration_cfg.get("agents") or [],
        "completion_criteria": iteration_cfg.get("completion_criteria") or {},
    }

    # Create iteration scaffold
    iteration_dir = iterations_dir / iteration_id
    iteration_dir.mkdir(parents=True, exist_ok=True)

    context_md = f"""# Iteration Context: {iteration_id}

- **Workflow**: {workflow.get('name')}
- **Phase**: {phase_id}
- **Iteration**: {iteration_id}
- **Source**: `{Path(workflow.get('_path', str(workflow_path))).as_posix()}`

## Goal

{iteration_config['goal']}

## Notes

- Task cards are generated under `{(commands_cfg.get('task_cards_dir') or 'agent-sync/tasks')}`.
- Agents should post memos to `{coordination.get('agent_sync_dir', 'agent-sync')}/` when ready-to-consume.
"""
    (iteration_dir / "CONTEXT.md").write_text(context_md, encoding="utf-8")

    # Build a simple completion criteria doc (lightweight, but useful)
    deliverable_paths: list[str] = []
    for agent in iteration_config["agents"]:
        for d in agent.get("deliverables", []) or []:
            p = d.get("path")
            if p:
                deliverable_paths.append(str(p))

    requirements = (iteration_config["completion_criteria"].get("requirements") or [])
    if not isinstance(requirements, list):
        requirements = [str(requirements)]

    criteria_lines = "\n".join(f"- [ ] {req}" for req in requirements) if requirements else "- [ ] Deliverables created and non-trivial"
    deliverables_lines = "\n".join(f"- `{p}`" for p in sorted(set(deliverable_paths))) if deliverable_paths else "- (No deliverables specified)"

    completion_md = f"""# Completion Criteria: {iteration_id}

## Required Deliverables

{deliverables_lines}

## Checklist

{criteria_lines}
"""
    (iteration_dir / "COMPLETION_CRITERIA.md").write_text(completion_md, encoding="utf-8")

    readme_md = f"""# Iteration: {iteration_id}

## What was generated

- `CONTEXT.md`
- `COMPLETION_CRITERIA.md`
- Task cards in `{(commands_cfg.get('task_cards_dir') or 'agent-sync/tasks')}`

## Next steps (typical)

1. Agents execute tasks (from task index)
2. Agents post `ready-to-consume` memos in `{coordination.get('agent_sync_dir', 'agent-sync')}/`
3. Integrator runs `/integrator::apply_ready`
"""
    (iteration_dir / "README.md").write_text(readme_md, encoding="utf-8")

    # Generate task cards
    date_str = date.today().isoformat()
    tasks_dir_str = commands_cfg.get("task_cards_dir") or "agent-sync/tasks"
    tasks_dir = repo_root / tasks_dir_str
    task_cards = generate_task_cards(
        iteration_name=iteration_id,
        iteration_config=iteration_config,
        repo_root=repo_root,
        date_str=date_str,
        tasks_dir=tasks_dir,
    )

    # Create dispatch memo
    def _start_cmd(task_id: str) -> str:
        parts = task_id.split("-")
        role = "-".join(parts[3:-1]).lower().replace("-", "_") if len(parts) > 4 else "unknown"
        return f"/{role}::start_task({task_id})"

    start_commands = "\n".join(_start_cmd(p.stem) for p in sorted(task_cards))
    dispatch_memo_path = agent_sync_dir / f"{date_str}_orchestrator_task-dispatch_{iteration_id}.md"
    dispatch_memo_path.write_text(
        f"""# Task Dispatch: {iteration_id}

- **Date**: {date_str}
- **Audience**: `@all`
- **Status**: `draft`

## Workflow

- **Workflow**: {workflow.get('name')}
- **Phase**: {phase_id}
- **Iteration**: {iteration_id}

## Task Index

- `{(Path(tasks_dir_str) / f"{date_str}_{iteration_id}_INDEX.md").as_posix()}`

## Start Commands

```text
{start_commands}
```
""",
        encoding="utf-8",
    )

    # Optionally create worktrees (one per role for this iteration)
    created_worktrees: list[str] = []
    if bool(worktrees_cfg.get("enabled", True)):
        trunk_branch = project_cfg.get("trunk_branch") or ctx.get("trunk_branch") or "main"
        branch_prefix = worktrees_cfg.get("branch_prefix") or "feat"

        # Resolve base worktree location.
        location = worktrees_cfg.get("location")
        if isinstance(location, str) and location:
            project_name = project_cfg.get("name") or repo_root.name
            location = location.replace("{project}", project_name)
            worktree_base = Path(location)
            if not worktree_base.is_absolute():
                worktree_base = (repo_root / worktree_base).resolve()
        else:
            worktree_base = None

        manager = WorktreeManager(repo_root, worktree_base=worktree_base)
        roles = sorted({(a.get("role") or "unknown") for a in iteration_config["agents"]})
        for role in roles:
            try:
                wt = manager.create_worktree(role=role, task_name=iteration_id, base_branch=trunk_branch, branch_prefix=branch_prefix)
                created_worktrees.append(str(wt.path))
            except Exception:
                # If it already exists or git isn't available, don't fail the whole workflow generation.
                continue

    # Cursor CLI `agent` commands (optional)
    # This is the core "Cursor-agent orchestrates via CLI" loop:
    # an orchestrator agent can run Cursor CLI commands to spin up parallel work.
    # Docs: https://cursor.com/docs/cli/overview
    agent_commands: list[str] = []
    cursor_cfg = config.get("cursor") or {}
    if bool(cursor_cfg.get("enabled")) and cursor_cfg.get("agent_command"):
        try:
            from .cursor_launcher import build_agent_command_bash, windows_path_to_wsl
        except ImportError:
            from cursor_launcher import build_agent_command_bash, windows_path_to_wsl

        runner_prefix = cursor_cfg.get("agent_runner_prefix") or []
        use_wsl = False
        if isinstance(runner_prefix, list) and runner_prefix:
            first = str(runner_prefix[0]).lower()
            use_wsl = first in ("wsl", "wsl.exe")

        def _role_from_task_id(task_id: str) -> str:
            parts = task_id.split("-")
            return "-".join(parts[3:-1]).lower().replace("-", "_") if len(parts) > 4 else "unknown"

        def _worktree_for_role(role: str) -> str | None:
            # created_worktrees paths are typically: <base>/<role>/<iteration>
            for wt in created_worktrees:
                try:
                    p = Path(wt)
                    if len(p.parts) >= 2 and p.parts[-2].lower() == role:
                        return wt
                except Exception:
                    continue
            return None

        for card_path in sorted(task_cards):
            task_id = card_path.stem
            role = _role_from_task_id(task_id)
            role_cmd = _start_cmd(task_id)
            wt = _worktree_for_role(role)

            card_path_str = str(card_path)
            wt_str = str(wt) if wt else ""
            if use_wsl:
                card_path_str = windows_path_to_wsl(card_path_str)
                if wt_str:
                    wt_str = windows_path_to_wsl(wt_str)

            prompt = (
                f"You are the {role} agent.\n"
                f"Execute this task using the framework protocol.\n\n"
                f"- Task card: {card_path_str}\n"
                + (f"- Worktree: {wt_str}\n" if wt_str else "")
                + f"- Command shorthand: {role_cmd}\n\n"
                "Follow the task card steps, make the required changes, commit, and post a ready-to-consume memo."
            )

            agent_commands.append(build_agent_command_bash(prompt, config))

        # Append section to dispatch memo (best-effort)
        try:
            existing = dispatch_memo_path.read_text(encoding="utf-8")
            addition = (
                "\n\n## Cursor CLI Agent Commands (optional)\n\n"
                "If you have Cursor CLI installed, you can run these from a terminal to start agents via CLI.\n"
                "See: https://cursor.com/docs/cli/overview\n\n"
                "```bash\n"
                + ("\n".join(agent_commands) if agent_commands else "# (no tasks)\n")
                + "\n```\n"
            )
            if "## Cursor CLI Agent Commands" not in existing:
                dispatch_memo_path.write_text(existing + addition, encoding="utf-8")
        except Exception:
            pass

    # Optional: open created worktrees (or iteration dir) in Cursor via Cursor CLI.
    cursor_cfg = config.get("cursor") or {}
    opened_in_cursor: list[str] = []
    if bool(cursor_cfg.get("enabled")) and bool(cursor_cfg.get("auto_open_worktrees")):
        try:
            from .cursor_launcher import open_in_cursor
        except ImportError:
            from cursor_launcher import open_in_cursor

        targets = [Path(p) for p in created_worktrees] if created_worktrees else [iteration_dir]
        for target in targets:
            res = open_in_cursor(target, config)
            if res.success:
                opened_in_cursor.append(str(target))

    return CommandResult(
        success=True,
        message=f"Workflow '{workflow.get('name')}' generated: {phase_id} / {iteration_id}",
        data={
            "workflow": workflow.get("name"),
            "phase": phase_id,
            "iteration": iteration_id,
            "iteration_dir": str(iteration_dir),
            "task_count": len(task_cards),
            "dispatch_memo": str(dispatch_memo_path),
            "worktrees_created": created_worktrees,
            "cursor_opened": opened_in_cursor,
            "cursor_agent_commands": agent_commands,
        },
    )


@register_handler('orchestrator', 'generate_iteration')
def handle_generate_iteration(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::generate_iteration(iteration).
    
    TODO: Replace with real implementation that:
    - Reads workflow config
    - Generates CONTEXT.md, COMPLETION_CRITERIA.md
    - Generates agent prompts
    - Outputs allocation summary
    """
    # Keep the 1-arg signature, but allow encoding workflow + phase + iteration:
    # /orchestrator::generate_iteration(workflow:phase:iteration)
    spec = cmd.args[0]
    if ":" not in spec:
        return CommandResult(
            success=False,
            message="generate_iteration expects 'workflow:phase:iteration' (single arg)",
            data={"arg": spec},
        )

    workflow, phase, iteration = [p.strip() for p in spec.split(":", 2)]
    pseudo = ParsedCommand(role="orchestrator", command="start_workflow", args=[workflow, phase, iteration], raw=cmd.raw)
    return handle_start_workflow(pseudo, ctx)


@register_handler('orchestrator', 'monitor_progress')
def handle_monitor_progress(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::monitor_progress(iteration).
    
    TODO: Replace with real implementation that:
    - Checks agent status
    - Reports deliverables progress
    - Shows token budget utilization
    - Lists ready-to-consume memos
    """
    iteration = cmd.args[0]
    
    return CommandResult(
        success=True,
        message=f"Monitoring iteration '{iteration}'",
        data={
            'iteration': iteration,
            'agents': [],
            'progress': '0%'
        }
    )


@register_handler('orchestrator', 'launch_agents')
def handle_launch_agents(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::launch_agents(iteration[, dry-run]).

    This automates the key innovation:
    an orchestrator agent can use Cursor CLI (`agent`) to execute task cards
    without manual copy/paste.

    Cursor CLI docs: https://cursor.com/docs/cli/overview
    """
    import re
    import subprocess
    from datetime import datetime
    from pathlib import Path

    try:
        from .cursor_launcher import run_agent, build_agent_command, windows_path_to_wsl
    except ImportError:
        from cursor_launcher import run_agent, build_agent_command, windows_path_to_wsl

    iteration = cmd.args[0]
    args = cmd.args[1:]

    # Flags/options (positional, order-independent)
    dry_run = "dry-run" in args
    parallel = "parallel" in args
    apply_ready_flag = any(a.startswith("apply-ready") or a == "apply_ready" for a in args)
    apply_ready_each = "apply-ready-each" in args or "apply_ready_each" in args
    archive_tasks_flag = "archive-tasks" in args or "archive_tasks" in args

    # Optional: apply-ready target override: apply-ready=<branch>
    apply_ready_target: str | None = None
    for a in args:
        if a.startswith("apply-ready="):
            apply_ready_target = a.split("=", 1)[1].strip() or None

    # Optional max_parallel: either a bare integer or max_parallel=<n>
    requested_parallel: int | None = None
    for a in args:
        if a.isdigit():
            requested_parallel = int(a)
        elif a.startswith("max_parallel="):
            try:
                requested_parallel = int(a.split("=", 1)[1])
            except Exception:
                pass

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}

    cursor_cfg = (config.get("cursor") or {})
    runner_prefix = cursor_cfg.get("agent_runner_prefix") or []
    use_wsl = False
    if isinstance(runner_prefix, list) and runner_prefix:
        first = str(runner_prefix[0]).lower()
        use_wsl = first in ("wsl", "wsl.exe")

    if not bool(cursor_cfg.get("enabled")) or not cursor_cfg.get("agent_command"):
        return CommandResult(
            success=False,
            message="Cursor CLI agent integration is not enabled/configured (cursor.enabled + cursor.agent_command)",
            data={"cursor": cursor_cfg},
        )

    # Find latest task index for the iteration
    tasks_dir_str = ((config.get("commands") or {}).get("task_cards_dir")) or "agent-sync/tasks"
    tasks_dir = repo_root / tasks_dir_str
    if not tasks_dir.exists():
        return CommandResult(
            success=False,
            message=f"Tasks directory not found: {tasks_dir}",
            data={"tasks_dir": str(tasks_dir)},
        )

    index_candidates = sorted(tasks_dir.glob(f"*_{iteration}_INDEX.md"))
    if not index_candidates:
        return CommandResult(
            success=False,
            message=f"No task index found for iteration '{iteration}' in {tasks_dir}",
            data={"glob": f"*_{iteration}_INDEX.md", "tasks_dir": str(tasks_dir)},
        )
    index_path = index_candidates[-1]

    # Parse task card filenames from index
    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    card_files: list[str] = []
    for m in re.finditer(r"\]\(([^)]+\.md)\)", index_text):
        fname = m.group(1).strip()
        if fname.endswith("_INDEX.md"):
            continue
        card_files.append(fname)

    card_paths: list[Path] = []
    for fname in card_files:
        p = tasks_dir / fname
        if p.exists():
            card_paths.append(p)

    if not card_paths:
        return CommandResult(
            success=False,
            message=f"Task index found but no task cards could be resolved: {index_path.name}",
            data={"index": str(index_path), "tasks_dir": str(tasks_dir)},
        )

    # Run each task via Cursor CLI `agent` (non-interactive print mode).
    orchestration_cfg = config.get("orchestration") or {}
    iterations_dir = repo_root / orchestration_cfg.get("iterations_dir", ".orchestration/runtime/iterations")
    logs_dir = (iterations_dir / iteration / "agent-cli-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    launched: list[str] = []
    log_files: list[str] = []
    failures: list[dict] = []
    integrate_runs: list[dict] = []

    def _run_apply_ready_if_requested() -> tuple[bool, dict | None]:
        if dry_run or (not apply_ready_flag):
            return True, None
        orchestration_cfg = config.get("orchestration") or {}
        allow_auto = bool(orchestration_cfg.get("allow_auto_apply_ready", False))
        if not allow_auto:
            return True, {"skipped": True, "reason": "allow_auto_apply_ready is false"}
        try:
            args_for_apply: list[str] = []
            if apply_ready_target:
                args_for_apply.append(apply_ready_target)
            pseudo = ParsedCommand(role="integrator", command="apply_ready", args=args_for_apply, raw="/integrator::apply_ready")
            r = handle_apply_ready(pseudo, ctx)
            return r.success, {"success": r.success, "message": r.message, "data": r.data}
        except Exception as e:
            return False, {"success": False, "error": str(e)}

    def _prompt_for(card_path: Path) -> tuple[str, str]:
        task_id = card_path.stem
        role_match = re.search(
            r"^\s*-\s*\*\*Role\*\*:\s*(.+)\s*$",
            card_path.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        )
        role = role_match.group(1).strip() if role_match else "unknown"
        card_path_str = str(card_path)
        if use_wsl:
            card_path_str = windows_path_to_wsl(card_path_str)
        prompt = (
            f"You are the {role} agent.\n"
            f"Execute this task card from the orchestration framework.\n\n"
            f"Task card path: {card_path_str}\n"
            f"Iteration: {iteration}\n\n"
            "Follow the task card steps, make the required changes, commit, and post a ready-to-consume memo."
        )
        return task_id, prompt

    max_parallel_cfg = int(cursor_cfg.get("agent_max_parallel") or 1)
    max_parallel = max_parallel_cfg
    if requested_parallel is not None:
        max_parallel = max(1, min(int(requested_parallel), max_parallel_cfg))

    if dry_run:
        # Dry-run: don't execute, just write logs (and mark launched).
        for card_path in card_paths:
            task_id, prompt = _prompt_for(card_path)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_path = logs_dir / f"{task_id}.{stamp}.log"
            log_path.write_text(
                f"[DRY RUN] Would run Cursor CLI agent for {task_id}\n\nPrompt:\n{prompt}\n",
                encoding="utf-8",
            )
            launched.append(task_id)
            log_files.append(str(log_path))
    elif not parallel or max_parallel <= 1:
        # Sequential execution (default).
        for card_path in card_paths:
            task_id, prompt = _prompt_for(card_path)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_path = logs_dir / f"{task_id}.{stamp}.log"

            res = run_agent(prompt, config, cwd=repo_root)
            log_content = (
                f"command: {' '.join(res.command)}\n"
                f"returncode: {res.returncode}\n"
                f"success: {res.success}\n"
                f"stdout:\n{res.stdout or ''}\n"
                f"stderr:\n{res.stderr or ''}\n"
            )
            log_path.write_text(log_content, encoding="utf-8")
            log_files.append(str(log_path))

            if res.success:
                launched.append(task_id)
                if apply_ready_each:
                    ok_apply, payload = _run_apply_ready_if_requested()
                    integrate_runs.append({"when": "after-task", "task_id": task_id, "result": payload})
                    if not ok_apply:
                        failures.append({"task_id": task_id, "returncode": None, "error": "apply_ready failed", "log": None})
                        break
            else:
                failures.append(
                    {
                        "task_id": task_id,
                        "returncode": res.returncode,
                        "error": res.error,
                        "log": str(log_path),
                    }
                )
    else:
        # Parallel execution (bounded concurrency).
        queue = list(card_paths)
        running: dict[str, tuple[subprocess.Popen, Path]] = {}
        any_success_in_batch = False

        def _start_one(card_path: Path) -> None:
            task_id, prompt = _prompt_for(card_path)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_path = logs_dir / f"{task_id}.{stamp}.log"
            cmd_list = build_agent_command(prompt, config)
            f = log_path.open("w", encoding="utf-8", errors="replace")
            p = subprocess.Popen(cmd_list, cwd=str(repo_root), stdout=f, stderr=subprocess.STDOUT, text=True)
            running[task_id] = (p, log_path)
            log_files.append(str(log_path))

        while queue or running:
            while queue and len(running) < max_parallel:
                _start_one(queue.pop(0))

            # Poll running tasks
            finished: list[str] = []
            for task_id, (proc, log_path) in running.items():
                rc = proc.poll()
                if rc is None:
                    continue
                finished.append(task_id)
                if rc == 0:
                    launched.append(task_id)
                    any_success_in_batch = True
                else:
                    failures.append(
                        {
                            "task_id": task_id,
                            "returncode": rc,
                            "error": None,
                            "log": str(log_path),
                        }
                    )

            for tid in finished:
                running.pop(tid, None)

            # If requested, run convergence after any successes in this polling batch.
            if apply_ready_each and any_success_in_batch and finished:
                ok_apply, payload = _run_apply_ready_if_requested()
                integrate_runs.append({"when": "after-batch", "result": payload})
                any_success_in_batch = False
                if not ok_apply:
                    break

    ok = len(failures) == 0

    # Optional: auto-integrate ready-to-consume work after launching agents.
    orchestration_cfg = config.get("orchestration") or {}
    allow_auto = bool(orchestration_cfg.get("allow_auto_apply_ready", False))
    auto_integrate_ran = False
    auto_integrate_result: dict | None = None
    if (not dry_run) and ok and apply_ready_flag and allow_auto and (not apply_ready_each):
        try:
            args_for_apply = []
            if apply_ready_target:
                args_for_apply.append(apply_ready_target)
            pseudo = ParsedCommand(role="integrator", command="apply_ready", args=args_for_apply, raw="/integrator::apply_ready")
            r = handle_apply_ready(pseudo, ctx)
            auto_integrate_ran = True
            auto_integrate_result = {"success": r.success, "message": r.message, "data": r.data}
            ok = ok and r.success
        except Exception as e:
            auto_integrate_ran = True
            auto_integrate_result = {"success": False, "error": str(e)}
            ok = False

    # Optional: archive task cards + index to keep tasks directory clean.
    archive_result: dict | None = None
    if (not dry_run) and ok and archive_tasks_flag:
        try:
            try:
                from .task_archiver import archive_iteration_tasks
            except ImportError:
                from task_archiver import archive_iteration_tasks
            commands_cfg = config.get("commands") or {}
            archive_root = repo_root / (commands_cfg.get("task_archive_dir") or str(tasks_dir / "_archive"))
            ar = archive_iteration_tasks(
                tasks_dir=tasks_dir,
                iteration=iteration,
                archive_root=archive_root,
                dry_run=False,
                index_path=index_path,
                card_paths=card_paths,
            )
            archive_result = {
                "success": ar.success,
                "message": ar.message,
                "archive_dir": str(ar.archive_dir) if ar.archive_dir else None,
                "moved_count": len(ar.moved or []),
                "skipped_count": len(ar.skipped or []),
            }
            ok = ok and ar.success
        except Exception as e:
            archive_result = {"success": False, "error": str(e)}
            ok = False

    return CommandResult(
        success=ok,
        message=f"launch_agents processed {len(card_paths)} task(s) from {index_path.name}",
        data={
            "iteration": iteration,
            "dry_run": dry_run,
            "mode": "parallel" if (parallel and not dry_run and max_parallel > 1) else "sequential",
            "max_parallel": max_parallel,
            "apply_ready_requested": apply_ready_flag,
            "apply_ready_each": apply_ready_each,
            "archive_tasks": archive_tasks_flag,
            "apply_ready_target": apply_ready_target,
            "integrate_runs": integrate_runs,
            "allow_auto_apply_ready": allow_auto,
            "auto_integrate_ran": auto_integrate_ran,
            "auto_integrate_result": auto_integrate_result,
            "archive_result": archive_result,
            "index": str(index_path),
            "tasks": [str(p) for p in card_paths],
            "launched": launched,
            "failures": failures,
            "logs_dir": str(logs_dir),
            "log_files": log_files,
        },
    )


@register_handler('orchestrator', 'apply_ready_to')
def handle_apply_ready_to(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::apply_ready_to(target_branch[, dry-run]).

    Convenience wrapper so the orchestrator can converge ready-to-consume work into:
    - trunk (e.g. main)
    - an integration branch (e.g. integration/2026-01-12)
    - another agent's branch/worktree (dependency handoff)
    """
    target_branch = cmd.args[0]
    dry_run = len(cmd.args) == 2 and cmd.args[1] == "dry-run"

    # Delegate to integrator handler, reusing the existing merge logic.
    pseudo = ParsedCommand(
        role="integrator",
        command="apply_ready",
        args=[target_branch] + (["dry-run"] if dry_run else []),
        raw=cmd.raw,
    )
    result = handle_apply_ready(pseudo, ctx)

    # Slightly adjust messaging so it's clear this came from orchestrator wrapper.
    return CommandResult(
        success=result.success,
        message=f"apply_ready_to({target_branch}) -> {result.message}",
        data=result.data,
    )


@register_handler('orchestrator', 'ingest_project')
def handle_ingest_project(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::ingest_project([path][, dry-run]).

    Generates:
      - `.orchestration/config/project_profile.yaml` (commit-able)
      - `.orchestration/config/PROJECT_CONTEXT.md`  (commit-able)
    """
    from pathlib import Path

    try:
        from .project_ingestion import ingest_project
    except ImportError:
        from project_ingestion import ingest_project

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}

    args = cmd.args or []
    dry_run = "dry-run" in args
    non_flags = [a for a in args if a != "dry-run"]
    path = non_flags[0] if non_flags else None

    result = ingest_project(repo_root=repo_root, config=config, path=path, dry_run=dry_run)
    return CommandResult(
        success=True,
        message="Project ingestion complete" + (" (dry-run)" if dry_run else ""),
        data={
            "dry_run": dry_run,
            "scope": result.profile.get("scope"),
            "profile_path": str(result.profile_path),
            "context_path": str(result.context_path),
            "languages": result.profile.get("languages"),
            "package_managers": result.profile.get("package_managers"),
        },
    )


@register_handler('orchestrator', 'derive_roles')
def handle_derive_roles(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::derive_roles([path][, dry-run]).

    Generates:
      - `.orchestration/config/derived_roles.yaml` (commit-able)
      - `.cursor/rules/30-derived-roles.mdc` (commit-able, only if cursor.enabled)
    """
    from pathlib import Path

    try:
        from .project_ingestion import ingest_project
        from .role_deriver import derive_roles_from_profile, write_derived_roles
    except ImportError:
        from project_ingestion import ingest_project
        from role_deriver import derive_roles_from_profile, write_derived_roles

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}

    args = cmd.args or []
    dry_run = "dry-run" in args
    non_flags = [a for a in args if a != "dry-run"]
    path = non_flags[0] if non_flags else None

    # Ensure we have a profile to derive from (write it unless dry-run).
    ingest_res = ingest_project(repo_root=repo_root, config=config, path=path, dry_run=dry_run)
    derived = derive_roles_from_profile(ingest_res.profile)
    write_res = write_derived_roles(repo_root=repo_root, derived=derived, config=config, dry_run=dry_run)

    return CommandResult(
        success=True,
        message="Derived recommended roles" + (" (dry-run)" if dry_run else ""),
        data={
            "dry_run": dry_run,
            "profile_path": str(ingest_res.profile_path),
            "derived_roles_path": str(write_res.derived_path),
            "cursor_rule_path": str(write_res.cursor_rule_path) if write_res.cursor_rule_path else None,
            "recommended_roles": [r.get("role") for r in (derived.get("recommended_roles") or [])],
        },
    )


@register_handler('orchestrator', 'archive_tasks')
def handle_archive_tasks(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::archive_tasks(iteration[, dry-run]).

    Archives (moves) the latest `*_<iteration>_INDEX.md` plus all referenced task cards
    into: `<task_archive_dir>/<iteration>/<timestamp>/`.
    """
    from pathlib import Path
    try:
        from .task_archiver import archive_iteration_tasks
    except ImportError:
        from task_archiver import archive_iteration_tasks

    iteration = cmd.args[0]
    dry_run = len(cmd.args) == 2 and cmd.args[1] == "dry-run"

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}
    commands_cfg = config.get("commands") or {}

    tasks_dir = repo_root / (commands_cfg.get("task_cards_dir") or "agent-sync/tasks")
    archive_root = repo_root / (commands_cfg.get("task_archive_dir") or (str(tasks_dir / "_archive")))

    res = archive_iteration_tasks(tasks_dir=tasks_dir, iteration=iteration, archive_root=archive_root, dry_run=dry_run)
    return CommandResult(
        success=res.success,
        message=res.message,
        data={
            "iteration": iteration,
            "dry_run": dry_run,
            "tasks_dir": str(tasks_dir),
            "archive_root": str(archive_root),
            "archive_dir": str(res.archive_dir) if res.archive_dir else None,
            "moved": res.moved or [],
            "skipped": res.skipped or [],
        },
    )


@register_handler('orchestrator', 'update_knowledge')
def handle_update_knowledge(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::update_knowledge([iteration][, dry-run]).

    Generates/refreshes `.orchestration/knowledge/` (commit-able).
    """
    from pathlib import Path
    try:
        from .knowledge_manager import update_knowledge_base
    except ImportError:
        from knowledge_manager import update_knowledge_base

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}
    args = cmd.args or []
    dry_run = "dry-run" in args
    non_flags = [a for a in args if a != "dry-run"]
    iteration = non_flags[0] if non_flags else None

    res = update_knowledge_base(repo_root=repo_root, config=config, iteration=iteration, dry_run=dry_run)
    return CommandResult(
        success=res.success,
        message=res.message,
        data={
            "dry_run": dry_run,
            "iteration": iteration,
            "knowledge_dir": str(res.knowledge_dir),
            "written": res.written,
        },
    )


@register_handler('orchestrator', 'render_status')
def handle_render_status(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::render_status([iteration][, dry-run]).
    Generates `.orchestration/runtime/status/STATUS.md` and `.html`.
    """
    from pathlib import Path
    try:
        from .status_renderer import render_status
    except ImportError:
        from status_renderer import render_status

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}
    args = cmd.args or []
    dry_run = "dry-run" in args
    non_flags = [a for a in args if a != "dry-run"]
    iteration = non_flags[0] if non_flags else None

    res = render_status(repo_root=repo_root, config=config, iteration=iteration, dry_run=dry_run)
    return CommandResult(
        success=res.success,
        message=res.message,
        data={
            "dry_run": dry_run,
            "iteration": iteration,
            "markdown_path": str(res.markdown_path),
            "html_path": str(res.html_path),
        },
    )


@register_handler('orchestrator', 'update_framework')
def handle_update_framework(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::update_framework([source][, dry-run]).

    - If `source` is a local path, it will update from that directory.
    - If `source` looks like a URL, you can add `@ref` to pick a branch/tag:
        `https://github.com/org/repo.git@main`
    - If omitted, uses `updates.source` from config.
    """
    from pathlib import Path
    try:
        from .framework_updater import update_framework
    except ImportError:
        from framework_updater import update_framework

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}

    args = cmd.args or []
    dry_run = "dry-run" in args
    non_flags = [a for a in args if a != "dry-run"]
    source_arg = non_flags[0] if non_flags else None

    res = update_framework(repo_root=repo_root, config=config, source_arg=source_arg, dry_run=dry_run)
    return CommandResult(
        success=res.success,
        message=res.message,
        data={
            "dry_run": res.dry_run,
            "source_dir": str(res.source_dir),
            "dest_dir": str(res.dest_dir),
            "files_considered": res.files_considered,
            "files_changed": res.files_changed,
            "report_path": str(res.report_path) if res.report_path else None,
            "actions": res.actions,
        },
    )


@register_handler('orchestrator', 'sync_work_items')
def handle_sync_work_items(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /orchestrator::sync_work_items(provider[, repo][, state][, dry-run]).

    Currently supported providers:
      - github (GitHub Issues)
    """
    from pathlib import Path

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}
    orch = config.get("orchestration") or {}
    providers_cfg = config.get("providers") or {}

    args = cmd.args or []
    dry_run = "dry-run" in args
    parts = [a for a in args if a != "dry-run"]
    provider = parts[0] if parts else ""

    # Parse optional repo + state in any order (simple heuristics).
    repo_arg: str | None = None
    state_arg: str | None = None
    for a in parts[1:]:
        if a in ("open", "closed", "all"):
            state_arg = a
        elif "/" in a and "://" not in a:
            repo_arg = a

    work_items_dir = repo_root / (orch.get("work_items_dir") or "work_items")

    if provider == "github":
        gh = (providers_cfg.get("github") or {})
        repo_name = repo_arg or gh.get("default_repo")
        if not repo_name:
            return CommandResult(
                success=False,
                message="GitHub provider requires repo (owner/name) via args or providers.github.default_repo",
                data={"provider": "github"},
            )
        state = state_arg or gh.get("default_state") or "open"
        dest_subdir = gh.get("dest_subdir") or "github/issues"
        dest_dir = work_items_dir / dest_subdir

        try:
            from .providers.github_issues import sync_github_issues
        except ImportError:
            from providers.github_issues import sync_github_issues

        res = sync_github_issues(
            repo_root=repo_root,
            repo=str(repo_name),
            state=str(state),
            dest_dir=dest_dir,
            api_base=str(gh.get("api_base") or "https://api.github.com"),
            token_env_var=str(gh.get("token_env_var") or "GITHUB_TOKEN"),
            per_page=int(gh.get("per_page") or 100),
            max_issues=int(gh.get("max_issues") or 200),
            include_pull_requests=bool(gh.get("include_pull_requests") or False),
            dry_run=dry_run,
        )

        return CommandResult(
            success=res.success,
            message=res.message,
            data={
                "provider": "github",
                "dry_run": res.dry_run,
                "repo": res.repo,
                "state": res.state,
                "dest_dir": str(res.dest_dir),
                "fetched": res.fetched,
                "written": res.written,
                "updated": res.updated,
                "skipped": res.skipped,
                "errors": res.errors,
            },
        )

    return CommandResult(
        success=False,
        message=f"Unknown provider: {provider}",
        data={"supported": ["github"]},
    )


@register_handler('integrator', 'apply_ready')
def handle_apply_ready(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle:
      - /integrator::apply_ready
      - /integrator::apply_ready(dry-run)
      - /integrator::apply_ready(main)
      - /integrator::apply_ready(main, dry-run)
    
    Scans agent-sync/ for ready-to-consume memos and integrates them.
    """
    from pathlib import Path
    try:
        from .integration_manager import IntegrationManager
    except ImportError:
        from integration_manager import IntegrationManager
    
    args = cmd.args or []
    dry_run = "dry-run" in args
    branch_overrides = [a for a in args if a != "dry-run"]
    target_override = branch_overrides[0] if branch_overrides else None
    
    # Get repo root from context
    repo_root = ctx.get('repo_root', Path.cwd())
    config = ctx.get('config') or {}
    trunk_branch = ctx.get("trunk_branch") or (config.get('project') or {}).get('trunk_branch') or 'main'

    # Default to an integration branch (not trunk) unless explicitly overridden.
    integration_cfg = config.get("integration") or {}
    target_pattern = integration_cfg.get("target_branch_pattern") or "integration/{date}"

    from datetime import date as _date
    today = _date.today().isoformat()
    target_branch = str(target_pattern).replace("{date}", today)
    if target_override:
        target_branch = target_override
    if not target_branch:
        target_branch = trunk_branch

    agent_sync_dir = repo_root / ((config.get('coordination') or {}).get('agent_sync_dir') or "agent-sync")
    
    try:
        manager = IntegrationManager(
            repo_root,
            target_branch=target_branch,
            trunk_branch=trunk_branch,
            agent_sync_dir=agent_sync_dir,
        )
        result = manager.apply_ready(dry_run=dry_run)
        
        return CommandResult(
            success=result.success,
            message=result.message,
            data={
                'dry_run': dry_run,
                'target_branch': target_branch,
                'trunk_branch': trunk_branch,
                'merged_branches': result.merged_branches,
                'failed_branches': result.failed_branches,
                'skipped_memos': result.skipped_memos,
                'total_processed': result.total_processed
            }
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Integration failed: {e}",
            data={'error': str(e)}
        )


@register_handler('integrator', 'validate_iteration')
def handle_validate_iteration(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /integrator::validate_iteration(iteration).
    
    TODO: Replace with real implementation that:
    - Reads COMPLETION_CRITERIA.md
    - Checks file existence
    - Validates file sizes
    - Runs content checks
    - Generates validation report
    """
    iteration = cmd.args[0]
    
    return CommandResult(
        success=True,
        message=f"Iteration '{iteration}' validated",
        data={
            'iteration': iteration,
            'files_checked': 0,
            'criteria_met': True
        }
    )


@register_handler('integrator', 'evaluate_iteration')
def handle_evaluate_iteration(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /integrator::evaluate_iteration(iteration[, dry-run]).

    Produces a prompt/rules effectiveness report under `.orchestration/knowledge/evaluations/`.
    """
    from pathlib import Path
    try:
        from .iteration_evaluator import evaluate_iteration
    except ImportError:
        from iteration_evaluator import evaluate_iteration

    iteration = cmd.args[0]
    dry_run = len(cmd.args) == 2 and cmd.args[1] == "dry-run"

    repo_root = Path(ctx.get("repo_root", Path.cwd()))
    config = ctx.get("config") or {}
    res = evaluate_iteration(repo_root=repo_root, config=config, iteration=iteration, dry_run=dry_run)
    return CommandResult(
        success=res.success,
        message=res.message,
        data={
            "dry_run": dry_run,
            "iteration": iteration,
            "output_path": str(res.output_path),
            "suggestions": res.suggestions,
        },
    )


@register_handler('integrator', 'distribute_tasks')
def handle_distribute_tasks(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /integrator::distribute_tasks(iteration).
    
    Generates task cards for an iteration.
    """
    from pathlib import Path
    try:
        from .task_cards import generate_task_cards
    except ImportError:
        from task_cards import generate_task_cards
    
    iteration = cmd.args[0]
    
    # Get configuration from context
    repo_root = ctx.get('repo_root', Path.cwd())
    config = ctx.get('config') or {}
    tasks_dir_str = (config.get('commands') or {}).get('task_cards_dir')
    tasks_dir = (repo_root / tasks_dir_str) if tasks_dir_str else None
    
    try:
        # For now, use a simple configuration
        # In production, this would load from config.yaml
        iteration_config = ctx.get('iteration_config', {})
        
        task_cards = generate_task_cards(
            iteration_name=iteration,
            iteration_config=iteration_config,
            repo_root=repo_root,
            tasks_dir=tasks_dir,
        )
        
        return CommandResult(
            success=True,
            message=f"Distributed {len(task_cards)} task(s) for '{iteration}'",
            data={
                'iteration': iteration,
                'task_count': len(task_cards),
                'task_cards': [str(p) for p in task_cards],
            }
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Task distribution failed: {e}",
            data={'error': str(e)}
        )


@register_handler('role', 'start_task')
def handle_start_task(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /<role>::start_task(work_item_id).
    
    This is a role-specific command that should be handled by agents.
    The CLI can provide guidance but not execute directly.
    """
    work_item_id = cmd.args[0]
    role = cmd.role
    
    return CommandResult(
        success=True,
        message=f"Task '{work_item_id}' ready for {role}",
        data={
            'role': role,
            'work_item': work_item_id,
            'note': 'This command should be executed by an agent with the appropriate role'
        }
    )


@register_handler('role', 'start_next')
def handle_start_next(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /<role>::start_next.
    
    This is a role-specific command that should be handled by agents.
    The CLI can provide guidance but not execute directly.
    """
    role = cmd.role
    
    return CommandResult(
        success=True,
        message=f"Next task ready for {role}",
        data={
            'role': role,
            'note': 'This command should be executed by an agent with the appropriate role'
        }
    )


@register_handler('role', 'report_token_usage')
def handle_report_token_usage(cmd: ParsedCommand, ctx: dict) -> CommandResult:
    """
    Handle /<role>::report_token_usage.
    
    This is a role-specific command that should be handled by agents.
    The CLI can provide guidance but not execute directly.
    """
    role = cmd.role
    
    return CommandResult(
        success=True,
        message=f"Token usage report for {role}",
        data={
            'role': role,
            'note': 'This command should be executed by an agent with the appropriate role'
        }
    )


if __name__ == "__main__":
    # Example usage and testing
    try:
        from .command_parser import parse_command
    except ImportError:
        from command_parser import parse_command
    
    print("Testing command router:")
    print("=" * 70)
    
    test_commands = [
        "/orchestrator::start_workflow(workflow1, phase1, iter1)",
        "/integrator::apply_ready",
        "/integrator::apply_ready(dry-run)",
        "/product_analyst::start_task(US-E01-010)",
        "/backend_developer::start_next",
    ]
    
    for test_cmd in test_commands:
        print(f"\n{test_cmd}")
        
        parsed = parse_command(test_cmd)
        if parsed:
            result = execute_command(parsed)
            print(f"  {result}")
            if result.data:
                print(f"  Data: {result.data}")
        else:
            print(f"  ✗ Parse failed")
    
    print("\n" + "=" * 70)
    print("\nRegistered commands:")
    router = get_router()
    for role, commands in router.list_commands().items():
        print(f"  {role}: {', '.join(commands)}")
