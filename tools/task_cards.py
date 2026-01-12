#!/usr/bin/env python3
"""
Task card generation for Generic Orchestration Framework.

Generates structured task cards for agent coordination.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional


@dataclass
class TaskCard:
    """Represents a task card."""
    task_id: str
    role: str
    work_item: str
    deliverables: list[str]
    priority: str = "Normal"
    effort: str = "Unknown"
    token_budget: int = 0
    dependencies: list[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class TaskCardGenerator:
    """Generates task cards from iteration configuration."""
    
    def __init__(self, repo_root: Path, tasks_dir: Optional[Path] = None):
        """
        Initialize task card generator.
        
        Args:
            repo_root: Repository root directory (used to locate agent-sync/)
            tasks_dir: Optional explicit tasks directory (defaults to <repo_root>/agent-sync/tasks)
        """
        self.repo_root = Path(repo_root)
        self.tasks_dir = Path(tasks_dir) if tasks_dir else (self.repo_root / "agent-sync" / "tasks")
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_from_iteration(
        self,
        iteration_name: str,
        iteration_config: dict,
        date_str: Optional[str] = None
    ) -> list[Path]:
        """
        Generate task cards from iteration configuration.
        
        Args:
            iteration_name: Name of the iteration
            iteration_config: Iteration configuration dict
            date_str: Optional date string (defaults to today)
            
        Returns:
            List of generated task card paths
        """
        if date_str is None:
            date_str = date.today().isoformat()
        
        task_cards = []
        
        # Get agents from iteration config
        agents = iteration_config.get('agents', [])
        
        for agent_idx, agent in enumerate(agents):
            role = agent.get('role', 'unknown')
            inputs = agent.get('inputs', [])
            deliverables = agent.get('deliverables', [])
            token_budget = agent.get('token_budget', 20000)
            dependencies = agent.get('dependencies', [])
            
            for input_idx, work_item in enumerate(inputs):
                # Generate task ID
                task_id = f"{date_str}-{role.upper().replace('_', '-')}-{input_idx+1:02d}"
                
                # Create task card
                card = TaskCard(
                    task_id=task_id,
                    role=role,
                    work_item=work_item,
                    deliverables=[d.get('path', '') for d in deliverables],
                    priority=agent.get('priority', 'Normal'),
                    effort=agent.get('effort', 'Unknown'),
                    token_budget=token_budget,
                    dependencies=dependencies
                )
                
                # Write task card file
                card_path = self._write_task_card(
                    card,
                    iteration_name,
                    iteration_config.get('goal', ''),
                    iteration_config.get('completion_criteria', {})
                )
                
                task_cards.append(card_path)
        
        # Generate INDEX
        index_path = self._generate_index(
            iteration_name,
            task_cards,
            date_str
        )
        
        return task_cards
    
    def _write_task_card(
        self,
        card: TaskCard,
        iteration_name: str,
        goal: str,
        completion_criteria: dict
    ) -> Path:
        """Write a task card to file."""
        card_path = self.tasks_dir / f"{card.task_id}.md"
        
        content = f"""# Task: {card.task_id}

- **Role**: {card.role}
- **Status**: ready-to-start
- **Work Item**: {card.work_item}
- **Priority**: {card.priority}
- **Estimated Effort**: {card.effort}
- **Token Budget**: {card.token_budget:,} tokens
- **Dependencies**: {', '.join(card.dependencies) if card.dependencies else 'None'}

## Objective

{goal}

## Work Item

`{card.work_item}`

## Deliverables

{self._format_deliverables(card.deliverables)}

## Steps

1. Read work item file: `{card.work_item}`
2. Execute all deliverables per your boot prompt
3. Commit to your worktree branch
4. Post ready-to-consume memo with Branch+SHA

## Acceptance Criteria

{self._format_criteria(completion_criteria)}

## Resources

- **Iteration Context**: See iteration CONTEXT.md for architecture, standards, examples
- **Completion Criteria**: See iteration COMPLETION_CRITERIA.md for objective checklist
- **Boot Prompt**: See your role-specific boot prompt in iteration directory

## Command to Start

```bash
/{card.role}::start_task({card.task_id})
```

---

**Status Transitions**:
- `ready-to-start` → `in-progress` (when you begin)
- `in-progress` → `ready-to-consume` (when complete, post memo)
- `ready-to-consume` → `completed` (after integration)
"""
        
        card_path.write_text(content, encoding="utf-8")
        return card_path
    
    def _format_deliverables(self, deliverables: list[str]) -> str:
        """Format deliverables as markdown list."""
        if not deliverables:
            return "- (No deliverables specified)"
        return "\n".join(f"- `{d}`" for d in deliverables)
    
    def _format_criteria(self, criteria: dict) -> str:
        """Format acceptance criteria as markdown checklist."""
        requirements = criteria.get('requirements', [])
        if not requirements:
            return "- [ ] Task completed per boot prompt instructions"
        
        return "\n".join(f"- [ ] {req}" for req in requirements)
    
    def _generate_index(
        self,
        iteration_name: str,
        task_cards: list[Path],
        date_str: str
    ) -> Path:
        """Generate task INDEX file."""
        index_path = self.tasks_dir / f"{date_str}_{iteration_name}_INDEX.md"
        
        # Group tasks by role
        tasks_by_role: dict[str, list[Path]] = {}
        for card_path in task_cards:
            task_id = card_path.stem
            # Parse role from task ID (e.g., "2026-01-10-PROD-ANALYST-01" -> "PROD-ANALYST")
            parts = task_id.split('-')
            role = '-'.join(parts[3:-1]) if len(parts) > 4 else 'UNKNOWN'
            
            if role not in tasks_by_role:
                tasks_by_role[role] = []
            tasks_by_role[role].append(card_path)
        
        content = f"""# Task Index: {iteration_name}

