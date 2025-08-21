"""
Portfolio State Manager Service
F003-US001 Task 3: Redis-based real-time portfolio state management

Handles:
- Real-time portfolio allocation state
- Current P&L tracking  
- Pending rebalancing decisions
- Portfolio risk metrics caching
- Sub-second latency requirements
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Set
import redis.asyncio as redis
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class PortfolioStatus(Enum):
    ACTIVE = "active"
    REBALANCING = "rebalancing"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class PortfolioAllocation:
    """Portfolio allocation state"""
    strategy_id: str
    current_weight: Decimal
    target_weight: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    last_updated: datetime
    drift_percentage: Decimal = Decimal('0')
    allocation_status: str = "active"

@dataclass
class PortfolioState:
    """Complete portfolio state snapshot"""
    portfolio_id: str
    status: PortfolioStatus
    total_value: Decimal
    total_pnl: Decimal
    cash_balance: Decimal
    allocations: Dict[str, PortfolioAllocation]
    last_updated: datetime
    
    # Risk metrics
    portfolio_volatility: Optional[Decimal] = None
    portfolio_sharpe: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    var_1d_95: Optional[Decimal] = None
    
    # Rebalancing state
    pending_rebalance: bool = False
    rebalance_reason: Optional[str] = None
    target_allocations: Optional[Dict[str, Decimal]] = None

@dataclass
class RebalancingDecision:
    """Pending rebalancing decision"""
    decision_id: str
    trigger_type: str
    trigger_timestamp: datetime
    current_allocations: Dict[str, Decimal]
    target_allocations: Dict[str, Decimal]
    expected_return_change: Optional[Decimal] = None
    expected_risk_change: Optional[Decimal] = None
    approved: bool = False
    approved_by: Optional[str] = None

class PortfolioStateManager:
    """Redis-based portfolio state management with sub-second latency"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.portfolio_prefix = "portfolio:"
        self.allocation_prefix = "allocation:"
        self.pnl_prefix = "pnl:"
        self.rebalance_prefix = "rebalance:"
        self.risk_prefix = "risk:"
        
        # Cache TTL settings
        self.state_ttl = 300  # 5 minutes for portfolio state
        self.pnl_ttl = 60     # 1 minute for P&L data
        self.risk_ttl = 900   # 15 minutes for risk metrics
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis_client.ping()
            logger.info("Portfolio state manager connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_portfolio_state(self, portfolio_id: str = "main") -> Optional[PortfolioState]:
        """Get current portfolio state with sub-second latency"""
        try:
            key = f"{self.portfolio_prefix}{portfolio_id}"
            data = await self.redis_client.get(key)
            
            if not data:
                return None
                
            state_dict = json.loads(data)
            
            # Reconstruct PortfolioState object
            allocations = {}
            for strategy_id, alloc_data in state_dict.get("allocations", {}).items():
                allocations[strategy_id] = PortfolioAllocation(
                    strategy_id=alloc_data["strategy_id"],
                    current_weight=Decimal(alloc_data["current_weight"]),
                    target_weight=Decimal(alloc_data["target_weight"]),
                    market_value=Decimal(alloc_data["market_value"]),
                    unrealized_pnl=Decimal(alloc_data["unrealized_pnl"]),
                    last_updated=datetime.fromisoformat(alloc_data["last_updated"]),
                    drift_percentage=Decimal(alloc_data.get("drift_percentage", "0")),
                    allocation_status=alloc_data.get("allocation_status", "active")
                )
            
            portfolio_state = PortfolioState(
                portfolio_id=state_dict["portfolio_id"],
                status=PortfolioStatus(state_dict["status"]),
                total_value=Decimal(state_dict["total_value"]),
                total_pnl=Decimal(state_dict["total_pnl"]),
                cash_balance=Decimal(state_dict["cash_balance"]),
                allocations=allocations,
                last_updated=datetime.fromisoformat(state_dict["last_updated"]),
                portfolio_volatility=Decimal(state_dict["portfolio_volatility"]) if state_dict.get("portfolio_volatility") else None,
                portfolio_sharpe=Decimal(state_dict["portfolio_sharpe"]) if state_dict.get("portfolio_sharpe") else None,
                max_drawdown=Decimal(state_dict["max_drawdown"]) if state_dict.get("max_drawdown") else None,
                var_1d_95=Decimal(state_dict["var_1d_95"]) if state_dict.get("var_1d_95") else None,
                pending_rebalance=state_dict.get("pending_rebalance", False),
                rebalance_reason=state_dict.get("rebalance_reason"),
                target_allocations={k: Decimal(v) for k, v in state_dict.get("target_allocations", {}).items()} if state_dict.get("target_allocations") else None
            )
            
            return portfolio_state
            
        except Exception as e:
            logger.error(f"Error getting portfolio state for {portfolio_id}: {e}")
            return None
    
    async def update_portfolio_state(self, state: PortfolioState) -> bool:
        """Update portfolio state in Redis with sub-second latency"""
        try:
            # Convert to serializable format
            state_dict = {
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
            
            key = f"{self.portfolio_prefix}{state.portfolio_id}"
            await self.redis_client.setex(
                key, 
                self.state_ttl, 
                json.dumps(state_dict, default=str)
            )
            
            logger.debug(f"Updated portfolio state for {state.portfolio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating portfolio state: {e}")
            return False
    
    async def update_strategy_allocation(self, portfolio_id: str, allocation: PortfolioAllocation) -> bool:
        """Update individual strategy allocation"""
        try:
            # Update in main portfolio state
            state = await self.get_portfolio_state(portfolio_id)
            if state:
                state.allocations[allocation.strategy_id] = allocation
                state.last_updated = datetime.utcnow()
                return await self.update_portfolio_state(state)
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating strategy allocation: {e}")
            return False
    
    async def get_real_time_pnl(self, portfolio_id: str = "main") -> Dict[str, Decimal]:
        """Get real-time P&L by strategy"""
        try:
            key = f"{self.pnl_prefix}{portfolio_id}"
            data = await self.redis_client.hgetall(key)
            
            if not data:
                return {}
                
            return {strategy_id: Decimal(pnl) for strategy_id, pnl in data.items()}
            
        except Exception as e:
            logger.error(f"Error getting real-time P&L: {e}")
            return {}
    
    async def update_strategy_pnl(self, portfolio_id: str, strategy_id: str, unrealized_pnl: Decimal, realized_pnl: Decimal) -> bool:
        """Update strategy P&L with sub-second latency"""
        try:
            pnl_key = f"{self.pnl_prefix}{portfolio_id}"
            
            # Store both unrealized and realized P&L
            pnl_data = {
                f"{strategy_id}:unrealized": str(unrealized_pnl),
                f"{strategy_id}:realized": str(realized_pnl),
                f"{strategy_id}:total": str(unrealized_pnl + realized_pnl),
                f"{strategy_id}:updated_at": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.hmset(pnl_key, pnl_data)
            await self.redis_client.expire(pnl_key, self.pnl_ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating strategy P&L: {e}")
            return False
    
    async def get_pending_rebalancing_decisions(self, portfolio_id: str = "main") -> List[RebalancingDecision]:
        """Get pending rebalancing decisions"""
        try:
            key = f"{self.rebalance_prefix}{portfolio_id}:pending"
            decision_ids = await self.redis_client.smembers(key)
            
            decisions = []
            for decision_id in decision_ids:
                decision_key = f"{self.rebalance_prefix}{portfolio_id}:decision:{decision_id}"
                data = await self.redis_client.get(decision_key)
                
                if data:
                    decision_dict = json.loads(data)
                    decision = RebalancingDecision(
                        decision_id=decision_dict["decision_id"],
                        trigger_type=decision_dict["trigger_type"],
                        trigger_timestamp=datetime.fromisoformat(decision_dict["trigger_timestamp"]),
                        current_allocations={k: Decimal(v) for k, v in decision_dict["current_allocations"].items()},
                        target_allocations={k: Decimal(v) for k, v in decision_dict["target_allocations"].items()},
                        expected_return_change=Decimal(decision_dict["expected_return_change"]) if decision_dict.get("expected_return_change") else None,
                        expected_risk_change=Decimal(decision_dict["expected_risk_change"]) if decision_dict.get("expected_risk_change") else None,
                        approved=decision_dict.get("approved", False),
                        approved_by=decision_dict.get("approved_by")
                    )
                    decisions.append(decision)
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error getting pending rebalancing decisions: {e}")
            return []
    
    async def add_rebalancing_decision(self, portfolio_id: str, decision: RebalancingDecision) -> bool:
        """Add new rebalancing decision"""
        try:
            decision_dict = {
                "decision_id": decision.decision_id,
                "trigger_type": decision.trigger_type,
                "trigger_timestamp": decision.trigger_timestamp.isoformat(),
                "current_allocations": {k: str(v) for k, v in decision.current_allocations.items()},
                "target_allocations": {k: str(v) for k, v in decision.target_allocations.items()},
                "expected_return_change": str(decision.expected_return_change) if decision.expected_return_change else None,
                "expected_risk_change": str(decision.expected_risk_change) if decision.expected_risk_change else None,
                "approved": decision.approved,
                "approved_by": decision.approved_by
            }
            
            # Store decision
            decision_key = f"{self.rebalance_prefix}{portfolio_id}:decision:{decision.decision_id}"
            await self.redis_client.setex(decision_key, 3600, json.dumps(decision_dict))  # 1 hour TTL
            
            # Add to pending set
            pending_key = f"{self.rebalance_prefix}{portfolio_id}:pending"
            await self.redis_client.sadd(pending_key, decision.decision_id)
            await self.redis_client.expire(pending_key, 3600)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding rebalancing decision: {e}")
            return False
    
    async def approve_rebalancing_decision(self, portfolio_id: str, decision_id: str, approved_by: str) -> bool:
        """Approve a rebalancing decision"""
        try:
            decision_key = f"{self.rebalance_prefix}{portfolio_id}:decision:{decision_id}"
            data = await self.redis_client.get(decision_key)
            
            if data:
                decision_dict = json.loads(data)
                decision_dict["approved"] = True
                decision_dict["approved_by"] = approved_by
                decision_dict["approved_at"] = datetime.utcnow().isoformat()
                
                await self.redis_client.setex(decision_key, 3600, json.dumps(decision_dict))
                
                # Remove from pending
                pending_key = f"{self.rebalance_prefix}{portfolio_id}:pending"
                await self.redis_client.srem(pending_key, decision_id)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error approving rebalancing decision: {e}")
            return False
    
    async def cache_portfolio_risk_metrics(self, portfolio_id: str, risk_metrics: Dict[str, Any]) -> bool:
        """Cache portfolio risk metrics"""
        try:
            key = f"{self.risk_prefix}{portfolio_id}"
            
            # Convert Decimal values to strings for JSON serialization
            serializable_metrics = {}
            for metric_name, value in risk_metrics.items():
                if isinstance(value, Decimal):
                    serializable_metrics[metric_name] = str(value)
                else:
                    serializable_metrics[metric_name] = value
            
            serializable_metrics["calculated_at"] = datetime.utcnow().isoformat()
            
            await self.redis_client.setex(
                key, 
                self.risk_ttl, 
                json.dumps(serializable_metrics)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching risk metrics: {e}")
            return False
    
    async def get_cached_risk_metrics(self, portfolio_id: str = "main") -> Optional[Dict[str, Any]]:
        """Get cached portfolio risk metrics"""
        try:
            key = f"{self.risk_prefix}{portfolio_id}"
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached risk metrics: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connection and performance"""
        try:
            start_time = datetime.utcnow()
            await self.redis_client.ping()
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
            
            info = await self.redis_client.info()
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "redis_version": info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_rebalancing_needed(self, portfolio_id: str, drift_threshold: float = 0.05) -> bool:
        """
        Check if portfolio needs rebalancing based on drift threshold
        
        Args:
            portfolio_id: Portfolio identifier
            drift_threshold: Maximum allowed drift from target allocation (default 5%)
            
        Returns:
            True if rebalancing is needed
        """
        try:
            portfolio_state = await self.get_portfolio_state(portfolio_id)
            if not portfolio_state:
                return False
            
            needs_rebalancing = False
            for strategy_id, allocation in portfolio_state.allocations.items():
                drift = abs(float(allocation.current_weight - allocation.target_weight))
                if drift > drift_threshold:
                    needs_rebalancing = True
                    allocation.drift_percentage = Decimal(str(drift))
                    allocation.allocation_status = "rebalance_needed"
                    logger.info(f"Strategy {strategy_id} drift: {drift:.2%} exceeds threshold {drift_threshold:.2%}")
            
            if needs_rebalancing:
                portfolio_state.pending_rebalance = True
                portfolio_state.rebalance_reason = f"Portfolio drift exceeds {drift_threshold:.0%} threshold"
                await self.update_portfolio_state(portfolio_state)
                
            return needs_rebalancing
            
        except Exception as e:
            logger.error(f"Error checking rebalancing for portfolio {portfolio_id}: {e}")
            return False
    
    async def get_real_time_pnl(self, portfolio_id: str) -> Dict[str, Decimal]:
        """Get real-time P&L for all strategies in portfolio"""
        try:
            portfolio_state = await self.get_portfolio_state(portfolio_id)
            if not portfolio_state:
                return {}
            
            pnl_data = {}
            for strategy_id, allocation in portfolio_state.allocations.items():
                pnl_data[strategy_id] = allocation.unrealized_pnl
            
            return pnl_data
            
        except Exception as e:
            logger.error(f"Error getting real-time P&L: {e}")
            return {}

# Global instance
portfolio_state_manager = PortfolioStateManager()

async def get_portfolio_state_manager() -> PortfolioStateManager:
    """Get the global portfolio state manager instance"""
    if not portfolio_state_manager.redis_client:
        await portfolio_state_manager.connect()
    return portfolio_state_manager