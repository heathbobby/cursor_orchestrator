#!/usr/bin/env python3
"""
Command parser for Generic Orchestration Framework.

Parses slash commands into structured format for programmatic execution.

Example:
    /orchestrator::start_workflow(user-story-refinement, phase-1, iter-1)
    -> {
        'role': 'orchestrator',
        'command': 'start_workflow',
        'args': ['user-story-refinement', 'phase-1', 'iter-1']
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ParsedCommand:
    """Represents a parsed slash command."""
    role: str
    command: str
    args: list[str]
    raw: str
    
    def __str__(self) -> str:
        args_str = ", ".join(self.args) if self.args else ""
        return f"/{self.role}::{self.command}({args_str})"
    
    @property
    def is_orchestrator(self) -> bool:
        """Check if command is for orchestrator role."""
        return self.role == "orchestrator"
    
    @property
    def is_integrator(self) -> bool:
        """Check if command is for integrator role."""
        return self.role == "integrator"
    
    @property
    def is_role_command(self) -> bool:
        """Check if command is for a specific agent role."""
        return not (self.is_orchestrator or self.is_integrator)


class CommandParser:
    """Parser for slash commands."""
    
    # Pattern: /role::command or /role::command(arg1, arg2, ...)
    COMMAND_PATTERN = re.compile(
        r'^/(?P<role>[\w-]+)::(?P<command>[\w-]+)(?:\((?P<args>[^)]*)\))?$'
    )
    
    def parse(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse a slash command into structured format.
        
        Args:
            command: Slash command string
            
        Returns:
            ParsedCommand if valid, None otherwise
            
        Examples:
            >>> parser = CommandParser()
            >>> cmd = parser.parse("/orchestrator::start_workflow(workflow, phase, iter)")
            >>> cmd.role
            'orchestrator'
            >>> cmd.command
            'start_workflow'
            >>> cmd.args
            ['workflow', 'phase', 'iter']
        """
        command = command.strip()
        
        match = self.COMMAND_PATTERN.match(command)
        if not match:
            return None
        
        role = match.group('role')
        cmd = match.group('command')
        args_str = match.group('args')
        
        # Parse arguments
        args = []
        if args_str:
            # Split by comma, strip whitespace, preserve quotes
            args = [arg.strip().strip('"\'') for arg in args_str.split(',')]
            args = [arg for arg in args if arg]  # Remove empty strings
        
        return ParsedCommand(
            role=role,
            command=cmd,
            args=args,
            raw=command
        )
    
    def is_valid_command(self, command: str) -> bool:
        """Check if command matches slash command format."""
        return self.COMMAND_PATTERN.match(command.strip()) is not None


