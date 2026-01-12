# Phase 1 Implementation Guide

**Goal**: Extract the generic orchestration framework from the documentation system  
**Duration**: 1 week  
**Status**: Ready to begin

---

## Overview

This guide walks through extracting the proven orchestration components from the documentation system and making them generic, configuration-driven, and reusable for any workflow.

**What we're extracting**:
- Orchestration tools (generate_prompts.py, orchestrate_full.sh, etc.)
- Agent role definitions
- Prompt templates
- Workflow configurations

**What we're creating**:
- Configuration schema (YAML)
- Generic prompt templates (Jinja2)
- Refactored tools (configuration-driven)
- Example workflows

---

## Phase 1 Tasks

### Task 1: Extract and Refactor `generate_prompts.py` (2 days)

**Current State**: Tool is specific to documentation workflows
- Hardcoded file patterns
- Hardcoded agent roles
- Embedded complexity calculations

**Target State**: Generic, configuration-driven tool
- Reads workflow configuration from YAML
- Loads agent roles from YAML
- Dynamically allocates work based on strategy

#### Steps

1. **Create Configuration Schema** (4 hours)

```yaml
# schemas/workflow-config.schema.yaml
workflow:
  name: string
  version: string
  description: string
  execution_mode: enum[static, dynamic]
  
  phases:
    - phase: string
      name: string
      goal: string
      dependencies: [string]
      
      iterations:
        - name: string
          agents:
            - role: string
              allocation:
                strategy: enum[round_robin, single, by_criteria]
                max_per_agent: integer
                complexity_per_item: integer
              inputs:
                - pattern: string
                  filter: string (optional)
              deliverables:
                - path: string (with variables)
                  template: string (optional)
          
          completion_criteria:
            files: [string]
            content: [string]
            commands: [string]
```

2. **Refactor `generate_prompts.py`** (8 hours)

```python
# orchestration-framework/tools/generate_prompts.py

import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List

class PromptGenerator:
    def __init__(self, workflow_config_path: str):
        """Initialize with workflow configuration."""
        self.config = self._load_config(workflow_config_path)
        self.agent_roles = self._load_agent_roles()
        self.template_env = Environment(
            loader=FileSystemLoader('templates/')
        )
    
    def _load_config(self, path: str) -> Dict:
        """Load workflow configuration from YAML."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_agent_roles(self) -> Dict:
        """Load agent role definitions."""
        roles = {}
        for role_file in Path('agent-roles/').glob('*.yaml'):
            with open(role_file, 'r') as f:
                role = yaml.safe_load(f)
                roles[role['role_id']] = role
        return roles
    
    def generate_iteration(self, phase_id: str, iteration_name: str, 
                          output_dir: str):
        """Generate complete iteration structure."""
        iteration = self._find_iteration(phase_id, iteration_name)
        
        # Create iteration directory structure
        iter_dir = Path(output_dir)
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CONTEXT.md
        self._generate_context(iteration, iter_dir)
        
        # Generate COMPLETION_CRITERIA.md
        self._generate_completion_criteria(iteration, iter_dir)
        
        # Generate README.md
        self._generate_readme(iteration, iter_dir)
        
        # Generate agent prompts
        self._generate_agent_prompts(iteration, iter_dir)
    
    def _generate_agent_prompts(self, iteration: Dict, iter_dir: Path):
        """Generate prompts for each agent in the iteration."""
        for agent_config in iteration['agents']:
            role_id = agent_config['role']
            role = self.agent_roles[role_id]
            
            # Find target work items
            targets = self._find_targets(agent_config['inputs'])
            
            # Allocate targets to agents based on strategy
            allocations = self._allocate_targets(
                targets, 
                agent_config['allocation'],
                role
            )
            
            # Generate prompt for each agent instance
            for idx, allocation in enumerate(allocations):
                prompt = self._render_prompt(
                    role, 
                    allocation, 
                    iteration,
                    agent_config
                )
                
                prompt_path = iter_dir / f"{role_id}-agent-{idx+1}-prompt.md"
                prompt_path.write_text(prompt)
                
                print(f"Generated: {prompt_path}")
    
    def _allocate_targets(self, targets: List, allocation: Dict, 
                         role: Dict) -> List[List]:
        """Allocate targets to agent instances based on strategy."""
        strategy = allocation['strategy']
        max_per_agent = allocation.get('max_per_agent')
        complexity_per_item = allocation.get('complexity_per_item', 1)
        
        if strategy == 'single':
            # All targets to one agent
            return [targets]
        
        elif strategy == 'round_robin':
            # Distribute evenly across multiple agents
            token_budget = role['constraints']['token_budget']
            max_complexity = role['constraints']['complexity_threshold']
            
            # Calculate how many agents needed
            total_complexity = len(targets) * complexity_per_item
            agents_needed = (total_complexity + max_complexity - 1) // max_complexity
            
            # Split targets evenly
            chunk_size = (len(targets) + agents_needed - 1) // agents_needed
            return [targets[i:i+chunk_size] 
                   for i in range(0, len(targets), chunk_size)]
        
        elif strategy.startswith('by_'):
            # Custom allocation strategy
            criteria = strategy[3:]  # Extract criteria (e.g., 'service', 'domain')
            return self._allocate_by_criteria(targets, criteria)
        
        else:
            raise ValueError(f"Unknown allocation strategy: {strategy}")
    
    def _render_prompt(self, role: Dict, targets: List, 
                      iteration: Dict, agent_config: Dict) -> str:
        """Render prompt template with context."""
        template_name = f"{role['role_id']}.md.j2"
        template = self.template_env.get_template(template_name)
        
        return template.render(
            role=role,
            targets=targets,
            iteration=iteration,
            deliverables=agent_config['deliverables'],
            context=iteration.get('context', {}),
            completion_criteria=iteration.get('completion_criteria', {})
        )

# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate agent prompts')
    parser.add_argument('--workflow', required=True, 
                       help='Path to workflow configuration YAML')
    parser.add_argument('--phase', required=True,
                       help='Phase ID')
    parser.add_argument('--iteration', required=True,
                       help='Iteration name')
    parser.add_argument('--output', required=True,
                       help='Output directory')
    
    args = parser.parse_args()
    
    generator = PromptGenerator(args.workflow)
    generator.generate_iteration(args.phase, args.iteration, args.output)
```

