#!/usr/bin/env python3
"""
Integration automation for Generic Orchestration Framework.

Implements the apply-ready workflow for converging agent work.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .memo_scanner import MemoScanner, Memo
from .worktree_manager import WorktreeManager


@dataclass
class IntegrationResult:
    """Result of integration operation."""
    success: bool
    message: str
    merged_branches: list[str]
    failed_branches: list[str]
    skipped_memos: list[str]
    
    @property
    def total_processed(self) -> int:
        """Total number of items processed."""
        return len(self.merged_branches) + len(self.failed_branches) + len(self.skipped_memos)


class IntegrationManager:
    """Manages integration of agent work into target branch."""
    
    def __init__(
        self,
        repo_root: Path,
        target_branch: str = 'main',
        trunk_branch: str = 'main',
        agent_sync_dir: Optional[Path] = None
    ):
        """
        Initialize integration manager.
        
        Args:
            repo_root: Root directory of the git repository
            target_branch: Target branch for integration
            agent_sync_dir: Path to agent-sync directory (defaults to repo_root/agent-sync)
        """
        self.repo_root = Path(repo_root)
        self.target_branch = target_branch
        self.trunk_branch = trunk_branch
        
        if agent_sync_dir is None:
            self.agent_sync_dir = self.repo_root / "agent-sync"
        else:
            self.agent_sync_dir = Path(agent_sync_dir)
        
        self.memo_scanner = MemoScanner(self.agent_sync_dir)
        self.worktree_manager = WorktreeManager(repo_root)
    
    def apply_ready(self, dry_run: bool = False) -> IntegrationResult:
        """
        Apply all ready-to-consume work to target branch.
        
        Args:
            dry_run: If True, don't actually merge, just report what would happen
            
        Returns:
            IntegrationResult with summary of operations
        """
        # Scan for ready-to-consume memos
        ready_memos = self.memo_scanner.scan_ready_to_consume()
        
        if not ready_memos:
            return IntegrationResult(
                success=True,
                message="No ready-to-consume work found",
                merged_branches=[],
                failed_branches=[],
                skipped_memos=[]
            )
        
        print(f"Found {len(ready_memos)} ready-to-consume memo(s)")
        
        merged_branches = []
        failed_branches = []
        skipped_memos = []
        
        for memo in ready_memos:
            if not memo.branch:
                print(f"  WARN Skipping {memo.path.name}: No branch specified")
                skipped_memos.append(str(memo.path.name))
                continue
            
            print(f"\n  Processing: {memo.path.name}")
            print(f"    Branch: {memo.branch}")
            print(f"    SHA: {memo.sha or 'unknown'}")
            
            if dry_run:
                print(f"    [DRY RUN] Would merge {memo.branch}")
                merged_branches.append(memo.branch)
                continue
            
            # Attempt merge
            try:
                self._merge_branch(memo.branch, memo)
                merged_branches.append(memo.branch)
                print("    OK Merged successfully")
                
                # Update memo status
                # Align with documented memo lifecycle: ready-to-consume -> ready-to-merge
                self._update_memo_status(memo, 'ready-to-merge')
                
            except Exception as e:
                print(f"    ERR Merge failed: {e}")
                failed_branches.append(memo.branch)
                
                # Update memo status
                # Use documented status values; attach error detail.
                self._update_memo_status(memo, 'blocked', str(e))
        
        # Summary
        success = len(failed_branches) == 0
        message = f"Processed {len(ready_memos)} memo(s): {len(merged_branches)} merged, {len(failed_branches)} failed, {len(skipped_memos)} skipped"
        
        return IntegrationResult(
            success=success,
            message=message,
            merged_branches=merged_branches,
            failed_branches=failed_branches,
            skipped_memos=skipped_memos
        )
    
    def _merge_branch(self, branch: str, memo: Memo) -> None:
        """
        Merge a branch into target branch.
        
        Args:
            branch: Branch name to merge
            memo: Memo associated with the branch
            
        Raises:
            subprocess.CalledProcessError: If merge fails
        """
        self._ensure_target_branch()
        
        # Pull latest changes (if remote exists)
        try:
            subprocess.run(
                ['git', 'pull', 'origin', self.target_branch],
                cwd=self.repo_root,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # No remote or other error - skip pull
            pass
        
        # Merge the branch
        commit_message = f"feat: integrate {memo.work_item or branch}\n\nFrom: {memo.role or 'agent'}\nMemo: {memo.path.name}"
        
        subprocess.run(
            ['git', 'merge', '--no-ff', '-m', commit_message, branch],
            cwd=self.repo_root,
            check=True,
            capture_output=True
        )

    def _ensure_target_branch(self) -> None:
        """
        Ensure the target branch exists locally and is checked out.

        If the target branch doesn't exist, create it from trunk_branch.
        This is especially useful for integration branches like `integration/YYYY-MM-DD`.
        """
        # First try checkout directly (works if branch already exists).
        try:
            subprocess.run(
                ['git', 'checkout', self.target_branch],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            return
        except subprocess.CalledProcessError:
            pass

        # Ensure trunk is available locally; best-effort pull.
        try:
            subprocess.run(
                ['git', 'checkout', self.trunk_branch],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Unable to checkout trunk branch '{self.trunk_branch}': {e.stderr.decode(errors='ignore') if e.stderr else e}")

        try:
            subprocess.run(
                ['git', 'pull', 'origin', self.trunk_branch],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass

        # Create the target branch from trunk.
        subprocess.run(
            ['git', 'checkout', '-b', self.target_branch],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
    
    def _update_memo_status(self, memo: Memo, new_status: str, error_message: Optional[str] = None) -> None:
        """
        Update memo status in file.
        
        Args:
            memo: Memo to update
            new_status: New status value
            error_message: Optional error message for failed merges
        """
        try:
            content = memo.path.read_text(encoding='utf-8')
            
            # Update status line
            import re
            pattern = re.compile(r'(\*\*Status\*\*:\s*)`?([^`\n]+)`?', re.IGNORECASE)
            
            if error_message:
                replacement = f'\\1`{new_status}` - {error_message}'
            else:
                replacement = f'\\1`{new_status}`'
            
            updated_content = pattern.sub(replacement, content)
            
            # Add integration timestamp
            timestamp = datetime.now().isoformat()
            integration_note = f"\n\n**Integrated**: {timestamp}\n"
            
            if integration_note not in updated_content:
                updated_content += integration_note
            
            memo.path.write_text(updated_content, encoding='utf-8')
            
        except Exception as e:
            print(f"    Warning: Failed to update memo status: {e}")
    
    def list_ready_work(self) -> list[Memo]:
        """
        List all ready-to-consume work.
        
        Returns:
            List of ready-to-consume Memo objects
        """
        return self.memo_scanner.scan_ready_to_consume()
    
    def check_merge_conflicts(self, branch: str) -> tuple[bool, str]:
        """
        Check if merging a branch would cause conflicts.
        
        Args:
            branch: Branch name to check
            
        Returns:
            Tuple of (has_conflicts, message)
        """
        try:
            # Use git merge with --no-commit and --no-ff to test merge
            result = subprocess.run(
                ['git', 'merge', '--no-commit', '--no-ff', branch],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            
            # Abort the test merge
            subprocess.run(
                ['git', 'merge', '--abort'],
                cwd=self.repo_root,
                capture_output=True
            )
            
            if result.returncode != 0:
                return True, result.stderr
            
            return False, "No conflicts detected"
            
        except Exception as e:
            return True, str(e)


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    import shutil
    
    print("Testing integration automation:")
    print("=" * 70)
    
    # Create a temporary git repository for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
        
        # Create initial commit
        (repo_path / 'README.md').write_text('# Test Repo')
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True, capture_output=True)
        
        # Create agent-sync directory
        agent_sync = repo_path / "agent-sync"
        agent_sync.mkdir()
        
        # Create a feature branch with changes
        subprocess.run(['git', 'checkout', '-b', 'feat/product-analyst/US-E01-010'], cwd=repo_path, check=True, capture_output=True)
        (repo_path / 'feature.md').write_text('# New Feature')
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Add feature'], cwd=repo_path, check=True, capture_output=True)
        
        # Get SHA
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=repo_path, capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        
        # Go back to main
        subprocess.run(['git', 'checkout', 'main'], cwd=repo_path, check=True, capture_output=True)
        
        # Create ready-to-consume memo
        memo_path = agent_sync / "2026-01-10_product-analyst_US-E01-010.md"
        memo_path.write_text(f"""# Ready-to-Consume: US-E01-010

