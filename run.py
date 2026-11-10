"""One-command runner for Project Shikayat Karo backend server.

Supports local development and production cloud deployment (reads PORT and HOST from environment).

Usage:
    python run.py
"""

import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting Project Shikayat Karo backend on http://{host}:{port} ...")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