3. **Test with User Story Refinement Workflow** (4 hours)

```bash
# Create test workflow configuration
cat > workflows/user-story-refinement.yaml <<EOF
workflow:
  name: user-story-refinement
  version: 1.0
  description: Multi-phase refinement of user stories
  
  phases:
    - phase: 1-definition
      name: Requirements Definition
      iterations:
        - name: requirements-extraction
          agents:
            - role: product_analyst
              allocation:
                strategy: round_robin
                max_per_agent: 10
                complexity_per_item: 3
              inputs:
                - pattern: "work_items/E01/US-*.md"
              deliverables:
                - path: "work_items/{epic}/{story_id}/REQUIREMENTS.md"
EOF

# Test generation
python tools/generate_prompts.py \
  --workflow workflows/user-story-refinement.yaml \
  --phase 1-definition \
  --iteration requirements-extraction \
  --output test-iterations/refinement-001/

# Verify outputs
ls -la test-iterations/refinement-001/
```

---

### Task 2: Create Generic Prompt Templates (1 day)

**Current State**: Templates embedded in generate_prompts.py
- Hardcoded context sections
- Hardcoded completion criteria
- Documentation-specific language

**Target State**: Jinja2 templates with variables
- Role-agnostic structure
- Configurable sections
- Domain-neutral language

#### Steps

1. **Create Template Structure** (2 hours)

```
orchestration-framework/templates/
├── _base.md.j2                  # Base template (shared structure)
├── product_analyst.md.j2        # Product Analyst role
├── backend_developer.md.j2      # Backend Developer role
├── qa_engineer.md.j2            # QA Engineer role
├── system_architect.md.j2       # System Architect role
└── ...                          # Other roles
```

2. **Create Base Template** (2 hours)

```jinja2
{# templates/_base.md.j2 #}
# {{ role.name }} - Agent Prompt

## Role Context

**Role**: {{ role.name }}
**Perspective**: {{ role.perspective }}

**Responsibilities**:
{% for responsibility in role.responsibilities %}
- {{ responsibility }}
{% endfor %}

**Capabilities**:
{% for capability in role.capabilities %}
- {{ capability }}
{% endfor %}

---

## Iteration Context

**Iteration Goal**: {{ iteration.goal }}

**Your Task**: {{ iteration.description }}

{% if iteration.context %}
### Reference Information

{{ iteration.context }}
{% endif %}

---

## Your Assigned Work

You have been assigned **{{ targets|length }} items** to work on:

{% for target in targets %}
{{ loop.index }}. {{ target.path }}
   - {{ target.description }}
{% endfor %}

---

## Deliverables

For each assigned item, you must produce:

{% for deliverable in deliverables %}
- **{{ deliverable.path }}**
  {% if deliverable.template %}
  - Template: `{{ deliverable.template }}`
  {% endif %}
  {% if deliverable.description %}
  - {{ deliverable.description }}
  {% endif %}
{% endfor %}

---

## Completion Criteria

Your work is complete when:

{% for criterion in completion_criteria.files %}
- {{ criterion }}
{% endfor %}

{% if completion_criteria.content %}
**Content Requirements**:
{% for criterion in completion_criteria.content %}
- {{ criterion }}
{% endfor %}
{% endif %}

---

## Standards and Guidelines

{% block standards %}
{# Role-specific standards go here #}
{% endblock %}

---

## Output Location

Place your deliverables in the following structure:

```
{{ output_structure }}
```

---

## Token Budget

**Allocated Token Budget**: {{ role.constraints.token_budget }}
**Estimated Usage**: {{ estimated_tokens }}
**Risk Level**: {{ risk_level }}

{% if risk_level == 'HIGH' %}
⚠️ **WARNING**: This allocation is at HIGH RISK of exceeding token budget.
Consider splitting work or simplifying scope.
{% endif %}

---

## Need Help?

- Review iteration `CONTEXT.md` for shared knowledge
- Check `COMPLETION_CRITERIA.md` for validation checklist
- See `README.md` for execution guidance
```

