# Generic Orchestration Framework

**Version**: 1.0  
**Date**: 2026-01-10  
**Purpose**: Reusable orchestration framework for delegating complex tasks to specialized AI agents

---

## Executive Summary

This framework extracts the successful patterns from our documentation orchestration system and generalizes them into a reusable, configuration-driven orchestration engine. It enables a Master Orchestrator to decompose any complex task into iterations, assign work to specialized agents, monitor execution, validate results, and apply learnings continuously.

**Key Insight**: Any complex task that can be decomposed into specialized subtasks can benefit from automated orchestration with role-based AI agents.

---

## Framework Overview

### Core Principles

1. **Orchestrator Delegates, Agents Execute**: The Master Orchestrator makes decisions but never does the work itself
2. **Role-Based Specialization**: Each agent has a specific role, perspective, and expertise
3. **Iteration-Based Execution**: Work is organized into iterations with clear goals and completion criteria
4. **Template-Driven Automation**: Prompts are generated from templates, not hand-written
5. **Continuous Improvement**: Feedback is collected after each iteration and applied to future work
6. **Token Budget Awareness**: Complexity is estimated and allocations are risk-scored
7. **Deterministic Validation**: Completion is validated programmatically, not subjectively

---

## Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Orchestrator                       │
│  (Assesses situation, makes decisions, delegates work)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ generates
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Iteration                                │
│  - CONTEXT.md (shared knowledge)                             │
│  - COMPLETION_CRITERIA.md (objective validation)             │
│  - README.md (execution guide)                               │
│  - agent-prompts/ (generated from templates)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ executes via
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Orchestration Tools                           │
│  - generate_prompts.py (template → prompts)                  │
│  - orchestrate_full.sh (full lifecycle automation)           │
│  - monitor_enhanced.sh (intelligent monitoring)              │
│  - validate_iteration.sh (deterministic validation)          │
│  - collect_feedback.sh (feedback loop)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ launches & monitors
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Specialized Agents (parallel)                   │
│  - Each agent has: role, perspective, capabilities, limits   │
│  - Examples: Developer, QA, Architect, Writer, Analyst       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ produces
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Deliverables                               │
│  - Code, documentation, analysis, decisions, etc.            │
│  - Validated against COMPLETION_CRITERIA.md                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Master Orchestrator

**Responsibilities**:
- Assess the current situation and desired outcome
- Decompose complex tasks into iterations
- Select appropriate agent roles for each iteration
- Generate iteration context and completion criteria
- Monitor agent execution
- Validate results
- Apply learnings from feedback

**Does NOT**:
- Execute tasks directly (delegates to specialized agents)
- Write code or documentation (agents do this)
- Make assumptions (asks clarifying questions if needed)

**Configuration**:
```yaml
orchestrator:
  role: Master Orchestrator
  perspective: Project Manager + System Architect
  capabilities:
    - Task decomposition
    - Agent selection and allocation
    - Risk assessment
    - Progress monitoring
    - Feedback synthesis
  decision_framework:
    - Assess → Decide → Delegate → Monitor → Validate → Learn
```

---

### 2. Agent Roles

**Generic Role Template**:
```yaml
agent_role:
  name: <role_name>
  perspective: <viewpoint>
  responsibilities:
    - <responsibility_1>
    - <responsibility_2>
  capabilities:
    - <capability_1>
    - <capability_2>
  constraints:
    - Token budget: <estimate>
    - Complexity threshold: <max_files_or_tasks>
    - Dependencies: [<other_roles>]
  output_format:
    - <deliverable_type>
```

**Example Roles** (from documentation orchestration):
- **Tech Lead**: Backend development, API design
- **QA Lead**: Testing strategy, quality gates
- **SRE**: Operational runbooks, monitoring
- **Tech Writer**: Release documentation, user guides
- **Architect**: System design, infrastructure
- **Data Architect**: Schema design, data models

**New Roles** (for other use cases):
- **Developer**: Implement user stories, write tests
- **Product Analyst**: Requirements analysis, acceptance criteria
- **Security Analyst**: Threat modeling, security reviews
- **Data Scientist**: ML models, feature engineering
- **Frontend Developer**: UI components, UX flows

---

### 3. Iteration Structure

**Standard Files** (every iteration has these):

#### `CONTEXT.md`
- **Purpose**: Shared knowledge for all agents in the iteration
- **Contents**:
  - Iteration goal and scope
  - Reference documents and examples
  - Standards and conventions to follow
  - Domain-specific knowledge
  - Constraints and non-goals

#### `COMPLETION_CRITERIA.md`
- **Purpose**: Objective validation checklist
- **Contents**:
  - Required deliverables (with exact file paths)
  - Quality standards (what "good" looks like)
  - Scope compliance checks
  - Validation commands (automated checks)

