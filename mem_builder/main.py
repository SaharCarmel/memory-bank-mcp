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

            # Copy memory_bank_core to sandbox
            logger.info("Copying memory_bank_core to sandbox...")
            sandbox_manager.copy_memory_bank_core()
            logger.info("memory_bank_core copied successfully")

            # Set up docs environment if commit provided
            
            # Use provided name, environment variable, or generate timestamp-based name
            docs_folder_name = os.getenv("MEMBANK_DOCS_FOLDER")
            if not docs_folder_name:
                # Fallback to timestamp-based name
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                docs_folder_name = f"membank_docs_{timestamp}"

            # Create docs directory inside the repo for processing
            custom_docs_dir = os.path.join(project_dir, docs_folder_name)
            
            # Memory bank will be created in sandbox user root, outside the repo
            sandbox_user_root = sandbox_manager.sandbox.get_user_root_dir()
            memory_bank_output_dir = os.path.join(sandbox_user_root, docs_folder_name)

            if commit_hash:
                logger.info(f"Setting up docs environment for commit {commit_hash}")
                repo_manager.setup_docs_environment(project_dir, commit_hash, repo, custom_docs_dir)
                logger.info(f"Docs environment ready: {custom_docs_dir}")

            # Run memory_bank_core CLI with appropriate arguments
            logger.info("Running memory_bank_core CLI...")
            logger.info(f"Memory bank will be created at: {memory_bank_output_dir}")
            memory_bank_output = sandbox_manager.run_memory_bank_core(
                project_dir=project_dir,
                memory_bank_output_dir=memory_bank_output_dir,
                docs_folder_name=docs_folder_name
            )
            logger.info("memory_bank_core execution completed")

            # Download files (memory bank output directory)
            logger.info("Downloading memory bank directory...")
            local_docs_upload_dir = download_manager.download_all_files(
                repo, memory_bank_output_dir, memory_bank_output_dir
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
