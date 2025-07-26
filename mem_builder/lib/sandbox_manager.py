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
    
    def copy_memory_bank_core(self):
        """Copy memory_bank_core directory to sandbox."""
        if not self.sandbox:
            raise RuntimeError("Sandbox not created yet")
        
        import os
        import tarfile
        import tempfile
        
        # Get the memory_bank_core path relative to this file
        current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up two levels from lib/
        memory_bank_core_path = os.path.join(current_dir, "..", "memory_bank_core")
        memory_bank_core_path = os.path.abspath(memory_bank_core_path)
        
        if not os.path.exists(memory_bank_core_path):
            raise FileNotFoundError(f"memory_bank_core directory not found at {memory_bank_core_path}")
        
        # Create a tar archive of memory_bank_core
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_tar:
            with tarfile.open(temp_tar.name, 'w:gz') as tar:
                tar.add(memory_bank_core_path, arcname='memory_bank_core')
            
            # Upload and extract to sandbox
            user_root = self.sandbox.get_user_root_dir()
            target_path = f"{user_root}/memory_bank_core.tar.gz"
            
            with open(temp_tar.name, 'rb') as f:
                self.sandbox.fs.upload_file(f.read(), target_path)
            
            # Extract the archive
            self.sandbox.process.exec(f"cd {user_root} && tar -xzf memory_bank_core.tar.gz")
            self.sandbox.process.exec(f"rm {user_root}/memory_bank_core.tar.gz")
            
            self.logger.info(f"memory_bank_core copied to {user_root}/memory_bank_core")
            
            # Install memory_bank_core dependencies
            self.sandbox.process.exec(f"cd {user_root}/memory_bank_core && pip install -e .")
            self.logger.info("memory_bank_core dependencies installed")
            
            # Copy system_prompt.md to user root
            current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up two levels from lib/
            system_prompt_path = os.path.join(current_dir, "..", "system_prompt.md")
            system_prompt_path = os.path.abspath(system_prompt_path)
            
            if os.path.exists(system_prompt_path):
                with open(system_prompt_path, 'r') as f:
                    system_prompt_content = f.read()
                
                self.sandbox.fs.upload_file(
                    system_prompt_content.encode('utf-8'),
                    f"{user_root}/system_prompt.md"
                )
                self.logger.info("system_prompt.md copied to sandbox")
            else:
                self.logger.warning(f"system_prompt.md not found at {system_prompt_path}")
            
            # Clean up temp file
            os.unlink(temp_tar.name)
    
    def run_memory_bank_core(self, project_dir, memory_bank_output_dir, docs_folder_name, stream_output=True):
        """Run memory_bank_core CLI with appropriate build/update command in the sandbox."""
        if not self.sandbox:
            raise RuntimeError("Sandbox not created yet")
        
        user_root = self.sandbox.get_user_root_dir()
        memory_bank_core_path = f"{user_root}/memory_bank_core"
        
        # Memory bank name will be determined based on output directory logic below
        self.logger.info(f"Docs folder name: {docs_folder_name}")
        
        # Validate project directory exists in sandbox
        project_exists_cmd = f"[ -d '{project_dir}' ] && echo 'exists' || echo 'not_exists'"
        result = self.sandbox.process.exec(project_exists_cmd)
        output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
        if 'not_exists' in output.lower():
            raise RuntimeError(f"Project directory does not exist in sandbox: {project_dir}")
        
        # Check if memory bank already exists to decide between build/update
        # Memory bank directory structure: {memory_bank_name}/memory-bank/
        existing_memory_bank_path = f"{user_root}/{memory_bank_name}"
        memory_bank_exists = False
        
        # Use more robust check: directory must exist AND be readable
        # Also check for memory-bank subdirectory to ensure it's a valid memory bank
        robust_check_cmd = f"[ -d '{existing_memory_bank_path}' ] && [ -r '{existing_memory_bank_path}' ] && ls '{existing_memory_bank_path}' >/dev/null 2>&1 && echo 'exists' || echo 'not_exists'"
        result = self.sandbox.process.exec(robust_check_cmd)
        output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
        memory_bank_exists = 'exists' in output.lower()
        
        # Additional check: if directory exists, verify it has memory bank content
        if memory_bank_exists:
            # Check if it looks like a proper memory bank (has memory-bank subdirectory or md files)
            content_check_cmd = f"[ -d '{existing_memory_bank_path}/memory-bank' ] || [ -f '{existing_memory_bank_path}'/*.md ] 2>/dev/null && echo 'valid_membank' || echo 'empty_dir'"
            content_result = self.sandbox.process.exec(content_check_cmd)
            content_output = getattr(content_result, 'stdout', getattr(content_result, 'result', str(content_result)))
            
            if 'empty_dir' in content_output.lower():
                self.logger.info(f"Directory exists but appears empty, treating as new build")
                memory_bank_exists = False
            else:
                # Debug: list what's actually in the directory
                debug_cmd = f"ls -la '{existing_memory_bank_path}/' 2>/dev/null | head -10"
                debug_result = self.sandbox.process.exec(debug_cmd)
                debug_output = getattr(debug_result, 'stdout', getattr(debug_result, 'result', str(debug_result)))
                self.logger.info(f"Directory contents: {debug_output.strip()}")
        
        self.logger.info(f"Memory bank exists check: {memory_bank_exists} at {existing_memory_bank_path}")
        
        # Set the root path to the specified output directory if provided, otherwise use user_root
        if memory_bank_output_dir:
            # Ensure the output directory exists
            self.sandbox.process.exec(f"mkdir -p '{memory_bank_output_dir}'")
            # Use parent directory as root_path to avoid duplication
            import os
            root_path = os.path.dirname(memory_bank_output_dir)
            # Use basename of output dir as memory bank name to avoid duplication
            memory_bank_name = os.path.basename(memory_bank_output_dir)
        else:
            root_path = user_root
            # Use the docs_folder_name as the memory bank name for default case
            memory_bank_name = docs_folder_name
        
        self.logger.info(f"Using memory bank name: {memory_bank_name}")
        
        # Build the appropriate command
        # Set PYTHONPATH to include the parent directory so memory_bank_core can be imported
        # Note: --root-path and --verbose are group-level options and must come before the subcommand
        pythonpath_cmd = f"cd {user_root} && PYTHONPATH='{user_root}' python -m memory_bank_core.main --root-path '{root_path}' --verbose"
        
        if memory_bank_exists:
            # Update existing memory bank
            command = f"{pythonpath_cmd} update '{project_dir}' '{memory_bank_name}'"
            self.logger.info(f"Running UPDATE command for existing memory bank: {memory_bank_name}")
        else:
            # Build new memory bank
            command = f"{pythonpath_cmd} build '{project_dir}' --output-name '{memory_bank_name}'"
            self.logger.info(f"Running BUILD command for new memory bank: {memory_bank_name}")
        
        self.logger.info(f"Executing command: {command}")
        self.logger.info(f"Root path: {root_path}")
        self.logger.info(f"Project directory: {project_dir}")
        self.logger.info(f"Memory bank name: {memory_bank_name}")
        
        if stream_output:
            return self._run_with_streaming(command)
        else:
            # Fallback to original method
            result = self.sandbox.process.exec(command, timeout=900) # 15 minutes
            output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
            self.logger.info(f"memory_bank_core execution output: {output}")
            return output
    
    def _run_with_streaming(self, command):
        """Run command with real-time stdout streaming."""
        import uuid
        import time
        
        # Generate unique session ID
        session_id = f"membank-session-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create session
            self.sandbox.process.create_session(session_id)
            self.logger.info(f"Created streaming session: {session_id}")
            
            # Execute command asynchronously
            cmd_result = self.sandbox.process.execute_session_command(
                session_id, 
                {"command": command, "async": True},
                timeout=900 # 15 minutes
            )
            
            if hasattr(cmd_result, 'cmd_id'):
                cmd_id = cmd_result.cmd_id
            else:
                cmd_id = getattr(cmd_result, 'cmdId', None)
            
            if not cmd_id:
                self.logger.error("Failed to get command ID for streaming")
                raise RuntimeError("Could not obtain command ID for streaming")
            
            self.logger.info(f"Started memory_bank_core execution with streaming (cmd_id: {cmd_id})")
            
            # Stream logs by polling
            full_output = []
            
            # Poll for logs in a loop with improved streaming
            import time
            max_retries = 600  # 10 minutes with 1-second intervals
            retries = 0
            last_output_length = 0
            consecutive_empty_polls = 0
            
            while retries < max_retries:
                try:
                    # Get current logs
                    logs_result = self.sandbox.process.get_session_command_logs(session_id, cmd_id)
                    
                    if logs_result:
                        # Handle different response formats
                        if hasattr(logs_result, 'logs'):
                            log_content = logs_result.logs
                        elif hasattr(logs_result, 'stdout'):
                            log_content = logs_result.stdout
                        else:
                            log_content = str(logs_result)
                        
                        if log_content:
                            # Clean and process new content
                            clean_content = log_content.replace('\x00', '').replace('\r', '')
                            current_length = len(clean_content)
                            
                            # If we have new content since last poll
                            if current_length > last_output_length:
                                new_content = clean_content[last_output_length:]
                                
                                # Log each line separately for better streaming visibility
                                for line in new_content.split('\n'):
                                    if line.strip():
                                        # Use different prefixes for different types of output
                                        if '[BUILD_PROGRESS]' in line or '[UPDATE_PROGRESS]' in line:
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif '[TURN' in line:  # Capture our new turn-based logging
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif '[ATTEMPT' in line:  # Capture restart attempt logs
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif '[TERMINATION]' in line:  # Capture termination analysis
                                            self.logger.warning(f"[STREAM] {line.strip()}")
                                        elif '[WARNING]' in line:  # Capture warnings about limits
                                            self.logger.warning(f"[STREAM] {line.strip()}")
                                        elif '[RESTART]' in line:  # Capture restart messages
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif '[SUCCESS]' in line:  # Capture success messages
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif '[DEBUG]' in line:  # Capture debug information
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif 'LEGACY_' in line:
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif 'ERROR:' in line or 'Exception:' in line:
                                            self.logger.error(f"[STREAM] {line.strip()}")
                                        elif '✅' in line or '❌' in line or '🚀' in line or '📁' in line:  # Capture emoji status messages
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        elif line.strip().startswith('Claude:') or 'Creating file:' in line or 'Reading:' in line:
                                            self.logger.info(f"[STREAM] {line.strip()}")
                                        else:
                                            # Still log other lines but with less priority
                                            self.logger.debug(f"[STREAM] {line.strip()}")
                                
                                last_output_length = current_length
                                consecutive_empty_polls = 0
                                full_output = [clean_content]
                            else:
                                consecutive_empty_polls += 1
                        else:
                            consecutive_empty_polls += 1
                    else:
                        consecutive_empty_polls += 1
                    
                    # Check if command is still running
                    try:
                        cmd_status = self.sandbox.process.get_session_command_status(session_id, cmd_id)
                        if hasattr(cmd_status, 'finished') and cmd_status.finished:
                            self.logger.info("[STREAM] Command execution finished")
                            break
                        elif hasattr(cmd_status, 'status') and cmd_status.status in ['completed', 'failed', 'finished']:
                            self.logger.info(f"[STREAM] Command status: {cmd_status.status}")
                            break
                    except Exception:
                        # If we can't get status, continue polling for a bit more
                        pass
                    
                    # Adaptive polling: faster when getting output, slower when idle
                    if consecutive_empty_polls < 5:
                        time.sleep(1)  # Fast polling when active
                    elif consecutive_empty_polls < 30:
                        time.sleep(5)    # Normal polling
                    else:
                        time.sleep(10)    # Slow polling when idle
                    
                    retries += 1
                    
                    # Log progress every minute for long-running operations
                    if retries % 60 == 0:
                        self.logger.info(f"[STREAM] Still running... ({retries//60} minutes elapsed)")
                    
                except Exception as log_error:
                    self.logger.warning(f"Error polling logs (attempt {retries}): {log_error}")
                    time.sleep(2)
                    retries += 1
            
            return ''.join(full_output)
            
        except Exception as e:
            self.logger.error(f"Error during streaming execution: {e}")
            # Fallback to non-streaming execution
            self.logger.info("Falling back to non-streaming execution")
            result = self.sandbox.process.exec(command)
            output = getattr(result, 'stdout', getattr(result, 'result', str(result)))
            self.logger.info(f"memory_bank_core execution output: {output}")
            return output
        
        finally:
            # Clean up session if it was created
            try:
                self.sandbox.process.delete_session(session_id)
                self.logger.info(f"Cleaned up session: {session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up session {session_id}: {e}")
    
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
        self.cleanup(force_delete=True) # TODO: change to False for inspection
        return False  # Don't suppress exceptions
