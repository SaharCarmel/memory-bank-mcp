import os
from lib.github_auth import get_github_app_token
from lib.git_utils import validate_and_normalize_git_url
from lib.consts import WORKING_REPO
from lib.logger import get_logger
from lib.turbopuffer_manager import TurbopufferManager


class RepoManager:
    """Handles repository cloning and Git operations."""
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.logger = get_logger("repo_manager")
        
    def setup_auth(self, repo_url: str) -> str:
        """Setup GitHub authentication and return token."""
        app_id = os.getenv("GITHUB_APP_ID")
        installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        
        if app_id:
            self.logger.info(f"Using GitHub App {app_id} for authentication...")
            github_token = get_github_app_token(app_id, "mem.pem", installation_id, repo_url)
            self.logger.debug(f"Generated token: {github_token[:10]}...")
        else:
            github_token = os.getenv("GITHUB_TOKEN")
            self.logger.info("Using manual GITHUB_TOKEN...")
        
        if not github_token:
            raise ValueError("No GitHub authentication token available")
            
        return github_token
    
    def clone_repository(self, repo_url: str) -> tuple[str, str]:
        """
        Clone repository and return project directory and token.
        
        Returns:
            tuple: (project_dir, github_token)
        """
        # Validate and normalize URL
        repo_url = validate_and_normalize_git_url(repo_url)
        
        # Setup authentication
        github_token = self.setup_auth(repo_url)
        
        # Get project directory
        root_dir = self.sandbox.get_user_root_dir()
        project_dir = os.path.join(root_dir, WORKING_REPO)
        
        # Try cloning with main branch first, fallback to master
        try:
            self.sandbox.git.clone(
                url=repo_url,
                path=project_dir,
                branch="main",
                username="git",
                password=github_token
            )
        except Exception:
            self.sandbox.git.clone(
                url=repo_url,
                path=project_dir,
                branch="master",
                username="git",
                password=github_token
            )
        
        # Pull latest changes
        self.sandbox.git.pull(project_dir, username="git", password=github_token)
        
        return project_dir, github_token
    
    def setup_docs_environment(self, project_dir: str, commit_hash: str, repo_url: str, custom_docs_dir: str = None) -> str:
        """
        Set up a complete documentation environment with custom docs folder, diff generation, and namespace downloads.
        
        This function creates a comprehensive docs environment by:
        1. Creating a custom docs folder with unique name (from env var or timestamp)
        2. Generating git diff as one component
        3. Downloading all files from the Turbopuffer namespace
        4. Preparing the environment for download and upload
        
        Args:
            project_dir: Project directory path
            commit_hash: Commit hash to diff from
            repo_url: Repository URL for namespace operations
            custom_docs_dir: Custom folder path (if None, generates timestamp-based name)
        
        Returns:
            custom_docs_dir: Path to the custom docs directory
        """
        # Create the custom docs directory
        self.sandbox.process.exec(f"mkdir -p {custom_docs_dir}")

        # Generate diff file in the project root (where memory_bank_core expects it)
        diff_file_path = os.path.join(project_dir, "git.diff")
        diff_command = f"cd {project_dir} && git diff {commit_hash} HEAD > {diff_file_path}"
        
        result = self.sandbox.process.exec(diff_command)
        if result.exit_code != 0:
            self.logger.error(f"Git diff command failed: {result.result}")
            raise RuntimeError(f"Failed to generate diff: {result.result}")
        
        # Check if diff file was created
        check_result = self.sandbox.process.exec(f"test -f {diff_file_path} && echo 'exists'")
        if "exists" not in check_result.result:
            raise RuntimeError(f"Diff file was not created at {diff_file_path}")
        
        # Download all files from Turbopuffer namespace and upload to sandbox
        try:
            turbopuffer_manager = TurbopufferManager()
            namespace_dir = os.path.join(custom_docs_dir, "namespace_files")
            
            # Check if namespace exists before trying to download
            if turbopuffer_manager.namespace_exists(repo_url):
                self.logger.info("Downloading files from Turbopuffer namespace and uploading to sandbox...")
                success = turbopuffer_manager.download_all_files_to_sandbox(repo_url, self.sandbox, namespace_dir)
                
                if success:
                    self.logger.info(f"Successfully uploaded namespace files to sandbox: {namespace_dir}")
                else:
                    self.logger.warning("No files downloaded from namespace (namespace may be empty)")
            else:
                self.logger.info("Namespace does not exist yet - skipping download (will be created during upload)")
                
        except ValueError as e:
            self.logger.warning(f"Turbopuffer download skipped: {e}")
        except Exception as e:
            self.logger.error(f"Error downloading from Turbopuffer namespace: {e}")
        
        self.logger.info(f"Docs environment set up successfully: {custom_docs_dir}")
        self.logger.info(f"Documentation components created:")
        self.logger.info(f"  - Git diff: {diff_file_path}")
        self.logger.info(f"  - Namespace files: {os.path.join(custom_docs_dir, 'namespace_files')}")
        
        return custom_docs_dir