#### `README.md`
- **Purpose**: Execution guide for the orchestrator
- **Contents**:
  - Iteration overview
  - Execution options (automated vs manual)
  - Expected outputs
  - Troubleshooting guide

#### `agent-prompts/`
- **Purpose**: Generated prompts for each agent
- **Generated from**: Templates + configuration
- **Example**: `developer-agent-prompt.md`, `qa-agent-prompt.md`

---

### 4. Orchestration Tools

#### `generate_prompts.py`
**Purpose**: Generate agent prompts from templates and configuration

**Inputs**:
- Workflow configuration (YAML)
- Agent role definitions
- Target entities (files, stories, tasks)
- Prompt templates

**Outputs**:
- Agent-specific prompts with allocated work
- Token budget estimates and risk scores
- Execution manifest

**Usage**:
```bash
python generate_prompts.py \
  --workflow user-story-refinement \
  --config workflows/user-story-refinement.yaml \
  --targets "E01/*.md" \
  --output iterations/refinement-iteration-01/
```

---

#### `orchestrate_full.sh`
**Purpose**: Full lifecycle automation (generate → launch → monitor → validate)

**Steps**:
1. Generate agent prompts
2. Launch agents in parallel (Cursor Composer)
3. Monitor execution (intelligent polling)
4. Validate deliverables
5. Collect feedback

**Usage**:
```bash
./orchestrate_full.sh iterations/refinement-iteration-01/
```

---

#### `monitor_enhanced.sh`
**Purpose**: Intelligent monitoring with progress estimation

**Features**:
- Polls output directory for deliverables
- Estimates progress based on file sizes
- Detects stalls (no progress for N minutes)
- Validates partial outputs
- Alerts when agents complete

---

#### `validate_iteration.sh`
**Purpose**: Deterministic validation against COMPLETION_CRITERIA.md

**Checks**:
- All required files exist
- File sizes meet minimums (e.g., > 1KB)
- Content validation (keyword checks, schema validation)
- Format validation (Markdown, YAML, JSON)

---

#### `collect_feedback.sh`
**Purpose**: Collect feedback from agents and synthesize learnings

**Process**:
1. Read agent outputs
2. Identify patterns (token budget issues, scope confusion, etc.)
3. Generate feedback report
4. Update templates/roles/processes based on learnings

---

## Configuration Schema

### Workflow Configuration

```yaml
workflow:
  name: user-story-refinement
  description: Refine user stories with technical implementation details
  
  iterations:
    - name: requirements-analysis
      goal: Extract and validate requirements from user stories
      agents:
        - role: product_analyst
          targets: ["stories/*.md"]
          deliverables:
            - "stories/{story_id}/requirements.md"
          complexity_per_target: 3  # points
      completion_criteria:
        - All user stories have requirements.md
        - Requirements follow SMART criteria
        - Acceptance criteria are testable
    
    - name: technical-design
      goal: Design technical implementation for refined requirements
      dependencies: [requirements-analysis]
      agents:
        - role: developer
          targets: ["stories/*/requirements.md"]
          deliverables:
            - "stories/{story_id}/technical-design.md"
            - "stories/{story_id}/test-plan.md"
          complexity_per_target: 5  # points
      completion_criteria:
        - All stories have technical-design.md
        - All stories have test-plan.md
        - Designs include API contracts and data models

agent_roles:
  product_analyst:
    perspective: Product Owner + Business Analyst
    responsibilities:
      - Extract functional requirements
      - Define acceptance criteria
      - Validate business rules
    capabilities:
      - Requirements elicitation
      - User story refinement
      - Acceptance criteria definition
    token_budget: 30000
    complexity_threshold: 10  # stories per agent
  
  developer:
    perspective: Senior Backend Engineer
    responsibilities:
      - Design technical implementation
      - Define API contracts
      - Plan testing approach
    capabilities:
      - System design
      - API design
      - Test planning
    token_budget: 50000
    complexity_threshold: 5  # stories per agent

templates:
  product_analyst: templates/product-analyst.md.j2
  developer: templates/developer.md.j2
```

---

## Use Case Examples

### Use Case 1: User Story Refinement

**Goal**: Take raw user stories and refine them with technical implementation details

**Iterations**:
1. **Requirements Analysis**: Product Analyst extracts requirements, defines acceptance criteria
2. **Technical Design**: Developer designs implementation, defines API contracts
3. **Test Planning**: QA defines test strategy and test cases
4. **Security Review**: Security Analyst performs threat modeling
5. **Estimation**: Tech Lead estimates effort and identifies risks

**Agents**: Product Analyst, Developer, QA, Security Analyst, Tech Lead

**Deliverables** (per story):
- `requirements.md` - Functional requirements and acceptance criteria
- `technical-design.md` - Implementation approach, API contracts, data models
- `test-plan.md` - Test strategy, test cases
- `security-review.md` - Threat model, security requirements
- `estimation.md` - Effort estimate, risks, dependencies

---

