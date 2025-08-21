"""
WebSocket Manager for Real-Time Progress Updates
Task 19: Setup Real-Time Progress Updates with <1s latency
"""
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
from loguru import logger
import uuid


class ConnectionManager:
    """Manages WebSocket connections and broadcasts progress updates"""
    
    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Track subscriptions: task_id -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {}
        # Task progress cache
        self.task_progress: Dict[str, Dict[str, Any]] = {}
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        async with self.lock:
            self.active_connections[client_id] = websocket
            
        logger.info(f"WebSocket client {client_id} connected")
        
        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            client_id
        )
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Remove connection and clean up subscriptions"""
        async with self.lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                
            # Remove from all subscriptions
            for task_id, subscribers in self.subscriptions.items():
                subscribers.discard(client_id)
            
            # Clean up empty subscription sets
            self.subscriptions = {
                k: v for k, v in self.subscriptions.items() if v
            }
        
        logger.info(f"WebSocket client {client_id} disconnected")
    
    async def subscribe_to_task(self, client_id: str, task_id: str):
        """Subscribe client to task progress updates"""
        async with self.lock:
            if task_id not in self.subscriptions:
                self.subscriptions[task_id] = set()
            self.subscriptions[task_id].add(client_id)
        
        logger.debug(f"Client {client_id} subscribed to task {task_id}")
        
        # Send current progress if available
        if task_id in self.task_progress:
            await self.send_personal_message(
                self.task_progress[task_id],
                client_id
            )
    
    async def unsubscribe_from_task(self, client_id: str, task_id: str):
        """Unsubscribe client from task updates"""
        async with self.lock:
            if task_id in self.subscriptions:
                self.subscriptions[task_id].discard(client_id)
                if not self.subscriptions[task_id]:
                    del self.subscriptions[task_id]
        
        logger.debug(f"Client {client_id} unsubscribed from task {task_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast_task_progress(
        self,
        task_id: str,
        progress_type: str,
        data: Dict[str, Any]
    ):
        """Broadcast progress update to all subscribed clients"""
        message = {
            "type": "progress",
            "task_id": task_id,
            "progress_type": progress_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the progress
        async with self.lock:
            self.task_progress[task_id] = message
        
        # Get subscribers
        subscribers = self.subscriptions.get(task_id, set()).copy()
        
        # Send to all subscribers
        disconnected = []
        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)
    
    async def send_backtesting_progress(
        self,
        task_id: str,
        current_step: int,
        total_steps: int,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send backtesting progress update"""
        progress_data = {
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": round((current_step / total_steps * 100), 2) if total_steps > 0 else 0,
            "status": status,
            "details": details or {}
        }
        
        await self.broadcast_task_progress(
            task_id=task_id,
            progress_type="backtesting",
            data=progress_data
        )
    
    async def send_indicator_calculation_progress(
        self,
        task_id: str,
        indicator: str,
        symbol: str,
        percentage: float
    ):
        """Send indicator calculation progress"""
        progress_data = {
            "indicator": indicator,
            "symbol": symbol,
            "percentage": round(percentage, 2),
            "status": "calculating"
        }
        
        await self.broadcast_task_progress(
            task_id=task_id,
            progress_type="indicator_calculation",
            data=progress_data
        )
    
    async def send_validation_progress(
        self,
        task_id: str,
        validation_type: str,
        passed: bool,
        message: str,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Send validation progress update"""
        progress_data = {
            "validation_type": validation_type,
            "passed": passed,
            "message": message,
            "metrics": metrics or {}
        }
        
        await self.broadcast_task_progress(
            task_id=task_id,
            progress_type="validation",
            data=progress_data
        )
    
    async def send_completion_notification(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Send task completion notification"""
        message = {
            "type": "completion",
            "task_id": task_id,
            "success": success,
            "result": result,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Clear progress cache for completed task
        async with self.lock:
            if task_id in self.task_progress:
                del self.task_progress[task_id]
        
        # Get subscribers
        subscribers = self.subscriptions.get(task_id, set()).copy()
        
        # Send to all subscribers
        for client_id in subscribers:
            await self.send_personal_message(message, client_id)
        
        # Clean up subscriptions for completed task
        async with self.lock:
            if task_id in self.subscriptions:
                del self.subscriptions[task_id]
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming message from client"""
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            task_id = message.get("task_id")
            if task_id:
                await self.subscribe_to_task(client_id, task_id)
                await self.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    client_id
                )
        
        elif msg_type == "unsubscribe":
            task_id = message.get("task_id")
            if task_id:
                await self.unsubscribe_from_task(client_id, task_id)
                await self.send_personal_message(
                    {
                        "type": "unsubscription_confirmed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    client_id
                )
        
        elif msg_type == "ping":
            await self.send_personal_message(
                {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                },
                client_id
            )
        
        else:
            logger.warning(f"Unknown message type from {client_id}: {msg_type}")


# Global connection manager instance
manager = ConnectionManager()


def get_websocket_manager() -> ConnectionManager:
    """Get the global WebSocket manager instance"""
    return manager