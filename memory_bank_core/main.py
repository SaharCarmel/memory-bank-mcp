#!/usr/bin/env python3
"""
Memory Bank Core CLI
Command-line interface for building and managing memory banks
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

import click

from .services.job_manager import JobManager
from .models.build_job import BuildJobRequest, BuildJobType, BuildJobStatus
from .integrations.legacy import LegacyScriptExecutor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--root-path', '-r', default='.', 
              help='Root path for memory banks (default: current directory)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, root_path: str, verbose: bool):
    """Memory Bank Core CLI - Build and manage memory banks from any repository"""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure the context object exists
    ctx.ensure_object(dict)
    
    # Store config in context
    ctx.obj['root_path'] = Path(root_path).resolve()
    ctx.obj['verbose'] = verbose
    
    # Create root directory if it doesn't exist
    ctx.obj['root_path'].mkdir(parents=True, exist_ok=True)
    
    if verbose:
        click.echo(f"Root path: {ctx.obj['root_path']}")


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--output-name', '-o', help='Name for the output memory bank directory')
@click.option('--wait/--no-wait', default=True, help='Wait for job completion (default: wait)')
@click.option('--legacy', is_flag=True, help='Force use of legacy bash scripts')
@click.pass_context
def build(ctx, repo_path: str, output_name: Optional[str], wait: bool, legacy: bool):
    """Build a memory bank from a repository"""
    
    root_path = ctx.obj['root_path']
    repo_path = Path(repo_path).resolve()
    
    if not repo_path.exists():
        click.echo(f"❌ Repository path does not exist: {repo_path}", err=True)
        sys.exit(1)
    
    if not repo_path.is_dir():
        click.echo(f"❌ Repository path is not a directory: {repo_path}", err=True)
        sys.exit(1)
    
    # Set legacy mode if requested
    if legacy:
        os.environ['USE_LEGACY_SCRIPTS'] = 'true'
        click.echo("🔄 Using legacy script mode")
    
    click.echo(f"🚀 Building memory bank for: {repo_path}")
    click.echo(f"📁 Output location: {root_path}")
    
    if output_name:
        click.echo(f"📝 Output name: {output_name}")
    
    # Run the build
    asyncio.run(_run_build(root_path, str(repo_path), output_name, wait))


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.argument('memory_bank_name')
@click.option('--wait/--no-wait', default=True, help='Wait for job completion (default: wait)')
@click.option('--legacy', is_flag=True, help='Force use of legacy bash scripts')
@click.pass_context
def update(ctx, repo_path: str, memory_bank_name: str, wait: bool, legacy: bool):
    """Update an existing memory bank with changes from repository"""
    
    root_path = ctx.obj['root_path']
    repo_path = Path(repo_path).resolve()
    
    if not repo_path.exists():
        click.echo(f"❌ Repository path does not exist: {repo_path}", err=True)
        sys.exit(1)
    
    # Check if memory bank exists
    memory_bank_path = root_path / memory_bank_name
    if not memory_bank_path.exists():
        click.echo(f"❌ Memory bank does not exist: {memory_bank_name}", err=True)
        click.echo(f"   Expected at: {memory_bank_path}")
        sys.exit(1)
    
    # Set legacy mode if requested
    if legacy:
        os.environ['USE_LEGACY_SCRIPTS'] = 'true'
        click.echo("🔄 Using legacy script mode")
    
    click.echo(f"🔄 Updating memory bank: {memory_bank_name}")
    click.echo(f"📁 Repository: {repo_path}")
    
    # Run the update
    asyncio.run(_run_update(root_path, str(repo_path), memory_bank_name, wait))


@cli.command()
@click.pass_context
def list(ctx):
    """List all memory banks in the root directory"""
    
    root_path = ctx.obj['root_path']
    
    click.echo(f"📂 Memory banks in: {root_path}")
    click.echo()
    
    # Find memory bank directories (those containing memory-bank subdirectory)
    memory_banks = []
    for item in root_path.iterdir():
        if item.is_dir():
            memory_bank_dir = item / "memory-bank"
            if memory_bank_dir.exists():
                memory_banks.append(item)
    
    if not memory_banks:
        click.echo("   No memory banks found")
        click.echo("   Use 'memory-bank build <repo_path>' to create one")
        return
    
    for memory_bank in sorted(memory_banks):
        memory_bank_dir = memory_bank / "memory-bank"
        
        # Check for basic memory bank files
        files = list(memory_bank_dir.glob("*.md"))
        file_count = len(files)
        
        # Get modification time
        try:
            mtime = memory_bank.stat().st_mtime
            import datetime
            mod_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            mod_date = "unknown"
        
        click.echo(f"   📦 {memory_bank.name}")
        click.echo(f"      Files: {file_count} markdown files")
        click.echo(f"      Modified: {mod_date}")
        click.echo()


@cli.command()
@click.option('--max-jobs', default=3, help='Maximum number of concurrent jobs')
@click.pass_context
def worker(ctx, max_jobs: int):
    """Start a persistent worker to process build jobs"""
    
    root_path = ctx.obj['root_path']
    
    click.echo(f"🏃 Starting memory bank worker")
    click.echo(f"📁 Root path: {root_path}")
    click.echo(f"🔧 Max concurrent jobs: {max_jobs}")
    click.echo("   Press Ctrl+C to stop")
    click.echo()
    
    # Run the worker
    asyncio.run(_run_worker(root_path, max_jobs))


async def _run_build(root_path: Path, repo_path: str, output_name: Optional[str], wait: bool):
    """Run a build job"""
    
    # Create job manager
    job_manager = JobManager(str(root_path))
    
    # Create job request
    request = BuildJobRequest(
        type=BuildJobType.BUILD,
        repo_path=repo_path,
        output_name=output_name
    )
    
    try:
        # Start worker
        await job_manager.start_worker()
        
        # Create and queue job
        job = await job_manager.create_job(request)
        click.echo(f"📋 Created job: {job.id}")
        
        if not wait:
            click.echo(f"🎯 Job queued. Use job ID to check status: {job.id}")
            return
        
        # Wait for completion
        click.echo("⏳ Waiting for job completion...")
        
        while True:
            job = job_manager.get_job(job.id)
            if job.status in [BuildJobStatus.COMPLETED, BuildJobStatus.FAILED, BuildJobStatus.CANCELLED]:
                break
            
            # Show recent logs
            if job.logs:
                latest_log = job.logs[-1]
                if latest_log and not latest_log.startswith("Logs saved to:"):
                    click.echo(f"   {latest_log}")
            
            await asyncio.sleep(2)
        
        # Show final result
        job = job_manager.get_job(job.id)
        
        if job.status == BuildJobStatus.COMPLETED:
            click.echo(f"✅ Build completed successfully!")
            click.echo(f"📁 Output: {job.output_path}")
            if job.result and 'files_written' in job.result:
                file_count = len(job.result['files_written'])
                click.echo(f"📝 Created {file_count} files")
        elif job.status == BuildJobStatus.FAILED:
            click.echo(f"❌ Build failed: {job.error_message}")
            sys.exit(1)
        else:
            click.echo(f"⚠️  Build was cancelled")
    
    finally:
        # Stop worker
        await job_manager.stop_worker()


async def _run_update(root_path: Path, repo_path: str, memory_bank_name: str, wait: bool):
    """Run an update job"""
    
    # Create job manager
    job_manager = JobManager(str(root_path))
    
    # Create job request
    request = BuildJobRequest(
        type=BuildJobType.UPDATE,
        repo_path=repo_path,
        memory_bank_name=memory_bank_name
    )
    
    try:
        # Start worker
        await job_manager.start_worker()
        
        # Create and queue job
        job = await job_manager.create_job(request)
        click.echo(f"📋 Created update job: {job.id}")
        
        if not wait:
            click.echo(f"🎯 Job queued. Use job ID to check status: {job.id}")
            return
        
        # Wait for completion
        click.echo("⏳ Waiting for update completion...")
        
        while True:
            job = job_manager.get_job(job.id)
            if job.status in [BuildJobStatus.COMPLETED, BuildJobStatus.FAILED, BuildJobStatus.CANCELLED]:
                break
            
            # Show recent logs
            if job.logs:
                latest_log = job.logs[-1]
                if latest_log and not latest_log.startswith("Logs saved to:"):
                    click.echo(f"   {latest_log}")
            
            await asyncio.sleep(2)
        
        # Show final result
        job = job_manager.get_job(job.id)
        
        if job.status == BuildJobStatus.COMPLETED:
            click.echo(f"✅ Update completed successfully!")
            click.echo(f"📁 Memory bank: {memory_bank_name}")
            if job.result and 'files_written' in job.result:
                file_count = len(job.result['files_written'])
                click.echo(f"📝 Updated {file_count} files")
        elif job.status == BuildJobStatus.FAILED:
            click.echo(f"❌ Update failed: {job.error_message}")
            sys.exit(1)
        else:
            click.echo(f"⚠️  Update was cancelled")
    
    finally:
        # Stop worker
        await job_manager.stop_worker()


async def _run_worker(root_path: Path, max_jobs: int):
    """Run a persistent worker"""
    
    # Create job manager
    job_manager = JobManager(str(root_path), max_concurrent_jobs=max_jobs)
    
    try:
        # Start worker
        await job_manager.start_worker()
        
        click.echo("✅ Worker started and ready")
        
        # Keep running until interrupted
        while True:
            # Show status
            all_jobs = job_manager.get_all_jobs()
            running_jobs = job_manager.get_jobs_by_status(BuildJobStatus.RUNNING)
            pending_jobs = job_manager.get_jobs_by_status(BuildJobStatus.PENDING)
            
            status = f"Jobs: {len(running_jobs)} running, {len(pending_jobs)} pending, {len(all_jobs)} total"
            click.echo(f"🔄 {status}")
            
            await asyncio.sleep(10)
    
    except KeyboardInterrupt:
        click.echo("\n🛑 Shutting down worker...")
    
    finally:
        # Stop worker
        await job_manager.stop_worker()
        click.echo("✅ Worker stopped")


if __name__ == "__main__":
    cli()