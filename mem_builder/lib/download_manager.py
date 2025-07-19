import os
from datetime import datetime
from typing import List
from lib.git_utils import extract_repo_name
from lib.logger import get_logger
from daytona import Sandbox


class DownloadManager:
    """Handles file downloads from sandbox to local storage."""
    
    def __init__(self, sandbox):
        self.sandbox: Sandbox = sandbox
        self.logger = get_logger("download_manager")
        
    def create_local_directories(self, repo_url: str) -> str:
        """Create timestamped local directories for downloads."""
        repo_name = extract_repo_name(repo_url)
        local_base_dir = f"downloads/{repo_name}"
        
        os.makedirs(local_base_dir, exist_ok=True)
        
        return local_base_dir
    
    def _download_single_file(self, file_path: str, project_dir: str, local_docs_dir: str) -> None:
        """Download a single file maintaining directory structure within docs folder."""
        # Create relative path for local storage
        rel_path = os.path.relpath(file_path, project_dir)
        local_file_path = os.path.join(local_docs_dir, rel_path)
        
        # Create local directory structure
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        
        # Download and save file
        file_data = self.sandbox.fs.download_file(file_path)
        with open(local_file_path, "wb") as f:
            f.write(file_data)
    
    def download_all_files(self, repo_url: str, project_dir: str, custom_docs_dir: str = None) -> str:
        """
        Download custom docs directory and organize into namespace and docs subfolders.
        
        Args:
            repo_url: Repository URL for naming
            project_dir: Project directory path
            custom_docs_dir: Path to the custom docs directory to download
        
        Returns:
            Path to local docs directory for upload to turbopuffer
        """
        local_base_dir = self.create_local_directories(repo_url)
        
        if custom_docs_dir:
            # Use the custom docs folder name as the local directory name
            custom_docs_folder_name = os.path.basename(custom_docs_dir)
            local_custom_docs_dir = os.path.join(local_base_dir, custom_docs_folder_name)
            
            # Create organized subfolders
            local_namespace_dir = os.path.join(local_custom_docs_dir, "namespace")
            local_docs_dir = os.path.join(local_custom_docs_dir, "docs")
            
            os.makedirs(local_namespace_dir, exist_ok=True)
            os.makedirs(local_docs_dir, exist_ok=True)
            
            # Download and organize the custom docs directory
            docs_count = self.download_and_organize_custom_docs(
                custom_docs_dir, project_dir, local_namespace_dir, local_docs_dir
            )
            self.logger.info(f"Downloaded {docs_count} files and organized into namespace and docs folders")
            
            return local_docs_dir  # Return docs folder for upload to turbopuffer
        else:
            self.logger.warning("No custom docs directory provided, nothing to download")
            return local_base_dir
    
    def download_custom_docs_directory(self, custom_docs_dir: str, project_dir: str, local_docs_dir: str) -> int:
        """
        Download all files from the custom docs directory.
        
        Args:
            custom_docs_dir: Path to the custom docs directory
            project_dir: Project directory path for relative path calculation
            local_docs_dir: Local docs directory for downloads
        
        Returns:
            Number of files downloaded
        """
        # Check if custom docs directory exists
        docs_exists_result = self.sandbox.process.exec(
            f"test -d {custom_docs_dir} && echo 'exists' || echo 'not_exists'"
        )
        
        if "exists" not in docs_exists_result.result:
            self.logger.error(f"Custom docs directory does not exist: {custom_docs_dir}")
            return 0
        
        # Get list of all files in the custom docs directory
        find_result = self.sandbox.process.exec(f"find {custom_docs_dir} -type f")
        
        if find_result.exit_code != 0:
            self.logger.error(f"Find command failed on custom docs directory: {find_result.result}")
            return 0
            
        doc_files = [f.strip() for f in find_result.result.split('\n') if f.strip()]
        
        if not doc_files:
            self.logger.warning("Custom docs directory exists but is empty")
            return 0
        
        # Download each file
        downloaded_count = 0
        for doc_file in doc_files:
            try:
                self._download_single_file(doc_file, project_dir, local_docs_dir)
                downloaded_count += 1
                self.logger.debug(f"Downloaded: {os.path.relpath(doc_file, project_dir)}")
            except Exception as e:
                self.logger.error(f"Error downloading file {doc_file}: {e}")
                continue
        
        custom_docs_name = os.path.basename(custom_docs_dir)
        self.logger.info(f"Downloaded {downloaded_count} files from custom docs '{custom_docs_name}' to custom docs folder")
        return downloaded_count
    
    def download_and_organize_custom_docs(self, custom_docs_dir: str, project_dir: str, 
                                         local_namespace_dir: str, local_docs_dir: str) -> int:
        """
        Download and organize files from custom docs directory into namespace and docs folders.
        
        Args:
            custom_docs_dir: Path to the custom docs directory in sandbox
            project_dir: Project directory path for relative path calculation
            local_namespace_dir: Local directory for namespace files (old docs from turbopuffer)
            local_docs_dir: Local directory for new docs (to upload to turbopuffer)
        
        Returns:
            Total number of files downloaded
        """
        # Check if custom docs directory exists
        docs_exists_result = self.sandbox.process.exec(
            f"test -d {custom_docs_dir} && echo 'exists' || echo 'not_exists'"
        )
        
        if "exists" not in docs_exists_result.result:
            self.logger.error(f"Custom docs directory does not exist: {custom_docs_dir}")
            return 0
        
        # Get list of all files in the custom docs directory
        find_result = self.sandbox.process.exec(f"find {custom_docs_dir} -type f")
        
        if find_result.exit_code != 0:
            self.logger.error(f"Find command failed on custom docs directory: {find_result.result}")
            return 0
            
        doc_files = [f.strip() for f in find_result.result.split('\n') if f.strip()]
        
        if not doc_files:
            self.logger.warning("Custom docs directory exists but is empty")
            return 0
        
        # Download and organize each file
        downloaded_count = 0
        for doc_file in doc_files:
            try:
                # Determine which folder this file should go to
                rel_path = os.path.relpath(doc_file, custom_docs_dir)
                
                if rel_path.startswith("namespace_files/"):
                    # This is a namespace file (old docs from turbopuffer)
                    # Remove the namespace_files/ prefix and put in namespace folder
                    namespace_rel_path = rel_path[len("namespace_files/"):]
                    local_file_path = os.path.join(local_namespace_dir, namespace_rel_path)
                    target_dir = "namespace"
                else:
                    # This is a new doc file (like git.diff)
                    local_file_path = os.path.join(local_docs_dir, rel_path)
                    target_dir = "docs"
                
                # Create directory structure
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download and save file
                file_data = self.sandbox.fs.download_file(doc_file)
                with open(local_file_path, "wb") as f:
                    f.write(file_data)
                
                downloaded_count += 1
                self.logger.debug(f"Downloaded {rel_path} to {target_dir} folder")
                
            except Exception as e:
                self.logger.error(f"Error downloading file {doc_file}: {e}")
                continue
        
        custom_docs_name = os.path.basename(custom_docs_dir)
        self.logger.info(f"Organized {downloaded_count} files from '{custom_docs_name}' into namespace and docs folders")
        return downloaded_count
