import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, Tuple

# Configure logging
logger = logging.getLogger("pgcopydb-api-utils")

def run_command(cmd: str) -> Tuple[str, str, int]:
    """
    Run a shell command and return the output, error and return code.
    
    Args:
        cmd: Command to execute
        
    Returns:
        Tuple containing stdout, stderr and return code
    """
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode
        
    except Exception as e:
        logger.exception(f"Exception executing command {cmd}")
        return "", str(e), -1


def get_log_directory() -> str:
    """
    Get the directory for storing logs.
    
    Returns:
        Path to log directory
    """
    log_dir = "/app/pgcopydb_files/logs" if os.path.exists("/app/pgcopydb_files/logs") else "/tmp/logs"
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def write_to_log(log_file: str, message: str) -> None:
    """
    Write a message to a log file.
    
    Args:
        log_file: Path to log file
        message: Message to write
    """
    try:
        with open(log_file, 'a') as f:
            f.write(f"{message}\n")
    except Exception as e:
        logger.exception(f"Error writing to log file {log_file}: {str(e)}")


def update_job_status(jobs: Dict, job_id: str, status: Dict) -> None:
    """
    Update the status of a job in the jobs dictionary.
    
    Args:
        jobs: Dictionary containing all jobs
        job_id: ID of the job to update
        status: New status information
    """
    if job_id in jobs:
        jobs[job_id].update(status)
        

def log_job_execution(job_id: str, cmd: str, status: str, log_file: str) -> None:
    """
    Log information about a job execution to the shared log file.
    
    Args:
        job_id: ID of the job
        cmd: Command that was executed
        status: Status of the job execution
        log_file: Path to the log file where the execution details were written
    """
    log_dir = get_log_directory()
    shared_log_file = f"{log_dir}/pgcopydb-executions.log"
    
    try:
        with open(shared_log_file, 'a') as sf:
            sf.write(f"\n{'='*50}\n")
            sf.write(f"Job ID: {job_id}\n")
            sf.write(f"Command: {cmd}\n")
            sf.write(f"Status: {status}\n")
            sf.write(f"Log file: {log_file}\n")
            sf.write(f"Timestamp: {datetime.now().isoformat()}\n")
            sf.write(f"{'='*50}\n\n")
    except Exception as e:
        logger.exception(f"Error writing to shared log file: {str(e)}")
