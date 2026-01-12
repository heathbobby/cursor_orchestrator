# Agent-Sync Communication Conventions

**Purpose**: Make cross-agent coordination fast and unambiguous through structured communication.

---

## Overview

When multiple AI agents work concurrently on a project, clear communication is essential. This document defines:
- **Memo format** for coordination
- **Status definitions** for work tracking
- **Role targeting** for audience clarity
- **Command shorthand** for efficiency

---

## Coordination Memos

### Required Header

At the top of each coordination memo in `agent-sync/`, include:

```markdown
- **Date**: YYYY-MM-DD
- **Audience**: `@role1 @role2` (or `@all`)
- **Status**: `draft` | `ready-to-consume` | `ready-to-merge` | `blocked`
- **Branch**: `<branch-name>` (if applicable)
- **SHA**: `<commit-sha>` (if applicable)
```

---

## Status Definitions

### `draft`
- Work in progress
- Not ready for consumption by other agents
- May have incomplete sections or TODOs
- Updates expected

### `ready-to-consume`
- Safe for other agents to use as dependency
- Branch contains complete, working changes
- Not yet merged to trunk
- Other agents can merge or cherry-pick

### `ready-to-merge`
- Passed all quality gates
- Safe to merge into trunk
- Integration complete
- No blockers

### `blocked`
- Waiting on dependency
- Blocked by external factor
- Requires input or decision
- Cannot proceed until unblocked

---

## Role Tags

Use these role tags in the **Audience** line to target specific agents:

### Orchestration Roles
- `@orchestrator` — Workflow coordination, iteration management
- `@integrator` — Integration queue management, convergence, trunk stewardship

### Development Roles
- `@backend_developer` — Backend implementation, APIs, services
- `@frontend_developer` — UI/UX implementation, frontend features
- `@mobile_developer` — iOS/Android development
- `@devops_engineer` — Infrastructure, CI/CD, deployment

### Quality Roles
- `@qa_engineer` — Test planning, test implementation, quality assurance
- `@qa_lead` — Test strategy, acceptance criteria
- `@test_automation_engineer` — Test automation framework
- `@performance_engineer` — Performance testing, optimization

### Product & Design Roles
- `@product_analyst` — Requirements analysis, business logic
- `@ux_designer` — User experience design, workflows
- `@ui_designer` — Visual design, components

### Operations Roles
- `@sre` — Site reliability, operational runbooks
- `@security_engineer` — Security review, threat modeling
- `@data_engineer` — Data pipelines, ETL

### Documentation Roles
- `@tech_writer` — User documentation, guides
- `@api_documenter` — API documentation, SDKs

### Special Audiences
- `@all` — All agents (use sparingly)
- `@<custom-role>` — Project-specific roles

**See**: `../AGENT_ROLE_LIBRARY.md` for complete role definitions

---

## File Naming Convention

Use this format for coordination memos:

```
agent-sync/YYYY-MM-DD_<role>_<topic>.md
```

**Examples**:
- `agent-sync/2026-01-10_product-analyst_US-E01-010.md`
- `agent-sync/2026-01-10_integrator_integration-complete.md`
- `agent-sync/2026-01-10_orchestrator_task-dispatch.md`

**For initiatives or multi-agent coordination**:
```
agent-sync/YYYY-MM-DD_initiative_<topic>.md
```

---

## Ready-to-Consume Announcement Template

When your work is ready for others to consume, post this memo:

```markdown
# Ready-to-Consume: <Work Item ID or Topic>

- **Date**: YYYY-MM-DD
- **Audience**: `@integrator` (and any directly impacted roles)
- **Status**: `ready-to-consume`
- **Branch**: `<branch-name>`
- **SHA**: `<commit-sha>`

## What Changed

- <Summary of changes>
- <Key deliverables>

## Why It Matters

- <Business/technical value>
- <Dependencies satisfied>

## How to Consume

```bash
# Option 1: Merge branch
git merge <branch-name>

# Option 2: Cherry-pick commits
git cherry-pick <sha>
```

## Deliverables

- `<path1>` (created/updated)
- `<path2>` (created/updated)

## Token Usage

- Tokens Used: X,XXX / X,XXX (XX%)
- Status: ✅ Within budget | ⚠️ Approaching limit | ❌ Over budget

## Caveats

- <Any limitations or known issues>
- <Dependencies or prerequisites>

## Next Steps

- <What should happen next>
- <Who should take action>
```

---

## Command Shorthand (Slash Commands)

For faster agent coordination, use slash commands instead of verbose prompts.

### Quick Reference

```bash
# Orchestration
/orchestrator::start_workflow(<workflow>, <phase>, <iteration>)
/orchestrator::generate_iteration(<iteration>)
/orchestrator::monitor_progress(<iteration>)

# Integration
/integrator::apply_ready
/integrator::validate_iteration(<iteration>)
/integrator::distribute_tasks(<iteration>)

# Role-Specific
/<role>::start_task(<work-item-id>)
/<role>::start_next
/<role>::report_token_usage
```

**Complete command reference**: See `COMMAND_SHORTHAND.md`

---

## Memo Examples

### Example 1: Ready-to-Consume Work

```markdown
# Ready-to-Consume: US-E01-010 Requirements Analysis

- **Date**: 2026-01-10
- **Audience**: `@integrator @backend_developer`
- **Status**: `ready-to-consume`
- **Branch**: `feat/product-analyst/US-E01-010`
- **SHA**: `a3f4c2b`

## What Changed

- Completed requirements analysis for user authentication
- Documented technical specifications
- Defined acceptance criteria
- Identified dependencies

## How to Consume

```bash
git merge feat/product-analyst/US-E01-010
```

## Deliverables

- `work_items/E01/US-E01-010.md` (updated with full specifications)

## Token Usage

- Tokens Used: 4,234 / 5,000 (85%)
- Status: ⚠️ Approaching limit

## Next Steps

- Backend developer can begin implementation
- QA engineer can write test cases
```

