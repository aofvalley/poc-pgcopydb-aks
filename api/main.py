import subprocess
import logging
import os
import uuid
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import socket

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pgcopydb-api")

# Validación de hostname del pod
POD_NAME = os.environ.get("POD_NAME", socket.gethostname())

# Diccionario para guardar los trabajos en progreso
jobs: Dict[str, Dict] = {}

app = FastAPI(
    title="pgcopydb API", 
    description="API para interactuar con pgcopydb en un entorno Kubernetes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS para permitir solicitudes de diferentes orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar según tus necesidades de seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos para validación de datos
class ConnectionString(BaseModel):
    """Modelo para cadenas de conexión a PostgreSQL."""
    connection_string: str = Field(..., description="Cadena de conexión PostgreSQL (postgresql://usuario:contraseña@host:puerto/basedatos)")
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('La cadena de conexión debe comenzar con postgresql://')
        return v

class CloneRequest(BaseModel):
    source: str = Field(..., description="Cadena de conexión a la base de datos origen")
    target: str = Field(..., description="Cadena de conexión a la base de datos destino")
    options: Optional[List[str]] = Field(default=[], description="Opciones adicionales para pgcopydb clone")
    
    @validator('source', 'target')
    def validate_connection_strings(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Las cadenas de conexión deben comenzar con postgresql://')
        return v

class DumpRequest(BaseModel):
    source: str = Field(..., description="Cadena de conexión a la base de datos origen")
    dir: str = Field(..., description="Directorio donde se almacenará el dump")
    tables: Optional[List[str]] = Field(default=None, description="Lista de tablas específicas a incluir")
    exclude_tables: Optional[List[str]] = Field(default=None, description="Lista de tablas a excluir")
    schema_only: Optional[bool] = Field(default=False, description="Realizar dump solo del esquema")
    data_only: Optional[bool] = Field(default=False, description="Realizar dump solo de los datos")
    
    @validator('source')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('La cadena de conexión debe comenzar con postgresql://')
        return v

class RestoreRequest(BaseModel):
    target: str = Field(..., description="Cadena de conexión a la base de datos destino")
    dir: str = Field(..., description="Directorio donde se encuentra el dump")
    tables: Optional[List[str]] = Field(default=None, description="Lista de tablas específicas a restaurar")
    exclude_tables: Optional[List[str]] = Field(default=None, description="Lista de tablas a excluir")
    schema_only: Optional[bool] = Field(default=False, description="Restaurar solo el esquema")
    data_only: Optional[bool] = Field(default=False, description="Restaurar solo los datos")
    
    @validator('target')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('La cadena de conexión debe comenzar con postgresql://')
        return v

class CopyRequest(BaseModel):
    source: str = Field(..., description="Cadena de conexión a la base de datos origen")
    target: str = Field(..., description="Cadena de conexión a la base de datos destino")
    tables: Optional[List[str]] = Field(default=None, description="Lista de tablas específicas a copiar")
    exclude_tables: Optional[List[str]] = Field(default=None, description="Lista de tablas a excluir")
    
    @validator('source', 'target')
    def validate_connection_strings(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Las cadenas de conexión deben comenzar con postgresql://')
        return v

class FilterTablesRequest(BaseModel):
    connection_string: str = Field(..., description="Cadena de conexión a la base de datos")
    filter: str = Field(..., description="Filtro para las tablas (like_pattern)")
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('La cadena de conexión debe comenzar con postgresql://')
        return v

class JobStatus(BaseModel):
    job_id: str
    status: str
    command: str
    output: Optional[str] = None
    error: Optional[str] = None
    finished: bool

# Función auxiliar para ejecutar comandos en background
def run_command_background(job_id: str, cmd: str):
    try:
        logger.info(f"Ejecutando comando: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error en comando {cmd}: {result.stderr}")
            jobs[job_id] = {
                "status": "error",
                "command": cmd,
                "output": result.stdout,
                "error": result.stderr,
                "finished": True
            }
        else:
            logger.info(f"Comando completado exitosamente: {cmd}")
            jobs[job_id] = {
                "status": "completed",
                "command": cmd,
                "output": result.stdout,
                "finished": True
            }
    except Exception as e:
        logger.exception(f"Excepción al ejecutar comando {cmd}")
        jobs[job_id] = {
            "status": "error",
            "command": cmd,
            "error": str(e),
            "finished": True
        }

@app.get("/", summary="Información de la API")
async def root():
    return {
        "name": "pgcopydb API",
        "version": "1.0.0",
        "pod": POD_NAME,
        "endpoints": [
            "/clone", "/dump", "/restore", "/copy", "/list-tables",
            "/filter-tables", "/check-status", "/health"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health", summary="Verificar la salud del servicio")
async def health_check():
    try:
        # Verificar que pgcopydb está instalado
        result = subprocess.run("pgcopydb --version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="pgcopydb no está disponible"
            )
        return {
            "status": "healthy",
            "pgcopydb_version": result.stdout.strip(),
            "pod": POD_NAME
        }
    except Exception as e:
        logger.exception("Error en health check")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en health check: {str(e)}"
        )

@app.post("/clone", summary="Clonar una base de datos PostgreSQL", response_model=JobStatus)
async def clone(request: CloneRequest, background_tasks: BackgroundTasks):
    try:
        job_id = str(uuid.uuid4())
        
        # Construir el comando con opciones adicionales y usando flags --source y --target
        options_str = " ".join(request.options) if request.options else ""
        cmd = f"pgcopydb clone --source \"{request.source}\" --target \"{request.target}\" {options_str}"
        
        # Inicializar estado del trabajo
        jobs[job_id] = {
            "status": "running",
            "command": cmd,
            "finished": False
        }
        
        # Ejecutar en segundo plano
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            "status": "running",
            "command": cmd,
            "finished": False
        }
    except Exception as e:
        logger.exception("Error al iniciar clonación")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dump", summary="Realizar un dump de una base de datos PostgreSQL", response_model=JobStatus)
async def dump(request: DumpRequest, background_tasks: BackgroundTasks):
    try:
        job_id = str(uuid.uuid4())
        
        # Construir comando con flags completos
        cmd = f"pgcopydb dump --source \"{request.source}\" --output-dir \"{request.dir}\""
        
        if request.schema_only:
            cmd += " --schema-only"
        if request.data_only:
            cmd += " --data-only"
        if request.tables:
            tables_str = " ".join([f"--table {t}" for t in request.tables])
            cmd += f" {tables_str}"
        if request.exclude_tables:
            exclude_str = " ".join([f"--exclude-table {t}" for t in request.exclude_tables])
            cmd += f" {exclude_str}"
        
        # Inicializar estado del trabajo
        jobs[job_id] = {
            "status": "running",
            "command": cmd,
            "finished": False
        }
        
        # Ejecutar en segundo plano
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            "status": "running",
            "command": cmd,
            "finished": False
        }
    except Exception as e:
        logger.exception("Error al iniciar dump")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restore", summary="Restaurar una base de datos PostgreSQL", response_model=JobStatus)
async def restore(request: RestoreRequest, background_tasks: BackgroundTasks):
    try:
        job_id = str(uuid.uuid4())
        
        # Construir comando con flags completos
        cmd = f"pgcopydb restore --target \"{request.target}\" --input-dir \"{request.dir}\""
        
        if request.schema_only:
            cmd += " --schema-only"
        if request.data_only:
            cmd += " --data-only"
        if request.tables:
            tables_str = " ".join([f"--table {t}" for t in request.tables])
            cmd += f" {tables_str}"
        if request.exclude_tables:
            exclude_str = " ".join([f"--exclude-table {t}" for t in request.exclude_tables])
            cmd += f" {exclude_str}"
        
        # Inicializar estado del trabajo
        jobs[job_id] = {
            "status": "running",
            "command": cmd,
            "finished": False
        }
        
        # Ejecutar en segundo plano
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            "status": "running",
            "command": cmd,
            "finished": False
        }
    except Exception as e:
        logger.exception("Error al iniciar restauración")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copy", summary="Copiar tablas específicas entre bases de datos", response_model=JobStatus)
async def copy_tables(request: CopyRequest, background_tasks: BackgroundTasks):
    try:
        job_id = str(uuid.uuid4())
        
        # Construir comando con opciones usando flags --source y --target
        cmd = f"pgcopydb copy-db --source \"{request.source}\" --target \"{request.target}\""
        
        if request.tables:
            tables_str = " ".join([f"--table {t}" for t in request.tables])
            cmd += f" {tables_str}"
        if request.exclude_tables:
            exclude_str = " ".join([f"--exclude-table {t}" for t in request.exclude_tables])
            cmd += f" {exclude_str}"
        
        # Inicializar estado del trabajo
        jobs[job_id] = {
            "status": "running",
            "command": cmd,
            "finished": False
        }
        
        # Ejecutar en segundo plano
        background_tasks.add_task(run_command_background, job_id, cmd)
        
        return {
            "job_id": job_id,
            "status": "running",
            "command": cmd,
            "finished": False
        }
    except Exception as e:
        logger.exception("Error al iniciar copia de tablas")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/list-tables", summary="Listar tablas de una base de datos")
async def list_tables(request: ConnectionString):
    try:
        cmd = f"pgcopydb list tables --source {request.connection_string}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error al listar tablas: {result.stderr}")
            raise HTTPException(status_code=500, detail=result.stderr)
        
        # Procesar el resultado para obtener una lista de tablas
        tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        return {
            "success": True,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        logger.exception("Error al listar tablas")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter-tables", summary="Filtrar tablas con un patrón")
async def filter_tables(request: FilterTablesRequest):
    try:
        cmd = f"pgcopydb list tables --source {request.connection_string} --like '{request.filter}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error al filtrar tablas: {result.stderr}")
            raise HTTPException(status_code=500, detail=result.stderr)
        
        # Procesar el resultado para obtener una lista de tablas
        tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        return {
            "success": True,
            "filter": request.filter,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        logger.exception("Error al filtrar tablas")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check-status/{job_id}", summary="Verificar el estado de un trabajo", response_model=JobStatus)
async def check_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el trabajo con ID {job_id}"
        )
    
    job_info = jobs[job_id]
    return {
        "job_id": job_id,
        **job_info
    }

if __name__ == "__main__":
    import uvicorn
    # Usar puerto 8000 por convención para FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
