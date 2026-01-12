# Contributing to mixed-sample

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
git switch main
git worktree add -b <type>/<scope>/<short-desc> \
  ../mixed-sample.worktrees/<agent>/<type>-<short-desc> \
  main
```

### Work in Your Worktree

```bash
cd ../mixed-sample.worktrees/<agent>/<branch>
# Make changes, commit, etc.
```

### Announce Ready-to-Consume

Post a memo to `.orchestration/runtime/agent-sync/`:

```markdown
- **Date**: 2026-01-12
- **Audience**: `@integrator`
- **Status**: `ready-to-consume`
- **Branch**: `<branch>`
- **SHA**: `<sha>`
- **Work Item**: <work-item-id>
- **Deliverables**:
  - <path1> (created/updated)
  - <path2> (created/updated)
```

See `.orchestration/runtime/agent-sync/COMMAND_SHORTHAND.md` for complete command reference.

## Integration

The integrator role manages convergence of ready-to-consume work:

```bash
/integrator::apply_ready
```

This will:
- Scan `.orchestration/runtime/agent-sync/` for ready-to-consume memos
- Cherry-pick or merge agent work
- Run merge gate checks (validation, tests, coverage)
- Update memos to ready-to-merge

## Framework Documentation

- **Getting Started**: `orchestration-framework/README.md`
- **Command Reference**: `.orchestration/runtime/agent-sync/COMMAND_SHORTHAND.md`
- **Workflow Catalog**: `orchestration-framework/WORKFLOW_CATALOG.md`
- **Agent Roles**: `orchestration-framework/AGENT_ROLE_LIBRARY.md`

## Configuration

Framework configuration is in: `orchestration-framework/config.yaml`

Customize:
- Project name and trunk branch
- Worktree location
- Agent roles
- Merge gate settings
- Token budget limits

## Getting Help

- Read the framework docs in `orchestration-framework/`
- Check examples in `orchestration-framework/examples/`
- Review completed iterations in `.orchestration/runtime/iterations/`
