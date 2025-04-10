import uvicorn
from app.core.application import create_app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    # Run the application using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
