import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="pgcopydb API", description="API para interactuar con pgcopydb")

class CloneRequest(BaseModel):
    source: str
    target: str

class DumpRequest(BaseModel):
    source: str
    dir: str

class RestoreRequest(BaseModel):
    target: str
    dir: str

@app.post("/clone", summary="Clonar una base de datos PostgreSQL")
async def clone(request: CloneRequest):
    try:
        cmd = f"pgcopydb clone {request.source} {request.target}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dump", summary="Realizar un dump de una base de datos PostgreSQL")
async def dump(request: DumpRequest):
    try:
        cmd = f"pgcopydb dump -s {request.source} -o {request.dir}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restore", summary="Restaurar una base de datos PostgreSQL")
async def restore(request: RestoreRequest):
    try:
        cmd = f"pgcopydb restore -t {request.target} -i {request.dir}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
