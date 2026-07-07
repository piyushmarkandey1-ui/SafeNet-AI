"""
SafeNet AI — Vercel Serverless Function Entry Point

This file adapts the FastAPI app for Vercel's serverless architecture.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment for production
os.environ["VERCEL_ENV"] = "production"

# Import and configure the FastAPI app
try:
    from app.main import app
    
    # Configure for serverless deployment
    app.title = "SafeNet AI - Production API"
    app.description = "Digital public safety intelligence platform - deployed on Vercel"
    
    # Add production middleware and settings
    from fastapi.middleware.cors import CORSMiddleware
    
    # Update CORS for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://*.vercel.app",
            "https://safenet-ai.vercel.app",
            "https://localhost:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
except ImportError as e:
    # Fallback minimal app if imports fail
    from fastapi import FastAPI
    
    app = FastAPI(title="SafeNet AI - Fallback")
    
    @app.get("/")
    def fallback_root():
        return {
            "status": "error",
            "message": f"Import failed: {str(e)}",
            "note": "Some dependencies may be missing in serverless environment"
        }

# Vercel handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request)