3. **Create Role-Specific Templates** (4 hours)

```jinja2
{# templates/product_analyst.md.j2 #}
{% extends "_base.md.j2" %}

{% block standards %}
### Requirements Standards

**Functional Requirements**:
- Clear, unambiguous statements
- Structured format (numbered list)
- Traceable to user story

**Acceptance Criteria**:
- Given/When/Then format
- Testable and measurable
- Cover happy path and edge cases

**Business Rules**:
- Explicitly stated constraints
- Validation rules defined
- Error scenarios identified

### Template Structure

For each user story, create `REQUIREMENTS.md` with:

1. **Functional Requirements**
   - List of what the system must do
   - Numbered for traceability

2. **Acceptance Criteria**
   - Given/When/Then scenarios
   - At least 3-5 criteria per story

3. **Business Rules**
   - Constraints and validations
   - Error handling requirements

4. **Edge Cases**
   - Unusual scenarios
   - Error conditions

5. **Dependencies**
   - Other stories/features required
   - External systems/APIs needed

### Example

```markdown
# US-E01-010: User Authentication

## Functional Requirements

1. System shall authenticate users via email and password
2. System shall enforce password complexity (8+ chars, 1 uppercase, 1 number)
3. System shall lock account after 5 failed attempts
...

## Acceptance Criteria

**AC1: Successful Login**
- Given: Valid email and password
- When: User submits login form
- Then: User is redirected to dashboard

**AC2: Failed Login**
- Given: Invalid password
- When: User submits login form
- Then: Error message displayed, attempt counter incremented
...
```
{% endblock %}
```

---

### Task 3: Refactor Orchestration Scripts (1 day)

**Current State**: Scripts are documentation-specific
- Hardcoded paths
- Hardcoded validation rules
- Documentation-specific messaging

**Target State**: Generic, configuration-driven scripts
- Read configuration from YAML
- Dynamic validation based on completion criteria
- Domain-neutral messaging

#### Steps

1. **Refactor `orchestrate_full.sh`** (4 hours)

```bash
#!/bin/bash
# orchestration-framework/tools/orchestrate_full.sh
# Full lifecycle orchestration (generate → launch → monitor → validate)

set -e

ITERATION_DIR="$1"
CONFIG_FILE="$2"

if [ -z "$ITERATION_DIR" ] || [ -z "$CONFIG_FILE" ]; then
    echo "Usage: $0 <iteration-dir> <workflow-config.yaml>"
    exit 1
fi

echo "=== Orchestration Full Lifecycle ==="
echo "Iteration: $ITERATION_DIR"
echo "Config: $CONFIG_FILE"
echo ""

# Step 1: Generate agent prompts (if not already generated)
if [ ! -d "$ITERATION_DIR/agent-prompts" ]; then
    echo "Step 1: Generating agent prompts..."
    python tools/generate_prompts.py \
        --workflow "$CONFIG_FILE" \
        --output "$ITERATION_DIR"
    echo "✅ Prompts generated"
else
    echo "ℹ️  Prompts already generated, skipping..."
fi

# Step 2: Launch agents
echo ""
echo "Step 2: Launching agents..."
./tools/launch_agents.sh "$ITERATION_DIR"
echo "✅ Agents launched"

# Step 3: Monitor execution
echo ""
echo "Step 3: Monitoring execution..."
./tools/monitor_enhanced.sh "$ITERATION_DIR"
echo "✅ Monitoring complete"

# Step 4: Validate results
echo ""
echo "Step 4: Validating results..."
./tools/validate_iteration.sh "$ITERATION_DIR"
VALIDATION_EXIT=$?

if [ $VALIDATION_EXIT -eq 0 ]; then
    echo "✅ Validation passed"
else
    echo "❌ Validation failed"
    exit 1
fi

# Step 5: Collect feedback
echo ""
echo "Step 5: Collecting feedback..."
./tools/collect_feedback.sh "$ITERATION_DIR"
echo "✅ Feedback collected"

echo ""
echo "=== Orchestration Complete ==="
```

