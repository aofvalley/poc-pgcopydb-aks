from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ConnectionString(BaseModel):
    """Model for PostgreSQL connection strings."""
    connection_string: str = Field(..., description="PostgreSQL connection string (postgresql://user:password@host:port/database)")
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection string must start with postgresql://')
        return v


class CloneRequest(BaseModel):
    source: str = Field(..., description="Source database connection string")
    target: str = Field(..., description="Target database connection string")
    options: Optional[List[str]] = Field(default=[], description="Additional options for pgcopydb clone")
    
    @validator('source', 'target')
    def validate_connection_strings(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection strings must start with postgresql://')
        return v


class DumpRequest(BaseModel):
    source: str = Field(..., description="Source database connection string")
    dir: str = Field(..., description="Directory where the dump will be stored")
    tables: Optional[List[str]] = Field(default=None, description="List of specific tables to include")
    exclude_tables: Optional[List[str]] = Field(default=None, description="List of tables to exclude")
    dump_type: str = Field(default="full", description="Dump type: 'full', 'schema', or 'roles'")
    no_role_passwords: Optional[bool] = Field(default=False, description="Don't include passwords for roles")
    snapshot: Optional[str] = Field(default=None, description="Use an exported snapshot")
    skip_extensions: Optional[bool] = Field(default=False, description="Skip restoring extensions")
    filters_file: Optional[str] = Field(default=None, description="File with defined filters")
    
    @validator('source')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection string must start with postgresql://')
        return v
        
    @validator('dump_type')
    def validate_dump_type(cls, v):
        allowed_types = ['full', 'schema', 'roles']
        if v not in allowed_types:
            raise ValueError(f'Dump type must be one of {", ".join(allowed_types)}')
        return v


class RestoreRequest(BaseModel):
    target: str = Field(..., description="Target database connection string")
    dir: str = Field(..., description="Directory where the dump is located")
    tables: Optional[List[str]] = Field(default=None, description="List of specific tables to restore")
    exclude_tables: Optional[List[str]] = Field(default=None, description="List of tables to exclude")
    schema_only: Optional[bool] = Field(default=False, description="Restore schema only")
    data_only: Optional[bool] = Field(default=False, description="Restore data only")
    
    @validator('target')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection string must start with postgresql://')
        return v


class CopyRequest(BaseModel):
    source: str = Field(..., description="Source database connection string")
    target: str = Field(..., description="Target database connection string")
    tables: Optional[List[str]] = Field(default=None, description="List of specific tables to copy")
    exclude_tables: Optional[List[str]] = Field(default=None, description="List of tables to exclude")
    
    @validator('source', 'target')
    def validate_connection_strings(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection strings must start with postgresql://')
        return v


class FilterTablesRequest(BaseModel):
    connection_string: str = Field(..., description="Database connection string")
    filter: str = Field(..., description="Filter for tables (like_pattern)")
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Connection string must start with postgresql://')
        return v
