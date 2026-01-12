# Workflow Catalog

**Version**: 1.0  
**Date**: 2026-01-10  
**Purpose**: Pre-built workflows for common orchestration use cases

---

## Catalog Overview

This catalog provides ready-to-use workflow configurations for common development tasks. Each workflow includes:
- Iteration structure
- Agent role assignments
- Deliverables specification
- Completion criteria
- Example configurations

---

## Workflow 1: User Story Refinement

**Use Case**: Refine raw user stories with complete technical implementation details

###

 Workflow Configuration

```yaml
workflow:
  name: user-story-refinement
  version: 1.0
  description: Multi-phase refinement of user stories from requirements to implementation-ready
  
  phases:
    - phase: 1-definition
      name: Requirements Definition
      goal: Extract and validate functional requirements
      
      iterations:
        - name: requirements-extraction
          agents:
            - role: product_analyst
              allocation:
                strategy: round_robin  # Distribute stories evenly
                max_per_agent: 10
                complexity_per_item: 3
              inputs:
                - pattern: "work_items/{epic}/US-*.md"
                  filter: "status != 'refined'"
              deliverables:
                - path: "work_items/{epic}/{story_id}/REQUIREMENTS.md"
                  template: "requirements-template.md"
              
          completion_criteria:
            files:
              - All matching stories have REQUIREMENTS.md
              - File size > 1KB
            content:
              - Contains "Functional Requirements" section
              - Contains "Acceptance Criteria" section
              - All acceptance criteria are testable (Given/When/Then format)
    
    - phase: 2-product
      name: Product Refinement
      goal: Define user experience and product behavior
      dependencies: [1-definition]
      
      iterations:
        - name: product-specification
          agents:
            - role: product_designer
              allocation:
                strategy: round_robin
                max_per_agent: 8
                complexity_per_item: 5
              inputs:
                - pattern: "work_items/{epic}/{story_id}/REQUIREMENTS.md"
              deliverables:
                - path: "work_items/{epic}/{story_id}/PRODUCT_SPEC.md"
                  template: "product-spec-template.md"
              
          completion_criteria:
            files:
              - All stories have PRODUCT_SPEC.md
              - File size > 2KB
            content:
              - Contains "User Flows" section
              - Contains "UI/UX Requirements" section
              - Contains "Edge Cases" section
    
    - phase: 3-technical
      name: Technical Design
      goal: Design technical implementation with APIs, data models, tests
      dependencies: [2-product]
      
      iterations:
        - name: api-design
          agents:
            - role: backend_developer
              allocation:
                strategy: round_robin
                max_per_agent: 5
                complexity_per_item: 8
              inputs:
                - pattern: "work_items/{epic}/{story_id}/PRODUCT_SPEC.md"
              deliverables:
                - path: "work_items/{epic}/{story_id}/TECHNICAL_DESIGN.md"
                  template: "technical-design-template.md"
                - path: "work_items/{epic}/{story_id}/API_CONTRACT.yaml"
                  template: "openapi-template.yaml"
              
          completion_criteria:
            files:
              - All stories have TECHNICAL_DESIGN.md
              - All API-related stories have API_CONTRACT.yaml
              - File sizes meet minimums
            content:
              - Technical design includes data models
              - Technical design includes API endpoints
              - OpenAPI contracts are valid YAML
        
        - name: test-planning
          agents:
            - role: qa_engineer
              allocation:
                strategy: round_robin
                max_per_agent: 8
                complexity_per_item: 4
              inputs:
                - pattern: "work_items/{epic}/{story_id}/TECHNICAL_DESIGN.md"
              deliverables:
                - path: "work_items/{epic}/{story_id}/TEST_PLAN.md"
                  template: "test-plan-template.md"
              
          completion_criteria:
            files:
              - All stories have TEST_PLAN.md
            content:
              - Test plan includes unit tests
              - Test plan includes integration tests
              - Test plan includes acceptance tests

agent_roles:
  product_analyst:
    name: Product Analyst
    perspective: Product Owner + Business Analyst
    responsibilities:
      - Extract functional requirements from user stories
      - Define clear, testable acceptance criteria
      - Identify edge cases and error scenarios
      - Validate business rules and constraints
    capabilities:
      - Requirements elicitation
      - User story refinement
      - Acceptance criteria definition (Given/When/Then)
      - Business rule analysis
    constraints:
      token_budget: 30000
      max_items: 10
      complexity_threshold: 30  # total complexity points
    output_format:
      - REQUIREMENTS.md in structured format
  
  product_designer:
    name: Product Designer
    perspective: UX Designer + Product Manager
    responsibilities:
      - Define user flows and interactions
      - Specify UI/UX requirements
      - Document edge cases and error states
      - Define validation rules
    capabilities:
      - User flow design
      - UI/UX specification
      - Error handling design
      - Validation rule definition
    constraints:
      token_budget: 40000
      max_items: 8
      complexity_threshold: 40
    output_format:
      - PRODUCT_SPEC.md with user flows and UI specs
  
  backend_developer:
    name: Backend Developer
    perspective: Senior Backend Engineer
    responsibilities:
      - Design technical implementation
      - Define API contracts (OpenAPI)
      - Design data models and schemas
      - Plan database migrations
      - Identify technical dependencies
    capabilities:
      - System design
      - API design (REST, GraphQL)
      - Database schema design
      - Dependency analysis
    constraints:
      token_budget: 50000
      max_items: 5
      complexity_threshold: 40
    output_format:
      - TECHNICAL_DESIGN.md with implementation details
      - API_CONTRACT.yaml (OpenAPI 3.0)
  
  qa_engineer:
    name: QA Engineer
    perspective: Quality Assurance + Test Automation
    responsibilities:
      - Design test strategy
      - Define test cases (unit, integration, E2E)
      - Identify test data requirements
      - Plan test automation
    capabilities:
      - Test strategy design
      - Test case definition
      - Test automation planning
      - Test data generation
    constraints:
      token_budget: 35000
      max_items: 8
      complexity_threshold: 32
    output_format:
      - TEST_PLAN.md with comprehensive test strategy
```