- **Date**: {date_str}
- **Iteration**: {iteration_name}
- **Total Tasks**: {len(task_cards)}

## Task Summary by Role

{self._format_task_summary(tasks_by_role)}

## All Tasks

{self._format_task_list(task_cards)}

## Quick Start Commands

Copy these commands to start tasks:

```bash
{self._format_start_commands(task_cards)}
```

## How to Use

1. **Agent selects task**: Find your role in the list above
2. **Start task**: Copy the command for your task
3. **Execute**: Run the command (e.g., `/product_analyst::start_task(...)`)
4. **Complete**: Post ready-to-consume memo when done

## Status Tracking

- ✅ `ready-to-start` - Task is available to begin
- 🔄 `in-progress` - Agent is working on task
- ✔️ `ready-to-consume` - Task complete, ready for integration
- ⏹️ `blocked` - Task is blocked by dependency
- ✓ `completed` - Task integrated and validated

---

**For details on any task**, see: `agent-sync/tasks/<task-id>.md`
"""
        
        index_path.write_text(content, encoding="utf-8")
        return index_path
    
    def _format_task_summary(self, tasks_by_role: dict[str, list[Path]]) -> str:
        """Format task summary by role."""
        lines = []
        for role, tasks in sorted(tasks_by_role.items()):
            lines.append(f"- **{role}**: {len(tasks)} task(s)")
        return "\n".join(lines) if lines else "- No tasks"
    
    def _format_task_list(self, task_cards: list[Path]) -> str:
        """Format complete task list."""
        lines = []
        for card_path in sorted(task_cards):
            task_id = card_path.stem
            lines.append(f"- [{task_id}]({card_path.name})")
        return "\n".join(lines) if lines else "- No tasks"
    
    def _format_start_commands(self, task_cards: list[Path]) -> str:
        """Format start commands for all tasks."""
        lines = []
        for card_path in sorted(task_cards):
            task_id = card_path.stem
            # Parse role from task ID
            parts = task_id.split('-')
            role = '-'.join(parts[3:-1]).lower().replace('-', '_') if len(parts) > 4 else 'unknown'
            lines.append(f"/{role}::start_task({task_id})")
        return "\n".join(lines) if lines else "# No tasks"


def generate_task_cards(
    iteration_name: str,
    iteration_config: dict,
    repo_root: Path,
    date_str: Optional[str] = None,
    tasks_dir: Optional[Path] = None,
) -> list[Path]:
    """
    Convenience function to generate task cards.
    
    Args:
        iteration_name: Name of the iteration
        iteration_config: Iteration configuration dict
        repo_root: Repository root directory (task cards are written to agent-sync/tasks)
        date_str: Optional date string (defaults to today)
        tasks_dir: Optional explicit tasks directory (overrides <repo_root>/agent-sync/tasks)
        
    Returns:
        List of generated task card paths
    """
    generator = TaskCardGenerator(repo_root, tasks_dir=tasks_dir)
    return generator.generate_from_iteration(iteration_name, iteration_config, date_str)


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    
    # Example iteration config
    example_config = {
        'name': 'requirements-extraction',
        'goal': 'Extract and document requirements from user stories',
        'agents': [
            {
                'role': 'product_analyst',
                'inputs': ['US-E01-010', 'US-E01-020'],
                'deliverables': [
                    {'path': 'work_items/E01/US-E01-010.md', 'description': 'Requirements analysis'},
                    {'path': 'work_items/E01/US-E01-020.md', 'description': 'Requirements analysis'},
                ],
                'token_budget': 5000,
                'priority': 'High',
                'effort': '2-3 hours',
            },
            {
                'role': 'backend_developer',
                'inputs': ['US-E02-010'],
                'deliverables': [
                    {'path': 'work_items/E02/US-E02-010.md', 'description': 'Technical design'},
                ],
                'token_budget': 8000,
                'dependencies': ['product_analyst'],
            },
        ],
        'completion_criteria': {
            'requirements': [
                'All work items have complete requirements',
                'Technical designs are documented',
                'Acceptance criteria are testable',
            ]
        }
    }
    
    # Generate task cards
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        print("Generating task cards...")
        print("=" * 70)
        
        task_cards = generate_task_cards(
            'requirements-extraction',
            example_config,
            output_dir,
            '2026-01-10'
        )
        
        print(f"\n✓ Generated {len(task_cards)} task cards:")
        for card_path in task_cards:
            print(f"  - {card_path.name}")
        
        # Show INDEX content
        index_path = output_dir / "agent-sync" / "tasks" / "2026-01-10_requirements-extraction_INDEX.md"
        if index_path.exists():
            print(f"\n✓ Generated INDEX: {index_path.name}")
            print("\nINDEX Preview:")
            print("-" * 70)
            content = index_path.read_text()
            # Show first 30 lines
            lines = content.split('\n')[:30]
            print('\n'.join(lines))
            if len(content.split('\n')) > 30:
                print("...")
