"""
GitHub API Mock Framework

Comprehensive mocking infrastructure for PyGithub library used in 
project_storage.py (293 lines) and GitHub integration features.

Provides realistic simulation of:
- Repository operations and management
- Branch and commit operations
- Pull request lifecycle management
- Issue tracking and management  
- File operations (create, read, update, delete)
- Authentication and rate limiting
- Webhook and API events

Designed for government audit compliance with 95%+ test coverage requirements.
"""

import base64
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from unittest.mock import Mock, MagicMock
from enum import Enum

logger = logging.getLogger(__name__)


class MockGitHubCommitStatus(Enum):
    """Mock GitHub commit status states"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    FAILURE = "failure"


class MockGitHubPullRequestState(Enum):
    """Mock GitHub pull request states"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class MockGitHubIssueState(Enum):
    """Mock GitHub issue states"""
    OPEN = "open"
    CLOSED = "closed"


class MockGitHubUser:
    """Mock GitHub user object"""
    
    def __init__(self, login: str = None, user_id: int = None):
        self.login = login or f"test_user_{random.randint(1000, 9999)}"
        self.id = user_id or random.randint(1000000, 9999999)
        self.name = f"Test User {random.randint(100, 999)}"
        self.email = f"{self.login}@example.com"
        self.avatar_url = f"https://avatars.githubusercontent.com/u/{self.id}"
        self.html_url = f"https://github.com/{self.login}"
        self.type = "User"
        self.site_admin = False
        self.created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1000))
        self.updated_at = datetime.now(timezone.utc)
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'login': self.login,
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'html_url': self.html_url,
            'type': self.type,
            'site_admin': self.site_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MockGitHubCommit:
    """Mock GitHub commit object"""
    
    def __init__(self, sha: str = None, message: str = None, author: MockGitHubUser = None):
        self.sha = sha or f"{random.randint(1000000000, 9999999999):040x}"[:40]
        self.message = message or f"Mock commit message {random.randint(1000, 9999)}"
        self.author = author or MockGitHubUser()
        self.committer = self.author
        self.created_at = datetime.now(timezone.utc)
        self.html_url = f"https://github.com/test/repo/commit/{self.sha}"
        self.parents = []
        self.files = []
        self.stats = {
            'additions': random.randint(1, 100),
            'deletions': random.randint(0, 50),
            'total': 0
        }
        self.stats['total'] = self.stats['additions'] + self.stats['deletions']
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'sha': self.sha,
            'message': self.message,
            'author': self.author.to_dict(),
            'committer': self.committer.to_dict(),
            'created_at': self.created_at.isoformat(),
            'html_url': self.html_url,
            'stats': self.stats
        }


class MockGitHubFile:
    """Mock GitHub file/content object"""
    
    def __init__(self, path: str, content: str = "", encoding: str = "base64"):
        self.path = path
        self.name = path.split('/')[-1]
        self.content = base64.b64encode(content.encode()).decode() if encoding == "base64" else content
        self.encoding = encoding
        self.size = len(content)
        self.sha = f"{hash(content) % 1000000000:040x}"[:40]
        self.type = "file"
        self.html_url = f"https://github.com/test/repo/blob/main/{path}"
        self.download_url = f"https://raw.githubusercontent.com/test/repo/main/{path}"
        
    def decoded_content(self) -> str:
        """Get decoded content"""
        if self.encoding == "base64":
            return base64.b64decode(self.content).decode()
        return self.content
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'path': self.path,
            'name': self.name,
            'content': self.content,
            'encoding': self.encoding,
            'size': self.size,
            'sha': self.sha,
            'type': self.type,
            'html_url': self.html_url,
            'download_url': self.download_url
        }


class MockGitHubBranch:
    """Mock GitHub branch object"""
    
    def __init__(self, name: str = None, commit: MockGitHubCommit = None):
        self.name = name or "main"
        self.commit = commit or MockGitHubCommit()
        self.protected = name == "main" if name else True
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'commit': self.commit.to_dict(),
            'protected': self.protected
        }