---

## Workflow 2: Task Execution Orchestration

**Use Case**: Decompose and execute a complex task with specialized agents

### Workflow Configuration

```yaml
workflow:
  name: task-execution
  version: 1.0
  description: Break down complex task and delegate to specialized agents
  
  # Dynamic workflow - orchestrator decomposes task at runtime
  execution_mode: dynamic
  
  orchestrator_prompt: |
    You are given a complex task. Your job is to:
    1. Analyze the task and identify required specialized skills
    2. Decompose the task into parallel subtasks
    3. Assign each subtask to an appropriate agent role
    4. Generate iteration structure with CONTEXT.md and COMPLETION_CRITERIA.md
    5. Monitor execution and validate results
    
    Task: {task_description}
    
    Available agent roles: {available_roles}
    
    Output:
    - Iteration structure (CONTEXT.md, COMPLETION_CRITERIA.md, agent prompts)
  
  available_roles:
    - architect
    - backend_developer
    - frontend_developer
    - qa_engineer
    - security_analyst
    - tech_writer
    - sre
    - data_scientist
  
  decomposition_strategy:
    max_subtasks: 10
    prefer_parallelization: true
    dependency_detection: auto
  
  validation_strategy:
    mode: dynamic  # Completion criteria generated by orchestrator
    min_deliverables: 1
    require_tests: true

agent_roles:
  architect:
    name: System Architect
    perspective: Senior Architect + Technical Lead
    responsibilities:
      - Design system architecture
      - Define component interfaces
      - Identify technical risks
      - Document architectural decisions (ADRs)
    capabilities:
      - System design
      - Architecture patterns
      - Technology selection
      - Risk assessment
    constraints:
      token_budget: 60000
      complexity_threshold: high
    output_format:
      - Architecture diagrams (Mermaid/PlantUML)
      - ADRs (Architecture Decision Records)
      - Component specifications
  
  backend_developer:
    name: Backend Developer
    perspective: Full-Stack Backend Engineer
    responsibilities:
      - Implement backend logic
      - Write unit and integration tests
      - Document APIs
      - Handle error cases
    capabilities:
      - Code implementation (Node.js, Python, Go, etc.)
      - Test automation
      - API documentation
      - Error handling
    constraints:
      token_budget: 80000
      complexity_threshold: medium
    output_format:
      - Source code files
      - Test files
      - API documentation
  
  frontend_developer:
    name: Frontend Developer
    perspective: Senior Frontend Engineer
    responsibilities:
      - Implement UI components
      - Write component tests
      - Ensure accessibility (WCAG 2.1)
      - Document component APIs
    capabilities:
      - React/Vue/Svelte implementation
      - Component testing (Jest, Testing Library)
      - Accessibility (a11y)
      - CSS/styling
    constraints:
      token_budget: 70000
      complexity_threshold: medium
    output_format:
      - Component source files
      - Component tests
      - Storybook stories
  
  security_analyst:
    name: Security Analyst
    perspective: Application Security Expert
    responsibilities:
      - Perform threat modeling
      - Identify security vulnerabilities
      - Define security requirements
      - Review authentication/authorization
    capabilities:
      - Threat modeling (STRIDE)
      - Vulnerability assessment
      - Security requirements definition
      - Auth/AuthZ review
    constraints:
      token_budget: 40000
      complexity_threshold: high
    output_format:
      - Threat model diagrams
      - Security requirements
      - Vulnerability report
```

