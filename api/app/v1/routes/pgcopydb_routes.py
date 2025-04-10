import uuid
import os
import socket
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List

from app.v1.models.requests import (
    ConnectionString, CloneRequest, DumpRequest, 
    RestoreRequest, CopyRequest, FilterTablesRequest
)
from app.v1.models.responses import (
    JobStatus, JobResponse, TableListResponse, 
    FilterTablesResponse, HealthResponse, ApiInfo
)
from app.v1.services.job_service import (
    run_command_background, get_job_status, 
    init_job, get_job_log, jobs
)
from app.v1.services.pgcopydb_service import (
    check_pgcopydb_version, build_clone_command, 
    build_dump_command, build_restore_command, 
    build_copy_command, list_tables, filter_tables
)

# Get pod name for identification
POD_NAME = os.environ.get("POD_NAME", socket.gethostname())

# Create router
router = APIRouter(prefix="/v1")


@router.get("/", response_model=ApiInfo, summary="API information")
async def root():
    """Get information about the API and available endpoints."""
    return {
        "name": "pgcopydb API",
        "version": "1.0.0",
        "pod": POD_NAME,
        "endpoints": [
            "/v1/clone", "/v1/dump", "/v1/restore", "/v1/copy", 
            "/v1/list-tables", "/v1/filter-tables", 
            "/v1/check-status/{job_id}", "/v1/health"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@router.get("/health", response_model=HealthResponse, summary="Check service health")
async def health_check():
    """
    Check if the service is healthy and pgcopydb is available.
    
    Returns:
        Health status information
    """
    try:
        pgcopydb_version = check_pgcopydb_version()
        return {
            "status": "healthy",
            "pgcopydb_version": pgcopydb_version,
            "pod": POD_NAME
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check error: {str(e)}"
        )


@router.post("/clone", response_model=JobStatus, summary="Clone a PostgreSQL database")
async def clone(request: CloneRequest, background_tasks: BackgroundTasks):
    """
    Clone a source PostgreSQL database to a target.
    
    Args:
        request: Clone operation parameters
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Job status information
    """
    try:
        job_id = str(uuid.uuid4())
        cmd = build_clone_command(request.source, request.target, request.options)
        
        # Initialize job status
        job_status = init_job(job_id, cmd)
        
        # Execute in background
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            **job_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dump", response_model=JobStatus, summary="Dump a PostgreSQL database")
async def dump(request: DumpRequest, background_tasks: BackgroundTasks):
    """
    Dump a PostgreSQL database schema, data, and/or roles.
    
    Args:
        request: Dump operation parameters
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Job status information
    """
    try:
        job_id = str(uuid.uuid4())
        
        cmd = build_dump_command(
            source=request.source,
            directory=request.dir,
            dump_type=request.dump_type,
            tables=request.tables,
            exclude_tables=request.exclude_tables,
            no_role_passwords=request.no_role_passwords,
            snapshot=request.snapshot,
            skip_extensions=request.skip_extensions,
            filters_file=request.filters_file
        )
        
        # Initialize job status
        job_status = init_job(job_id, cmd)
        
        # Execute in background
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            **job_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore", response_model=JobStatus, summary="Restore a PostgreSQL database")
async def restore(request: RestoreRequest, background_tasks: BackgroundTasks):
    """
    Restore a PostgreSQL database from a dump.
    
    Args:
        request: Restore operation parameters
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Job status information
    """
    try:
        job_id = str(uuid.uuid4())
        
        cmd = build_restore_command(
            target=request.target,
            directory=request.dir,
            schema_only=request.schema_only,
            data_only=request.data_only,
            tables=request.tables,
            exclude_tables=request.exclude_tables
        )
        
        # Initialize job status
        job_status = init_job(job_id, cmd)
        
        # Execute in background
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            **job_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/copy", response_model=JobStatus, summary="Copy tables between databases")
async def copy_tables(request: CopyRequest, background_tasks: BackgroundTasks):
    """
    Copy specific tables between PostgreSQL databases.
    
    Args:
        request: Copy operation parameters
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Job status information
    """
    try:
        job_id = str(uuid.uuid4())
        
        cmd = build_copy_command(
            source=request.source,
            target=request.target,
            tables=request.tables,
            exclude_tables=request.exclude_tables
        )
        
        # Initialize job status
        job_status = init_job(job_id, cmd)
        
        # Execute in background
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            **job_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list-tables", response_model=TableListResponse, summary="List database tables")
async def list_db_tables(request: ConnectionString):
    """
    List all tables in a PostgreSQL database.
    
    Args:
        request: Database connection string
    
    Returns:
        List of tables in the database
    """
    try:
        table_list = list_tables(request.connection_string)
        return {
            "success": True,
            "tables": table_list,
            "count": len(table_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter-tables", response_model=FilterTablesResponse, summary="Filter tables by pattern")
async def filter_db_tables(request: FilterTablesRequest):
    """
    Filter tables in a PostgreSQL database by a pattern.
    
    Args:
        request: Filter parameters
    
    Returns:
        Filtered list of tables
    """
    try:
        filtered_tables = filter_tables(request.connection_string, request.filter)
        return {
            "success": True,
            "filter": request.filter,
            "tables": filtered_tables,
            "count": len(filtered_tables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-status/{job_id}", response_model=JobStatus, summary="Check job status")
async def check_status(job_id: str):
    """
    Check the status of a job by ID.
    
    Args:
        job_id: ID of the job to check
    
    Returns:
        Job status information
    """
    job_info = get_job_status(job_id)
    if not job_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return {
        "job_id": job_id,
        **job_info
    }


@router.get("/logs/{job_id}", summary="Get job logs")
async def get_job_logs(job_id: str):
    """
    Get logs for a specific job.
    
    Args:
        job_id: ID of the job
    
    Returns:
        Job logs
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    job_info = jobs[job_id]
    logs = get_job_log(job_id)
    
    return {
        "job_id": job_id,
        "status": job_info["status"],
        "command": job_info["command"],
        "finished": job_info["finished"],
        "logs": logs
    }


@router.get("/execution-logs", summary="Get all execution logs")
async def get_execution_logs():
    """
    Get logs for all executions.
    
    Returns:
        Combined logs for all executions
    """
    log_dir = "/app/pgcopydb_files/logs" if os.path.exists("/app/pgcopydb_files/logs") else "/tmp/logs"
    shared_log_file = f"{log_dir}/pgcopydb-executions.log"
    
    if not os.path.exists(shared_log_file):
        return {
            "logs": "No execution logs found"
        }
    
    with open(shared_log_file, 'r') as f:
        logs = f.read()
    
    return {
        "logs": logs
    }