- **Date**: 2026-01-10
- **Audience**: `@integrator`
- **Status**: `ready-to-consume`
- **Branch**: `feat/product-analyst/US-E01-010`
- **SHA**: `{sha}`
- **Work Item**: US-E01-010

## Deliverables

- `feature.md` (created)

Ready to integrate!
""")
        
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Add memo'], cwd=repo_path, check=True, capture_output=True)
        
        print(f"Repository: {repo_path}")
        print()
        
        # Create integration manager
        manager = IntegrationManager(repo_path)
        
        # List ready work
        ready_work = manager.list_ready_work()
        print(f"Ready-to-consume work: {len(ready_work)}")
        for memo in ready_work:
            print(f"  - {memo.path.name} ({memo.branch})")
        print()
        
        # Dry run
        print("Dry run:")
        result = manager.apply_ready(dry_run=True)
        print(f"  {result.message}")
        print(f"  Would merge: {', '.join(result.merged_branches)}")
        print()
        
        # Actually apply
        print("Applying ready work:")
        result = manager.apply_ready(dry_run=False)
        print(f"  {result.message}")
        print(f"  Success: {result.success}")
        print(f"  Merged: {len(result.merged_branches)} branch(es)")
        print()
        
        # Verify merge
        subprocess.run(['git', 'log', '--oneline', '-5'], cwd=repo_path, check=False)
        
        print("\n✓ Integration automation test complete")