---

## Workflow 3: Code Review Orchestration

**Use Case**: Comprehensive code review with multiple specialized perspectives

### Workflow Configuration

```yaml
workflow:
  name: code-review
  version: 1.0
  description: Multi-perspective code review for PRs
  
  trigger:
    event: pull_request_opened
    filters:
      - changed_files > 5
      - additions > 100
  
  phases:
    - phase: automated-checks
      name: Automated Checks
      goal: Run automated quality checks before human review
      
      checks:
        - linting: eslint/pylint
        - type_checking: typescript/mypy
        - security_scan: snyk
        - test_coverage: jest/pytest
      
      gate:
        condition: all_checks_pass
        action_on_failure: block_review
    
    - phase: specialist-review
      name: Specialist Reviews
      goal: Deep review from multiple specialized perspectives
      dependencies: [automated-checks]
      
      iterations:
        - name: functional-review
          agents:
            - role: senior_developer
              allocation:
                strategy: single  # One senior dev reviews all
              inputs:
                - pattern: "changed_files"
              deliverables:
                - path: "reviews/{pr_id}/functional-review.md"
              
        - name: security-review
          agents:
            - role: security_analyst
              allocation:
                strategy: single
              inputs:
                - pattern: "changed_files"
                  filter: "security_sensitive"
              deliverables:
                - path: "reviews/{pr_id}/security-review.md"
        
        - name: performance-review
          agents:
            - role: performance_engineer
              allocation:
                strategy: conditional
                condition: "performance_sensitive_files_changed"
              inputs:
                - pattern: "changed_files"
                  filter: "performance_critical"
              deliverables:
                - path: "reviews/{pr_id}/performance-review.md"

agent_roles:
  senior_developer:
    name: Senior Developer
    perspective: Experienced Engineer + Mentor
    responsibilities:
      - Review code logic and algorithms
      - Check for edge cases and error handling
      - Validate test coverage
      - Suggest improvements
    capabilities:
      - Code review
      - Algorithm analysis
      - Best practices enforcement
      - Mentoring
    constraints:
      token_budget: 100000
      complexity_threshold: high
    output_format:
      - Code review comments (inline + summary)
      - functional-review.md
  
  performance_engineer:
    name: Performance Engineer
    perspective: Performance Optimization Specialist
    responsibilities:
      - Identify performance bottlenecks
      - Review database queries (N+1, indexing)
      - Check caching strategies
      - Validate scalability
    capabilities:
      - Performance profiling
      - Query optimization
      - Caching design
      - Load testing
    constraints:
      token_budget: 60000
      complexity_threshold: high
    output_format:
      - Performance analysis
      - Optimization recommendations
      - performance-review.md
```

---

## Workflow 4: Documentation Generation

**Use Case**: Generate comprehensive documentation from code and specifications

### Workflow Configuration

