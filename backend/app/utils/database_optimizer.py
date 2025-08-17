"""
Database query optimization and performance utilities
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import text, select, func, and_, or_, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy.sql import Select
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def add_pagination(query: Select, page: int = 1, page_size: int = 20) -> Select:
        """Add efficient pagination to query"""
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
    
    @staticmethod
    def add_time_range_filter(query: Select, 
                            time_column, 
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Select:
        """Add optimized time range filtering"""
        if start_time:
            query = query.where(time_column >= start_time)
        if end_time:
            query = query.where(time_column <= end_time)
        return query
    
    @staticmethod
    def add_bulk_filter(query: Select, column, values: List[Any]) -> Select:
        """Add efficient bulk filtering using IN clause"""
        if not values:
            return query
        
        # Split large IN clauses to avoid database limits
        if len(values) > 1000:
            # Use OR with multiple IN clauses for very large lists
            conditions = []
            for i in range(0, len(values), 1000):
                chunk = values[i:i+1000]
                conditions.append(column.in_(chunk))
            return query.where(or_(*conditions))
        else:
            return query.where(column.in_(values))

class ConnectionPoolManager:
    """Manage database connection pools for optimal performance"""
    
    def __init__(self, engine):
        self.engine = engine
        self.pool_stats = {
            "active_connections": 0,
            "total_queries": 0,
            "avg_query_time": 0,
            "slow_queries": 0
        }
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with performance tracking"""
        start_time = time.time()
        
        async with AsyncSession(self.engine) as session:
            self.pool_stats["active_connections"] += 1
            try:
                yield session
            finally:
                query_time = time.time() - start_time
                self.pool_stats["active_connections"] -= 1
                self.pool_stats["total_queries"] += 1
                
                # Update average query time
                current_avg = self.pool_stats["avg_query_time"]
                total_queries = self.pool_stats["total_queries"]
                self.pool_stats["avg_query_time"] = (
                    (current_avg * (total_queries - 1) + query_time) / total_queries
                )
                
                # Track slow queries (>1 second)
                if query_time > 1.0:
                    self.pool_stats["slow_queries"] += 1
                    logger.warning(f"Slow query detected: {query_time:.2f}s")
    
    def get_pool_stats(self) -> Dict:
        """Get connection pool statistics"""
        return self.pool_stats.copy()

class OpportunityQueryOptimizer:
    """Optimized queries for opportunity data"""
    
    def __init__(self, session_manager: ConnectionPoolManager):
        self.session_manager = session_manager
    
    async def get_recent_opportunities(self, 
                                     limit: int = 100,
                                     min_score: float = 0.7,
                                     asset_classes: List[str] = None) -> List[Dict]:
        """Get recent opportunities with optimized query"""
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            # Build optimized query
            query = select(Opportunity).order_by(Opportunity.discovered_at.desc())
            
            # Add filters
            if min_score > 0:
                query = query.where(Opportunity.inefficiency_score >= min_score)
            
            if asset_classes:
                query = QueryOptimizer.add_bulk_filter(query, Opportunity.asset_class, asset_classes)
            
            # Add pagination
            query = query.limit(limit)
            
            # Execute with timing
            start_time = time.time()
            result = await session.execute(query)
            opportunities = result.scalars().all()
            
            query_time = time.time() - start_time
            logger.debug(f"Retrieved {len(opportunities)} opportunities in {query_time:.3f}s")
            
            return [opp.to_dict() for opp in opportunities]
    
    async def get_opportunities_by_timeframe(self,
                                           start_time: datetime,
                                           end_time: datetime,
                                           page: int = 1,
                                           page_size: int = 50) -> Tuple[List[Dict], int]:
        """Get opportunities within timeframe with pagination"""
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            # Base query
            base_query = select(Opportunity)
            base_query = QueryOptimizer.add_time_range_filter(
                base_query, Opportunity.discovered_at, start_time, end_time
            )
            
            # Get total count (for pagination info)
            count_query = select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.discovered_at >= start_time,
                    Opportunity.discovered_at <= end_time
                )
            )
            
            # Add ordering and pagination
            query = base_query.order_by(Opportunity.discovered_at.desc())
            query = QueryOptimizer.add_pagination(query, page, page_size)
            
            # Execute both queries concurrently
            results = await asyncio.gather(
                session.execute(query),
                session.execute(count_query)
            )
            
            opportunities = results[0].scalars().all()
            total_count = results[1].scalar()
            
            return [opp.to_dict() for opp in opportunities], total_count
    
    async def get_top_opportunities_by_asset_class(self, 
                                                  asset_class: str,
                                                  limit: int = 20) -> List[Dict]:
        """Get top opportunities for specific asset class"""
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            query = select(Opportunity).where(
                Opportunity.asset_class == asset_class
            ).order_by(
                Opportunity.inefficiency_score.desc(),
                Opportunity.signal_strength.desc()
            ).limit(limit)
            
            result = await session.execute(query)
            opportunities = result.scalars().all()
            
            return [opp.to_dict() for opp in opportunities]

