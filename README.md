# Generic Orchestration Framework - README

**Status**: Framework Design Complete  
**Version**: 1.0  
**Date**: 2026-01-10

---

## What Is This?

This is a **generic, reusable orchestration framework** for delegating complex tasks to specialized AI agents. It extracts the successful patterns from our documentation orchestration system and makes them configuration-driven and applicable to any domain.

**Key Insight**: Any complex task that can be decomposed into specialized subtasks can benefit from automated orchestration with role-based AI agents.

---

## The Key Innovation: Cursor-Agent Orchestrates via CLI

This framework is designed so that an **agent running inside the Cursor IDE** (the “orchestrator agent”) can run **multi-step orchestration** by issuing **CLI commands** from a terminal.

That gives you an actual, scriptable control surface:

- The orchestrator agent runs: `python cli.py execute "/orchestrator::start_workflow(...)"`.
- The framework generates task cards, iteration scaffold, and (optionally) worktrees.
- The orchestrator agent can optionally use **Cursor CLI** (command: `agent`) to drive work from a terminal (interactive or non-interactive), per the official docs: [`https://cursor.com/docs/cli/overview`](https://cursor.com/docs/cli/overview).
- The framework can (optionally) open those worktrees/iteration folders in the Cursor app via a CLI command (often `cursor ...`) so other agents can be started quickly.
- As role agents finish, they post `ready-to-consume` memos in the configured agent-sync directory (default: `.orchestration/runtime/agent-sync/`).
- The orchestrator (or an integrator agent) runs: `python cli.py execute "/integrator::apply_ready(...)"` to converge work.

This is why the slash-command protocol is so powerful: it’s not just “nice shorthand for humans” — it’s the **automation interface** an agent can drive.

---

## Quick Start

### 0. Run This Repo Standalone (2 minutes)

```bash
# Install deps
python -m pip install -r requirements.txt

# List available commands
python cli.py list

# Generate an example iteration + task cards + dispatch memo
python cli.py execute "/orchestrator::start_workflow(example-workflow, phase-1, iteration-1)"

# OPTIONAL: Automatically execute those tasks via Cursor CLI (agent) (dry-run)
# Cursor CLI docs: https://cursor.com/docs/cli/overview
python cli.py execute "/orchestrator::launch_agents(iteration-1, dry-run)"

# OPTIONAL: Run tasks in parallel (bounded by cursor.agent_max_parallel)
python cli.py execute "/orchestrator::launch_agents(iteration-1, parallel, 3, dry-run)"

# OPTIONAL: If (and only if) orchestration.allow_auto_apply_ready=true, the orchestrator can request
# an integration pass immediately after successful execution:
python cli.py execute "/orchestrator::launch_agents(iteration-1, apply-ready, dry-run)"

# OPTIONAL: Orchestrator can request apply_ready to a specific target branch
# (useful for long-running efforts where one agent’s output becomes another agent’s dependency)
python cli.py execute "/orchestrator::launch_agents(iteration-1, apply-ready=main, dry-run)"

# OPTIONAL: Incremental convergence (run apply_ready after each completed task / batch)
python cli.py execute "/orchestrator::launch_agents(iteration-1, parallel, 3, apply-ready=main, apply-ready-each, dry-run)"

# OPTIONAL: Orchestrator convenience wrapper for convergence into an explicit target branch
# (e.g. into another agent’s worktree branch to satisfy a dependency)
python cli.py execute "/orchestrator::apply_ready_to(feat/backend_developer/iteration-1, dry-run)"

# Integrate any ready-to-consume memos (dry-run)
python cli.py execute "/integrator::apply_ready(dry-run)"

# (Optional) integrate directly to trunk instead of integration/{date}
python cli.py execute "/integrator::apply_ready(main, dry-run)"
```

### 1. Install Framework in Your Project (5 minutes)

The framework is **portable and reusable**. Install it in any project:

```bash
# Copy framework to your project
cp -r orchestration-framework/ <your-project>/

# Navigate to your project
cd <your-project>/

# Bootstrap the framework
python orchestration-framework/bootstrap.py --init

# That's it! Framework is ready to use.
```

**What bootstrap does**:
- ✅ Creates directory structure (runtime artifacts under `.orchestration/runtime/`, configs under `.orchestration/config/`)
- ✅ Copies templates (command shorthand, communication conventions)
- ✅ Creates configuration file (`orchestration-framework/config.yaml`)
- ✅ Updates `.gitignore` (worktrees, agent logs)
- ✅ Creates `CONTRIBUTING.md` with orchestration workflow
- ✅ Sets up Cursor rules (optional)

**Bootstrap options**:
```bash
# Custom project name
python orchestration-framework/bootstrap.py --init --project-name "MyProject"

# Different trunk branch
python orchestration-framework/bootstrap.py --init --trunk-branch develop

# Disable Cursor integration
python orchestration-framework/bootstrap.py --init --no-cursor

# Custom worktree location
python orchestration-framework/bootstrap.py --init --worktree-location ../worktrees
```

---

### 2. Understand the Framework (15 minutes)

Read these documents in order:
1. **[GENERIC_ORCHESTRATION_FRAMEWORK.md](./GENERIC_ORCHESTRATION_FRAMEWORK.md)** - Core concepts and architecture
2. **[WORKFLOW_CATALOG.md](./WORKFLOW_CATALOG.md)** - Pre-built workflows (user story refinement, task execution, code review, etc.)
3. **[AGENT_ROLE_LIBRARY.md](./AGENT_ROLE_LIBRARY.md)** - Comprehensive role definitions (Developer, QA, Architect, etc.)
4. **[templates/COMMAND_SHORTHAND.md](./templates/COMMAND_SHORTHAND.md)** - Slash commands for efficient coordination

---

### 3. Configure for Your Project (10 minutes)

Edit `orchestration-framework/config.yaml`:

```yaml
project:
  name: "YourProjectName"  # Change this
  trunk_branch: "main"     # Or develop, master, etc.

# Customize roles for your project
roles:
  - backend_developer
  - frontend_developer
  - qa_engineer
  # Add/remove as needed

# Customize token budgets
token_budget:
  default_per_agent: 20000  # Adjust based on task complexity
```

---

### 4. Choose Your Use Case

**Option A: Use Pre-Built Workflow**
- Pick a workflow from `WORKFLOW_CATALOG.md`
- Customize configuration for your needs
- Run with slash commands or CLI

**Option B: Create Custom Workflow**
- Use workflow template from catalog
- Define your iterations and agent roles
- Generate configuration YAML

---

### 5. Run Your First Workflow

#### Option A: Using Slash Commands (Recommended)

```bash
# Start a workflow (orchestrator agent)
/orchestrator::start_workflow(user-story-refinement, phase-1, requirements-extraction)

# Agents execute their tasks
/product_analyst::start_task(US-E01-010)
/backend_developer::start_task(US-E02-020)
/qa_engineer::start_next

# Integrate ready work (integrator agent)
/integrator::apply_ready

# Validate iteration (integrator agent)
/integrator::validate_iteration(requirements-extraction)
```

**Benefits**: 95% less typing, standardized format, clear coordination

#### Option B: Using CLI Directly

```bash
# Example: User Story Refinement
cd <your-project>/

# Generate agent prompts from workflow config
python orchestration-framework/tools/generate_prompts.py \
  --workflow workflows/user-story-refinement.yaml \
  --targets "work_items/E01/US-*.md" \
  --output iterations/refinement-001/

# Execute full workflow (generate → launch → monitor → validate)
orchestration-framework/tools/orchestrate_full.sh iterations/refinement-001/

# Monitor progress
tail -f iterations/refinement-001/outputs/*.log

# Validate results
orchestration-framework/tools/validate_iteration.sh iterations/refinement-001/
```

---

## Framework Components

### Core Documents

| Document | Purpose | Read When |
|----------|---------|-----------|
| **GENERIC_ORCHESTRATION_FRAMEWORK.md** | Architecture and principles | First - understanding |
| **WORKFLOW_CATALOG.md** | Pre-built workflow configurations | Second - selecting workflow |
| **AGENT_ROLE_LIBRARY.md** | Comprehensive role definitions | Third - understanding agents |
| **IMPLEMENTATION_GUIDE.md** | Step-by-step migration guide | When implementing |
| **CONFIGURATION_GUIDE.md** | YAML configuration reference | When customizing |

### Tools (from documentation system)

| Tool | Purpose |
|------|---------|
| `generate_prompts.py` | Generate agent prompts from templates + config |
| `orchestrate_full.sh` | Full lifecycle automation |
| `monitor_enhanced.sh` | Intelligent progress monitoring |
| `validate_iteration.sh` | Deterministic validation |
| `collect_feedback.sh` | Feedback collection and synthesis |

---

## Use Cases

### ✅ Proven Use Cases (from documentation orchestration)

1. **Documentation Generation** (Proven)
   - Technical specifications
   - API documentation
   - User guides
   - Operational runbooks

### 🎯 Target Use Cases (Framework supports)

2. **User Story Refinement**
   - Requirements extraction
   - Technical design
   - Test planning
   - Security review

3. **Task Execution**
   - Decompose complex tasks
   - Delegate to specialists
   - Parallel execution
   - Result validation

4. **Code Review**
   - Functional review
   - Security review
   - Performance review
   - Test coverage review

5. **Feature Development**
   - Implementation
   - Testing
   - Documentation
   - Deployment

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   Master Orchestrator                         │
│  • Assesses situation                                         │
│  • Decomposes tasks                                           │
│  • Selects agents                                             │
│  • Monitors execution                                         │
│  • Validates results                                          │
│  • Applies learnings                                          │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Creates
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                    Iteration                                  │
│  • CONTEXT.md (shared knowledge)                              │
│  • COMPLETION_CRITERIA.md (validation checklist)              │
│  • README.md (execution guide)                                │
│  • agent-prompts/ (generated from templates)                  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Executes via
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              Orchestration Tools                              │
│  generate_prompts.py → orchestrate_full.sh → monitor → validate│
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Launches
                        ▼
┌──────────────────────────────────────────────────────────────┐
│           Specialized Agents (parallel)                       │
│  Developer | QA | Architect | Writer | Security | SRE | ...  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Produces
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                 Deliverables                                  │
│  Code, docs, designs, tests, reviews, etc.                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Orchestrator Delegates, Agents Execute
- **Master Orchestrator**: Makes decisions, never does the work
- **Agents**: Specialized roles that execute tasks
- **Separation of Concerns**: Clear boundaries

### 2. Role-Based Specialization
- Each agent has a specific perspective and expertise
- Examples: Developer, QA, Architect, Writer, Security, SRE
- Roles are reusable across workflows

### 3. Iteration-Based Execution
- Work organized into iterations with clear goals
- Each iteration has: context, completion criteria, agent prompts
- Iterations can depend on previous iterations

### 4. Template-Driven Automation
- Prompts generated from templates, not hand-written
- Configuration drives generation
- Reduces manual work by 93% (30 min → 2 min)

### 5. Token Budget Awareness
- Each agent has a token budget
- Complexity estimated per work item
- Risk-scored allocations (LOW/MEDIUM/HIGH)

### 6. Continuous Improvement
- Feedback collected after each iteration
- Patterns identified (token budget hits, scope confusion, etc.)
- Learnings applied to templates/roles/processes

---

## Success Metrics (from documentation orchestration)

### Proven Results

- ✅ **100% file completion rate** (no manual interventions)
- ✅ **93% faster prompt generation** (30 min → 2 min)
- ✅ **10-15x faster execution** vs manual sequential work
- ✅ **Zero flaky processes** (deterministic validation)
- ✅ **109 work items** successfully orchestrated across 4 MVPs

### Expected Results (for new workflows)

- **80-100%** automation rate
- **5-10x** efficiency gain over manual coordination
- **< 5%** rework rate
- **> 95%** quality consistency

---

## Migration Path

### Phase 1: Extract Core Framework (1 week)
1. Extract generic components from documentation system
2. Create configuration schema (YAML)
3. Refactor tools to be configuration-driven
4. Create generic prompt templates

### Phase 2: Build Example Workflows (1 week)
1. Implement user story refinement workflow
2. Implement task execution workflow
3. Implement code review workflow
4. Document each workflow

### Phase 3: Generalize Agent Roles (1 week)
1. Extract agent roles from documentation system
2. Create generic role templates
3. Define role library (Developer, QA, Architect, etc.)
4. Document role capabilities and constraints

### Phase 4: Validation & Testing (1 week)
1. Test each workflow with real tasks
2. Validate token budget accuracy
3. Refine completion criteria
4. Collect feedback and iterate

---

## File Structure

```
orchestration-framework/
├── README.md                                    ← You are here
├── GENERIC_ORCHESTRATION_FRAMEWORK.md          ← Core concepts
├── WORKFLOW_CATALOG.md                          ← Pre-built workflows
├── AGENT_ROLE_LIBRARY.md                        ← Role definitions
├── IMPLEMENTATION_GUIDE.md                      ← Migration guide
├── CONFIGURATION_GUIDE.md                       ← YAML reference
│
├── workflows/                                   ← Workflow configs
│   ├── user-story-refinement.yaml
│   ├── task-execution.yaml
│   ├── code-review.yaml
│   └── template.yaml
│
├── templates/                                   ← Prompt templates
│   ├── developer.md.j2
│   ├── qa-engineer.md.j2
│   ├── architect.md.j2
│   └── ...
│
├── tools/                                       ← Orchestration tools
│   ├── generate_prompts.py
│   ├── orchestrate_full.sh
│   ├── monitor_enhanced.sh
│   ├── validate_iteration.sh
│   └── collect_feedback.sh
│
└── examples/                                    ← Example iterations
    ├── user-story-refinement-example/
    ├── task-execution-example/
    └── code-review-example/
```

---

## Getting Help

### Documentation
- **Core Framework**: `GENERIC_ORCHESTRATION_FRAMEWORK.md`
- **Workflows**: `WORKFLOW_CATALOG.md`
- **Roles**: `AGENT_ROLE_LIBRARY.md`
- **Implementation**: `IMPLEMENTATION_GUIDE.md`

### Examples
- **User Story Refinement**: `examples/user-story-refinement-example/`
- **Task Execution**: `examples/task-execution-example/`
- **Code Review**: `examples/code-review-example/`

### Support
- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or share use cases

---

## Roadmap

### ✅ Phase 0: Documentation Orchestration (Complete)
- Proven system with 109 work items
- Full automation (generate → execute → validate)
- Continuous improvement loop

### 🎯 Phase 1: Generic Framework (Current)
- Extract core components
- Configuration-driven workflows
- Comprehensive documentation

### 📋 Phase 2: Common Workflows (Next)
- User story refinement
- Task execution
- Code review
- Feature development

### 🚀 Phase 3: Advanced Features (Future)
- Dynamic workflow generation
- Multi-tenant orchestration
- CI/CD integration
- Web UI for orchestration

---

## Contributing

We welcome contributions! Areas where we need help:

1. **New Workflows**: Share your workflow configurations
2. **New Agent Roles**: Define specialized roles for your domain
3. **Tool Improvements**: Enhance orchestration tools
4. **Documentation**: Improve guides and examples
5. **Templates**: Create better prompt templates

---

## License

[To be determined]

---

## Acknowledgments

This framework is based on lessons learned from orchestrating 109 work items across 4 MVPs in the Schedul-R documentation project. Special thanks to the Master Orchestrator Agent for pioneering this approach.

---

**Questions?** See `GENERIC_ORCHESTRATION_FRAMEWORK.md` for detailed concepts or `WORKFLOW_CATALOG.md` for examples.

**Ready to start?** Pick a workflow from the catalog and try it with a small batch of work!
