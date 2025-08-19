from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AlphaStrat Trading Platform...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Starting without database - some features may not work")
    yield
    logger.info("Shutting down AlphaStrat Trading Platform...")


app = FastAPI(
    title="AlphaStrat Trading Platform",
    description="AI-powered trading strategy discovery and validation system",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "AlphaStrat Trading Platform API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "operational",
            "redis": "operational"
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()