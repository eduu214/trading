"""
Portfolio WebSocket Service
F003-US001 Task 5: Configure WebSocket Portfolio Updates for real-time P&L tracking

Handles:
- Real-time portfolio state updates
- P&L streaming with <30s latency  
- Portfolio optimization progress updates
- Rebalancing alerts and notifications
- Risk metric updates
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Set
from dataclasses import asdict

from app.services.websocket_manager import get_websocket_manager
from app.services.portfolio_state_manager import get_portfolio_state_manager, PortfolioState, PortfolioAllocation
from app.core.config import settings

logger = logging.getLogger(__name__)

class PortfolioWebSocketService:
    """Portfolio-specific WebSocket service for real-time updates"""
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.portfolio_manager = None
        self.active_subscriptions: Dict[str, Set[str]] = {}  # portfolio_id -> client_ids
        self.update_intervals = {
            'pnl': 5,      # P&L updates every 5 seconds
            'state': 10,   # Portfolio state every 10 seconds  
            'risk': 30,    # Risk metrics every 30 seconds
        }
        self.last_updates: Dict[str, datetime] = {}
        
    async def initialize(self):
        """Initialize portfolio state manager"""
        if not self.portfolio_manager:
            self.portfolio_manager = await get_portfolio_state_manager()
    
    async def subscribe_to_portfolio(self, client_id: str, portfolio_id: str = "main"):
        """Subscribe client to portfolio updates"""
        await self.initialize()
        
        if portfolio_id not in self.active_subscriptions:
            self.active_subscriptions[portfolio_id] = set()
        
        self.active_subscriptions[portfolio_id].add(client_id)
        logger.info(f"Client {client_id} subscribed to portfolio {portfolio_id}")
        
        # Send current portfolio state immediately
        await self._send_current_portfolio_state(client_id, portfolio_id)
        
        # Send current P&L if available
        await self._send_current_pnl(client_id, portfolio_id)
    
    async def unsubscribe_from_portfolio(self, client_id: str, portfolio_id: str = "main"):
        """Unsubscribe client from portfolio updates"""
        if portfolio_id in self.active_subscriptions:
            self.active_subscriptions[portfolio_id].discard(client_id)
            if not self.active_subscriptions[portfolio_id]:
                del self.active_subscriptions[portfolio_id]
        
        logger.info(f"Client {client_id} unsubscribed from portfolio {portfolio_id}")
    
    async def _send_current_portfolio_state(self, client_id: str, portfolio_id: str):
        """Send current portfolio state to client"""
        try:
            portfolio_state = await self.portfolio_manager.get_portfolio_state(portfolio_id)
            
            if portfolio_state:
                message = {
                    "type": "portfolio_state",
                    "portfolio_id": portfolio_id,
                    "data": self._serialize_portfolio_state(portfolio_state),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket_manager.send_personal_message(message, client_id)
            else:
                # Send empty portfolio state
                await self._send_empty_portfolio_state(client_id, portfolio_id)
                
        except Exception as e:
            logger.error(f"Error sending portfolio state to {client_id}: {e}")
    
    async def _send_current_pnl(self, client_id: str, portfolio_id: str):
        """Send current P&L data to client"""
        try:
            pnl_data = await self.portfolio_manager.get_real_time_pnl(portfolio_id)
            
            message = {
                "type": "portfolio_pnl",
                "portfolio_id": portfolio_id,
                "data": {
                    "strategy_pnl": {k: str(v) for k, v in pnl_data.items()},
                    "total_pnl": str(sum(pnl_data.values())),
                    "last_updated": datetime.utcnow().isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_personal_message(message, client_id)
            
        except Exception as e:
            logger.error(f"Error sending P&L to {client_id}: {e}")
    
    async def _send_empty_portfolio_state(self, client_id: str, portfolio_id: str):
        """Send empty portfolio state for new portfolios"""
        message = {
            "type": "portfolio_state",
            "portfolio_id": portfolio_id,
            "data": {
                "portfolio_id": portfolio_id,
                "status": "inactive",
                "total_value": "0.00",
                "total_pnl": "0.00",
                "cash_balance": "10000.00",  # Default starting balance
                "allocations": {},
                "last_updated": datetime.utcnow().isoformat(),
                "portfolio_volatility": None,
                "portfolio_sharpe": None,
                "max_drawdown": None,
                "var_1d_95": None,
                "pending_rebalance": False,
                "rebalance_reason": None,
                "target_allocations": None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.send_personal_message(message, client_id)
    
    def _serialize_portfolio_state(self, state: PortfolioState) -> Dict[str, Any]:
        """Convert PortfolioState to JSON-serializable dict"""
        return {
            "portfolio_id": state.portfolio_id,
            "status": state.status.value,
            "total_value": str(state.total_value),
            "total_pnl": str(state.total_pnl),
            "cash_balance": str(state.cash_balance),
            "allocations": {
                strategy_id: {
                    "strategy_id": alloc.strategy_id,
                    "current_weight": str(alloc.current_weight),
                    "target_weight": str(alloc.target_weight),
                    "market_value": str(alloc.market_value),
                    "unrealized_pnl": str(alloc.unrealized_pnl),
                    "last_updated": alloc.last_updated.isoformat(),
                    "drift_percentage": str(alloc.drift_percentage),
                    "allocation_status": alloc.allocation_status
                }
                for strategy_id, alloc in state.allocations.items()
            },
            "last_updated": state.last_updated.isoformat(),
            "portfolio_volatility": str(state.portfolio_volatility) if state.portfolio_volatility else None,
            "portfolio_sharpe": str(state.portfolio_sharpe) if state.portfolio_sharpe else None,
            "max_drawdown": str(state.max_drawdown) if state.max_drawdown else None,
            "var_1d_95": str(state.var_1d_95) if state.var_1d_95 else None,
            "pending_rebalance": state.pending_rebalance,
            "rebalance_reason": state.rebalance_reason,
            "target_allocations": {k: str(v) for k, v in state.target_allocations.items()} if state.target_allocations else None
        }
    
    async def broadcast_portfolio_update(self, portfolio_id: str, update_type: str, data: Dict[str, Any]):
        """Broadcast portfolio update to all subscribed clients"""
        if portfolio_id not in self.active_subscriptions:
            return
        
        message = {
            "type": f"portfolio_{update_type}",
            "portfolio_id": portfolio_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        subscribers = self.active_subscriptions[portfolio_id].copy()
        disconnected = []
        
        for client_id in subscribers:
            try:
                await self.websocket_manager.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.active_subscriptions[portfolio_id].discard(client_id)
    
    async def broadcast_pnl_update(self, portfolio_id: str, strategy_pnl: Dict[str, Decimal]):
        """Broadcast P&L update to subscribed clients"""
        await self.broadcast_portfolio_update(
            portfolio_id=portfolio_id,
            update_type="pnl",
            data={
                "strategy_pnl": {k: str(v) for k, v in strategy_pnl.items()},
                "total_pnl": str(sum(strategy_pnl.values())),
                "last_updated": datetime.utcnow().isoformat()
            }
        )
    
    async def broadcast_risk_update(self, portfolio_id: str, risk_metrics: Dict[str, Any]):
        """Broadcast risk metrics update"""
        await self.broadcast_portfolio_update(
            portfolio_id=portfolio_id,
            update_type="risk",
            data=risk_metrics
        )
    
    async def broadcast_rebalancing_alert(self, portfolio_id: str, rebalancing_data: Dict[str, Any]):
        """Broadcast rebalancing alert to subscribed clients"""
        message = {
            "type": "portfolio_rebalancing_alert",
            "portfolio_id": portfolio_id,
            "data": rebalancing_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        
        if portfolio_id not in self.active_subscriptions:
            return
        
        subscribers = self.active_subscriptions[portfolio_id].copy()
        
        for client_id in subscribers:
            try:
                await self.websocket_manager.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"Error sending rebalancing alert to {client_id}: {e}")
    
    async def send_optimization_progress(self, task_id: str, portfolio_id: str, progress: Dict[str, Any]):
        """Send portfolio optimization progress update"""
        message = {
            "type": "portfolio_optimization_progress",
            "task_id": task_id,
            "portfolio_id": portfolio_id,
            "data": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to task subscribers (via main WebSocket manager)
        await self.websocket_manager.broadcast_task_progress(
            task_id=task_id,
            progress_type="portfolio_optimization",
            data=progress
        )
        
        # Also send to portfolio subscribers
        if portfolio_id in self.active_subscriptions:
            subscribers = self.active_subscriptions[portfolio_id].copy()
            for client_id in subscribers:
                try:
                    await self.websocket_manager.send_personal_message(message, client_id)
                except Exception as e:
                    logger.error(f"Error sending optimization progress to {client_id}: {e}")
    
    async def handle_portfolio_message(self, client_id: str, message: Dict[str, Any]):
        """Handle portfolio-specific WebSocket messages"""
        msg_type = message.get("type")
        
        if msg_type == "subscribe_portfolio":
            portfolio_id = message.get("portfolio_id", "main")
            await self.subscribe_to_portfolio(client_id, portfolio_id)
            
        elif msg_type == "unsubscribe_portfolio":
            portfolio_id = message.get("portfolio_id", "main")
            await self.unsubscribe_from_portfolio(client_id, portfolio_id)
            
        elif msg_type == "request_portfolio_refresh":
            portfolio_id = message.get("portfolio_id", "main")
            await self._send_current_portfolio_state(client_id, portfolio_id)
            await self._send_current_pnl(client_id, portfolio_id)
            
        elif msg_type == "request_risk_metrics":
            portfolio_id = message.get("portfolio_id", "main")
            await self._send_risk_metrics(client_id, portfolio_id)
            
        else:
            logger.warning(f"Unknown portfolio message type from {client_id}: {msg_type}")
    
    async def _send_risk_metrics(self, client_id: str, portfolio_id: str):
        """Send cached risk metrics to client"""
        try:
            risk_metrics = await self.portfolio_manager.get_cached_risk_metrics(portfolio_id)
            
            if risk_metrics:
                message = {
                    "type": "portfolio_risk",
                    "portfolio_id": portfolio_id,
                    "data": risk_metrics,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket_manager.send_personal_message(message, client_id)
                
        except Exception as e:
            logger.error(f"Error sending risk metrics to {client_id}: {e}")
    
    async def cleanup_client(self, client_id: str):
        """Clean up client from all portfolio subscriptions"""
        for portfolio_id in list(self.active_subscriptions.keys()):
            self.active_subscriptions[portfolio_id].discard(client_id)
            if not self.active_subscriptions[portfolio_id]:
                del self.active_subscriptions[portfolio_id]

# Global portfolio WebSocket service instance
portfolio_ws_service = PortfolioWebSocketService()

async def get_portfolio_websocket_service() -> PortfolioWebSocketService:
    """Get the global portfolio WebSocket service instance"""
    await portfolio_ws_service.initialize()
    return portfolio_ws_service