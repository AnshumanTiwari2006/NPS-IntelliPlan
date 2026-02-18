"""
FastAPI Application Main Entry Point

This module initializes the FastAPI app and configures middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Create FastAPI app
app = FastAPI(
    title="NPS IntelliPlan API",
    description="AI-Driven Retirement Corpus & Pension Forecasting Engine",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routes
from backend.api import routes
app.include_router(routes.router, prefix="/api")

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def read_root():
    """Serve the main frontend page."""
    frontend_index = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"message": "NPS IntelliPlan API is running. Visit /docs for API documentation."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NPS IntelliPlan",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