---

### Example 2: Integration Complete

```markdown
# Integration Complete: Iteration Requirements-Extraction

- **Date**: 2026-01-10
- **Audience**: `@orchestrator @all`
- **Status**: `ready-to-merge`
- **Branch**: `integration/2026-01-10`
- **SHA**: `b7d8e5a`

## What Changed

- Integrated 5 agent contributions
- All merge gates passed
- 15 work items refined

## Merge Gates Status

- ✅ Deliverables validation (15/15 files present)
- ✅ Token budget check (all agents within budget)
- ✅ Test coverage (N/A for documentation)
- ✅ No conflicts

## How to Consume

```bash
git merge integration/2026-01-10
```

## Next Steps

- Ready to proceed to next iteration
- Orchestrator can start Phase 2
```

---

### Example 3: Blocked Work

```markdown
# Blocked: API Integration Tests

- **Date**: 2026-01-10
- **Audience**: `@integrator @backend_developer`
- **Status**: `blocked`
- **Branch**: `feat/qa-engineer/api-tests`
- **SHA**: `c9e1f3d`

## Blocker

Cannot complete API integration tests because authentication endpoint
is not yet implemented.

## Dependencies

- Waiting on: US-E05-010 (OIDC SSO implementation)
- Blocked by: @backend_developer
- Estimated unblock: 2026-01-12

## Work Completed So Far

- Test framework setup
- Mock data created
- Test cases defined (but cannot execute)

## Next Steps

- Resume when US-E05-010 is ready-to-consume
- @backend_developer please post memo when auth endpoint is complete
```

---

## Communication Best Practices

### 1. **Be Specific**
- ❌ "Updated some files"
- ✅ "Updated work_items/E01/US-E01-010.md with technical specifications"

### 2. **Include Context**
- ❌ "Changes ready"
- ✅ "Requirements analysis complete. Backend team can begin implementation."

### 3. **Tag the Right Audience**
- ❌ `@all` for everything
- ✅ `@integrator @backend_developer` (only relevant roles)

### 4. **Update Status Promptly**
- Post memos when work transitions (draft → ready-to-consume → ready-to-merge)
- Update blocked work when unblocked

### 5. **Track Token Usage**
- Report token usage in ready-to-consume memos
- Flag if approaching budget limit
- Helps orchestrator manage future allocations

### 6. **Use Commands When Possible**
- ❌ Long prompt asking agent to start task
- ✅ `/product_analyst::start_task(US-E01-010)`

---

## Task Cards

Task cards in `agent-sync/tasks/` provide structured work items for agents.

### Task Card Location
```
agent-sync/tasks/
├── 2026-01-10_iteration_INDEX.md
├── 2026-01-10_iteration_PROD-01.md
├── 2026-01-10_iteration_BACK-01.md
└── 2026-01-10_iteration_QA-01.md
```

### Task Card Format

See `COMMAND_SHORTHAND.md` for complete task card format.

---

## Worktree Operating Model

When agents work concurrently using worktrees, follow these conventions:

### Worktree Layout
```
../<project>.worktrees/
├── product-analyst/
│   └── feat-US-E01-010/
├── backend-developer/
│   └── feat-US-E02-020/
└── qa-engineer/
    └── feat-US-E03-030/
```

### Worktree Guidelines
- **One agent = one branch = one worktree**
- Never work directly in repo root during concurrent work
- Clean up worktrees after merging
- Use descriptive branch names (conventional commits format)

**Complete worktree guide**: See `WORKTREE_OPERATING_MODEL.md` (if available)

---

## Integration Workflow

### Phase 1: Agents Work in Isolation
- Each agent works in their worktree
- Commits to their branch
- Posts memos as work progresses

### Phase 2: Announce Ready-to-Consume
- Agent posts ready-to-consume memo with Branch+SHA
- Integrator is notified via `@integrator` tag

### Phase 3: Integration
- Integrator runs: `/integrator::apply_ready`
- Cherry-picks or merges agent work
- Runs merge gate checks
- Updates memos to ready-to-merge

### Phase 4: Validation
- Integrator runs: `/integrator::validate_iteration(<iteration>)`
- Checks all completion criteria
- Posts validation report

### Phase 5: Merge to Trunk
- Integration branch merged to trunk
- Worktrees cleaned up
- Next iteration can begin

---

## Questions & Troubleshooting

### Q: When should I post a memo?
**A**: Post a memo when:
- Work transitions status (draft → ready-to-consume → ready-to-merge)
- You're blocked and need help
- You complete a significant deliverable
- Other agents need to know about your work

### Q: Can I update an existing memo?
**A**: Yes! Update the memo when status changes. Keep the same filename but update:
- Status field
- SHA (if new commits)
- Add updates section

### Q: What if I don't know the right role tag?
**A**: Use `@integrator` — they'll route to appropriate agent. Or check `../AGENT_ROLE_LIBRARY.md`.

### Q: Do I need memos for every commit?
**A**: No. Post memos when work is ready to consume or when status changes. Not for every commit.

### Q: How do I discover available tasks?
**A**: Check `agent-sync/tasks/*_INDEX.md` for task list. Or use `/<role>::start_next` command.

---

**For complete orchestration guide**, see: `../README.md`

**For command reference**, see: `COMMAND_SHORTHAND.md`

**For role definitions**, see: `../AGENT_ROLE_LIBRARY.md`