class MockGitHubPullRequest:
    """Mock GitHub pull request object"""
    
    def __init__(self, number: int = None, title: str = None, 
                 head_branch: str = None, base_branch: str = None):
        self.number = number or random.randint(1, 9999)
        self.title = title or f"Mock PR {self.number}"
        self.body = f"This is a mock pull request for testing purposes."
        self.state = MockGitHubPullRequestState.OPEN
        self.head = MockGitHubBranch(head_branch or "feature-branch")
        self.base = MockGitHubBranch(base_branch or "main")
        self.user = MockGitHubUser()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.closed_at = None
        self.merged_at = None
        self.html_url = f"https://github.com/test/repo/pull/{self.number}"
        self.mergeable = True
        self.merged = False
        self.draft = False
        self.commits = random.randint(1, 10)
        self.additions = random.randint(10, 500)
        self.deletions = random.randint(0, 100)
        self.changed_files = random.randint(1, 20)
        
    def merge(self, commit_title: str = None, commit_message: str = None, 
             merge_method: str = "merge"):
        """Mock merge operation"""
        if self.state != MockGitHubPullRequestState.OPEN:
            raise ValueError(f"Cannot merge PR in state {self.state.value}")
            
        self.state = MockGitHubPullRequestState.MERGED
        self.merged = True
        self.merged_at = datetime.now(timezone.utc)
        self.updated_at = self.merged_at
        
        # Create merge commit
        merge_commit = MockGitHubCommit(
            message=commit_title or f"Merge pull request #{self.number}",
            author=self.user
        )
        
        logger.debug(f"Mock PR #{self.number} merged with method {merge_method}")
        return merge_commit
        
    def close(self):
        """Mock close operation"""
        if self.state == MockGitHubPullRequestState.CLOSED:
            return
            
        self.state = MockGitHubPullRequestState.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        self.updated_at = self.closed_at
        logger.debug(f"Mock PR #{self.number} closed")
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'number': self.number,
            'title': self.title,
            'body': self.body,
            'state': self.state.value,
            'user': self.user.to_dict(),
            'head': self.head.to_dict(),
            'base': self.base.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'html_url': self.html_url,
            'mergeable': self.mergeable,
            'merged': self.merged,
            'draft': self.draft,
            'commits': self.commits,
            'additions': self.additions,
            'deletions': self.deletions,
            'changed_files': self.changed_files
        }


class MockGitHubIssue:
    """Mock GitHub issue object"""
    
    def __init__(self, number: int = None, title: str = None):
        self.number = number or random.randint(1, 9999)
        self.title = title or f"Mock Issue {self.number}"
        self.body = f"This is a mock issue for testing purposes."
        self.state = MockGitHubIssueState.OPEN
        self.user = MockGitHubUser()
        self.assignee = None
        self.assignees = []
        self.labels = []
        self.milestone = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.closed_at = None
        self.html_url = f"https://github.com/test/repo/issues/{self.number}"
        self.comments = random.randint(0, 10)
        
    def close(self):
        """Mock close operation"""
        if self.state == MockGitHubIssueState.CLOSED:
            return
            
        self.state = MockGitHubIssueState.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        self.updated_at = self.closed_at
        logger.debug(f"Mock Issue #{self.number} closed")
        
    def reopen(self):
        """Mock reopen operation"""
        if self.state == MockGitHubIssueState.OPEN:
            return
            
        self.state = MockGitHubIssueState.OPEN
        self.closed_at = None
        self.updated_at = datetime.now(timezone.utc)
        logger.debug(f"Mock Issue #{self.number} reopened")
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'number': self.number,
            'title': self.title,
            'body': self.body,
            'state': self.state.value,
            'user': self.user.to_dict(),
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'assignees': [a.to_dict() for a in self.assignees],
            'labels': self.labels,
            'milestone': self.milestone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'html_url': self.html_url,
            'comments': self.comments
        }


