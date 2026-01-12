#!/usr/bin/env python3
"""
Bootstrap script for Generic Orchestration Framework.

This script initializes the framework in any project by:
- Creating required directory structure
- Copying template files
- Setting up configuration
- Updating .gitignore
- Optionally setting up Cursor rules
- Creating CONTRIBUTING.md with orchestration workflow

Usage:
    python orchestration-framework/bootstrap.py --init
    python orchestration-framework/bootstrap.py --init --project-name "MyProject"
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Optional


def _configure_stdout() -> None:
    """
    Make CLI output robust on Windows consoles with limited default encodings.
    Best-effort only.
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def print_header(message: str) -> None:
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {message}")
    print(f"{'='*70}\n")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"OK  {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"INFO {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"ERR {message}", file=sys.stderr)


def create_directory_structure(repo_root: Path, config: dict) -> None:
    """Create required directory structure."""
    print_info("Creating directory structure...")
    
    dirs = [
        # Coordination and communication
        repo_root / config["coordination"]["agent_sync_dir"],
        repo_root / config["coordination"]["agent_sync_dir"] / "tasks",
        
        # Iterations and outputs
        repo_root / config["orchestration"]["iterations_dir"],
        
        # Work items (if work_items_dir specified)
        repo_root / config["orchestration"].get("work_items_dir", "work_items"),
        
        # Workflows and templates
        repo_root / config["orchestration"]["workflows_dir"],
    ]
    
    # Cursor rules if enabled
    if config["cursor"]["enabled"]:
        dirs.append(repo_root / config["cursor"]["rules_dir"])
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print_success(f"Created {d.relative_to(repo_root)}")


def update_gitignore(repo_root: Path, config: dict) -> None:
    """Update .gitignore with worktree patterns and framework artifacts."""
    print_info("Updating .gitignore...")
    
    gitignore = repo_root / ".gitignore"
    
    patterns = [
        "",
        "# Generic Orchestration Framework",
        "# Orchestration runtime artifacts",
        ".orchestration/runtime/",
        "# Git worktrees (multi-agent orchestration)",
        f"# Worktrees should be outside repo ({config['worktrees']['location']}), but ignore if created inside",
        ".worktrees/",
        "_wt/",
        f"{Path(config['worktrees']['location']).name}/",
        "",
        "# Agent outputs and logs (optional - may want to commit some)",
        f"{config['orchestration']['iterations_dir']}/*/outputs/agent_*.log",
        f"{config['orchestration']['iterations_dir']}/*/outputs/agent_pids.txt",
        "",
        "# Python cache",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".pytest_cache/",
        "",
        "# IDE",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
    ]
    
    if gitignore.exists():
        content = gitignore.read_text()
        if "# Generic Orchestration Framework" not in content:
            with gitignore.open("a") as f:
                f.write("\n" + "\n".join(patterns))
            print_success("Updated .gitignore")
        else:
            print_info(".gitignore already has framework patterns")
    else:
        gitignore.write_text("\n".join(patterns))
        print_success("Created .gitignore")


