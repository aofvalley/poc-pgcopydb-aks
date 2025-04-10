from typing import Optional, Dict, Any
from pydantic import BaseModel


class JobStatus(BaseModel):
    job_id: str
    status: str
    command: str
    output: Optional[str] = None
    error: Optional[str] = None
    finished: bool
    log_file: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    command: str
    finished: bool


class TableListResponse(BaseModel):
    success: bool
    tables: list[str]
    count: int


class FilterTablesResponse(BaseModel):
    success: bool
    filter: str
    tables: list[str]
    count: int


class HealthResponse(BaseModel):
    status: str
    pgcopydb_version: str
    pod: str


class ApiInfo(BaseModel):
    name: str
    version: str
    pod: str
    endpoints: list[str]
    documentation: Dict[str, str]
