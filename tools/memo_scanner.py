#!/usr/bin/env python3
"""
Memo scanning for Generic Orchestration Framework.

Scans agent-sync/ directory for coordination memos and extracts metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Memo:
    """Represents a coordination memo."""
    path: Path
    date: Optional[datetime]
    audience: list[str]
    status: str
    branch: Optional[str]
    sha: Optional[str]
    role: Optional[str]
    work_item: Optional[str]
    deliverables: list[str]
    
    @property
    def is_ready_to_consume(self) -> bool:
        """Check if memo status is ready-to-consume."""
        return 'ready-to-consume' in self.status.lower()
    
    @property
    def is_ready_to_merge(self) -> bool:
        """Check if memo status is ready-to-merge."""
        return 'ready-to-merge' in self.status.lower()
    
    @property
    def is_blocked(self) -> bool:
        """Check if memo status is blocked."""
        return 'blocked' in self.status.lower()
    
    @property
    def is_draft(self) -> bool:
        """Check if memo status is draft."""
        return 'draft' in self.status.lower()


class MemoScanner:
    """Scans and parses coordination memos."""
    
    # Regex patterns for parsing memo headers
    DATE_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Date\*\*:\s*([^\n]+)', re.IGNORECASE)
    AUDIENCE_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Audience\*\*:\s*([^\n]+)', re.IGNORECASE)
    STATUS_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Status\*\*:\s*`?([^`\n]+)`?', re.IGNORECASE)
    BRANCH_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Branch\*\*:\s*`?([^`\n]+)`?', re.IGNORECASE)
    SHA_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*SHA\*\*:\s*`?([0-9a-f]{6,40})`?', re.IGNORECASE)
    WORK_ITEM_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Work Item\*\*:\s*([^\n]+)', re.IGNORECASE)
    DELIVERABLES_PATTERN = re.compile(r'(?:^|\n)\s*-?\s*\*\*Deliverables\*\*:\s*\n((?:\s*-\s*[^\n]+\n?)*)', re.IGNORECASE)
    
    def __init__(self, agent_sync_dir: Path):
        """
        Initialize memo scanner.
        
        Args:
            agent_sync_dir: Path to agent-sync directory
        """
        self.agent_sync_dir = Path(agent_sync_dir)
    
    def scan_all(self) -> list[Memo]:
        """
        Scan all memos in agent-sync directory.
        
        Returns:
            List of Memo objects
        """
        if not self.agent_sync_dir.exists():
            return []
        
        memos = []
        for memo_path in sorted(self.agent_sync_dir.glob('*.md')):
            # Skip certain files
            if memo_path.name in ('COMMAND_SHORTHAND.md', 'COMMUNICATION_CONVENTIONS.md', 
                                  'WORKTREE_OPERATING_MODEL.md', 'README.md'):
                continue
            
            memo = self.parse_memo(memo_path)
            if memo:
                memos.append(memo)
        
        return memos
    
    def scan_ready_to_consume(self) -> list[Memo]:
        """
        Scan for memos with ready-to-consume status.
        
        Returns:
            List of Memo objects with ready-to-consume status
        """
        all_memos = self.scan_all()
        return [m for m in all_memos if m.is_ready_to_consume]
    
    def scan_ready_to_merge(self) -> list[Memo]:
        """
        Scan for memos with ready-to-merge status.
        
        Returns:
            List of Memo objects with ready-to-merge status
        """
        all_memos = self.scan_all()
        return [m for m in all_memos if m.is_ready_to_merge]
    
    def scan_blocked(self) -> list[Memo]:
        """
        Scan for memos with blocked status.
        
        Returns:
            List of Memo objects with blocked status
        """
        all_memos = self.scan_all()
        return [m for m in all_memos if m.is_blocked]
    
    def parse_memo(self, memo_path: Path) -> Optional[Memo]:
        """
        Parse a memo file and extract metadata.
        
        Args:
            memo_path: Path to memo file
            
        Returns:
            Memo object if successfully parsed, None otherwise
        """
        try:
            content = memo_path.read_text(encoding='utf-8')
        except Exception:
            return None
        
        # Extract metadata using regex
        date_match = self.DATE_PATTERN.search(content)
        audience_match = self.AUDIENCE_PATTERN.search(content)
        status_match = self.STATUS_PATTERN.search(content)
        branch_match = self.BRANCH_PATTERN.search(content)
        sha_match = self.SHA_PATTERN.search(content)
        work_item_match = self.WORK_ITEM_PATTERN.search(content)
        deliverables_match = self.DELIVERABLES_PATTERN.search(content)
        
        # Parse date
        date = None
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                pass
        
        # Parse audience (extract @role tags)
        audience = []
        if audience_match:
            audience_str = audience_match.group(1)
            # Find all @role tags
            audience = re.findall(r'@([\w-]+)', audience_str)
        
        # Parse status
        status = status_match.group(1).strip() if status_match else 'unknown'
        
        # Parse branch and SHA
        branch = branch_match.group(1).strip() if branch_match else None
        sha = sha_match.group(1).strip() if sha_match else None
        
        # Parse work item
        work_item = work_item_match.group(1).strip() if work_item_match else None
        
        # Parse deliverables
        deliverables = []
        if deliverables_match:
            deliverables_text = deliverables_match.group(1)
            # Extract each deliverable line
            for line in deliverables_text.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    deliverable = line.lstrip('- ').strip()
                    if deliverable:
                        deliverables.append(deliverable)
        
        # Extract role from filename (format: YYYY-MM-DD_role_topic.md)
        role = None
        filename_parts = memo_path.stem.split('_')
        if len(filename_parts) >= 2:
            # Second part is typically the role
            role = filename_parts[1]
        
        return Memo(
            path=memo_path,
            date=date,
            audience=audience,
            status=status,
            branch=branch,
            sha=sha,
            role=role,
            work_item=work_item,
            deliverables=deliverables
        )


def scan_ready_to_consume(agent_sync_dir: Path) -> list[Memo]:
    """
    Convenience function to scan for ready-to-consume memos.
    
    Args:
        agent_sync_dir: Path to agent-sync directory
        
    Returns:
        List of ready-to-consume Memo objects
    """
    scanner = MemoScanner(agent_sync_dir)
    return scanner.scan_ready_to_consume()


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    
    print("Testing memo scanner:")
    print("=" * 70)
    
    # Create test memos
    with tempfile.TemporaryDirectory() as tmpdir:
        agent_sync = Path(tmpdir) / "agent-sync"
        agent_sync.mkdir()
        
        # Create test memo 1 (ready-to-consume)
        memo1 = agent_sync / "2026-01-10_product-analyst_US-E01-010.md"
        memo1.write_text("""# Ready-to-Consume: US-E01-010

