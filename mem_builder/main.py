import os
import click
from dotenv import load_dotenv
from lib.sandbox_manager import SandboxManager
from lib.repo_manager import RepoManager
from lib.download_manager import DownloadManager
from lib.turbopuffer_manager import TurbopufferManager
from lib.logger import setup_logger


@click.command()
@click.option("--repo", default="https://github.com/uriafranko/circle-chat-agents", help="Repository URL to clone")
@click.option("--commit-hash", default="2b71929f3a96968eff69e05a973519f580ae27b3", help="Specific commit hash to process")
def main(repo, commit_hash):
    """Main function to clone repository, generate diff, and download files."""
    # Setup logger
    logger = setup_logger()
    
    # Load environment variables
    load_dotenv()
    
    # Generate unique docs folder name if commit is provided
    custom_docs_folder = None
    if commit_hash:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_docs_folder = f"membank_docs_{timestamp}"
    
    # Use context manager for sandbox lifecycle
    with SandboxManager(custom_docs_folder=custom_docs_folder) as sandbox_manager:
        try:
            sandbox = sandbox_manager.sandbox
            
            # Initialize managers
            repo_manager = RepoManager(sandbox)
            download_manager = DownloadManager(sandbox)
            
            # Clone repository
            logger.info(f"Cloning repository: {repo}")
            project_dir, github_token = repo_manager.clone_repository(repo)
            logger.info("Repository cloned successfully")
            
            # Install tools
            sandbox_manager.install_tools()

            # Set up docs environment if commit provided
            
            # Use provided name, environment variable, or generate timestamp-based name
            custom_docs_dir = os.getenv("MEMBANK_DOCS_FOLDER")
            if not custom_docs_dir:
                # Fallback to timestamp-based name
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                custom_docs_dir = f"membank_docs_{timestamp}"

            custom_docs_dir = os.path.join(project_dir, custom_docs_dir)

            if commit_hash:
                logger.info(f"Setting up docs environment for commit {commit_hash}")
                repo_manager.setup_docs_environment(project_dir, commit_hash, repo, custom_docs_dir)
                logger.info(f"Docs environment ready: {custom_docs_dir}")

            # TODO: Add Sahar mem builder to sandbox
            # TODO: make sure to use env vars

            # Download files (only the custom docs directory)
            logger.info("Downloading custom docs directory...")
            local_docs_upload_dir = download_manager.download_all_files(
                repo, project_dir, custom_docs_dir
            )
            
            logger.info(f"Files organized and ready for upload from: {local_docs_upload_dir}")
            
            # Upload to Turbopuffer if API key is available
            try:
                turbopuffer_manager = TurbopufferManager()
                logger.info("Uploading new docs to Turbopuffer...")
                success = turbopuffer_manager.upload_files(local_docs_upload_dir, repo)
                
                if success:
                    logger.info("Successfully uploaded files to Turbopuffer")
                else:
                    logger.warning("Failed to upload files to Turbopuffer")
                    
            except ValueError as e:
                logger.warning(f"Turbopuffer upload skipped: {e}")
            except Exception as e:
                logger.error(f"Error during Turbopuffer upload: {e}")
            
            logger.info(f"All operations completed. Files saved to: {local_docs_upload_dir}")
            
        except Exception as error:
            logger.error(f"Error: {error}")
            raise


if __name__ == "__main__":
    main()
