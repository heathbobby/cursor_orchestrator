# Bootstrap Testing Workspace

This directory contains **throwaway test projects** used to validate the framework bootstrap process.

It is intentionally **gitignored**.

## What gets tested

- Copying this framework into a host project under `orchestration-framework/`
- Running `python orchestration-framework/bootstrap.py --init`
- Verifying the host project gets:
  - `.orchestration/config/workflows/` (configurable + commit-able)
  - `.orchestration/runtime/` (runtime artifacts, typically not committed)
  - `work_items/` scaffold
  - `CONTRIBUTING.md` orchestration section
  - `.gitignore` updated with orchestration runtime + worktree patterns

## Test projects

- `python-sample/`: minimal Python app + tests
- `node-sample/`: minimal Node app
- `mixed-sample/`: small mixed-language repo