class ScanResultQueryOptimizer:
    """Optimized queries for scan results"""
    
    def __init__(self, session_manager: ConnectionPoolManager):
        self.session_manager = session_manager
    
    async def get_scan_history(self, 
                              limit: int = 50,
                              include_results: bool = False) -> List[Dict]:
        """Get scan history with optional result details"""
        async with self.session_manager.get_session() as session:
            from app.models.scan_result import ScanResult
            
            query = select(ScanResult).order_by(ScanResult.created_at.desc()).limit(limit)
            
            if include_results:
                # Use joinedload for eager loading of related data
                query = query.options(joinedload(ScanResult.opportunities))
            
            result = await session.execute(query)
            scans = result.scalars().unique().all()  # unique() for joinedload
            
            return [scan.to_dict(include_opportunities=include_results) for scan in scans]
    
    async def get_scan_performance_stats(self, days: int = 30) -> Dict:
        """Get scan performance statistics"""
        async with self.session_manager.get_session() as session:
            from app.models.scan_result import ScanResult
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Build comprehensive stats query
            stats_query = select(
                func.count(ScanResult.id).label('total_scans'),
                func.avg(ScanResult.duration_seconds).label('avg_duration'),
                func.max(ScanResult.duration_seconds).label('max_duration'),
                func.min(ScanResult.duration_seconds).label('min_duration'),
                func.sum(ScanResult.opportunities_found).label('total_opportunities'),
                func.avg(ScanResult.opportunities_found).label('avg_opportunities_per_scan')
            ).where(ScanResult.created_at >= start_date)
            
            result = await session.execute(stats_query)
            stats = result.first()
            
            return {
                'total_scans': stats.total_scans or 0,
                'avg_duration_seconds': float(stats.avg_duration or 0),
                'max_duration_seconds': float(stats.max_duration or 0),
                'min_duration_seconds': float(stats.min_duration or 0),
                'total_opportunities_found': stats.total_opportunities or 0,
                'avg_opportunities_per_scan': float(stats.avg_opportunities_per_scan or 0),
                'period_days': days
            }