```yaml
workflow:
  name: documentation-generation
  version: 1.0
  description: Multi-format documentation from codebase
  
  phases:
    - phase: extraction
      name: Content Extraction
      goal: Extract documentable content from codebase
      
      iterations:
        - name: api-extraction
          agents:
            - role: api_documenter
              allocation:
                strategy: by_service
              inputs:
                - pattern: "src/**/openapi.yaml"
                - pattern: "src/**/*.controller.ts"
              deliverables:
                - path: "docs/api/{service}/api-reference.md"
        
        - name: architecture-extraction
          agents:
            - role: architect_documenter
              allocation:
                strategy: single
              inputs:
                - pattern: "docs/architecture/**/*.md"
                - pattern: "src/**/README.md"
              deliverables:
                - path: "docs/architecture/ARCHITECTURE.md"
    
    - phase: user-guides
      name: User Documentation
      goal: Create end-user documentation
      dependencies: [extraction]
      
      iterations:
        - name: user-guide-generation
          agents:
            - role: technical_writer
              allocation:
                strategy: by_persona
              inputs:
                - pattern: "docs/api/**/*.md"
                - pattern: "features/**/*.md"
              deliverables:
                - path: "docs/guides/{persona}/getting-started.md"
                - path: "docs/guides/{persona}/tutorials.md"

agent_roles:
  api_documenter:
    name: API Documenter
    perspective: API Documentation Specialist
    responsibilities:
      - Generate API reference from OpenAPI specs
      - Create code examples for each endpoint
      - Document authentication and authorization
      - Provide troubleshooting guides
    capabilities:
      - OpenAPI to Markdown conversion
      - Code example generation
      - API best practices
    constraints:
      token_budget: 50000
    output_format:
      - API reference documentation (Markdown)
      - Postman/Insomnia collections
  
  technical_writer:
    name: Technical Writer
    perspective: User-Focused Documentation Expert
    responsibilities:
      - Write user-friendly guides
      - Create tutorials and examples
      - Explain complex concepts simply
      - Organize documentation structure
    capabilities:
      - Technical writing
      - Tutorial design
      - Information architecture
      - Plain language writing
    constraints:
      token_budget: 60000
    output_format:
      - User guides (Markdown)
      - Tutorials (step-by-step)
      - FAQ documents
```

---

## Workflow Template

Use this template to create new workflows:

```yaml
workflow:
  name: <workflow-name>
  version: 1.0
  description: <brief-description>
  
  # Static workflow (pre-defined iterations) or dynamic (orchestrator decides)
  execution_mode: static | dynamic
  
  phases:
    - phase: <phase-id>
      name: <phase-name>
      goal: <what-this-phase-achieves>
      dependencies: [<other-phase-ids>]  # Optional
      
      iterations:
        - name: <iteration-name>
          agents:
            - role: <agent-role>
              allocation:
                strategy: round_robin | single | by_<criteria>
                max_per_agent: <number>  # Optional
                complexity_per_item: <number>  # Optional
              inputs:
                - pattern: <glob-pattern>
                  filter: <filter-expression>  # Optional
              deliverables:
                - path: <output-path-with-variables>
                  template: <template-file>  # Optional
          
          completion_criteria:
            files:
              - <file-existence-check>
              - <file-size-check>
            content:
              - <content-validation-check>
            commands:
              - <automated-validation-command>

agent_roles:
  <role-id>:
    name: <Role Name>
    perspective: <Role Perspective>
    responsibilities:
      - <responsibility-1>
      - <responsibility-2>
    capabilities:
      - <capability-1>
      - <capability-2>
    constraints:
      token_budget: <number>
      max_items: <number>
      complexity_threshold: <number-or-level>
    output_format:
      - <deliverable-format-1>
      - <deliverable-format-2>
```

---

## Next Steps

1. **Select a workflow** from the catalog
2. **Customize configuration** for your use case
3. **Test with pilot** (small batch of work items)
4. **Refine based on feedback**
5. **Scale to full workload**

---

**Document Owner**: Master Orchestrator Agent  
**Related Documents**:
- `GENERIC_ORCHESTRATION_FRAMEWORK.md`
- `AGENT_ROLE_LIBRARY.md`
- `CONFIGURATION_GUIDE.md`
