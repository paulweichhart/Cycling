"""Vercel entrypoint for the API project (root directory: src).

Vercel looks for a FastAPI `app` in index.py / app.py / main.py at the project
root; the real app lives in service/app.py.
"""
from service.app import app  # noqa: F401
