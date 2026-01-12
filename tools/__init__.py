"""
Generic Orchestration Framework - Tools Package

Command-line tools and utilities for the orchestration framework.
"""

from .command_parser import (
    CommandParser,
    CommandValidator,
    ParsedCommand,
    parse_command,
    validate_command,
)

from .command_router import (
    CommandResult,
    CommandRouter,
    execute_command,
    get_router,
    register_handler,
)

from .task_cards import (
    TaskCard,
    TaskCardGenerator,
    generate_task_cards,
)

from .worktree_manager import (
    Worktree,
    WorktreeManager,
    create_agent_worktree,
)

from .memo_scanner import (
    Memo,
    MemoScanner,
    scan_ready_to_consume,
)

from .integration_manager import (
    IntegrationResult,
    IntegrationManager,
)

__all__ = [
    # Parser
    'CommandParser',
    'CommandValidator',
    'ParsedCommand',
    'parse_command',
    'validate_command',
    # Router
    'CommandResult',
    'CommandRouter',
    'execute_command',
    'get_router',
    'register_handler',
    # Task Cards
    'TaskCard',
    'TaskCardGenerator',
    'generate_task_cards',
    # Worktrees
    'Worktree',
    'WorktreeManager',
    'create_agent_worktree',
    # Memos
    'Memo',
    'MemoScanner',
    'scan_ready_to_consume',
    # Integration
    'IntegrationResult',
    'IntegrationManager',
]
