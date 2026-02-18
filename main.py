"""
Main application runner

Starts the FastAPI server with uvicorn
"""

if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app
    
    print("=" * 60)
    print("NPS IntelliPlan - Retirement Forecasting Engine")
    print("=" * 60)
    print("\nStarting server...")
    print("Dashboard: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
