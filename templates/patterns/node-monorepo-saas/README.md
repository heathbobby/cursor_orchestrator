# Pattern: node-monorepo-saas

Generic starter pattern for a **Node.js monorepo** SaaS platform.

## What it seeds

- Workflow YAML(s) into `.orchestration/config/workflows/`

## How to use

From the target project root:

```bash
python orchestration-framework/bootstrap.py --list-patterns
python orchestration-framework/bootstrap.py --init --pattern node-monorepo-saas
```

Then customize the seeded workflow’s `inputs` to point at your real work items.

