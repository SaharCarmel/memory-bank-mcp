import os
from daytona import Daytona, CreateSandboxBaseParams, Sandbox
from lib.config import get_daytona_config
from lib.logger import get_logger


class SandboxManager:
    """Manages Daytona sandbox lifecycle and operations with auto-cleanup."""
    
    def __init__(self, auto_stop_minutes=15, auto_archive_days=1, auto_delete_days=2, custom_docs_folder=None):
        self.config = get_daytona_config()
        self.daytona = Daytona(self.config)
        self.sandbox: Sandbox = None
        self.logger = get_logger("sandbox_manager")
        self.custom_docs_folder = custom_docs_folder
        
        # Configure auto-cleanup intervals (convert to minutes for Daytona API)
        self.auto_stop_interval = auto_stop_minutes  # Minutes of inactivity before auto-stop
        self.auto_archive_interval = auto_archive_days * 24 * 60  # Days to minutes
        self.auto_delete_interval = auto_delete_days * 24 * 60  # Days to minutes
    
    def create_sandbox(self):
        """Create a new Daytona sandbox with environment variables."""
        # Prepare environment variables for the sandbox
        env_vars = {}
        
        # Add Anthropic API key if available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            env_vars["ANTHROPIC_API_KEY"] = anthropic_key
            self.logger.info("Adding ANTHROPIC_API_KEY to sandbox environment")
        
        # Add OpenAI API key if available (for embeddings)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            env_vars["OPENAI_API_KEY"] = openai_key
            self.logger.info("Adding OPENAI_API_KEY to sandbox environment")
        
        # Add Turbopuffer API key if available
        turbopuffer_key = os.getenv("TURBOPUFFER_API_KEY")
        if turbopuffer_key:
            env_vars["TURBOPUFFER_API_KEY"] = turbopuffer_key
            self.logger.info("Adding TURBOPUFFER_API_KEY to sandbox environment")
        
        # Add custom docs folder name if provided
        if self.custom_docs_folder:
            env_vars["MEMBANK_DOCS_FOLDER"] = self.custom_docs_folder
            self.logger.info(f"Adding custom docs folder to sandbox environment: {self.custom_docs_folder}")
        
        # Create sandbox with environment variables and auto-cleanup configuration
        params = CreateSandboxBaseParams(
            language="python",
            env_vars=env_vars,
            auto_stop_interval=self.auto_stop_interval,
            auto_archive_interval=self.auto_archive_interval,
            auto_delete_interval=self.auto_delete_interval
        )
        
        self.sandbox = self.daytona.create(params)
        self.logger.info(f"Sandbox created with auto-cleanup: stop={self.auto_stop_interval}min, "
                        f"archive={self.auto_archive_interval//1440}days, "
                        f"delete={self.auto_delete_interval//1440}days")
        
        return self.sandbox
    
    def install_tools(self):
        """Install required tools in the sandbox."""
        if not self.sandbox:
            raise RuntimeError("Sandbox not created yet")
        
        # Install Claude Code globally
        self.sandbox.process.exec("npm install -g @anthropic-ai/claude-code")
        self.logger.info("Claude Code installed in sandbox")
        
        # Create isolated Python packages directory
        self.sandbox.process.exec("mkdir -p ~/.membank-packages")
        self.logger.info("Created isolated packages directory: ~/.membank-packages")
        
        # Create custom requirements.txt for isolated packages using fs.upload_file
        requirements_content = """# MemBank custom packages - isolated from project dependencies
claude-code-sdk
"""
        self.sandbox.fs.upload_file(
            requirements_content.encode('utf-8'), 
            "~/.membank-packages/requirements.txt"
        )
        self.logger.info("Created custom requirements.txt in ~/.membank-packages")
        
        # Install packages from custom requirements file with user-level isolation
        self.sandbox.process.exec("pip install --user -r ~/.membank-packages/requirements.txt")
        self.logger.info("Installed custom packages: claude-code-sdk")
        
        # Verify installation
        try:
            result = self.sandbox.process.exec("python -c 'import claude_code_sdk; print(f\"claude-code-sdk version: {claude_code_sdk.__version__}\")'")
            output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
            self.logger.info(f"Package verification successful: {output.strip()}")
        except Exception as e:
            self.logger.warning(f"Package verification failed: {e}")
            # Try alternative verification
            try:
                result = self.sandbox.process.exec("pip list | grep claude-code-sdk")
                output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
                if output and output.strip():
                    self.logger.info(f"Package found in pip list: {output.strip()}")
                else:
                    self.logger.warning("claude-code-sdk not found in pip list")
            except Exception as e2:
                self.logger.error(f"Both verification methods failed: {e2}")
    
    def cleanup(self, force_delete=False):
        """Clean up sandbox resources."""
        if self.sandbox:
            try:
                if force_delete:
                    self.sandbox.delete()
                    self.logger.info("Sandbox deleted immediately")
                else:
                    self.sandbox.stop()
                    self.logger.info("Sandbox stopped (will auto-archive/delete per configuration)")
            except Exception as e:
                self.logger.error(f"Error cleaning up sandbox: {e}")
    
    def delete_sandbox(self):
        """Immediately delete the sandbox (bypassing auto-cleanup timers)."""
        if self.sandbox:
            try:
                self.sandbox.delete()
                self.logger.info("Sandbox deleted immediately")
                self.sandbox = None
            except Exception as e:
                self.logger.error(f"Error deleting sandbox: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.create_sandbox()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup(force_delete=True)
        return False  # Don't suppress exceptions