class CommandValidator:
    """Validates parsed commands against known commands."""
    
    # Known orchestrator commands
    ORCHESTRATOR_COMMANDS = {
        'start_workflow',
        'generate_iteration',
        'monitor_progress',
        'launch_agents',
        'apply_ready_to',
        'ingest_project',
        'derive_roles',
    }
    
    # Known integrator commands
    INTEGRATOR_COMMANDS = {
        'apply_ready',
        'validate_iteration',
        'distribute_tasks',
    }
    
    # Known role commands (generic, applicable to any role)
    ROLE_COMMANDS = {
        'start_task',
        'start_next',
        'report_token_usage',
    }
    
    def validate(self, cmd: ParsedCommand) -> tuple[bool, Optional[str]]:
        """
        Validate a parsed command.
        
        Args:
            cmd: Parsed command to validate
            
        Returns:
            (is_valid, error_message) tuple
            
        Examples:
            >>> validator = CommandValidator()
            >>> cmd = ParsedCommand('orchestrator', 'start_workflow', ['w', 'p', 'i'], '/...')
            >>> valid, error = validator.validate(cmd)
            >>> valid
            True
        """
        if cmd.is_orchestrator:
            return self._validate_orchestrator(cmd)
        elif cmd.is_integrator:
            return self._validate_integrator(cmd)
        else:
            return self._validate_role(cmd)
    
    def _validate_orchestrator(self, cmd: ParsedCommand) -> tuple[bool, Optional[str]]:
        """Validate orchestrator command."""
        if cmd.command not in self.ORCHESTRATOR_COMMANDS:
            return False, f"Unknown orchestrator command: {cmd.command}"
        
        # Validate argument counts
        if cmd.command == 'start_workflow' and len(cmd.args) != 3:
            return False, f"start_workflow requires 3 args (workflow, phase, iteration), got {len(cmd.args)}"
        
        if cmd.command == 'generate_iteration' and len(cmd.args) != 1:
            return False, f"generate_iteration requires 1 arg (iteration), got {len(cmd.args)}"
        
        if cmd.command == 'monitor_progress' and len(cmd.args) != 1:
            return False, f"monitor_progress requires 1 arg (iteration), got {len(cmd.args)}"

        if cmd.command == 'launch_agents' and len(cmd.args) < 1:
            return False, "launch_agents requires at least 1 arg (iteration)"
        if cmd.command == 'launch_agents' and len(cmd.args) > 6:
            return False, f"launch_agents accepts up to 6 args (iteration[, parallel][, max_parallel][, apply-ready][, apply-ready-each][, dry-run]), got {len(cmd.args)}"
        
        if cmd.command == 'apply_ready_to' and len(cmd.args) not in (1, 2):
            return False, f"apply_ready_to requires 1-2 args (target_branch[, dry-run]), got {len(cmd.args)}"

        if cmd.command == 'ingest_project' and len(cmd.args) > 2:
            return False, f"ingest_project accepts 0-2 args ([path][, dry-run]), got {len(cmd.args)}"

        if cmd.command == 'derive_roles' and len(cmd.args) > 2:
            return False, f"derive_roles accepts 0-2 args ([path][, dry-run]), got {len(cmd.args)}"

        return True, None
    
    def _validate_integrator(self, cmd: ParsedCommand) -> tuple[bool, Optional[str]]:
        """Validate integrator command."""
        if cmd.command not in self.INTEGRATOR_COMMANDS:
            return False, f"Unknown integrator command: {cmd.command}"
        
        # Validate argument counts
        if cmd.command == 'apply_ready' and len(cmd.args) > 2:
            return False, f"apply_ready accepts 0-2 args (optional: <target-branch>, dry-run), got {len(cmd.args)}"
        
        if cmd.command == 'validate_iteration' and len(cmd.args) != 1:
            return False, f"validate_iteration requires 1 arg (iteration), got {len(cmd.args)}"
        
        if cmd.command == 'distribute_tasks' and len(cmd.args) != 1:
            return False, f"distribute_tasks requires 1 arg (iteration), got {len(cmd.args)}"
        
        # Light semantic validation for apply_ready args.
        if cmd.command == 'apply_ready' and cmd.args:
            # allow 'dry-run' anywhere; allow at most one non-dry-run arg (treated as branch override)
            non_flags = [a for a in cmd.args if a != "dry-run"]
            if len(non_flags) > 1:
                return False, "apply_ready accepts at most one target branch override (plus optional dry-run)"
            if any(not a.strip() for a in cmd.args):
                return False, "apply_ready args must be non-empty"

        return True, None
    
    def _validate_role(self, cmd: ParsedCommand) -> tuple[bool, Optional[str]]:
        """Validate role command."""
        if cmd.command not in self.ROLE_COMMANDS:
            return False, f"Unknown role command: {cmd.command}"
        
        # Validate argument counts
        if cmd.command == 'start_task' and len(cmd.args) != 1:
            return False, f"start_task requires 1 arg (work_item_id), got {len(cmd.args)}"
        
        if cmd.command == 'start_next' and len(cmd.args) != 0:
            return False, f"start_next requires 0 args, got {len(cmd.args)}"
        
        if cmd.command == 'report_token_usage' and len(cmd.args) != 0:
            return False, f"report_token_usage requires 0 args, got {len(cmd.args)}"
        
        return True, None


def parse_command(command: str) -> Optional[ParsedCommand]:
    """
    Convenience function to parse a slash command.
    
    Args:
        command: Slash command string
        
    Returns:
        ParsedCommand if valid, None otherwise
    """
    parser = CommandParser()
    return parser.parse(command)


def validate_command(cmd: ParsedCommand) -> tuple[bool, Optional[str]]:
    """
    Convenience function to validate a parsed command.
    
    Args:
        cmd: Parsed command to validate
        
    Returns:
        (is_valid, error_message) tuple
    """
    validator = CommandValidator()
    return validator.validate(cmd)


if __name__ == "__main__":
    # Example usage and testing
    parser = CommandParser()
    validator = CommandValidator()
    
    test_commands = [
        "/orchestrator::start_workflow(user-story-refinement, phase-1, iter-1)",
        "/integrator::apply_ready",
        "/integrator::apply_ready(dry-run)",
        "/product_analyst::start_task(US-E01-010)",
        "/backend_developer::start_next",
        "/invalid::command",
        "not a command",
    ]
    
    print("Testing command parser:")
    print("=" * 70)
    
    for test_cmd in test_commands:
        print(f"\nInput: {test_cmd}")
        
        parsed = parser.parse(test_cmd)
        if parsed:
            print(f"  OK Parsed: {parsed}")
            valid, error = validator.validate(parsed)
            if valid:
                print(f"  OK Valid")
            else:
                print(f"  ERR Invalid: {error}")
        else:
            print(f"  ERR Parse failed")
