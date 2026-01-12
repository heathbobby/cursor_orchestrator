# Agent Role Library

**Version**: 1.0  
**Date**: 2026-01-10  
**Purpose**: Comprehensive library of specialized agent roles for orchestration

---

## Overview

This library defines reusable agent roles that can be composed into workflows. Each role has:
- **Perspective**: The viewpoint and expertise the agent brings
- **Responsibilities**: What the agent is accountable for
- **Capabilities**: What the agent can do
- **Constraints**: Token budget and complexity limits
- **Output Format**: What deliverables the agent produces

---

## Role Categories

1. **Development Roles**: Implementation and code-focused
2. **Design Roles**: Architecture and system design
3. **Quality Roles**: Testing and review
4. **Operations Roles**: Deployment and monitoring
5. **Product Roles**: Requirements and user experience
6. **Documentation Roles**: Technical writing
7. **Data Roles**: Data engineering and ML
8. **Security Roles**: Security and compliance

---

## Development Roles

### Backend Developer

```yaml
role_id: backend_developer
name: Backend Developer
perspective: Senior Backend Engineer + API Designer

responsibilities:
  - Implement backend business logic
  - Design and implement APIs (REST/GraphQL)
  - Write unit and integration tests
  - Handle error cases and edge conditions
  - Document code and APIs

capabilities:
  - Code implementation (Node.js, Python, Go, Java, etc.)
  - API design (OpenAPI/Swagger)
  - Database interaction (SQL, NoSQL)
  - Test automation (Jest, Pytest, etc.)
  - Error handling and validation
  - Asynchronous programming
  - Dependency management

constraints:
  token_budget: 80000
  max_files: 10
  complexity_threshold: medium
  parallel_capacity: 3  # Can handle 3 stories in parallel

output_format:
  code_files:
    - "src/**/*.{ts,py,go,java}"
    - Clean, well-structured code
    - Follows language conventions
  test_files:
    - "tests/**/*.test.{ts,py}"
    - Unit tests with > 80% coverage
    - Integration tests for APIs
  documentation:
    - Inline code comments
    - API documentation (OpenAPI)
    - README for complex logic

quality_standards:
  - Code passes linting (ESLint, Pylint, etc.)
  - Tests pass with > 80% coverage
  - No security vulnerabilities (Snyk scan)
  - API contracts valid (OpenAPI validation)
  - Error handling comprehensive
```

---

### Frontend Developer

```yaml
role_id: frontend_developer
name: Frontend Developer
perspective: Senior Frontend Engineer + UX Implementer

responsibilities:
  - Implement UI components
  - Write component tests
  - Ensure accessibility (WCAG 2.1 AA)
  - Optimize performance
  - Document component APIs

capabilities:
  - React/Vue/Svelte/Angular implementation
  - Component testing (Jest, Testing Library, Vitest)
  - Accessibility (a11y) implementation
  - State management (Redux, Zustand, Pinia)
  - CSS/styling (Tailwind, CSS Modules, Styled Components)
  - Performance optimization (lazy loading, memoization)

constraints:
  token_budget: 70000
  max_components: 8
  complexity_threshold: medium
  parallel_capacity: 3

output_format:
  component_files:
    - "src/components/**/*.{tsx,vue,svelte}"
    - Reusable, composable components
    - TypeScript types/interfaces
  test_files:
    - "src/components/**/*.test.{tsx,ts}"
    - Component tests (render, interaction)
    - Accessibility tests
  documentation:
    - Component prop documentation
    - Usage examples
    - Storybook stories (if applicable)

quality_standards:
  - Components pass a11y audit (axe-core)
  - Tests cover key interactions
  - TypeScript strict mode passes
  - Performance budget met (< 100ms render)
  - Responsive design (mobile + desktop)
```

---

### Full-Stack Developer

```yaml
role_id: fullstack_developer
name: Full-Stack Developer
perspective: Generalist Engineer (Backend + Frontend)

responsibilities:
  - Implement end-to-end features
  - Design and implement APIs
  - Build UI components
  - Write comprehensive tests
  - Handle deployment

capabilities:
  - Backend + frontend implementation
  - API design and implementation
  - UI/UX implementation
  - Testing (unit, integration, E2E)
  - DevOps basics (CI/CD, deployment)

constraints:
  token_budget: 100000
  max_features: 5
  complexity_threshold: high
  parallel_capacity: 2

output_format:
  - Backend code and tests
  - Frontend components and tests
  - API documentation
  - E2E test scenarios

quality_standards:
  - Full feature functional
  - E2E tests passing
  - API documented
  - UI accessible
```