class BatchProcessor:
    """Efficient batch processing for database operations"""
    
    def __init__(self, session_manager: ConnectionPoolManager, batch_size: int = 1000):
        self.session_manager = session_manager
        self.batch_size = batch_size
    
    async def batch_insert_opportunities(self, opportunities_data: List[Dict]) -> int:
        """Batch insert opportunities for better performance"""
        if not opportunities_data:
            return 0
        
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            inserted_count = 0
            
            # Process in batches
            for i in range(0, len(opportunities_data), self.batch_size):
                batch = opportunities_data[i:i + self.batch_size]
                
                # Create opportunity objects
                opportunities = [Opportunity(**data) for data in batch]
                
                # Batch insert
                session.add_all(opportunities)
                
                try:
                    await session.commit()
                    inserted_count += len(batch)
                    logger.debug(f"Inserted batch of {len(batch)} opportunities")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Batch insert failed: {e}")
                    
                    # Try individual inserts for this batch
                    for opp_data in batch:
                        try:
                            opp = Opportunity(**opp_data)
                            session.add(opp)
                            await session.commit()
                            inserted_count += 1
                        except Exception as individual_error:
                            await session.rollback()
                            logger.error(f"Individual insert failed: {individual_error}")
            
            return inserted_count
    
    async def batch_update_opportunities(self, updates: List[Tuple[int, Dict]]) -> int:
        """Batch update opportunities"""
        if not updates:
            return 0
        
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            updated_count = 0
            
            # Process in batches
            for i in range(0, len(updates), self.batch_size):
                batch = updates[i:i + self.batch_size]
                
                try:
                    # Build bulk update
                    for opportunity_id, update_data in batch:
                        await session.execute(
                            text("UPDATE opportunities SET {} WHERE id = :id").format(
                                ", ".join(f"{k} = :{k}" for k in update_data.keys())
                            ),
                            {"id": opportunity_id, **update_data}
                        )
                    
                    await session.commit()
                    updated_count += len(batch)
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Batch update failed: {e}")
            
            return updated_count
    
    async def cleanup_old_opportunities(self, days_to_keep: int = 30) -> int:
        """Clean up old opportunities to maintain performance"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        async with self.session_manager.get_session() as session:
            from app.models.opportunity import Opportunity
            
            # Count before deletion
            count_query = select(func.count(Opportunity.id)).where(
                Opportunity.discovered_at < cutoff_date
            )
            count_result = await session.execute(count_query)
            old_count = count_result.scalar()
            
            if old_count == 0:
                return 0
            
            # Delete in batches to avoid long locks
            deleted_total = 0
            while True:
                delete_query = select(Opportunity.id).where(
                    Opportunity.discovered_at < cutoff_date
                ).limit(self.batch_size)
                
                result = await session.execute(delete_query)
                ids_to_delete = [row[0] for row in result.fetchall()]
                
                if not ids_to_delete:
                    break
                
                # Delete batch
                await session.execute(
                    text("DELETE FROM opportunities WHERE id = ANY(:ids)"),
                    {"ids": ids_to_delete}
                )
                await session.commit()
                
                deleted_total += len(ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} old opportunities")
            
            return deleted_total

class DatabasePerformanceMonitor:
    """Monitor database performance metrics"""
    
    def __init__(self, session_manager: ConnectionPoolManager):
        self.session_manager = session_manager
        self.metrics = {
            "slow_queries": [],
            "connection_usage": [],
            "query_patterns": {}
        }
    
    async def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        async with self.session_manager.get_session() as session:
            # Get basic database stats
            stats_queries = {
                "opportunities_count": "SELECT COUNT(*) FROM opportunities",
                "scan_results_count": "SELECT COUNT(*) FROM scan_results", 
                "strategies_count": "SELECT COUNT(*) FROM strategies",
                "database_size": """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """,
                "table_sizes": """
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                """
            }
            
            results = {}
            for name, query in stats_queries.items():
                try:
                    result = await session.execute(text(query))
                    if name == "table_sizes":
                        results[name] = [dict(row._mapping) for row in result.fetchall()]
                    else:
                        results[name] = result.scalar()
                except Exception as e:
                    logger.error(f"Failed to get {name}: {e}")
                    results[name] = "Error"
            
            # Add connection pool stats
            results["connection_pool"] = self.session_manager.get_pool_stats()
            
            return results
    
    async def analyze_query_performance(self) -> Dict:
        """Analyze query performance patterns"""
        async with self.session_manager.get_session() as session:
            # Get slow query stats from PostgreSQL
            slow_queries_query = """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE mean_time > 100 
                ORDER BY mean_time DESC 
                LIMIT 10
            """
            
            try:
                result = await session.execute(text(slow_queries_query))
                slow_queries = [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                logger.warning(f"Could not get pg_stat_statements data: {e}")
                slow_queries = []
            
            return {
                "slow_queries": slow_queries,
                "recommendations": self._generate_performance_recommendations(slow_queries)
            }
    
    def _generate_performance_recommendations(self, slow_queries: List[Dict]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        if not slow_queries:
            recommendations.append("Query performance looks good!")
            return recommendations
        
        for query_info in slow_queries:
            if query_info.get("mean_time", 0) > 1000:  # > 1 second
                recommendations.append(
                    f"Consider adding indexes for queries with mean time > 1s"
                )
                break
        
        if len(slow_queries) > 5:
            recommendations.append(
                "Multiple slow queries detected - consider query optimization review"
            )
        
        recommendations.extend([
            "Consider connection pooling if not already enabled",
            "Regular VACUUM and ANALYZE for PostgreSQL maintenance",
            "Monitor table sizes and archive old data if needed"
        ])
        
        return recommendations

# Global instances will be initialized with actual database engine
pool_manager = None
opportunity_optimizer = None
scan_optimizer = None
batch_processor = None
performance_monitor = None

def initialize_optimizers(engine):
    """Initialize optimizer instances with database engine"""
    global pool_manager, opportunity_optimizer, scan_optimizer, batch_processor, performance_monitor
    
    pool_manager = ConnectionPoolManager(engine)
    opportunity_optimizer = OpportunityQueryOptimizer(pool_manager)
    scan_optimizer = ScanResultQueryOptimizer(pool_manager)
    batch_processor = BatchProcessor(pool_manager)
    performance_monitor = DatabasePerformanceMonitor(pool_manager)