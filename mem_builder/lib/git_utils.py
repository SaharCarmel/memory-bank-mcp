import re
from urllib.parse import urlparse


def validate_and_normalize_git_url(url: str) -> str:
    """
    Validate and normalize a Git repository URL.
    
    Args:
        url: Git repository URL (GitHub, GitLab, etc.)
        
    Returns:
        Normalized Git URL with .git suffix
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    url = url.strip()
    
    # Handle different URL formats
    if url.startswith('git@'):
        # SSH format: git@github.com:user/repo.git
        if not url.startswith('git@github.com:'):
            raise ValueError("Only GitHub repositories are supported for now")
        if not url.endswith('.git'):
            url += '.git'
        return url
    
    elif url.startswith('http://') or url.startswith('https://'):
        # HTTPS format: https://github.com/user/repo or https://github.com/user/repo.git
        parsed = urlparse(url)
        
        if not parsed.netloc:
            raise ValueError("Invalid URL: missing hostname")
        
        # Check if it's GitHub
        if parsed.netloc.lower() not in ['github.com', 'www.github.com']:
            raise ValueError("Only GitHub repositories are supported for now")
        
        if not parsed.path or parsed.path == '/':
            raise ValueError("Invalid URL: missing repository path")
        
        # Remove trailing slash and add .git if needed
        path = parsed.path.rstrip('/')
        if not path.endswith('.git'):
            path += '.git'
        
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    
    else:
        # Try to handle as GitHub shorthand: user/repo
        if re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', url):
            return f"https://github.com/{url}.git"
        
        raise ValueError(f"Unsupported URL format: {url}")


def extract_repo_name(url: str) -> str:
    """
    Extract repository name from Git URL.
    
    Args:
        url: Git repository URL
        
    Returns:
        Repository name without .git suffix
    """
    # Handle SSH format
    if url.startswith('git@'):
        # git@github.com:user/repo.git -> repo
        return url.split('/')[-1].replace('.git', '')
    
    # Handle HTTPS format
    elif url.startswith('http'):
        # https://github.com/user/repo.git -> repo
        path = urlparse(url).path
        return path.split('/')[-1].replace('.git', '')
    
    # Handle shorthand format
    else:
        # user/repo -> repo
        return url.split('/')[-1]