- **Date**: 2026-01-10
- **Audience**: `@integrator @backend_developer`
- **Status**: `ready-to-consume`
- **Branch**: `feat/product-analyst/US-E01-010`
- **SHA**: `a3f4c2b`
- **Work Item**: US-E01-010

## Deliverables

- `work_items/E01/US-E01-010.md` (updated)
- Technical specifications complete

## How to Consume

```bash
git merge feat/product-analyst/US-E01-010
```
""")
        
        # Create test memo 2 (draft)
        memo2 = agent_sync / "2026-01-10_backend-developer_US-E02-020.md"
        memo2.write_text("""# Draft: US-E02-020

- **Date**: 2026-01-10
- **Audience**: `@integrator`
- **Status**: `draft`
- **Branch**: `feat/backend-developer/US-E02-020`
- **Work Item**: US-E02-020

Work in progress...
""")
        
        # Create test memo 3 (blocked)
        memo3 = agent_sync / "2026-01-10_qa-engineer_US-E03-030.md"
        memo3.write_text("""# Blocked: US-E03-030

- **Date**: 2026-01-10
- **Audience**: `@integrator @backend_developer`
- **Status**: `blocked`
- **Work Item**: US-E03-030

Waiting for backend implementation...
""")
        
        # Create test memo 4 (ready-to-merge)
        memo4 = agent_sync / "2026-01-09_tech-writer_US-E04-040.md"
        memo4.write_text("""# Ready-to-Merge: US-E04-040

- **Date**: 2026-01-09
- **Audience**: `@integrator`
- **Status**: `ready-to-merge`
- **Branch**: `feat/tech-writer/US-E04-040`
- **SHA**: `def789`
- **Work Item**: US-E04-040

## Deliverables

- `docs/user-guide.md` (created)

All gates passed. Ready to merge.
""")
        
        # Scan all memos
        scanner = MemoScanner(agent_sync)
        all_memos = scanner.scan_all()
        
        print(f"\nTotal memos: {len(all_memos)}")
        for memo in all_memos:
            print(f"\n  {memo.path.name}")
            print(f"    Role: {memo.role}")
            print(f"    Status: {memo.status}")
            print(f"    Branch: {memo.branch}")
            print(f"    SHA: {memo.sha}")
            print(f"    Work Item: {memo.work_item}")
            print(f"    Audience: {', '.join(memo.audience)}")
            if memo.deliverables:
                print(f"    Deliverables: {len(memo.deliverables)}")
        
        # Scan ready-to-consume
        ready_memos = scanner.scan_ready_to_consume()
        print(f"\n" + "=" * 70)
        print(f"Ready-to-consume memos: {len(ready_memos)}")
        for memo in ready_memos:
            print(f"  - {memo.path.name} (branch: {memo.branch}, sha: {memo.sha})")
        
        # Scan ready-to-merge
        merge_memos = scanner.scan_ready_to_merge()
        print(f"\nReady-to-merge memos: {len(merge_memos)}")
        for memo in merge_memos:
            print(f"  - {memo.path.name} (branch: {memo.branch}, sha: {memo.sha})")
        
        # Scan blocked
        blocked_memos = scanner.scan_blocked()
        print(f"\nBlocked memos: {len(blocked_memos)}")
        for memo in blocked_memos:
            print(f"  - {memo.path.name} (work item: {memo.work_item})")
        
        print("\n✓ Memo scanning complete")