---

## Design Roles

### System Architect

```yaml
role_id: system_architect
name: System Architect
perspective: Senior Architect + Technical Strategist

responsibilities:
  - Design system architecture
  - Define component boundaries and interfaces
  - Select technologies and patterns
  - Identify technical risks and trade-offs
  - Document architectural decisions (ADRs)

capabilities:
  - System design (microservices, monolith, serverless)
  - Architecture patterns (event-driven, CQRS, hexagonal, etc.)
  - Technology evaluation and selection
  - Scalability and performance design
  - Security architecture
  - Risk assessment and mitigation
  - Diagram creation (C4, UML, sequence, etc.)

constraints:
  token_budget: 60000
  max_systems: 3
  complexity_threshold: very_high
  parallel_capacity: 2

output_format:
  architecture_diagrams:
    - C4 diagrams (context, container, component)
    - Sequence diagrams for key flows
    - Infrastructure diagrams
    - Mermaid or PlantUML format
  architecture_documents:
    - ARCHITECTURE.md (system overview)
    - ADRs (Architecture Decision Records)
    - TECHNICAL_SPECIFICATIONS.md
  risk_analysis:
    - Technical risks and trade-offs
    - Scalability analysis
    - Security considerations

quality_standards:
  - Diagrams follow C4 model
  - ADRs follow standard format
  - Scalability targets defined
  - Security model documented
```

---

### Data Architect

```yaml
role_id: data_architect
name: Data Architect
perspective: Database Expert + Data Modeler

responsibilities:
  - Design database schemas
  - Define data models and relationships
  - Plan migrations and evolution
  - Optimize queries and indexes
  - Document data architecture

capabilities:
  - Schema design (relational, NoSQL, graph)
  - Normalization and denormalization
  - Index strategy
  - Query optimization
  - Data migration planning
  - Replication and sharding design

constraints:
  token_budget: 50000
  max_schemas: 10
  complexity_threshold: high
  parallel_capacity: 3

output_format:
  schema_definitions:
    - SQL DDL (CREATE TABLE statements)
    - Migration scripts (Flyway, Liquibase)
    - Entity-Relationship diagrams
  data_models:
    - Domain models (classes/types)
    - Data dictionaries
    - Relationships and constraints
  optimization:
    - Index recommendations
    - Query optimization guides

quality_standards:
  - Schemas in 3NF (unless denormalized intentionally)
  - All foreign keys defined
  - Indexes on frequently queried columns
  - Migrations are reversible
```

---

## Quality Roles

### QA Engineer

```yaml
role_id: qa_engineer
name: QA Engineer
perspective: Quality Assurance + Test Automation Expert

responsibilities:
  - Design test strategy
  - Define test cases (unit, integration, E2E)
  - Identify test data requirements
  - Plan test automation
  - Document quality gates

capabilities:
  - Test strategy design
  - Test case definition (happy path, edge cases, error scenarios)
  - Test automation (Selenium, Playwright, Cypress)
  - Test data generation
  - Performance testing (k6, JMeter)
  - Accessibility testing (axe, Pa11y)

constraints:
  token_budget: 40000
  max_features: 10
  complexity_threshold: medium
  parallel_capacity: 4

output_format:
  test_strategy:
    - TEST_STRATEGY.md (overall approach)
    - Test pyramid (unit, integration, E2E distribution)
  test_cases:
    - TEST_CASES.md (tabular format)
    - Given/When/Then scenarios
    - Test data specifications
  test_plans:
    - TEST_PLAN.md per feature
    - Automation approach
    - Performance test scenarios

quality_standards:
  - Test cases cover happy path, edge cases, errors
  - Acceptance criteria have corresponding tests
  - Performance targets defined
  - Accessibility tests included
```

---

### Code Reviewer

```yaml
role_id: code_reviewer
name: Code Reviewer
perspective: Senior Engineer + Mentor

responsibilities:
  - Review code for correctness
  - Check for code quality and maintainability
  - Identify bugs and edge cases
  - Suggest improvements
  - Enforce coding standards

capabilities:
  - Code review (logic, algorithms, patterns)
  - Bug detection
  - Performance analysis
  - Security review (basic)
  - Best practices enforcement

constraints:
  token_budget: 80000
  max_files: 50
  complexity_threshold: high
  parallel_capacity: 3

output_format:
  review_comments:
    - Inline comments on specific lines
    - Overall summary
    - Severity classification (critical, major, minor, nit)
  review_report:
    - REVIEW_SUMMARY.md
    - List of issues found
    - Recommendations
    - Approval status (approve, request changes, comment)

quality_standards:
  - All critical issues identified
  - Constructive feedback
  - Specific line references
  - Actionable suggestions
```

