# Agent Command Shorthand (Protocol)

This framework uses **human-friendly, copy/paste command shorthand** to reduce manual prompting overhead when coordinating multiple AI agents.

These commands are **conventions** (not enforced by the IDE). Agents must be prompted (via boot prompts) to recognize and follow them.

---

## Goals

- **Reduce prompting overhead** - One short command instead of verbose prompts (95% reduction)
- **Standardize task dispatch** - Consistent format for assigning work
- **Enable automation** - Commands map to CLI operations for future automation
- **Improve coordination** - Clear, unambiguous instructions between agents

---

## Command Format

Commands are written like:

```text
/<role>::<command>(<args>)
```

**Examples**:
```text
/orchestrator::start_workflow(user-story-refinement, phase-1, iteration-1)
/product_analyst::start_task(US-E01-010)
/integrator::apply_ready
```

---

## Supported Commands

### Orchestrator Commands

#### `/orchestrator::start_workflow(<workflow>, <phase>, <iteration>)`

**Intent**: Start complete workflow with all agents in isolated worktrees

**Expected Output**:
- Generate iteration structure from workflow YAML
- Create CONTEXT.md and COMPLETION_CRITERIA.md
- Generate agent-specific prompts
- Create worktrees for each agent (if enabled)
- Generate task cards in `agent-sync/tasks/`
- Post task dispatch memo with copy/paste commands for each agent

**CLI Equivalent**:
```bash
python orchestration-framework/cli.py start-workflow \
  --workflow <workflow> \
  --phase <phase> \
  --iteration <iteration>
```

---

#### `/orchestrator::generate_iteration(<iteration-name>)`

**Intent**: Generate iteration structure without starting agents

**Expected Output**:
- Read workflow configuration
- Generate CONTEXT.md, COMPLETION_CRITERIA.md
- Generate agent-specific prompts
- Output agent allocation summary

**CLI Equivalent**:
```bash
python orchestration-framework/tools/generate_prompts.py \
  --workflow workflows/<workflow>.yaml \
  --iteration <iteration-name> \
  --output iterations/<iteration-name>/
```

---

#### `/orchestrator::monitor_progress(<iteration>)`

**Intent**: Show real-time progress of iteration execution

**Expected Output**:
- Agent status (running, completed, blocked)
- Deliverables progress
- Token budget utilization
- Ready-to-consume memos

**CLI Equivalent**:
```bash
python orchestration-framework/tools/monitor_enhanced.sh \
  iterations/<iteration>/
```

---

### Integrator Commands

#### `/integrator::apply_ready`

**Intent**: Converge all "ready-to-consume" work into integration branch

**Default Behavior**:
- Scan `agent-sync/` for ready-to-consume memos
- Cherry-pick or merge each agent's work
- Run merge gate checks (validation, token budget, tests, coverage)
- Update memos to ready-to-merge status
- Commit updated integration queue memo

**CLI Equivalent**:
```bash
python orchestration-framework/cli.py integrate apply-ready \
  --target-branch integration/$(date +%Y-%m-%d) \
  --run-merge-gates
```

**Dry-run Variant**: `/integrator::apply_ready(dry-run)`
```bash
python orchestration-framework/cli.py integrate apply-ready \
  --target-branch integration/$(date +%Y-%m-%d) \
  --dry-run
```

---

#### `/integrator::validate_iteration(<iteration>)`

**Intent**: Validate iteration deliverables against completion criteria

**Expected Output**:
- File existence checks
- File size validation
- Content validation (if specified)
- Completion criteria checklist
- Validation report (pass/fail)

**CLI Equivalent**:
```bash
python orchestration-framework/tools/validate_iteration.sh \
  iterations/<iteration>/
```

---

#### `/integrator::distribute_tasks(<iteration>)`

**Intent**: Generate task cards and dispatch memo for iteration

**Expected Output**:
- Task cards in `agent-sync/tasks/<date>_<iteration>_<taskId>.md`
- Task INDEX in `agent-sync/tasks/<date>_<iteration>_INDEX.md`
- Task dispatch memo in `agent-sync/`
- Copy/paste command list for starting tasks

