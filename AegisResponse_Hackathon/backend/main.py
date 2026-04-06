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

# Routers — Phase 3
from backend.routes.health import router as health_router
from backend.routes.security import router as security_router
from backend.routes.operations import router as ops_router
from backend.routes.finance import router as finance_router

# Router — Phase 5: External Integrations
from backend.routes.integrations import router as integrations_router

# Router — Phase 4: Hierarchical Agent System
from backend.routes.agents import router as agents_router

# Router — Phase 6: Human-in-the-Loop + Security
from backend.routes.hitl import router as hitl_router

# Router — Phase 8: Advanced Features
from backend.routes.advanced import router as advanced_router

# Ensure structured logging is initialized immediately
setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown.
    Handles initializing background task queues and warming caches.
    """
    logger.info("═" * 60)
    logger.info("🏨  AEGIS HOSPITALITY OS — Starting Up")
    logger.info("═" * 60)

    # Load Auth0 configuration validation
    errors = settings.validate()
    if errors:
        logger.error(f"Configuration errors found: {errors}")
        logger.warning("Proceeding despite missing Auth0 config for development.")

    # Pre-fetch Auth0 JWKS in the background
    try:
        await _fetch_jwks()
        logger.info("Auth0 JWKS cache warmed up")
    except Exception as e:
        logger.error(f"Could not fetch JWKS on startup: {e}")

    # Start the orchestrator task queue (Phase 3)
    task_queue.start()
    logger.info("Task Queue started")

    # ── Phase 5: Initialize External Integrations ──
    from backend.database.hotel_db import hotel_db
    logger.info(f"📦 Database initialized: {len(hotel_db.get_hotels())} hotels loaded")

    from backend.integrations.iot_service import iot_simulator
    logger.info(f"🏗️  IoT Simulator: {len(iot_simulator.devices)} devices across 3 hotels")

    from backend.integrations.gmail_service import gmail_service
    from backend.integrations.notion_service import notion_service
    from backend.integrations.twilio_service import twilio_service
    logger.info(f"📧 Gmail: {'configured' if gmail_service.is_configured else 'mock mode'}")
    logger.info(f"📋 Notion: {'configured' if notion_service.is_configured else 'mock mode'}")
    logger.info(f"📱 Twilio: {'configured' if twilio_service.is_configured else 'mock mode'}")

    # ── Phase 4: Initialize Agent System ──
    from backend.agents.registry import agent_registry
    agents = agent_registry.list_agents()
    logger.info(f"🧠 Agent System: {len(agents)} agents initialized (brain: {agent_registry.get_brain_info().get('provider', 'unknown')})")

    logger.info("═" * 60)
    logger.info("🚀  AHOS Phase 3+4+5 — All Systems READY")
    logger.info("═" * 60)

    yield  # Application runs

    logger.info("🛑 Shutting down AHOS Backend...")
    # Clean shutdown of queues
    await task_queue.stop(wait_completion=True)
    logger.info("Task Queue stopped safely")


# Create FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Aegis Hospitality OS — Research-Grade Multi-Agent Hotel Chain Operating System\n\n"
        "**Phase 3**: Core Backend (Auth, Middleware, Orchestrator)\n"
        "**Phase 4**: Hierarchical Agent System (Executive → Domain → Sub-Agents, Pluggable LLM Brain)\n"
        "**Phase 5**: External Integrations (Gmail, Notion, Twilio, IoT, DB, Gateway, Monitoring)\n"
        "**Phase 6**: Human-in-the-Loop + Security (Approvals, Consent Logs, Anomaly Detection, Attack Sim)"
    ),
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

# Register API Routers — Phase 3
app.include_router(health_router)
app.include_router(security_router)
app.include_router(ops_router)
app.include_router(finance_router)

# Register API Router — Phase 5: External Integrations
app.include_router(integrations_router, prefix="/api/v1")

# Register API Router — Phase 4: Hierarchical Agent System
app.include_router(agents_router, prefix="/api/v1")

# Register API Router — Phase 6: Human-in-the-Loop + Security
app.include_router(hitl_router)

# Register API Router — Phase 8: Advanced Features
app.include_router(advanced_router)


# Provide root endpoints to ease navigation
@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs_url": "/docs"}