class MockGitHubRepo:
    """
    Comprehensive GitHub repository mock with realistic behavior simulation.
    
    Provides full simulation of repository operations including:
    - File operations (create, read, update, delete)
    - Branch and commit management
    - Pull request operations
    - Issue tracking
    - Repository settings and metadata
    """
    
    def __init__(self, full_name: str = None, owner: MockGitHubUser = None):
        self.full_name = full_name or "test/mock-repo"
        self.name = self.full_name.split('/')[-1]
        self.owner = owner or MockGitHubUser(login=self.full_name.split('/')[0])
        self.description = f"Mock repository for testing purposes"
        self.private = False
        self.fork = False
        self.created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))
        self.updated_at = datetime.now(timezone.utc)
        self.pushed_at = self.updated_at
        self.size = random.randint(100, 10000)
        self.stargazers_count = random.randint(0, 1000)
        self.watchers_count = random.randint(0, 100)
        self.forks_count = random.randint(0, 50)
        self.open_issues_count = random.randint(0, 20)
        self.default_branch = "main"
        self.html_url = f"https://github.com/{self.full_name}"
        self.clone_url = f"https://github.com/{self.full_name}.git"
        
        # Repository data
        self._branches: Dict[str, MockGitHubBranch] = {}
        self._files: Dict[str, MockGitHubFile] = {}
        self._commits: List[MockGitHubCommit] = []
        self._pull_requests: Dict[int, MockGitHubPullRequest] = {}
        self._issues: Dict[int, MockGitHubIssue] = {}
        
        # Initialize with default branch
        initial_commit = MockGitHubCommit(message="Initial commit", author=self.owner)
        self._commits.append(initial_commit)
        self._branches[self.default_branch] = MockGitHubBranch(self.default_branch, initial_commit)
        
        # Add default files
        self._files["README.md"] = MockGitHubFile("README.md", f"# {self.name}\n\nMock repository for testing")
        self._files[".gitignore"] = MockGitHubFile(".gitignore", "*.pyc\n__pycache__/\n.env")
        
        # Rate limiting simulation
        self._api_calls = 0
        self._rate_limit = 5000
        self._rate_limit_remaining = self._rate_limit
        self._rate_limit_reset = time.time() + 3600
        
    def _check_rate_limit(self):
        """Simulate GitHub API rate limiting"""
        current_time = time.time()
        if current_time > self._rate_limit_reset:
            self._rate_limit_remaining = self._rate_limit
            self._rate_limit_reset = current_time + 3600
            
        if self._rate_limit_remaining <= 0:
            raise Exception(f"GitHub API rate limit exceeded. Reset at {self._rate_limit_reset}")
            
        self._rate_limit_remaining -= 1
        self._api_calls += 1
        
    def get_contents(self, path: str, ref: str = None) -> MockGitHubFile:
        """Get file contents from repository"""
        self._check_rate_limit()
        
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
            
        return self._files[path]
        
    def create_file(self, path: str, message: str, content: str, 
                   branch: str = None, committer: MockGitHubUser = None) -> Dict:
        """Create a new file in repository"""
        self._check_rate_limit()
        
        if path in self._files:
            raise ValueError(f"File already exists: {path}")
            
        file_obj = MockGitHubFile(path, content)
        self._files[path] = file_obj
        
        # Create commit
        commit = MockGitHubCommit(
            message=message,
            author=committer or self.owner
        )
        self._commits.append(commit)
        
        logger.debug(f"Mock file created: {path}")
        return {
            'content': file_obj.to_dict(),
            'commit': commit.to_dict()
        }
        
    def update_file(self, path: str, message: str, content: str, sha: str,
                   branch: str = None, committer: MockGitHubUser = None) -> Dict:
        """Update existing file in repository"""
        self._check_rate_limit()
        
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
            
        file_obj = self._files[path]
        if file_obj.sha != sha:
            raise ValueError(f"SHA mismatch for file: {path}")
            
        # Update file
        file_obj.content = base64.b64encode(content.encode()).decode()
        file_obj.size = len(content)
        file_obj.sha = f"{hash(content) % 1000000000:040x}"[:40]
        
        # Create commit
        commit = MockGitHubCommit(
            message=message,
            author=committer or self.owner
        )
        self._commits.append(commit)
        
        logger.debug(f"Mock file updated: {path}")
        return {
            'content': file_obj.to_dict(),
            'commit': commit.to_dict()
        }
        
    def delete_file(self, path: str, message: str, sha: str,
                   branch: str = None, committer: MockGitHubUser = None) -> Dict:
        """Delete file from repository"""
        self._check_rate_limit()
        
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
            
        file_obj = self._files[path]
        if file_obj.sha != sha:
            raise ValueError(f"SHA mismatch for file: {path}")
            
        del self._files[path]
        
        # Create commit
        commit = MockGitHubCommit(
            message=message,
            author=committer or self.owner
        )
        self._commits.append(commit)
        
        logger.debug(f"Mock file deleted: {path}")
        return {
            'commit': commit.to_dict()
        }
        
    def get_branch(self, branch: str) -> MockGitHubBranch:
        """Get branch information"""
        self._check_rate_limit()
        
        if branch not in self._branches:
            raise KeyError(f"Branch not found: {branch}")
            
        return self._branches[branch]
        
    def create_branch(self, branch: str, sha: str) -> MockGitHubBranch:
        """Create new branch from commit SHA"""
        self._check_rate_limit()
        
        if branch in self._branches:
            raise ValueError(f"Branch already exists: {branch}")
            
        # Find commit by SHA
        commit = None
        for c in self._commits:
            if c.sha == sha:
                commit = c
                break
                
        if not commit:
            raise KeyError(f"Commit not found: {sha}")
            
        branch_obj = MockGitHubBranch(branch, commit)
        self._branches[branch] = branch_obj
        
        logger.debug(f"Mock branch created: {branch}")
        return branch_obj
        
    def get_pull_requests(self, state: str = "open", base: str = None,
                         head: str = None) -> List[MockGitHubPullRequest]:
        """Get pull requests"""
        self._check_rate_limit()
        
        prs = list(self._pull_requests.values())
        
        if state != "all":
            prs = [pr for pr in prs if pr.state.value == state]
        if base:
            prs = [pr for pr in prs if pr.base.name == base]
        if head:
            prs = [pr for pr in prs if pr.head.name == head]
            
        return prs
        
    def create_pull(self, title: str, body: str, head: str, base: str) -> MockGitHubPullRequest:
        """Create new pull request"""
        self._check_rate_limit()
        
        # Check that branches exist
        if head not in self._branches:
            raise KeyError(f"Head branch not found: {head}")
        if base not in self._branches:
            raise KeyError(f"Base branch not found: {base}")
            
        pr = MockGitHubPullRequest(
            title=title,
            head_branch=head,
            base_branch=base
        )
        pr.body = body
        
        self._pull_requests[pr.number] = pr
        
        logger.debug(f"Mock PR created: #{pr.number}")
        return pr
        
    def get_pull(self, number: int) -> MockGitHubPullRequest:
        """Get pull request by number"""
        self._check_rate_limit()
        
        if number not in self._pull_requests:
            raise KeyError(f"Pull request not found: #{number}")
            
        return self._pull_requests[number]
        
    def get_issues(self, state: str = "open", labels: List[str] = None) -> List[MockGitHubIssue]:
        """Get issues"""
        self._check_rate_limit()
        
        issues = list(self._issues.values())
        
        if state != "all":
            issues = [issue for issue in issues if issue.state.value == state]
        if labels:
            issues = [issue for issue in issues if any(label in issue.labels for label in labels)]
            
        return issues
        
    def create_issue(self, title: str, body: str = "", assignee: str = None,
                    labels: List[str] = None) -> MockGitHubIssue:
        """Create new issue"""
        self._check_rate_limit()
        
        issue = MockGitHubIssue(title=title)
        issue.body = body or ""
        if labels:
            issue.labels = labels
            
        self._issues[issue.number] = issue
        
        logger.debug(f"Mock issue created: #{issue.number}")
        return issue
        
    def get_issue(self, number: int) -> MockGitHubIssue:
        """Get issue by number"""
        self._check_rate_limit()
        
        if number not in self._issues:
            raise KeyError(f"Issue not found: #{number}")
            
        return self._issues[number]
        
    def get_commits(self, sha: str = None, path: str = None, 
                   since: datetime = None, until: datetime = None) -> List[MockGitHubCommit]:
        """Get repository commits"""
        self._check_rate_limit()
        
        commits = self._commits.copy()
        
        if since:
            commits = [c for c in commits if c.created_at >= since]
        if until:
            commits = [c for c in commits if c.created_at <= until]
            
        return commits
        
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return {
            'remaining': self._rate_limit_remaining,
            'limit': self._rate_limit,
            'reset': self._rate_limit_reset,
            'used': self._api_calls
        }
        
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'full_name': self.full_name,
            'name': self.name,
            'owner': self.owner.to_dict(),
            'description': self.description,
            'private': self.private,
            'fork': self.fork,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'pushed_at': self.pushed_at.isoformat(),
            'size': self.size,
            'stargazers_count': self.stargazers_count,
            'watchers_count': self.watchers_count,
            'forks_count': self.forks_count,
            'open_issues_count': self.open_issues_count,
            'default_branch': self.default_branch,
            'html_url': self.html_url,
            'clone_url': self.clone_url
        }


