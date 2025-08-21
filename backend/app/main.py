from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.services.websocket_manager import get_websocket_manager
from app.services.portfolio_websocket import get_portfolio_websocket_service

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
    """WebSocket endpoint for real-time progress updates and portfolio streaming"""
    manager = get_websocket_manager()
    portfolio_service = await get_portfolio_websocket_service()
    client_id = None
    
    try:
        # Connect client
        client_id = await manager.connect(websocket)
        
        # Handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Parse JSON message
            try:
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                # Route portfolio-specific messages
                if msg_type.startswith("portfolio_") or msg_type in [
                    "subscribe_portfolio", "unsubscribe_portfolio", 
                    "request_portfolio_refresh", "request_risk_metrics"
                ]:
                    await portfolio_service.handle_portfolio_message(client_id, message)
                else:
                    # Handle general WebSocket messages
                    await manager.handle_client_message(client_id, message)
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
    except WebSocketDisconnect:
        if client_id:
            await manager.disconnect(client_id)
            await portfolio_service.cleanup_client(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if client_id:
            await manager.disconnect(client_id)
            await portfolio_service.cleanup_client(client_id)