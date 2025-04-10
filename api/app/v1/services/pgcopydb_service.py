import uuid
import subprocess
import logging
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger("pgcopydb-api-operations")

def check_pgcopydb_version() -> str:
    """
    Check if pgcopydb is available and get its version.
    
    Returns:
        Version string or raises exception if pgcopydb is not available
    """
    try:
        result = subprocess.run("pgcopydb --version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("pgcopydb not available")
        return result.stdout.strip()
    except Exception as e:
        logger.exception("Error checking pgcopydb version")
        raise e


def build_clone_command(source: str, target: str, options: Optional[List[str]] = None) -> str:
    """
    Build command string for pgcopydb clone operation.
    
    Args:
        source: Source database connection string
        target: Target database connection string
        options: Additional command options
        
    Returns:
        Formatted command string
    """
    options_str = " ".join(options) if options else ""
    return f'pgcopydb clone --source "{source}" --target "{target}" {options_str}'


def build_dump_command(source: str, directory: str, dump_type: str = "full", 
                       tables: Optional[List[str]] = None,
                       exclude_tables: Optional[List[str]] = None,
                       no_role_passwords: bool = False,
                       snapshot: Optional[str] = None,
                       skip_extensions: bool = False,
                       filters_file: Optional[str] = None) -> str:
    """
    Build command string for pgcopydb dump operation.
    
    Args:
        source: Source database connection string
        directory: Directory where the dump will be stored
        dump_type: Type of dump ('full', 'schema', or 'roles')
        tables: List of tables to include
        exclude_tables: List of tables to exclude
        no_role_passwords: Whether to include role passwords
        snapshot: Snapshot to use
        skip_extensions: Whether to skip extensions
        filters_file: File with filters
        
    Returns:
        Formatted command string
    """
    if dump_type == "schema":
        cmd = f'pgcopydb dump schema --source "{source}" --dir "{directory}"'
        
        if skip_extensions:
            cmd += " --skip-extensions"
        if snapshot:
            cmd += f' --snapshot "{snapshot}"'
        if filters_file:
            cmd += f' --filters "{filters_file}"'
                
        if tables:
            tables_str = " ".join([f"--table {t}" for t in tables])
            cmd += f" {tables_str}"
        if exclude_tables:
            exclude_str = " ".join([f"--exclude-table {t}" for t in exclude_tables])
            cmd += f" {exclude_str}"
            
    elif dump_type == "roles":
        cmd = f'pgcopydb dump roles --source "{source}" --dir "{directory}"'
        
        if no_role_passwords:
            cmd += " --no-role-passwords"
                
    else:  # "full" - execute both schema and roles
        cmd = f'pgcopydb dump schema --source "{source}" --dir "{directory}"'
        
        if skip_extensions:
            cmd += " --skip-extensions"
        if snapshot:
            cmd += f' --snapshot "{snapshot}"'
        if filters_file:
            cmd += f' --filters "{filters_file}"'
                
        if tables:
            tables_str = " ".join([f"--table {t}" for t in tables])
            cmd += f" {tables_str}"
        if exclude_tables:
            exclude_str = " ".join([f"--exclude-table {t}" for t in exclude_tables])
            cmd += f" {exclude_str}"
            
        cmd += f' && pgcopydb dump roles --source "{source}" --dir "{directory}"'
        
        if no_role_passwords:
            cmd = cmd.replace("dump roles", "dump roles --no-role-passwords")
            
    return cmd


def build_restore_command(target: str, directory: str, 
                          schema_only: bool = False,
                          data_only: bool = False,
                          tables: Optional[List[str]] = None,
                          exclude_tables: Optional[List[str]] = None) -> str:
    """
    Build command string for pgcopydb restore operation.
    
    Args:
        target: Target database connection string
        directory: Directory where the dump is located
        schema_only: Whether to restore schema only
        data_only: Whether to restore data only
        tables: List of tables to restore
        exclude_tables: List of tables to exclude
        
    Returns:
        Formatted command string
    """
    cmd = f'pgcopydb restore --target "{target}" --input-dir "{directory}"'
    
    if schema_only:
        cmd += " --schema-only"
    if data_only:
        cmd += " --data-only"
    if tables:
        tables_str = " ".join([f"--table {t}" for t in tables])
        cmd += f" {tables_str}"
    if exclude_tables:
        exclude_str = " ".join([f"--exclude-table {t}" for t in exclude_tables])
        cmd += f" {exclude_str}"
        
    return cmd


def build_copy_command(source: str, target: str,
                       tables: Optional[List[str]] = None,
                       exclude_tables: Optional[List[str]] = None) -> str:
    """
    Build command string for pgcopydb copy operation.
    
    Args:
        source: Source database connection string
        target: Target database connection string
        tables: List of tables to copy
        exclude_tables: List of tables to exclude
        
    Returns:
        Formatted command string
    """
    cmd = f'pgcopydb copy-db --source "{source}" --target "{target}"'
    
    if tables:
        tables_str = " ".join([f"--table {t}" for t in tables])
        cmd += f" {tables_str}"
    if exclude_tables:
        exclude_str = " ".join([f"--exclude-table {t}" for t in exclude_tables])
        cmd += f" {exclude_str}"
        
    return cmd


def list_tables(connection_string: str) -> List[str]:
    """
    List tables from a database.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        List of table names
    """
    cmd = f"pgcopydb list tables --source {connection_string}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Error listing tables: {result.stderr}")
        raise Exception(result.stderr)
    
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def filter_tables(connection_string: str, filter_pattern: str) -> List[str]:
    """
    Filter tables using a pattern.
    
    Args:
        connection_string: Database connection string
        filter_pattern: Pattern to filter tables
        
    Returns:
        List of table names matching the pattern
    """
    cmd = f"pgcopydb list tables --source {connection_string} --like '{filter_pattern}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Error filtering tables: {result.stderr}")
        raise Exception(result.stderr)
    
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