def create_contributing(repo_root: Path, config: dict) -> None:
    """Create or update CONTRIBUTING.md with orchestration workflow."""
    print_info("Creating/updating CONTRIBUTING.md...")
    
    contributing = repo_root / "CONTRIBUTING.md"
    
    content = f"""# Contributing to {config['project']['name']}

This project uses the **Generic Orchestration Framework** for multi-agent coordination.

## Orchestration Workflow

When working on tasks that benefit from AI agent coordination, use the orchestration framework.

### Quick Start

1. **Start a workflow**:
   ```bash
   /orchestrator::start_workflow(<workflow-name>, <phase>, <iteration>)
   ```

2. **Agents execute tasks**:
   ```bash
   /<role>::start_task(<work-item-id>)
   # or
   /<role>::start_next
   ```

3. **Integrate ready work**:
   ```bash
   /integrator::apply_ready
   ```

4. **Validate iteration**:
   ```bash
   /integrator::validate_iteration(<iteration-name>)
   ```

## Worktree-Based Development

When multiple agents work concurrently, each agent uses its own git worktree to prevent conflicts.

### Create a Worktree

```bash
git switch {config['project']['trunk_branch']}
git worktree add -b <type>/<scope>/<short-desc> \\
  {config['worktrees']['location']}/<agent>/<type>-<short-desc> \\
  {config['project']['trunk_branch']}
```

### Work in Your Worktree

```bash
cd {config['worktrees']['location']}/<agent>/<branch>
# Make changes, commit, etc.
```

### Announce Ready-to-Consume

Post a memo to `{config['coordination']['agent_sync_dir']}/`:

```markdown
- **Date**: {date.today().isoformat()}
- **Audience**: `@integrator`
- **Status**: `ready-to-consume`
- **Branch**: `<branch>`
- **SHA**: `<sha>`
- **Work Item**: <work-item-id>
- **Deliverables**:
  - <path1> (created/updated)
  - <path2> (created/updated)
```

See `{config['coordination']['agent_sync_dir']}/COMMAND_SHORTHAND.md` for complete command reference.

## Integration

The integrator role manages convergence of ready-to-consume work:

```bash
/integrator::apply_ready
```

This will:
- Scan `{config['coordination']['agent_sync_dir']}/` for ready-to-consume memos
- Cherry-pick or merge agent work
- Run merge gate checks (validation, tests, coverage)
- Update memos to ready-to-merge

## Configuration

Framework configuration is in: `.orchestration/config/framework.yaml`

Customize:
- Project name and trunk branch
- Worktree location
- Agent roles
- Merge gate settings
- Token budget limits

## Getting Help

- Review command shorthand: `{config['coordination']['agent_sync_dir']}/COMMAND_SHORTHAND.md`
- Review completed iterations in `{config['orchestration']['iterations_dir']}/`
"""
    
    if contributing.exists():
        # Check if already has orchestration section
        existing = contributing.read_text()
        if "Generic Orchestration Framework" not in existing:
            # Append to existing
            with contributing.open("a") as f:
                f.write("\n\n" + "="*70 + "\n\n" + content)
            print_success("Updated CONTRIBUTING.md (appended orchestration section)")
        else:
            print_info("CONTRIBUTING.md already has orchestration workflow")
    else:
        contributing.write_text(content)
        print_success("Created CONTRIBUTING.md")


def copy_templates(repo_root: Path, framework_dir: Path, config: dict) -> None:
    """Copy template files to project."""
    print_info("Copying template files...")
    
    templates_dir = framework_dir / "templates"
    agent_sync = repo_root / config["coordination"]["agent_sync_dir"]
    
    # Copy command shorthand
    if (templates_dir / "COMMAND_SHORTHAND.md").exists():
        shutil.copy(
            templates_dir / "COMMAND_SHORTHAND.md",
            agent_sync / "COMMAND_SHORTHAND.md"
        )
        print_success("Copied COMMAND_SHORTHAND.md")
    
    # Copy communication conventions (if exists)
    if (templates_dir / "COMMUNICATION_CONVENTIONS.md").exists():
        shutil.copy(
            templates_dir / "COMMUNICATION_CONVENTIONS.md",
            agent_sync / "COMMUNICATION_CONVENTIONS.md"
        )
        print_success("Copied COMMUNICATION_CONVENTIONS.md")
    
    # Copy worktree operating model (if exists)
    if (templates_dir / "WORKTREE_OPERATING_MODEL.md").exists():
        shutil.copy(
            templates_dir / "WORKTREE_OPERATING_MODEL.md",
            agent_sync / "WORKTREE_OPERATING_MODEL.md"
        )
        print_success("Copied WORKTREE_OPERATING_MODEL.md")
    
    print_info(f"Template files copied to {agent_sync.relative_to(repo_root)}")


def setup_cursor_rules(repo_root: Path, framework_dir: Path, config: dict) -> None:
    """Set up Cursor IDE rules."""
    if not config["cursor"]["enabled"]:
        print_info("Cursor integration disabled (skipping)")
        return
    
    print_info("Setting up Cursor rules...")
    
    rules_dir = repo_root / config["cursor"]["rules_dir"]
    templates_dir = framework_dir / "templates" / "cursor-rules"
    
    if not templates_dir.exists():
        print_info("No cursor-rules templates found (skipping)")
        return
    
    # Copy cursor rule templates
    for rule_file in templates_dir.glob("*.mdc"):
        dest = rules_dir / rule_file.name
        shutil.copy(rule_file, dest)
        print_success(f"Copied {rule_file.name}")
    
    print_success("Cursor rules set up")