**CLI Equivalent**:
```bash
python orchestration-framework/cli.py tasks generate \
  --iteration <iteration> \
  --output agent-sync/tasks/
```

---

### Role-Specific Commands

#### `/<role>::start_task(<work-item-id>)`

**Intent**: Execute a specific work item

**Examples**:
- `/product_analyst::start_task(US-E01-010)`
- `/backend_developer::start_task(US-E02-020)`
- `/qa_engineer::start_task(US-E03-030)`
- `/tech_writer::start_task(US-E04-040)`
- `/sre::start_task(US-E05-050)`

**Agent Behavior**:
1. Locate work item file (e.g., `work_items/E01/US-E01-010.md`)
2. Execute all deliverables specified in agent prompt for that work item
3. Commit changes to agent's worktree branch
4. Post ready-to-consume memo to `agent-sync/`:

```markdown
- **Date**: YYYY-MM-DD
- **Audience**: `@integrator`
- **Status**: `ready-to-consume`
- **Branch**: `<branch-name>`
- **SHA**: `<commit-sha>`
- **Work Item**: <work-item-id>
- **Deliverables**:
  - <path1> (created/updated)
  - <path2> (created/updated)
- **Token Usage**: <tokens> / <budget> (<percentage>%)
```

---

#### `/<role>::start_next`

**Intent**: Execute the **next highest-priority** work item for the role

**Agent Behavior**:
1. Locate latest task dispatch memo or INDEX:
   - Prefer: `agent-sync/*_integrator_*_task-dispatch.md`
   - Fallback: `agent-sync/tasks/*_INDEX.md`
2. From task list, select first task assigned to role with `Status: ready-to-start`
3. Execute as `/<role>::start_task(<work-item-id>)`

**Example**:
```text
/product_analyst::start_next
```

---

#### `/<role>::report_token_usage`

**Intent**: Report current token usage for budget tracking

**Agent Behavior**:
- Report estimated tokens used so far
- Flag if approaching budget limit
- Suggest work splitting if needed
- Update memo with token usage

**Expected Output**:
```markdown
**Token Usage Report**:
- Tokens Used: 15,234 / 20,000 (76%)
- Status: ✅ Within budget
- Remaining Capacity: 4,766 tokens (~1-2 more work items)
```

---

## Task Card Format

Task cards are generated automatically in `agent-sync/tasks/`:

```markdown
# Task: 2026-01-10-PROD-ANALYST-01

- **Role**: product_analyst
- **Status**: ready-to-start | in-progress | ready-to-consume | completed | blocked
- **Work Item**: US-E01-010
- **Priority**: High | Normal | Low
- **Estimated Effort**: 2-4 hours
- **Token Budget**: 5,000 tokens
- **Dependencies**: None

## Objective

<High-level goal for this task>

## Work Item

`work_items/E01/US-E01-010.md`

## Deliverables

- `work_items/E01/US-E01-010.md` (updated with technical specifications)
- Technical design documented
- Acceptance criteria defined
- Test scenarios outlined

## Steps

1. Read work item file: `work_items/E01/US-E01-010.md`
2. Execute all deliverables per your boot prompt
3. Commit to your worktree branch: `feat/product-analyst/US-E01-010`
4. Post ready-to-consume memo with Branch+SHA

## Acceptance Criteria

- [ ] Technical specifications complete
- [ ] Acceptance criteria testable
- [ ] All non-functional requirements documented
- [ ] Dependencies identified

## Resources

- Iteration context: `iterations/<iteration>/CONTEXT.md`
- Completion criteria: `iterations/<iteration>/COMPLETION_CRITERIA.md`
- Boot prompt: `iterations/<iteration>/product-analyst-agent-prompt.md`
```

---

## Relationship to Boot Prompts

- Role agents should be started with their boot prompt from `iterations/<iteration>/<role>-agent-prompt.md`
- Boot prompts include a "Command Shorthand" section that documents role-specific commands
- After initial boot, agents can be sent simple one-line commands
- Agents are trained **once** via boot prompt, then commands work indefinitely

---

## CLI Mapping

