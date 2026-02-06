"""FastAPI server for OpenAlex Local with FTS5 search.

Provides HTTP relay server for remote database access.

Usage:
    openalex-local relay                    # Run on default port 31292
    openalex-local relay --port 8080        # Custom port

    # Or directly:
    uvicorn openalex_local.server:app --host 0.0.0.0 --port 31292
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__
from .routes import router

# Create FastAPI app
app = FastAPI(
    title="OpenAlex Local API",
    description="Fast full-text search across 284M+ scholarly works",
    version=__version__,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
def root():
    """API root with endpoint information."""
    return {
        "name": "OpenAlex Local API",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "search": "/works?q=<query>",
            "get_by_id": "/works/{id_or_doi}",
            "batch": "/works/batch",
        },
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    from .._core.db import get_db

    try:
        db = get_db()
        return {
            "status": "healthy",
            "database_connected": db is not None,
            "database_path": str(db.db_path) if db else None,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@app.get("/info")
def info():
    """Get database statistics."""
    from .._core.db import get_db

    db = get_db()

    # Use _metadata table for pre-computed counts (COUNT(*) on 459M rows is too slow)
    work_count = 0
    fts_count = 0
    try:
        row = db.fetchone("SELECT value FROM _metadata WHERE key = 'total_works'")
        if row:
            work_count = int(row["value"])
        row = db.fetchone("SELECT value FROM _metadata WHERE key = 'fts_total_indexed'")
        if row:
            fts_count = int(row["value"])
    except Exception:
        pass

    return {
        "name": "OpenAlex Local API",
        "version": __version__,
        "status": "running",
        "mode": "local",
        "total_works": work_count,
        "fts_indexed": fts_count,
        "database_path": str(db.db_path),
    }


# Default port: SCITEX convention (3129X scheme)
DEFAULT_PORT = int(os.environ.get("OPENALEX_LOCAL_PORT", "31292"))
DEFAULT_HOST = os.environ.get("OPENALEX_LOCAL_HOST", "0.0.0.0")


def run_server(host: str = None, port: int = None, force: bool = False):
    """Run the FastAPI server.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 31292)
        force: If True, kill any existing process using the port
    """
    import uvicorn

    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT

    if force:
        from .._cli.utils import kill_process_on_port

        kill_process_on_port(port)

    uvicorn.run(app, host=host, port=port)


__all__ = ["app", "run_server", "DEFAULT_PORT", "DEFAULT_HOST"]
