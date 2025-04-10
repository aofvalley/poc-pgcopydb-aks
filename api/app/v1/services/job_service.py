import os
import logging
import subprocess
from datetime import datetime
from typing import Dict

from app.utils.command import get_log_directory, write_to_log, log_job_execution

# Configure logging
logger = logging.getLogger("pgcopydb-api-service")

# Dictionary to store job information
jobs: Dict[str, Dict] = {}

def run_command_background(job_id: str, cmd: str) -> None:
    """
    Execute a command in the background and update job status.
    
    Args:
        job_id: Unique identifier for the job
        cmd: Command to execute
    """
    try:
        log_dir = get_log_directory()
        
        # Specific log file for this job
        log_file = f"{log_dir}/job-{job_id}.log"
        
        # Log the start of the command
        start_msg = f"[{datetime.now().isoformat()}] Starting command: {cmd}"
        logger.info(start_msg)
        
        with open(log_file, 'w') as f:
            f.write(f"{start_msg}\n")
            
            # Modify command to also write output to log files
            shared_log_file = f"{log_dir}/pgcopydb-executions.log"
            modified_cmd = f"{cmd} 2>&1 | tee -a {log_file} {shared_log_file}"
            
            # Execute the command
            process = subprocess.Popen(
                modified_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            stdout, stderr = process.communicate()
            
            # Log the result
            result_msg = f"[{datetime.now().isoformat()}] Command completed with code: {process.returncode}"
            f.write(f"{result_msg}\n")
            
            if process.returncode != 0:
                error_msg = f"[{datetime.now().isoformat()}] Error in command: {stderr}"
                logger.error(error_msg)
                f.write(f"{error_msg}\n")
                jobs[job_id] = {
                    "status": "error",
                    "command": cmd,
                    "output": stdout,
                    "error": stderr,
                    "finished": True,
                    "log_file": log_file
                }
            else:
                success_msg = f"[{datetime.now().isoformat()}] Command completed successfully"
                logger.info(success_msg)
                f.write(f"{success_msg}\n")
                jobs[job_id] = {
                    "status": "completed",
                    "command": cmd,
                    "output": stdout,
                    "finished": True,
                    "log_file": log_file
                }
                
            # Write to shared log file
            log_job_execution(
                job_id, 
                cmd, 
                'Completed' if process.returncode == 0 else 'Error', 
                log_file
            )
                
    except Exception as e:
        logger.exception(f"Exception executing command {cmd}")
        jobs[job_id] = {
            "status": "error",
            "command": cmd,
            "error": str(e),
            "finished": True
        }


def get_job_status(job_id: str) -> Dict:
    """
    Get the status of a job.
    
    Args:
        job_id: ID of the job to check
        
    Returns:
        Dictionary with job status information
    """
    if job_id in jobs:
        return jobs[job_id]
    return None


def init_job(job_id: str, cmd: str) -> Dict:
    """
    Initialize a new job.
    
    Args:
        job_id: Unique identifier for the job
        cmd: Command to be executed
        
    Returns:
        Dictionary with initial job status
    """
    job_status = {
        "status": "running",
        "command": cmd,
        "finished": False
    }
    
    jobs[job_id] = job_status
    return job_status


def get_job_log(job_id: str) -> str:
    """
    Get the log content for a job.
    
    Args:
        job_id: ID of the job
        
    Returns:
        Log content as string or error message
    """
    if job_id not in jobs:
        return "Job not found"
    
    job_info = jobs[job_id]
    log_file = job_info.get("log_file")
    
    if not log_file or not os.path.exists(log_file):
        return "No logs found for this job"
    
    try:
        with open(log_file, 'r') as f:
            return f.read()
    except Exception as e:
        logger.exception(f"Error reading log file for job {job_id}")
        return f"Error reading log file: {str(e)}"
