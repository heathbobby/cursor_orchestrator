#!/usr/bin/env python3
"""
Git worktree management for Generic Orchestration Framework.

Manages git worktrees for isolated agent workspaces.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Worktree:
    """Represents a git worktree."""
    path: Path
    branch: str
    head_sha: str
    is_bare: bool = False
    
    @property
    def exists(self) -> bool:
        """Check if worktree directory exists."""
        return self.path.exists()


class WorktreeManager:
    """Manages git worktrees for agent workspaces."""
    
    def __init__(self, repo_root: Path, worktree_base: Optional[Path] = None):
        """
        Initialize worktree manager.
        
        Args:
            repo_root: Root directory of the git repository
            worktree_base: Base directory for worktrees (defaults to ../repo.worktrees)
        """
        self.repo_root = Path(repo_root)
        
        if worktree_base is None:
            self.worktree_base = self.repo_root.parent / f"{self.repo_root.name}.worktrees"
        else:
            self.worktree_base = Path(worktree_base)
    
    def list_worktrees(self) -> list[Worktree]:
        """
        List all git worktrees.
        
        Returns:
            List of Worktree objects
        """
        result = subprocess.run(
            ['git', 'worktree', 'list', '--porcelain'],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        worktrees = []
        current = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                if current:
                    worktrees.append(Worktree(
                        path=Path(current['worktree']),
                        branch=current.get('branch', ''),
                        head_sha=current.get('HEAD', ''),
                        is_bare=current.get('bare', False)
                    ))
                    current = {}
                continue
            
            if line.startswith('worktree '):
                current['worktree'] = line.split(' ', 1)[1]
            elif line.startswith('HEAD '):
                current['HEAD'] = line.split(' ', 1)[1]
            elif line.startswith('branch '):
                branch = line.split(' ', 1)[1]
                # Remove refs/heads/ prefix
                if branch.startswith('refs/heads/'):
                    branch = branch[len('refs/heads/'):]
                current['branch'] = branch
            elif line == 'bare':
                current['bare'] = True
        
        # Handle last worktree
        if current:
            worktrees.append(Worktree(
                path=Path(current['worktree']),
                branch=current.get('branch', ''),
                head_sha=current.get('HEAD', ''),
                is_bare=current.get('bare', False)
            ))
        
        return worktrees
    
    def create_worktree(
        self,
        role: str,
        task_name: str,
        base_branch: str = 'main',
        branch_prefix: str = 'feat'
    ) -> Worktree:
        """
        Create a new worktree for an agent.
        
        Args:
            role: Agent role name
            task_name: Task name or identifier
            base_branch: Base branch to create from
            branch_prefix: Branch prefix (feat/fix/chore/etc)
            
        Returns:
            Created Worktree object
        """
        # Create branch name
        branch_name = f"{branch_prefix}/{role}/{task_name}"
        
        # Create worktree path
        worktree_path = self.worktree_base / role / task_name
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create worktree
        subprocess.run(
            ['git', 'worktree', 'add', '-b', branch_name, str(worktree_path), base_branch],
            cwd=self.repo_root,
            check=True,
            capture_output=True
        )
        
        # Get HEAD SHA
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        head_sha = result.stdout.strip()
        
        return Worktree(
            path=worktree_path,
            branch=branch_name,
            head_sha=head_sha,
            is_bare=False
        )
    
    def remove_worktree(self, worktree_path: Path, force: bool = False) -> None:
        """
        Remove a worktree.
        
        Args:
            worktree_path: Path to the worktree
            force: Force removal even if worktree has changes
        """
        cmd = ['git', 'worktree', 'remove', str(worktree_path)]
        if force:
            cmd.append('--force')
        
        subprocess.run(cmd, cwd=self.repo_root, check=True)
    
    def prune_worktrees(self) -> None:
        """Remove worktree administrative files for deleted worktrees."""
        subprocess.run(
            ['git', 'worktree', 'prune'],
            cwd=self.repo_root,
            check=True
        )
    
    def get_worktree(self, branch: str) -> Optional[Worktree]:
        """
        Get worktree for a specific branch.
        
        Args:
            branch: Branch name
            
        Returns:
            Worktree object if found, None otherwise
        """
        for worktree in self.list_worktrees():
            if worktree.branch == branch:
                return worktree
        return None
    
    def worktree_exists(self, role: str, task_name: str) -> bool:
        """
        Check if a worktree exists for a role and task.
        
        Args:
            role: Agent role name
            task_name: Task name or identifier
            
        Returns:
            True if worktree exists
        """
        worktree_path = self.worktree_base / role / task_name
        return worktree_path.exists()


def create_agent_worktree(
    repo_root: Path,
    role: str,
    task_name: str,
    base_branch: str = 'main',
    worktree_base: Optional[Path] = None
) -> Worktree:
    """
    Convenience function to create an agent worktree.
    
    Args:
        repo_root: Root directory of the git repository
        role: Agent role name
        task_name: Task name or identifier
        base_branch: Base branch to create from
        worktree_base: Optional base directory for worktrees
        
    Returns:
        Created Worktree object
    """
    manager = WorktreeManager(repo_root, worktree_base)
    return manager.create_worktree(role, task_name, base_branch)


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    import shutil
    
    print("Testing worktree management:")
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
        
        # Create worktree manager
        manager = WorktreeManager(repo_path)
        
        print(f"Repository: {repo_path}")
        print(f"Worktree base: {manager.worktree_base}")
        print()
        
        # List initial worktrees
        worktrees = manager.list_worktrees()
        print(f"Initial worktrees: {len(worktrees)}")
        for wt in worktrees:
            print(f"  - {wt.path} (branch: {wt.branch})")
        print()
        
        # Create worktree for product analyst
        print("Creating worktree for product_analyst...")
        wt1 = manager.create_worktree('product_analyst', 'US-E01-010')
        print(f"✓ Created: {wt1.path}")
        print(f"  Branch: {wt1.branch}")
        print(f"  HEAD: {wt1.head_sha}")
        print()
        
        # Create worktree for backend developer
        print("Creating worktree for backend_developer...")
        wt2 = manager.create_worktree('backend_developer', 'US-E02-020')
        print(f"✓ Created: {wt2.path}")
        print(f"  Branch: {wt2.branch}")
        print()
        
        # List all worktrees
        worktrees = manager.list_worktrees()
        print(f"Total worktrees: {len(worktrees)}")
        for wt in worktrees:
            print(f"  - {wt.path.name if wt.path != repo_path else '(main)'} → {wt.branch}")
        print()
        
        # Check if worktree exists
        exists = manager.worktree_exists('product_analyst', 'US-E01-010')
        print(f"Worktree exists for product_analyst/US-E01-010: {exists}")
        print()
        
        # Get worktree by branch
        wt = manager.get_worktree('feat/product_analyst/US-E01-010')
        if wt:
            print(f"Found worktree by branch: {wt.path}")
        print()
        
        # Clean up
        print("Cleaning up worktrees...")
        manager.remove_worktree(wt1.path)
        manager.remove_worktree(wt2.path)
        manager.prune_worktrees()
        print("✓ Cleanup complete")