class MockGitHubAPI:
    """
    Mock GitHub API client with comprehensive functionality.
    
    Simulates PyGithub library behavior including:
    - Authentication and rate limiting
    - Repository operations
    - Organization management
    - User operations
    - Search functionality
    """
    
    def __init__(self, auth_token: str = None):
        self.auth_token = auth_token or "mock_token_12345"
        self._authenticated_user = MockGitHubUser(login="authenticated_user")
        self._repositories: Dict[str, MockGitHubRepo] = {}
        self._users: Dict[str, MockGitHubUser] = {}
        self._rate_limit_calls = 0
        
        # Add authenticated user
        self._users[self._authenticated_user.login] = self._authenticated_user
        
    def get_user(self, login: str = None) -> MockGitHubUser:
        """Get user information"""
        if login is None:
            return self._authenticated_user
            
        if login not in self._users:
            # Create mock user on demand
            user = MockGitHubUser(login=login)
            self._users[login] = user
            
        return self._users[login]
        
    def get_repo(self, full_name: str) -> MockGitHubRepo:
        """Get repository by full name"""
        if full_name not in self._repositories:
            # Create mock repository on demand
            owner_login = full_name.split('/')[0]
            owner = self.get_user(owner_login)
            repo = MockGitHubRepo(full_name=full_name, owner=owner)
            self._repositories[full_name] = repo
            
        return self._repositories[full_name]
        
    def create_repo(self, name: str, description: str = "", private: bool = False) -> MockGitHubRepo:
        """Create new repository"""
        full_name = f"{self._authenticated_user.login}/{name}"
        
        if full_name in self._repositories:
            raise ValueError(f"Repository already exists: {full_name}")
            
        repo = MockGitHubRepo(full_name=full_name, owner=self._authenticated_user)
        repo.description = description
        repo.private = private
        
        self._repositories[full_name] = repo
        logger.debug(f"Mock repository created: {full_name}")
        return repo
        
    def search_repositories(self, query: str, sort: str = "updated", 
                          order: str = "desc") -> List[MockGitHubRepo]:
        """Search repositories"""
        # Simple mock search - return all repos for testing
        return list(self._repositories.values())
        
    def get_rate_limit(self) -> Dict:
        """Get current rate limit status"""
        return {
            'core': {
                'limit': 5000,
                'remaining': 5000 - self._rate_limit_calls,
                'reset': time.time() + 3600,
                'used': self._rate_limit_calls
            },
            'search': {
                'limit': 30,
                'remaining': 30,
                'reset': time.time() + 60,
                'used': 0
            }
        }


def create_mock_github_api(auth_token: str = None) -> MockGitHubAPI:
    """Factory function to create a mock GitHub API client"""
    return MockGitHubAPI(auth_token)


def create_mock_github_repo(full_name: str = None, 
                           owner: MockGitHubUser = None) -> MockGitHubRepo:
    """Factory function to create a mock GitHub repository"""
    return MockGitHubRepo(full_name, owner)


# Export main classes for easy importing
__all__ = [
    'MockGitHubAPI',
    'MockGitHubRepo',
    'MockGitHubUser',
    'MockGitHubCommit',
    'MockGitHubFile',
    'MockGitHubBranch',
    'MockGitHubPullRequest',
    'MockGitHubIssue',
    'MockGitHubCommitStatus',
    'MockGitHubPullRequestState',
    'MockGitHubIssueState',
    'create_mock_github_api',
    'create_mock_github_repo'
]