"""
Error Handling Middleware — Global exception handlers.
Provides consistent JSON error responses with correlation IDs.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.logging_config import get_logger, correlation_id_var

logger = get_logger("middleware.errors")


def register_error_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle known HTTP exceptions with structured response."""
        corr_id = correlation_id_var.get("")

        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "extra_data": {
                    "status_code": exc.status_code,
                    "path": request.url.path,
                    "correlation_id": corr_id,
                }
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "correlation_id": corr_id,
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic/FastAPI request validation errors."""
        corr_id = correlation_id_var.get("")

        errors = []
        for error in exc.errors():
            errors.append({
                "field": " → ".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            })

        logger.warning(
            f"Validation error on {request.url.path}",
            extra={
                "extra_data": {
                    "errors": errors,
                    "correlation_id": corr_id,
                }
            },
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "status_code": 422,
                "detail": "Request validation failed",
                "validation_errors": errors,
                "correlation_id": corr_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler for unhandled exceptions."""
        corr_id = correlation_id_var.get("")

        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={
                "extra_data": {
                    "exception_type": type(exc).__name__,
                    "path": request.url.path,
                    "correlation_id": corr_id,
                }
            },
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "detail": "Internal server error",
                "correlation_id": corr_id,
            },
        )