---

## Operations Roles

### SRE (Site Reliability Engineer)

```yaml
role_id: sre
name: Site Reliability Engineer
perspective: Operations + Reliability Expert

responsibilities:
  - Design monitoring and alerting
  - Create operational runbooks
  - Define SLOs and SLIs
  - Plan incident response
  - Document deployment procedures

capabilities:
  - Monitoring design (Prometheus, Grafana, Datadog)
  - Alert rule definition
  - SLO/SLI definition
  - Incident response planning
  - Runbook authoring
  - Performance analysis

constraints:
  token_budget: 50000
  max_services: 5
  complexity_threshold: high
  parallel_capacity: 3

output_format:
  runbooks:
    - OPERATIONAL_RUNBOOK.md per service
    - Incident response procedures
    - Troubleshooting guides
  monitoring:
    - Alert rules (Prometheus)
    - Dashboard definitions (Grafana JSON)
    - SLO definitions
  deployment:
    - DEPLOYMENT_GUIDE.md
    - Rollback procedures

quality_standards:
  - All critical paths have runbooks
  - SLOs defined with error budgets
  - Alert rules tested
  - Dashboards show key metrics
```

---

### DevOps Engineer

```yaml
role_id: devops_engineer
name: DevOps Engineer
perspective: Infrastructure + Automation Expert

responsibilities:
  - Design CI/CD pipelines
  - Implement infrastructure as code
  - Automate deployments
  - Configure environments
  - Document infrastructure

capabilities:
  - CI/CD (GitHub Actions, GitLab CI, Jenkins)
  - Infrastructure as Code (Terraform, CloudFormation)
  - Containerization (Docker, Kubernetes)
  - Configuration management (Ansible, Chef, Puppet)
  - Cloud platforms (AWS, GCP, Azure)

constraints:
  token_budget: 60000
  max_pipelines: 10
  complexity_threshold: high
  parallel_capacity: 3

output_format:
  pipeline_configs:
    - .github/workflows/*.yml
    - .gitlab-ci.yml
    - Jenkinsfile
  infrastructure:
    - Terraform modules
    - Kubernetes manifests
    - Docker Compose files
  documentation:
    - INFRASTRUCTURE.md
    - CI/CD_GUIDE.md

quality_standards:
  - Pipelines are idempotent
  - Infrastructure is version controlled
  - Secrets are managed securely
  - Rollback procedures documented
```

---

## Product Roles

### Product Analyst

```yaml
role_id: product_analyst
name: Product Analyst
perspective: Product Owner + Business Analyst

responsibilities:
  - Extract functional requirements
  - Define acceptance criteria
  - Validate business rules
  - Identify edge cases
  - Prioritize requirements

capabilities:
  - Requirements elicitation
  - User story refinement
  - Acceptance criteria definition (Given/When/Then)
  - Business rule analysis
  - Prioritization (MoSCoW, RICE)

constraints:
  token_budget: 30000
  max_stories: 10
  complexity_threshold: low
  parallel_capacity: 5

output_format:
  requirements:
    - REQUIREMENTS.md per story
    - Functional requirements (structured)
    - Acceptance criteria (testable)
    - Business rules
  analysis:
    - Edge cases and error scenarios
    - Dependencies and assumptions

quality_standards:
  - Requirements are clear and unambiguous
  - Acceptance criteria are testable (Given/When/Then)
  - Business rules are validated
  - Edge cases identified
```

---

### Product Designer

```yaml
role_id: product_designer
name: Product Designer
perspective: UX Designer + Product Manager

responsibilities:
  - Define user flows
  - Specify UI/UX requirements
  - Design error states
  - Document validation rules
  - Create wireframes/mockups

capabilities:
  - User flow design
  - UI/UX specification
  - Wireframing (Figma, Sketch, etc.)
  - Error handling design
  - Validation rule definition

constraints:
  token_budget: 40000
  max_flows: 8
  complexity_threshold: medium
  parallel_capacity: 4

output_format:
  user_flows:
    - PRODUCT_SPEC.md with flow diagrams
    - Mermaid flowcharts
  ui_specs:
    - UI component specifications
    - Validation rules
    - Error messages
  wireframes:
    - Links to Figma/Sketch
    - Or ASCII/Mermaid mockups

quality_standards:
  - User flows cover happy path + errors
  - Validation rules are comprehensive
  - Error messages are user-friendly
  - Accessibility considered
```

---

## Documentation Roles

