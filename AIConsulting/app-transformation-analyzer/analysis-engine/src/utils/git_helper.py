"""
Git operations helper for repository analysis.
Handles cloning, branch management, and file operations.
"""

import os
import shutil
import tempfile
import logging
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError

logger = logging.getLogger(__name__)


class GitRepositoryError(Exception):
    """Custom exception for Git repository operations."""
    pass


class GitHelper:
    """Helper class for Git repository operations."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize GitHelper.
        
        Args:
            temp_dir: Optional temporary directory for cloning repositories
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cloned_repos: Dict[str, str] = {}
    
    def validate_repository_url(self, repo_url: str) -> bool:
        """
        Validate if the repository URL is properly formatted.
        
        Args:
            repo_url: Repository URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(repo_url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check for common Git hosting services
            valid_hosts = [
                'github.com', 'gitlab.com', 'bitbucket.org',
                'dev.azure.com', 'sourceforge.net'
            ]
            
            if not any(host in parsed.netloc for host in valid_hosts):
                logger.warning(f"Unknown Git host: {parsed.netloc}")
            
            return True
            
        except Exception as e:
            logger.error(f"Invalid repository URL format: {e}")
            return False
    
    def clone_repository(
        self, 
        repo_url: str, 
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        target_dir: Optional[str] = None
    ) -> str:
        """
        Clone a Git repository to local directory.
        
        Args:
            repo_url: Repository URL to clone
            branch: Specific branch to clone (defaults to default branch)
            depth: Shallow clone depth (None for full clone)
            target_dir: Target directory for cloning
            
        Returns:
            str: Path to cloned repository
            
        Raises:
            GitRepositoryError: If cloning fails
        """
        if not self.validate_repository_url(repo_url):
            raise GitRepositoryError(f"Invalid repository URL: {repo_url}")
        
        try:
            # Generate unique directory name
            repo_name = self._extract_repo_name(repo_url)
            if target_dir is None:
                target_dir = os.path.join(self.temp_dir, f"analysis_{repo_name}")
            
            # Remove existing directory if it exists
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            clone_kwargs = {
                'to_path': target_dir,
                'branch': branch if branch else None,
                'depth': depth if depth else None
            }
            
            # Remove None values
            clone_kwargs = {k: v for k, v in clone_kwargs.items() if v is not None}
            
            logger.info(f"Cloning repository {repo_url} to {target_dir}")
            repo = Repo.clone_from(repo_url, **clone_kwargs)
            
            # Store cloned repository path
            self.cloned_repos[repo_url] = target_dir
            
            logger.info(f"Successfully cloned repository to {target_dir}")
            return target_dir
            
        except GitCommandError as e:
            raise GitRepositoryError(f"Failed to clone repository: {e}")
        except Exception as e:
            raise GitRepositoryError(f"Unexpected error during cloning: {e}")
    
    def get_repository_info(self, repo_path: str) -> Dict[str, any]:
        """
        Get information about a Git repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dict containing repository information
            
        Raises:
            GitRepositoryError: If repository is invalid
        """
        try:
            repo = Repo(repo_path)
            
            # Get basic repository info
            info = {
                'path': repo_path,
                'active_branch': repo.active_branch.name,
                'remote_url': None,
                'commit_count': 0,
                'last_commit': None,
                'branches': [],
                'tags': [],
                'is_dirty': repo.is_dirty(),
                'untracked_files': repo.untracked_files
            }
            
            # Get remote URL
            if repo.remotes:
                info['remote_url'] = repo.remotes.origin.url
            
            # Get commit information
            commits = list(repo.iter_commits())
            info['commit_count'] = len(commits)
            
            if commits:
                last_commit = commits[0]
                info['last_commit'] = {
                    'sha': last_commit.hexsha,
                    'message': last_commit.message.strip(),
                    'author': str(last_commit.author),
                    'date': last_commit.committed_datetime.isoformat()
                }
            
            # Get branches
            info['branches'] = [branch.name for branch in repo.branches]
            
            # Get tags
            info['tags'] = [tag.name for tag in repo.tags]
            
            return info
            
        except InvalidGitRepositoryError:
            raise GitRepositoryError(f"Invalid Git repository: {repo_path}")
        except Exception as e:
            raise GitRepositoryError(f"Error reading repository info: {e}")
    
    def get_file_list(
        self, 
        repo_path: str, 
        extensions: Optional[List[str]] = None
    ) -> List[Dict[str, any]]:
        """
        Get list of files in the repository with metadata.
        
        Args:
            repo_path: Path to the repository
            extensions: List of file extensions to filter (e.g., ['.py', '.js'])
            
        Returns:
            List of file information dictionaries
        """
        try:
            repo = Repo(repo_path)
            files = []
            
            # Get all tracked files
            for item in repo.tree().traverse():
                if item.type == 'blob':  # It's a file, not a directory
                    file_path = item.path
                    
                    # Filter by extensions if specified
                    if extensions:
                        file_ext = os.path.splitext(file_path)[1].lower()
                        if file_ext not in extensions:
                            continue
                    
                    # Get file stats
                    full_path = os.path.join(repo_path, file_path)
                    file_info = {
                        'path': file_path,
                        'full_path': full_path,
                        'size': item.size,
                        'extension': os.path.splitext(file_path)[1].lower(),
                        'name': os.path.basename(file_path),
                        'directory': os.path.dirname(file_path)
                    }
                    
                    # Get file modification info from Git
                    try:
                        commits = list(repo.iter_commits(paths=file_path, max_count=1))
                        if commits:
                            last_commit = commits[0]
                            file_info.update({
                                'last_modified': last_commit.committed_datetime.isoformat(),
                                'last_author': str(last_commit.author),
                                'last_commit_sha': last_commit.hexsha
                            })
                    except Exception as e:
                        logger.warning(f"Could not get commit info for {file_path}: {e}")
                    
                    files.append(file_info)
            
            return files
            
        except Exception as e:
            raise GitRepositoryError(f"Error listing repository files: {e}")
    
    def get_file_content(self, repo_path: str, file_path: str) -> str:
        """
        Get content of a specific file from the repository.
        
        Args:
            repo_path: Path to the repository
            file_path: Relative path to the file within the repository
            
        Returns:
            str: File content
            
        Raises:
            GitRepositoryError: If file cannot be read
        """
        try:
            full_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_path):
                raise GitRepositoryError(f"File not found: {file_path}")
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
                
        except Exception as e:
            raise GitRepositoryError(f"Error reading file {file_path}: {e}")
    
    def cleanup_repository(self, repo_url: str) -> bool:
        """
        Clean up cloned repository directory.
        
        Args:
            repo_url: Repository URL to clean up
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        if repo_url in self.cloned_repos:
            try:
                repo_path = self.cloned_repos[repo_url]
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up repository at {repo_path}")
                
                del self.cloned_repos[repo_url]
                return True
                
            except Exception as e:
                logger.error(f"Error cleaning up repository: {e}")
                return False
        
        return True
    
    def cleanup_all(self) -> None:
        """Clean up all cloned repositories."""
        for repo_url in list(self.cloned_repos.keys()):
            self.cleanup_repository(repo_url)
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        
        # Remove .git extension if present
        if path.endswith('.git'):
            path = path[:-4]
        
        # Get the last part of the path (repository name)
        return path.split('/')[-1] if '/' in path else path


def get_repository_statistics(repo_path: str) -> Dict[str, any]:
    """
    Get comprehensive statistics about a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dict containing repository statistics
    """
    try:
        repo = Repo(repo_path)
        stats = {
            'total_commits': 0,
            'total_files': 0,
            'total_size_bytes': 0,
            'languages': {},
            'contributors': {},
            'commit_activity': {},
            'file_types': {}
        }
        
        # Count commits
        commits = list(repo.iter_commits())
        stats['total_commits'] = len(commits)
        
        # Analyze files
        for item in repo.tree().traverse():
            if item.type == 'blob':
                stats['total_files'] += 1
                stats['total_size_bytes'] += item.size
                
                # Count file types
                ext = os.path.splitext(item.path)[1].lower()
                stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
        
        # Analyze contributors
        for commit in commits:
            author = str(commit.author)
            stats['contributors'][author] = stats['contributors'].get(author, 0) + 1
        
        # Analyze commit activity by month
        for commit in commits:
            month_key = commit.committed_datetime.strftime('%Y-%m')
            stats['commit_activity'][month_key] = stats['commit_activity'].get(month_key, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating repository statistics: {e}")
        return {}