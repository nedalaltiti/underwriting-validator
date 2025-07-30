# underwriting_validation/api/__main__.py
"""
Package entry-point.

`python -m underwriting_validation.api` ➜ starts Uvicorn with the FastAPI app declared in
`underwriting_validation.api.app`.

All heavyweight initialisation (vector-store warm-up, etc.) is handled by the
lifespan context inside `app.py`, so we only need to start the server.
"""

from __future__ import annotations

import uvicorn
from underwriting_validation.config.settings import settings


def main() -> None:  
    """Boot Uvicorn with sane defaults taken from settings."""
    uvicorn.run(
        "underwriting_validation.api.app:app",         
        host=settings.host,  
        port=settings.port, 
        reload=settings.debug,        # hot-reload in dev
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__": 
    main()