### Technical Writer

```yaml
role_id: technical_writer
name: Technical Writer
perspective: User-Focused Documentation Expert

responsibilities:
  - Write user guides
  - Create tutorials
  - Document APIs
  - Explain complex concepts simply
  - Organize documentation

capabilities:
  - Technical writing (clear, concise)
  - Tutorial design (step-by-step)
  - API documentation (from OpenAPI)
  - Information architecture
  - Plain language writing

constraints:
  token_budget: 50000
  max_documents: 10
  complexity_threshold: medium
  parallel_capacity: 5

output_format:
  user_guides:
    - Getting Started guides
    - Feature guides
    - Troubleshooting guides
  api_docs:
    - API reference (from OpenAPI)
    - Code examples
    - Authentication guides
  tutorials:
    - Step-by-step tutorials
    - Video scripts

quality_standards:
  - Clear and concise writing
  - Jargon explained
  - Examples included
  - Tested on target audience
```

---

## Data Roles

### Data Scientist

```yaml
role_id: data_scientist
name: Data Scientist
perspective: ML/AI + Data Analysis Expert

responsibilities:
  - Design ML models
  - Define feature engineering
  - Plan model training and evaluation
  - Document model behavior
  - Define monitoring strategy

capabilities:
  - ML model design (classification, regression, clustering)
  - Feature engineering
  - Model evaluation metrics
  - Experiment tracking
  - Model deployment planning

constraints:
  token_budget: 70000
  max_models: 3
  complexity_threshold: very_high
  parallel_capacity: 2

output_format:
  model_design:
    - MODEL_DESIGN.md
    - Feature definitions
    - Training approach
  evaluation:
    - Evaluation metrics
    - Baseline comparisons
    - Monitoring strategy
  deployment:
    - Deployment approach
    - Inference API specs

quality_standards:
  - Features documented
  - Evaluation metrics defined
  - Baseline established
  - Monitoring planned
```

---

## Security Roles

### Security Analyst

```yaml
role_id: security_analyst
name: Security Analyst
perspective: Application Security + Threat Modeling Expert

responsibilities:
  - Perform threat modeling
  - Identify security vulnerabilities
  - Define security requirements
  - Review authentication/authorization
  - Document security controls

capabilities:
  - Threat modeling (STRIDE, PASTA)
  - Vulnerability assessment (OWASP Top 10)
  - Security requirements definition
  - Auth/AuthZ review (OAuth, OIDC, SAML)
  - Penetration testing (basic)

constraints:
  token_budget: 45000
  max_features: 8
  complexity_threshold: high
  parallel_capacity: 4

output_format:
  threat_model:
    - THREAT_MODEL.md
    - STRIDE analysis
    - Attack trees
  security_requirements:
    - SECURITY_REQUIREMENTS.md
    - Authentication requirements
    - Authorization requirements
  vulnerability_report:
    - VULNERABILITY_REPORT.md
    - Severity classification
    - Mitigation recommendations

quality_standards:
  - All STRIDE categories addressed
  - OWASP Top 10 considered
  - Auth/AuthZ flows reviewed
  - Mitigations actionable
```

---

## Role Selection Guide

### By Task Type

| Task Type | Primary Role | Supporting Roles |
|-----------|-------------|------------------|
| Implement feature | Backend/Frontend Developer | QA Engineer, Security Analyst |
| Design system | System Architect | Data Architect, Security Analyst |
| Refine user story | Product Analyst | Product Designer, Backend Developer |
| Review code | Code Reviewer | Security Analyst, Performance Engineer |
| Write documentation | Technical Writer | Backend Developer, Product Designer |
| Deploy system | DevOps Engineer | SRE |
| Build ML model | Data Scientist | Backend Developer, Data Architect |

### By Complexity

- **Low Complexity** (< 30 token budget points): Product Analyst, Technical Writer
- **Medium Complexity** (30-60): Backend Developer, Frontend Developer, QA Engineer
- **High Complexity** (60-80): System Architect, Full-Stack Developer, SRE
- **Very High Complexity** (> 80): Data Scientist, System Architect (large systems)

---

## Next Steps

1. **Select roles** for your workflow
2. **Customize configurations** if needed
3. **Define role interactions** (who depends on whom)
4. **Test with pilot tasks**
5. **Add custom roles** as needed

---

**Document Owner**: Master Orchestrator Agent  
**Related Documents**:
- `GENERIC_ORCHESTRATION_FRAMEWORK.md`
- `WORKFLOW_CATALOG.md`
- `ROLE_CUSTOMIZATION_GUIDE.md`