def setup_cursor_agent_file(repo_root: Path, framework_dir: Path, config: dict) -> None:
    """
    Create `.cursor/agent.md` so Cursor agents have a stable, project-local bootstrap doc.
    """
    if not config["cursor"]["enabled"]:
        return

    cursor_dir = repo_root / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)

    template_path = framework_dir / "templates" / "agent.md"
    dest = cursor_dir / "agent.md"

    if dest.exists():
        print_info(".cursor/agent.md already exists (skipping)")
        return

    if template_path.exists():
        shutil.copy(template_path, dest)
        print_success("Created .cursor/agent.md")
    else:
        # Fallback minimal file if template is missing
        dest.write_text(
            "# Cursor Agent Bootstrap\n\nSee `.orchestration/runtime/agent-sync/COMMAND_SHORTHAND.md`.\n",
            encoding="utf-8",
        )
        print_success("Created .cursor/agent.md (fallback)")


def create_config(repo_root: Path, framework_dir: Path, config: dict) -> None:
    """Create config.yaml if it doesn't exist."""
    config_path = repo_root / ".orchestration" / "config" / "framework.yaml"
    
    if config_path.exists():
        print_info("framework.yaml already exists (skipping)")
        return
    
    print_info("Creating framework.yaml...")
    
    config_content = f"""# Generic Orchestration Framework Configuration (Project)

project:
  name: "{config['project']['name']}"
  trunk_branch: "{config['project']['trunk_branch']}"

coordination:
  agent_sync_dir: "{config['coordination']['agent_sync_dir']}"
  memo_format: "YYYY-MM-DD_{{role}}_{{topic}}.md"
  status_values:
    - draft
    - ready-to-consume
    - ready-to-merge
    - blocked

worktrees:
  enabled: {str(config['worktrees']['enabled']).lower()}
  location: "{config['worktrees']['location']}"
  cleanup_on_merge: true

orchestration:
  workflows_dir: "{config['orchestration']['workflows_dir']}"
  iterations_dir: "{config['orchestration']['iterations_dir']}"
  work_items_dir: "{config['orchestration'].get('work_items_dir', 'work_items')}"
  
integration:
  target_branch_pattern: "integration/{{date}}"
  merge_gates:
    - validate_deliverables
    - check_token_budget
    - check_test_coverage
  auto_merge_to_trunk: false

token_budget:
  default_per_agent: 20000
  risk_thresholds:
    low: 70      # <70% utilization
    medium: 85   # 70-85% utilization
    high: 100    # 85-100% utilization

cursor:
  enabled: {str(config['cursor']['enabled']).lower()}
  rules_dir: "{config['cursor']['rules_dir']}"
  auto_open_worktrees: true

validation:
  file_existence: true
  file_size_min: 100  # bytes
  completion_criteria: true
"""
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_content)
    print_success(f"Created {config_path.relative_to(repo_root)}")


def create_example_workflow(repo_root: Path, config: dict) -> None:
    """Create an example workflow configuration."""
    print_info("Creating example workflow...")
    
    workflows_dir = repo_root / config['orchestration']['workflows_dir']
    example_workflow = workflows_dir / "example-workflow.yaml"
    
    if example_workflow.exists():
        print_info("Example workflow already exists (skipping)")
        return
    
    workflow_content = """# Example Workflow: Task Execution
# This workflow demonstrates basic task execution with multiple agents

name: example-workflow
description: Example workflow showing multi-agent task execution

phases:
  - id: phase-1
    name: Execution
    description: Execute tasks with specialized agents
    
    iterations:
      - id: iteration-1
        name: Task Execution
        description: Agents execute assigned tasks
        
        goal: |
          Execute tasks using specialized agents, each working in isolated
          worktrees to prevent conflicts.
        
        agents:
          - role: backend_developer
            inputs:
              - "task-001"
            deliverables:
              - path: "outputs/task-001-implementation.md"
                description: "Implementation details"
            token_budget: 15000
          
          - role: qa_engineer
            inputs:
              - "task-001"
            deliverables:
              - path: "outputs/task-001-tests.md"
                description: "Test specifications"
            token_budget: 10000
          
          - role: tech_writer
            inputs:
              - "task-001"
            deliverables:
              - path: "outputs/task-001-documentation.md"
                description: "User documentation"
            token_budget: 8000
        
        completion_criteria:
          files:
            - "outputs/task-001-implementation.md"
            - "outputs/task-001-tests.md"
            - "outputs/task-001-documentation.md"
          
          content_checks:
            - file: "outputs/task-001-implementation.md"
              must_contain: ["Implementation", "Technical Design"]
            
            - file: "outputs/task-001-tests.md"
              must_contain: ["Test Cases", "Acceptance Criteria"]
"""
    
    workflows_dir.mkdir(parents=True, exist_ok=True)
    example_workflow.write_text(workflow_content)
    print_success(f"Created {example_workflow.relative_to(repo_root)}")