| Slash Command | CLI Equivalent | Automation |
|--------------|----------------|------------|
| `/orchestrator::start_workflow(...)` | `cli.py start-workflow ...` | ✅ Full |
| `/orchestrator::generate_iteration(...)` | `generate_prompts.py ...` | ✅ Full |
| `/orchestrator::monitor_progress(...)` | `monitor_enhanced.sh ...` | ✅ Full |
| `/integrator::apply_ready` | `cli.py integrate apply-ready` | ✅ Full |
| `/integrator::validate_iteration(...)` | `validate_iteration.sh ...` | ✅ Full |
| `/integrator::distribute_tasks(...)` | `cli.py tasks generate` | ✅ Full |
| `/<role>::start_task(<id>)` | Agent interprets task card | 🟡 Semi |
| `/<role>::start_next` | Agent finds next task | 🟡 Semi |
| `/<role>::report_token_usage` | Agent reports metrics | 🟡 Semi |

---

## Automation Roadmap

### Phase 1: Soft Commands (Current)
- Agents interpret commands via boot prompts
- Manual copy/paste of commands
- CLI tools available but require manual invocation

### Phase 2: CLI Automation (Next)
- CLI command parser routes slash commands to Python functions
- Automation scripts can invoke commands programmatically
- CI/CD integration possible

### Phase 3: MCP Hooks (Future)
- Model Context Protocol integration
- IDE-native command recognition
- Full automation potential

---

## Example Workflow

### Complete User Story Refinement

```bash
# 1. Orchestrator starts workflow
/orchestrator::start_workflow(user-story-refinement, 1-definition, requirements-extraction)

# Orchestrator outputs:
# ✅ Generated 15 task cards
# ✅ Created 5 agent worktrees
# ✅ Posted task dispatch memo at agent-sync/2026-01-10_orchestrator_task-dispatch.md
#
# Copy these commands to start agents:
# /product_analyst::start_task(2026-01-10-PROD-01)
# /backend_developer::start_task(2026-01-10-BACK-01)
# /qa_engineer::start_task(2026-01-10-QA-01)
# /tech_writer::start_task(2026-01-10-TECH-01)
# /sre::start_task(2026-01-10-SRE-01)

# 2. User sends commands to respective agents (or agents run start_next)
/product_analyst::start_task(2026-01-10-PROD-01)
# Agent: ✅ Task complete. Branch: feat/product-analyst/US-E01-010, SHA: a3f4c2b
#        Memo: agent-sync/2026-01-10_product-analyst_US-E01-010.md

/backend_developer::start_task(2026-01-10-BACK-01)
# Agent: ✅ Task complete. Branch: feat/backend-dev/US-E02-020, SHA: b7d8e5a
#        Memo: agent-sync/2026-01-10_backend-developer_US-E02-020.md

# ... (other agents complete)

# 3. Integrator converges work
/integrator::apply_ready
# Integrator: ✅ Integrated 5 commits
#             ✅ Merge gates passed (validation: ✅, token budget: ✅, tests: ✅)
#             ✅ Posted integration memo at agent-sync/2026-01-10_integrator_integration-complete.md

# 4. Integrator validates iteration
/integrator::validate_iteration(requirements-extraction)
# Integrator: ✅ All deliverables present (15/15)
#             ✅ All completion criteria met (100%)
#             ✅ Iteration complete!
```

**Total coordination**: **6 one-line commands** vs hundreds of lines of prompts

---

## Customization

You can extend the command set by:

1. **Adding new commands** to this file
2. **Updating boot prompts** to document new commands
3. **Creating CLI equivalents** in `cli.py` if needed
4. **Documenting agent behavior** for each new command

---

## Notes

- These commands are **conventions** (not enforced by IDE/Cursor)
- Agents must be trained via boot prompts to recognize them
- The framework CLI provides programmatic equivalents for automation
- This protocol is designed to be **compatible with future automation** (CLI tools → MCP hooks)
- Command shorthand reduces coordination overhead by **~95%**

---

**For complete integration guide**, see: `COMMAND_SHORTHAND_INTEGRATION.md`

**For boot prompt templates**, see: `templates/_base.md.j2`

**For workflow examples**, see: `WORKFLOW_CATALOG.md`