### Use Case 2: Task Execution Orchestration

**Goal**: Given a complex task, decompose it and delegate to specialized agents

**Example Task**: "Implement OAuth2 authentication for the API"

**Orchestrator Actions**:
1. **Decompose Task** into subtasks:
   - Define OAuth2 flow and endpoints (Architect)
   - Implement token generation and validation (Developer)
   - Add integration tests (QA)
   - Document API endpoints (Tech Writer)
   - Create operational runbook (SRE)

2. **Create Iteration** with all subtasks

3. **Launch Agents** in parallel

4. **Validate** all deliverables produced

**Agents**: Architect, Developer, QA, Tech Writer, SRE

**Deliverables**:
- `oauth2-design.md` - Flow diagrams, endpoint specs
- `src/auth/oauth2.ts` - Implementation
- `tests/auth/oauth2.test.ts` - Tests
- `docs/api/oauth2.md` - API documentation
- `runbooks/oauth2-incidents.md` - Operational runbook

---

### Use Case 3: Code Review Orchestration

**Goal**: Perform comprehensive code review with multiple specialized perspectives

**Iterations**:
1. **Functional Review**: Developer checks logic, algorithms, edge cases
2. **Security Review**: Security Analyst checks for vulnerabilities
3. **Performance Review**: Performance Engineer checks for bottlenecks
4. **Test Review**: QA checks test coverage and quality
5. **Documentation Review**: Tech Writer checks API docs and comments

**Agents**: Developer, Security Analyst, Performance Engineer, QA, Tech Writer

**Deliverables** (per PR):
- `reviews/functional-review.md` - Logic and algorithm feedback
- `reviews/security-review.md` - Security findings
- `reviews/performance-review.md` - Performance concerns
- `reviews/test-review.md` - Test coverage gaps
- `reviews/docs-review.md` - Documentation improvements

---

### Use Case 4: Incident Response Orchestration

**Goal**: Coordinate incident response with specialized roles

**Iterations**:
1. **Triage**: SRE assesses severity and impact
2. **Investigation**: Developer investigates root cause
3. **Mitigation**: DevOps implements immediate fix
4. **Communication**: Tech Writer drafts incident report
5. **Postmortem**: All roles contribute to postmortem

**Agents**: SRE, Developer, DevOps, Tech Writer

**Deliverables**:
- `incidents/{id}/triage.md` - Severity, impact, affected systems
- `incidents/{id}/investigation.md` - Root cause analysis
- `incidents/{id}/mitigation.md` - Immediate fix and deployment
- `incidents/{id}/incident-report.md` - Customer communication
- `incidents/{id}/postmortem.md` - Lessons learned, action items

---

## Framework Benefits

### 1. Scalability
- Add new agent roles without changing core framework
- Add new workflows via configuration
- Parallelize work across multiple agents

### 2. Consistency
- Template-driven ensures consistent quality
- Completion criteria enforce standards
- Feedback loops drive continuous improvement

### 3. Efficiency
- Automated orchestration eliminates manual coordination
- Parallel execution maximizes throughput
- Token budget awareness prevents waste

### 4. Flexibility
- Configuration-driven workflows adapt to any domain
- Agent roles can be mixed and matched
- Iterations can be customized per use case

### 5. Observability
- Monitoring provides real-time progress
- Validation ensures quality gates
- Feedback enables continuous improvement

---

## Migration Path

### Phase 1: Extract Core Framework (Week 1)
1. Extract generic components from documentation orchestration
2. Create configuration schema (YAML)
3. Refactor tools to be configuration-driven
4. Create generic prompt templates

### Phase 2: Build Example Workflows (Week 2)
1. Implement user story refinement workflow
2. Implement task execution workflow
3. Implement code review workflow
4. Document each workflow

### Phase 3: Generalize Agent Roles (Week 3)
1. Extract agent roles from documentation system
2. Create generic role templates
3. Define role library (Developer, QA, Architect, etc.)
4. Document role capabilities and constraints

### Phase 4: Validation & Testing (Week 4)
1. Test each workflow with real tasks
2. Validate token budget accuracy
3. Refine completion criteria
4. Collect feedback and iterate

---

## Next Steps

1. **Review this framework** with stakeholders
2. **Prioritize use cases** (start with user story refinement?)
3. **Build Phase 1** (extract core framework)
4. **Test with pilot workflows**
5. **Iterate based on feedback**

---

**Document Owner**: Master Orchestrator Agent  
**Status**: Proposal  
**Next Action**: Review and approve framework architecture

---

**Related Documents**:
- `ORCHESTRATION_PATTERNS.md` - Detailed patterns and anti-patterns
- `WORKFLOW_CATALOG.md` - Library of pre-built workflows
- `AGENT_ROLE_LIBRARY.md` - Comprehensive role definitions
- `MIGRATION_GUIDE.md` - Step-by-step migration from doc system