def main() -> int:
    """Main entry point."""
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Bootstrap Generic Orchestration Framework in a project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize framework in current project
  python orchestration-framework/bootstrap.py --init
  
  # Initialize with custom project name
  python orchestration-framework/bootstrap.py --init --project-name "MyProject"
  
  # Initialize without Cursor integration
  python orchestration-framework/bootstrap.py --init --no-cursor
        """
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize framework in current directory"
    )
    
    parser.add_argument(
        "--project-name",
        default=None,
        help="Project name (defaults to current directory name)"
    )
    
    parser.add_argument(
        "--trunk-branch",
        default="main",
        help="Trunk branch name (default: main)"
    )
    
    parser.add_argument(
        "--no-cursor",
        action="store_true",
        help="Disable Cursor IDE integration"
    )
    
    parser.add_argument(
        "--worktree-location",
        default=None,
        help="Worktree location (default: ../<project>.worktrees)"
    )
    
    args = parser.parse_args()
    
    if not args.init:
        parser.print_help()
        return 1
    
    repo_root = Path.cwd()
    framework_dir = repo_root / "orchestration-framework"
    
    if not framework_dir.exists():
        print_error(f"Framework directory not found: {framework_dir}")
        print_info("Please copy the orchestration-framework/ directory to your project first")
        print_info("Or run this script from a directory containing orchestration-framework/")
        return 1
    
    # Determine project name
    project_name = args.project_name or repo_root.name
    
    # Determine worktree location
    if args.worktree_location:
        worktree_location = args.worktree_location
    else:
        worktree_location = f"../{project_name}.worktrees"
    
    # Build configuration
    config = {
        "project": {
            "name": project_name,
            "trunk_branch": args.trunk_branch,
        },
        "coordination": {
            "agent_sync_dir": ".orchestration/runtime/agent-sync",
        },
        "worktrees": {
            "enabled": True,
            "location": worktree_location,
        },
        "orchestration": {
            "workflows_dir": ".orchestration/config/workflows",
            "iterations_dir": ".orchestration/runtime/iterations",
            "work_items_dir": "work_items",
        },
        "cursor": {
            "enabled": not args.no_cursor,
            "rules_dir": ".cursor/rules",
        },
    }
    
    print_header(f"Bootstrapping Generic Orchestration Framework")
    print_info(f"Project: {project_name}")
    print_info(f"Location: {repo_root}")
    print_info(f"Framework: {framework_dir.relative_to(repo_root)}")
    print()
    
    try:
        create_directory_structure(repo_root, config)
        print()
        
        update_gitignore(repo_root, config)
        print()
        
        create_contributing(repo_root, config)
        print()
        
        copy_templates(repo_root, framework_dir, config)
        print()
        
        setup_cursor_rules(repo_root, framework_dir, config)
        print()

        setup_cursor_agent_file(repo_root, framework_dir, config)
        print()
        
        create_config(repo_root, framework_dir, config)
        print()
        
        create_example_workflow(repo_root, config)
        print()
        
        print_header("Bootstrap Complete!")
        
        print("\nNext Steps:\n")
        print("1. Review and customize: .orchestration/config/framework.yaml")
        print(f"2. Review command reference: {config['coordination']['agent_sync_dir']}/COMMAND_SHORTHAND.md")
        print(f"3. Create your first workflow in: {config['orchestration']['workflows_dir']}/")
        print("4. Start orchestration:")
        print("   /orchestrator::start_workflow(<workflow>, <phase>, <iteration>)")
        print("\nTip:\n")
        print("- Commit `.orchestration/config/` and `.cursor/` (agent setup)")
        print("- Keep `.orchestration/runtime/` out of git (runtime artifacts)")
        print()
        
        return 0
        
    except Exception as e:
        print_error(f"Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
