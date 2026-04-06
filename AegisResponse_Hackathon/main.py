"""
Aegis Hospitality OS — Root Entry Point
Re-exports the app from the modular backend package.

Run with:
    uvicorn main:app --reload --port 8000
"""

from backend.main import app  # noqa: F401
