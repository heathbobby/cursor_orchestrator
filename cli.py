#!/usr/bin/env python3
"""
Command-Line Interface for Generic Orchestration Framework.

Provides a CLI for executing orchestration commands and managing workflows.
"""

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `tools` can be imported as a package.
sys.path.insert(0, str(Path(__file__).parent))

from tools.command_parser import parse_command, validate_command
from tools.command_router import execute_command, get_router
from tools.repo_utils import find_repo_root
from tools.config_loader import load_config
from tools.env_loader import load_dotenv, load_dotenv_searching_parents


def _configure_stdout() -> None:
    """
    Make CLI output robust on Windows consoles with limited default encodings.

    We also avoid relying on Unicode glyphs in user-visible output elsewhere,
    but this helps prevent crashes if any slip through.
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # Best-effort only.
        pass


def cmd_execute(args):
    """Execute a slash command."""
    command = args.command
    
    print(f"Executing: {command}")
    print("-" * 70)
    
    # Parse command
    parsed = parse_command(command)
    if not parsed:
        print("ERROR: Invalid command format")
        print(f"\nExpected format: /role::command(arg1, arg2, ...)")
        print(f"Example: /orchestrator::start_workflow(workflow, phase, iteration)")
        return 1
    
    print(f"OK: Parsed: {parsed}")
    
    # Validate command
    valid, error = validate_command(parsed)
    if not valid:
        print(f"ERROR: {error}")
        return 1
    
    print("OK: Valid")
    
    # Execute command
    print(f"\nExecuting...")
    repo_root = find_repo_root(Path.cwd())
    # Load `.env` so provider tokens like GITHUB_TOKEN work automatically.
    # Prefer repo_root/.env; fallback to searching parents (useful in mono-repo/testing layouts).
    res = load_dotenv(repo_root / ".env", override=False)
    if not res.loaded:
        load_dotenv_searching_parents(Path.cwd(), max_depth=8, override=False)
    config = load_config(repo_root)
    trunk_branch = (config.get("project") or {}).get("trunk_branch", "main")
    result = execute_command(
        parsed,
        context={
            'cwd': Path.cwd(),
            'repo_root': repo_root,
            'config': config,
            'trunk_branch': trunk_branch,
        },
    )
    
    print(f"\n{result}")
    
    if result.data:
        print(f"\nResult Data:")
        for key, value in result.data.items():
            print(f"  {key}: {value}")
    
    return 0 if result.success else 1


def cmd_list_commands(args):
    """List available commands."""
    repo_root = find_repo_root(Path.cwd())
    res = load_dotenv(repo_root / ".env", override=False)
    if not res.loaded:
        load_dotenv_searching_parents(Path.cwd(), max_depth=8, override=False)
    router = get_router()
    commands = router.list_commands(args.role)
    
    print("Available Commands:")
    print("=" * 70)
    
    for role, cmds in sorted(commands.items()):
        if not cmds:
            continue
        
        print(f"\n{role.upper()} Commands:")
        for cmd in sorted(cmds):
            print(f"  /{role}::{cmd}")
    
    print()
    return 0


def cmd_validate(args):
    """Validate a command without executing it."""
    command = args.command
    
    print(f"Validating: {command}")
    print("-" * 70)
    
    # Parse command
    parsed = parse_command(command)
    if not parsed:
        print("ERROR: Parse failed: Invalid command format")
        return 1
    
    print("OK: Parsed successfully")
    print(f"  Role: {parsed.role}")
    print(f"  Command: {parsed.command}")
    print(f"  Args: {parsed.args}")
    
    # Validate command
    valid, error = validate_command(parsed)
    if not valid:
        print(f"ERROR: Validation failed: {error}")
        return 1
    
    print("OK: Valid command")
    return 0


def cmd_interactive(args):
    """Interactive command mode."""
    print("Generic Orchestration Framework - Interactive Mode")
    print("=" * 70)
    print("Enter commands (or 'help', 'list', 'exit'):")
    print()

    repo_root = find_repo_root(Path.cwd())
    res = load_dotenv(repo_root / ".env", override=False)
    if not res.loaded:
        load_dotenv_searching_parents(Path.cwd(), max_depth=8, override=False)
    config = load_config(repo_root)
    trunk_branch = (config.get("project") or {}).get("trunk_branch", "main")
    
    while True:
        try:
            command = input(">>> ").strip()
            
            if not command:
                continue
            
            if command in ('exit', 'quit', 'q'):
                print("Goodbye!")
                break
            
            if command == 'help':
                print("\nCommands:")
                print("  /role::command(args) - Execute a command")
                print("  list - List available commands")
                print("  help - Show this help")
                print("  exit - Exit interactive mode")
                print()
                continue
            
            if command == 'list':
                cmd_list_commands(argparse.Namespace(role=None))
                continue
            
            # Execute command
            parsed = parse_command(command)
            if not parsed:
                print("ERROR: Invalid command format")
                print("Use: /role::command(arg1, arg2, ...)")
                continue
            
            valid, error = validate_command(parsed)
            if not valid:
                print(f"ERROR: {error}")
                continue
            
            result = execute_command(
                parsed,
                context={
                    'cwd': Path.cwd(),
                    'repo_root': repo_root,
                    'config': config,
                    'trunk_branch': trunk_branch,
                },
            )
            print(result)
            
            if result.data:
                print("Data:", result.data)
            print()
            
        except KeyboardInterrupt:
            print("\nInterrupted. Use 'exit' to quit.")
            continue
        except EOFError:
            print("\nGoodbye!")
            break
    
    return 0


def main():
    """Main CLI entry point."""
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description='Generic Orchestration Framework CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute a command
  %(prog)s execute "/orchestrator::start_workflow(workflow1, phase1, iter1)"
  
  # List available commands
  %(prog)s list
  
  # List commands for specific role
  %(prog)s list --role orchestrator
  
  # Validate a command
  %(prog)s validate "/integrator::apply_ready"
  
  # Interactive mode
  %(prog)s interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Execute command
    execute_parser = subparsers.add_parser(
        'execute',
        aliases=['exec', 'run'],
        help='Execute a slash command'
    )
    execute_parser.add_argument(
        'command',
        help='Slash command to execute (e.g., /orchestrator::start_workflow(...))'
    )
    execute_parser.set_defaults(func=cmd_execute)
    
    # List commands
    list_parser = subparsers.add_parser(
        'list',
        aliases=['ls'],
        help='List available commands'
    )
    list_parser.add_argument(
        '--role',
        help='Filter by role (orchestrator, integrator, role)'
    )
    list_parser.set_defaults(func=cmd_list_commands)
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        aliases=['check'],
        help='Validate a command without executing it'
    )
    validate_parser.add_argument(
        'command',
        help='Slash command to validate'
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    # Interactive mode
    interactive_parser = subparsers.add_parser(
        'interactive',
        aliases=['i', 'repl'],
        help='Interactive command mode'
    )
    interactive_parser.set_defaults(func=cmd_interactive)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