2. **Refactor `validate_iteration.sh`** (4 hours)

```bash
#!/bin/bash
# orchestration-framework/tools/validate_iteration.sh
# Validate iteration deliverables against COMPLETION_CRITERIA.md

set -e

ITERATION_DIR="$1"
CRITERIA_FILE="$ITERATION_DIR/COMPLETION_CRITERIA.md"

if [ ! -f "$CRITERIA_FILE" ]; then
    echo "❌ COMPLETION_CRITERIA.md not found"
    exit 1
fi

echo "=== Validating Iteration ==="
echo "Iteration: $ITERATION_DIR"
echo ""

# Parse COMPLETION_CRITERIA.md and extract checks
# This is a simplified example - real implementation would parse YAML frontmatter
# or use a more structured format

PASSED=0
FAILED=0

# Check file existence
echo "Checking file existence..."
grep "^- \[" "$CRITERIA_FILE" | while read -r line; do
    # Extract file pattern from line
    file_pattern=$(echo "$line" | sed 's/.*\[\(.*\)\].*/\1/')
    
    # Find matching files
    matches=$(find "$ITERATION_DIR" -path "$file_pattern" 2>/dev/null | wc -l)
    
    if [ "$matches" -gt 0 ]; then
        echo "  ✅ $file_pattern ($matches files)"
        ((PASSED++))
    else
        echo "  ❌ $file_pattern (0 files)"
        ((FAILED++))
    fi
done

# Check file sizes
echo ""
echo "Checking file sizes..."
find "$ITERATION_DIR/outputs" -type f -name "*.md" | while read -r file; do
    size=$(wc -c < "$file")
    if [ "$size" -gt 1024 ]; then
        echo "  ✅ $file ($size bytes)"
        ((PASSED++))
    else
        echo "  ⚠️  $file ($size bytes - may be incomplete)"
    fi
done

echo ""
echo "=== Validation Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

exit 0
```

---

### Task 4: Create Example Workflows (1 day)

**Goal**: Create working examples for each pre-built workflow

#### Steps

1. **User Story Refinement Example** (2 hours)

Create complete example in `examples/user-story-refinement-example/`:
- Workflow configuration (YAML)
- Sample user stories (input)
- Generated prompts (show output)
- Expected deliverables (show structure)
- README with instructions

2. **Task Execution Example** (2 hours)

Create example for "Implement OAuth2 authentication":
- Workflow configuration
- Task description (input)
- Generated iteration structure
- Sample agent prompts
- README

3. **Code Review Example** (2 hours)

Create example for PR review:
- Workflow configuration
- Sample PR diff (input)
- Generated review prompts
- Sample review reports (output)
- README

4. **Test All Examples** (2 hours)

```bash
# Test each example
for example in examples/*/; do
    echo "Testing $example..."
    cd "$example"
    ./run-example.sh
    cd -
done
```

---

## Validation Criteria

Phase 1 is complete when:

- [ ] `generate_prompts.py` is refactored and configuration-driven
- [ ] Configuration schema (YAML) is defined and documented
- [ ] Generic prompt templates (Jinja2) are created for 5+ roles
- [ ] Orchestration scripts are refactored and generic
- [ ] 3+ example workflows are working end-to-end
- [ ] README and documentation are updated
- [ ] All tests pass

---

## Timeline

| Task | Duration | Assignee |
|------|----------|----------|
| Task 1: Refactor `generate_prompts.py` | 2 days | Engineer |
| Task 2: Create prompt templates | 1 day | Engineer |
| Task 3: Refactor orchestration scripts | 1 day | Engineer |
| Task 4: Create example workflows | 1 day | Engineer |
| **Total** | **5 days** | - |

---

## Next Steps After Phase 1

Once Phase 1 is complete, proceed to **Phase 2: Build Example Workflows** (1 week):
- Implement user story refinement workflow end-to-end
- Implement task execution workflow end-to-end
- Implement code review workflow end-to-end
- Test with real work items
- Collect feedback and refine

---

**Document Owner**: Master Orchestrator Agent  
**Status**: Ready to begin  
**Next Action**: Assign engineer and begin Task 1
