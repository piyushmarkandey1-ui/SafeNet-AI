"""
SafeNet AI — Vercel Serverless Function Entry Point (api/index.py)

All /api/* requests on Vercel are rewritten to this file via vercel.json.
This file loads the full FastAPI app (with all routers already mounted under /api)
and serves it as an ASGI application via Mangum.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path so app.* imports resolve correctly
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set production environment flag
os.environ.setdefault("VERCEL_ENV", "production")

# Import the fully-wired FastAPI app (loads dotenv, registers all routers under /api)
try:
    from app.main import app

except ImportError as e:
    # Fallback minimal app if backend imports fail (e.g. missing heavy deps on Vercel)
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="SafeNet AI - Fallback")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/")
    def fallback_root():
        return {
            "status": "error",
            "message": f"Import failed: {str(e)}",
            "note": "Some dependencies may be missing in the serverless environment.",
        }

# Vercel requires an ASGI handler named `app` — FastAPI is already ASGI-compatible.
# Vercel will pick up the `app` object exported from this module automatically.