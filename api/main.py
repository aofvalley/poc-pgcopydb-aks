import subprocess
import logging
import os
import uuid
from datetime import datetime
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
        # Crear directorio para logs si no existe
        log_dir = "/app/pgcopydb_files/logs" if os.path.exists("/app/pgcopydb_files/logs") else "/tmp/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Archivo de log específico para este trabajo
        log_file = f"{log_dir}/job-{job_id}.log"
        
        # Registrar el inicio del comando en el log principal y en el archivo específico
        start_msg = f"[{datetime.now().isoformat()}] Iniciando comando: {cmd}"
        logger.info(start_msg)
        
        with open(log_file, 'w') as f:
            f.write(f"{start_msg}\n")
            
            # Modificar el comando para que también escriba su salida al archivo de log
            # y a un archivo que puede ser accesible desde ambos contenedores
            shared_log_file = f"{log_dir}/pgcopydb-executions.log"
            modified_cmd = f"{cmd} 2>&1 | tee -a {log_file} {shared_log_file}"
            
            # Ejecutar el comando y redirigir la salida al archivo de log
            process = subprocess.Popen(
                modified_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            stdout, stderr = process.communicate()
            
            # Registrar el resultado en los logs
            result_msg = f"[{datetime.now().isoformat()}] Comando finalizado con código: {process.returncode}"
            f.write(f"{result_msg}\n")
            
            if process.returncode != 0:
                error_msg = f"[{datetime.now().isoformat()}] Error en comando: {stderr}"
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
                success_msg = f"[{datetime.now().isoformat()}] Comando completado exitosamente"
                logger.info(success_msg)
                f.write(f"{success_msg}\n")
                jobs[job_id] = {
                    "status": "completed",
                    "command": cmd,
                    "output": stdout,
                    "finished": True,
                    "log_file": log_file
                }
                
            # Escribir al archivo de log compartido
            with open(shared_log_file, 'a') as sf:
                sf.write(f"\n{'='*50}\n")
                sf.write(f"Job ID: {job_id}\n")
                sf.write(f"Comando: {cmd}\n")
                sf.write(f"Estado: {'Completado' if process.returncode == 0 else 'Error'}\n")
                sf.write(f"Finalizado: {datetime.now().isoformat()}\n")
                sf.write(f"{'='*50}\n\n")
                
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

@app.get("/logs/{job_id}", summary="Ver los logs de un trabajo específico")
async def get_job_logs(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el trabajo con ID {job_id}"
        )
    
    job_info = jobs[job_id]
    log_file = job_info.get("log_file")
    
    if not log_file or not os.path.exists(log_file):
        return {
            "job_id": job_id,
            "logs": "No se encontraron logs para este trabajo"
        }
    
    with open(log_file, 'r') as f:
        logs = f.read()
    
    return {
        "job_id": job_id,
        "status": job_info["status"],
        "command": job_info["command"],
        "finished": job_info["finished"],
        "logs": logs
    }

@app.get("/execution-logs", summary="Ver los logs de todas las ejecuciones")
async def get_execution_logs():
    log_dir = "/app/pgcopydb_files/logs" if os.path.exists("/app/pgcopydb_files/logs") else "/tmp/logs"
    shared_log_file = f"{log_dir}/pgcopydb-executions.log"
    
    if not os.path.exists(shared_log_file):
        return {
            "logs": "No se encontraron logs de ejecución"
        }
    
    with open(shared_log_file, 'r') as f:
        logs = f.read()
    
    return {
        "logs": logs
    }

if __name__ == "__main__":
    import uvicorn
    # Usar puerto 8000 por convención para FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
