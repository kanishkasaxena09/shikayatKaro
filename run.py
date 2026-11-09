"""One-command runner for Project Shikayat Karo backend server.

Usage:
    python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("Starting Project Shikayat Karo backend on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
