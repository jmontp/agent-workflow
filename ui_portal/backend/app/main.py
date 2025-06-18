"""
Main FastAPI application for the UI Portal Backend
"""

import logging
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import uvicorn

# Add project paths to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent.parent / "lib"))
sys.path.insert(0, str(current_dir.parent.parent / "scripts"))

from config import settings
from services.orchestrator_service import OrchestratorService
from services.websocket_service import WebSocketService
from middleware.auth import AuthMiddleware
from middleware.rate_limiter import RateLimitMiddleware
from middleware.logging import LoggingMiddleware
from routers import auth, projects, commands, config_router, status, websocket


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        *([logging.FileHandler(settings.log_file)] if settings.log_file else [])
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting UI Portal Backend...")
    
    # Initialize services
    try:
        # Initialize orchestrator service
        orchestrator_service = OrchestratorService()
        await orchestrator_service.initialize()
        app.state.orchestrator_service = orchestrator_service
        
        # Initialize WebSocket service
        websocket_service = WebSocketService()
        await websocket_service.initialize()
        app.state.websocket_service = websocket_service
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down UI Portal Backend...")
    
    try:
        if hasattr(app.state, 'orchestrator_service'):
            await app.state.orchestrator_service.shutdown()
        
        if hasattr(app.state, 'websocket_service'):
            await app.state.websocket_service.shutdown()
            
        logger.info("All services shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for the AI Agent TDD-Scrum Workflow UI Portal",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure based on deployment
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with enhanced error information"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": f"error_{hash(str(exc)) % 10000:04d}",
            "message": "An unexpected error occurred. Please contact support if the issue persists."
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(commands.router, prefix="/api/commands", tags=["Commands"])
app.include_router(config_router.router, prefix="/api/config", tags=["Configuration"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"  # Replace with actual timestamp
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Agent TDD-Scrum Workflow UI Portal Backend",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None,
        "health_url": "/health",
        "api_prefix": "/api"
    }


# Dependency to get orchestrator service
def get_orchestrator_service(request: Request) -> OrchestratorService:
    """Get orchestrator service from application state"""
    if not hasattr(request.app.state, 'orchestrator_service'):
        raise HTTPException(
            status_code=503,
            detail="Orchestrator service not available"
        )
    return request.app.state.orchestrator_service


# Dependency to get WebSocket service
def get_websocket_service(request: Request) -> WebSocketService:
    """Get WebSocket service from application state"""
    if not hasattr(request.app.state, 'websocket_service'):
        raise HTTPException(
            status_code=503,
            detail="WebSocket service not available"
        )
    return request.app.state.websocket_service


# Export dependencies for use in routers
app.dependency_overrides[OrchestratorService] = get_orchestrator_service
app.dependency_overrides[WebSocketService] = get_websocket_service


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )