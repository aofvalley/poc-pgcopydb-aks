import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pgcopydb-api")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="pgcopydb API", 
        description="API to interact with pgcopydb in a Kubernetes environment",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust according to security requirements
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    from app.v1.routes.pgcopydb_routes import router as pgcopydb_router
    
    # Root endpoint redirects to versioned API
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return {"message": "Welcome to pgcopydb API - use /v1 for API endpoints"}
    
    # Health check at root level for K8s probes
    @app.get("/health", include_in_schema=False)
    async def root_health():
        from app.v1.routes.pgcopydb_routes import health_check
        return await health_check()
    
    # Include the versioned router
    app.include_router(pgcopydb_router)
    
    return app
