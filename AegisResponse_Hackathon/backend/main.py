"""
Aegis Hospitality OS - FastAPI Entry Point
Sets up middleware, routes, services, and lifespan events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.logging_config import setup_logging, get_logger
from backend.middleware.audit_logger import AuditLogMiddleware
from backend.middleware.rate_limiter import RateLimiterMiddleware
from backend.middleware.error_handler import register_error_handlers
from backend.services.task_queue import task_queue
from backend.auth.jwt_validator import _fetch_jwks

# Routers
from backend.routes.health import router as health_router
from backend.routes.security import router as security_router
from backend.routes.operations import router as ops_router
from backend.routes.finance import router as finance_router

# Ensure structured logging is initialized immediately
setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown.
    Handles initializing background task queues and warming caches.
    """
    logger.info("Initializing AHOS Backend...")

    # Load Auth0 configuration validation
    errors = settings.validate()
    if errors:
        logger.error(f"Configuration errors found: {errors}")
        # Depending on strictness, we might raise SystemExit here
        # for Hackathon, just warn:
        logger.warning("Proceeding despite missing Auth0 config for development.")

    # Pre-fetch Auth0 JWKS in the background
    try:
        await _fetch_jwks()
        logger.info("Auth0 JWKS cache warmed up")
    except Exception as e:
        logger.error(f"Could not fetch JWKS on startup: {e}")

    # Start the orchestrator task queue
    task_queue.start()
    logger.info("Task Queue started")

    yield  # Application runs

    logger.info("Shutting down AHOS Backend...")
    # Clean shutdown of queues
    await task_queue.stop(wait_completion=True)
    logger.info("Task Queue stopped safely")


# Create FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Aegis Hospitality OS Core Orchestrator",
    lifespan=lifespan,
)

# Register Middleware (Execution order is bottom-to-top of this list)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon. Production should lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting Middleware
app.add_middleware(RateLimiterMiddleware)

# 3. Audit Logging Middleware (Top-level, runs first on incoming request)
app.add_middleware(AuditLogMiddleware)

# Register Global Error Handlers
register_error_handlers(app)

# Register API Routers
app.include_router(health_router)
app.include_router(security_router)
app.include_router(ops_router)
app.include_router(finance_router)


# Provide root endpoints to ease navigation
@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs_url": "/docs"}

