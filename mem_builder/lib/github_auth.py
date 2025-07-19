import jwt
import time
import requests
import os
from typing import Optional
from lib.logger import get_logger


def get_github_app_token(
    app_id: str,
    private_key_path: str = "mem.pem",
    installation_id: Optional[str] = None,
    repo_url: Optional[str] = None
) -> str:
    """
    Generate a GitHub App installation access token from private key.
    
    Args:
        app_id: GitHub App ID
        private_key_path: Path to the private key PEM file
        installation_id: Installation ID (if None, will auto-detect)
        repo_url: Repository URL to find the right installation
    
    Returns:
        Installation access token for git operations
    """
    logger = get_logger("github_auth")
    
    # Read the private key
    with open(private_key_path, 'rb') as key_file:
        private_key = key_file.read()
    
    # Create JWT payload
    now = int(time.time())
    payload = {
        'iat': now - 60,  # Issued at time (1 minute ago to account for clock skew)
        'exp': now + 600,  # Expires in 10 minutes
        'iss': app_id  # Issuer (GitHub App ID)
    }
    
    # Create JWT token
    jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
    
    # Get installation ID if not provided
    if not installation_id:
        if repo_url:
            installation_id = get_installation_for_repo(jwt_token, repo_url)
        else:
            installation_id = get_first_installation_id(jwt_token)
    
    # Get installation access token
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.post(
        f'https://api.github.com/app/installations/{installation_id}/access_tokens',
        headers=headers
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to get access token: {response.status_code} {response.text}")
    
    token = response.json()['token']
    logger.debug(f"Successfully generated installation token for installation {installation_id}")
    
    return token


def get_installation_for_repo(jwt_token: str, repo_url: str) -> str:
    """Get installation ID for a specific repository."""
    # Extract owner/repo from URL
    import re
    match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
    if not match:
        raise Exception(f"Could not parse repository from URL: {repo_url}")
    
    owner, repo = match.groups()
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Try to get installation for this specific repo
    response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/installation', headers=headers)
    
    if response.status_code == 200:
        return str(response.json()['id'])
    elif response.status_code == 404:
        raise Exception(f"GitHub App is not installed on {owner}/{repo} or repository doesn't exist")
    else:
        raise Exception(f"Failed to get installation for repo: {response.status_code} {response.text}")


def get_first_installation_id(jwt_token: str) -> str:
    """Get the first installation ID for the GitHub App."""
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get('https://api.github.com/app/installations', headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get installations: {response.status_code} {response.text}")
    
    installations = response.json()
    if not installations:
        raise Exception("No installations found for this GitHub App")
    
    return str(installations[0]['id'])