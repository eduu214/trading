"""
Correlation Calculation Engine
F001-US003 Task 2: Pandas-based correlation calculations from strategy returns

Handles:
- Strategy return correlation calculations
- Matrix generation for 50+ strategies
- 15-minute update cycle performance
- Multiple correlation methods (Pearson, Spearman, Kendall)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
import json
import hashlib

from app.models.strategy_correlation import (
    StrategyCorrelation, CorrelationMatrix, 
    DiversificationScore, StrategyCluster, CorrelationAlert
)
from app.core.database import get_db

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Engine for calculating and managing strategy correlations"""
    
    def __init__(self):
        self.min_sample_size = 30  # Minimum data points for correlation
        self.correlation_methods = ['pearson', 'spearman', 'kendall']
        self.time_periods = ['30d', '60d', '90d', '1y']
        self.high_correlation_threshold = 0.6
        self.very_high_correlation_threshold = 0.8
        self.cache_ttl = 900  # 15 minutes
        
    def calculate_correlation_matrix(
        self, 
        returns_df: pd.DataFrame,
        method: str = 'pearson',
        min_periods: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix from returns DataFrame
        
        Args:
            returns_df: DataFrame with strategies as columns, dates as index
            method: Correlation method ('pearson', 'spearman', 'kendall')
            min_periods: Minimum number of observations required per pair
            
        Returns:
            Correlation matrix DataFrame
        """
        try:
            if returns_df.empty or len(returns_df.columns) < 2:
                logger.warning("Insufficient data for correlation calculation")
                return pd.DataFrame()
            
            # Set default min_periods if not provided
            if min_periods is None:
                min_periods = max(self.min_sample_size, len(returns_df) // 4)
            
            # Calculate correlation matrix
            if method == 'pearson':
                corr_matrix = returns_df.corr(method='pearson', min_periods=min_periods)
            elif method == 'spearman':
                corr_matrix = returns_df.corr(method='spearman', min_periods=min_periods)
            elif method == 'kendall':
                corr_matrix = returns_df.corr(method='kendall', min_periods=min_periods)
            else:
                raise ValueError(f"Unknown correlation method: {method}")
            
            # Clean NaN values (set to 0 for missing correlations)
            corr_matrix = corr_matrix.fillna(0)
            
            # Ensure diagonal is 1.0
            np.fill_diagonal(corr_matrix.values, 1.0)
            
            # Ensure matrix is symmetric
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            np.fill_diagonal(corr_matrix.values, 1.0)
            
            return corr_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            raise
    
    def get_strategy_returns_data(
        self,
        strategy_ids: List[str],
        time_period: str = '30d',
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch strategy returns data for correlation calculation
        
        Args:
            strategy_ids: List of strategy IDs to include
            time_period: Time period for returns ('30d', '60d', '90d', '1y')
            end_date: End date for data (default: now)
            
        Returns:
            DataFrame with strategy returns
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            
            # Parse time period
            period_days = {
                '30d': 30,
                '60d': 60,
                '90d': 90,
                '1y': 365
            }.get(time_period, 30)
            
            start_date = end_date - timedelta(days=period_days)
            
            # Create sample returns data for demonstration
            # In production, this would fetch from database
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            returns_data = {}
            np.random.seed(42)  # For reproducible results
            
            for strategy_id in strategy_ids:
                # Generate sample returns with different characteristics
                if 'momentum' in strategy_id.lower():
                    # Momentum strategies: trending returns
                    trend = np.random.randn(len(dates)) * 0.01
                    returns = np.cumsum(trend) * 0.001 + np.random.randn(len(dates)) * 0.02
                elif 'mean_reversion' in strategy_id.lower():
                    # Mean reversion: oscillating returns
                    returns = np.sin(np.arange(len(dates)) * 0.1) * 0.01 + np.random.randn(len(dates)) * 0.015
                elif 'arbitrage' in strategy_id.lower():
                    # Arbitrage: low volatility, consistent returns
                    returns = np.random.randn(len(dates)) * 0.005 + 0.001
                else:
                    # Default: random returns
                    returns = np.random.randn(len(dates)) * 0.02
                
                returns_data[strategy_id] = returns
            
            returns_df = pd.DataFrame(returns_data, index=dates)
            
            # Add some correlation structure for realistic testing
            if len(strategy_ids) > 3:
                # Make some strategies correlated
                for i in range(0, min(3, len(strategy_ids)-1)):
                    if i+1 < len(returns_df.columns):
                        col1 = returns_df.columns[i]
                        col2 = returns_df.columns[i+1]
                        # Add correlation
                        returns_df[col2] = returns_df[col1] * 0.7 + returns_df[col2] * 0.3
            
            return returns_df
            
        except Exception as e:
            logger.error(f"Error fetching strategy returns: {e}")
            return pd.DataFrame()
    
    async def store_correlation_matrix(
        self,
        db: AsyncSession,
        corr_matrix: pd.DataFrame,
        time_period: str = '30d',
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store correlation matrix in database
        
        Args:
            db: Database session
            corr_matrix: Correlation matrix DataFrame
            time_period: Time period for correlation
            metadata: Additional metadata
            
        Returns:
            Matrix ID
        """
        try:
            # Generate unique matrix ID
            matrix_id = hashlib.md5(
                f"{datetime.utcnow().isoformat()}_{time_period}".encode()
            ).hexdigest()[:20]
            
            # Prepare matrix data for JSON storage
            matrix_data = {
                'strategies': corr_matrix.columns.tolist(),
                'matrix': corr_matrix.values.tolist(),
                'metadata': {
                    'time_period': time_period,
                    'sample_size': metadata.get('sample_size', 0) if metadata else 0,
                    'method': metadata.get('method', 'pearson') if metadata else 'pearson'
                }
            }
            
            # Calculate matrix statistics
            # Exclude diagonal for statistics
            mask = np.ones(corr_matrix.shape, dtype=bool)
            np.fill_diagonal(mask, False)
            off_diagonal = corr_matrix.values[mask]
            
            avg_correlation = float(np.mean(np.abs(off_diagonal)))
            max_correlation = float(np.max(off_diagonal))
            min_correlation = float(np.min(off_diagonal))
            
            # Mark existing matrices as not current
            from sqlalchemy import update
            await db.execute(
                update(CorrelationMatrix).where(
                    and_(
                        CorrelationMatrix.is_current == 'Y',
                        CorrelationMatrix.time_period == time_period
                    )
                ).values(is_current='N')
            )
            
            # Create new matrix record
            new_matrix = CorrelationMatrix(
                matrix_id=matrix_id,
                matrix_data=matrix_data,
                num_strategies=len(corr_matrix.columns),
                time_period=time_period,
                avg_correlation=avg_correlation,
                max_correlation=max_correlation,
                min_correlation=min_correlation,
                cache_ttl=self.cache_ttl,
                is_current='Y'
            )
            
            db.add(new_matrix)
            
            # Store individual correlations for detailed queries
            for i, strat1 in enumerate(corr_matrix.columns):
                for j, strat2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only store upper triangle
                        correlation = StrategyCorrelation(
                            strategy_id_1=strat1,
                            strategy_id_2=strat2,
                            correlation_coefficient=float(corr_matrix.iloc[i, j]),
                            time_period=time_period,
                            sample_size=metadata.get('sample_size', 0) if metadata else 0,
                            calculation_method=metadata.get('method', 'pearson') if metadata else 'pearson'
                        )
                        db.add(correlation)
            
            await db.commit()
            
            logger.info(f"Stored correlation matrix {matrix_id} with {len(corr_matrix.columns)} strategies")
            return matrix_id
            
        except Exception as e:
            logger.error(f"Error storing correlation matrix: {e}")
            await db.rollback()
            raise
    
    async def get_latest_correlation_matrix(
        self,
        db: AsyncSession,
        time_period: str = '30d'
    ) -> Optional[Dict]:
        """
        Retrieve the latest correlation matrix from database
        
        Args:
            db: Database session
            time_period: Time period for correlation
            
        Returns:
            Matrix data dictionary or None
        """
        try:
            result = await db.execute(
                select(CorrelationMatrix).where(
                    and_(
                        CorrelationMatrix.is_current == 'Y',
                        CorrelationMatrix.time_period == time_period
                    )
                ).order_by(CorrelationMatrix.calculated_at.desc())
            )
            
            matrix_record = result.scalars().first()
            
            if matrix_record:
                return {
                    'matrix_id': matrix_record.matrix_id,
                    'calculated_at': matrix_record.calculated_at.isoformat(),
                    'data': matrix_record.matrix_data,
                    'statistics': {
                        'avg_correlation': matrix_record.avg_correlation,
                        'max_correlation': matrix_record.max_correlation,
                        'min_correlation': matrix_record.min_correlation,
                        'num_strategies': matrix_record.num_strategies
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving correlation matrix: {e}")
            return None
    
    def identify_high_correlations(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float = None
    ) -> List[Dict]:
        """
        Identify strategy pairs with high correlations
        
        Args:
            corr_matrix: Correlation matrix DataFrame
            threshold: Correlation threshold (default: self.high_correlation_threshold)
            
        Returns:
            List of high correlation pairs
        """
        if threshold is None:
            threshold = self.high_correlation_threshold
        
        high_correlations = []
        
        # Check upper triangle only (avoid duplicates)
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) > threshold:
                    severity = 'critical' if abs(corr_value) > self.very_high_correlation_threshold else 'warning'
                    
                    high_correlations.append({
                        'strategy_1': corr_matrix.columns[i],
                        'strategy_2': corr_matrix.columns[j],
                        'correlation': float(corr_value),
                        'severity': severity
                    })
        
        # Sort by correlation value (descending)
        high_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return high_correlations
    
    async def create_correlation_alerts(
        self,
        db: AsyncSession,
        high_correlations: List[Dict]
    ) -> List[str]:
        """
        Create alerts for high correlation warnings
        
        Args:
            db: Database session
            high_correlations: List of high correlation pairs
            
        Returns:
            List of created alert IDs
        """
        alert_ids = []
        
        try:
            for corr_pair in high_correlations:
                # Generate alert ID
                alert_id = hashlib.md5(
                    f"{corr_pair['strategy_1']}_{corr_pair['strategy_2']}_{datetime.utcnow().date()}".encode()
                ).hexdigest()[:20]
                
                # Check if alert already exists
                existing = await db.execute(
                    select(CorrelationAlert).where(
                        and_(
                            CorrelationAlert.alert_id == alert_id,
                            CorrelationAlert.is_active == 'Y'
                        )
                    )
                )
                
                if not existing.scalars().first():
                    alert = CorrelationAlert(
                        alert_id=alert_id,
                        alert_type='high_correlation',
                        severity=corr_pair['severity'],
                        strategy_id_1=corr_pair['strategy_1'],
                        strategy_id_2=corr_pair['strategy_2'],
                        correlation_value=corr_pair['correlation'],
                        is_active='Y'
                    )
                    db.add(alert)
                    alert_ids.append(alert_id)
            
            await db.commit()
            
            if alert_ids:
                logger.info(f"Created {len(alert_ids)} correlation alerts")
            
            return alert_ids
            
        except Exception as e:
            logger.error(f"Error creating correlation alerts: {e}")
            await db.rollback()
            return []
    
    def calculate_clustering(
        self,
        corr_matrix: pd.DataFrame,
        n_clusters: int = 5
    ) -> Dict[str, List[str]]:
        """
        Cluster strategies based on correlation patterns
        
        Args:
            corr_matrix: Correlation matrix DataFrame
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary of cluster assignments
        """
        try:
            from sklearn.cluster import AgglomerativeClustering
            
            # Convert correlation to distance (1 - abs(correlation))
            distance_matrix = 1 - np.abs(corr_matrix.values)
            
            # Perform hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=min(n_clusters, len(corr_matrix.columns)),
                affinity='precomputed',
                linkage='average'
            )
            
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Group strategies by cluster
            clusters = {}
            for i, strategy in enumerate(corr_matrix.columns):
                cluster_id = f"cluster_{cluster_labels[i]}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(strategy)
            
            return clusters
            
        except ImportError:
            logger.warning("scikit-learn not available for clustering")
            # Fallback: simple grouping based on correlation threshold
            clusters = {'cluster_0': []}
            assigned = set()
            
            for i, strat1 in enumerate(corr_matrix.columns):
                if strat1 not in assigned:
                    cluster = [strat1]
                    assigned.add(strat1)
                    
                    for j, strat2 in enumerate(corr_matrix.columns):
                        if strat2 not in assigned and abs(corr_matrix.iloc[i, j]) > 0.5:
                            cluster.append(strat2)
                            assigned.add(strat2)
                    
                    cluster_id = f"cluster_{len(clusters)}"
                    clusters[cluster_id] = cluster
            
            return clusters
        except Exception as e:
            logger.error(f"Error calculating clusters: {e}")
            return {}
    
    async def run_correlation_update(
        self,
        db: AsyncSession,
        strategy_ids: List[str],
        time_periods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run complete correlation update cycle
        
        Args:
            db: Database session
            strategy_ids: List of strategy IDs to analyze
            time_periods: Time periods to calculate (default: all)
            
        Returns:
            Update results dictionary
        """
        results = {
            'success': False,
            'matrices_created': [],
            'alerts_created': [],
            'errors': []
        }
        
        try:
            if time_periods is None:
                time_periods = self.time_periods
            
            for period in time_periods:
                try:
                    # Get strategy returns
                    returns_df = self.get_strategy_returns_data(strategy_ids, period)
                    
                    if returns_df.empty:
                        results['errors'].append(f"No data for period {period}")
                        continue
                    
                    # Calculate correlation matrix
                    corr_matrix = self.calculate_correlation_matrix(returns_df)
                    
                    if corr_matrix.empty:
                        results['errors'].append(f"Failed to calculate correlations for {period}")
                        continue
                    
                    # Store matrix
                    matrix_id = await self.store_correlation_matrix(
                        db, corr_matrix, period,
                        metadata={
                            'sample_size': len(returns_df),
                            'method': 'pearson'
                        }
                    )
                    results['matrices_created'].append(matrix_id)
                    
                    # Identify high correlations
                    high_correlations = self.identify_high_correlations(corr_matrix)
                    
                    # Create alerts
                    if high_correlations:
                        alert_ids = await self.create_correlation_alerts(db, high_correlations)
                        results['alerts_created'].extend(alert_ids)
                    
                except Exception as e:
                    logger.error(f"Error processing period {period}: {e}")
                    results['errors'].append(f"Period {period}: {str(e)}")
            
            results['success'] = len(results['matrices_created']) > 0
            
        except Exception as e:
            logger.error(f"Error in correlation update cycle: {e}")
            results['errors'].append(str(e))
        
        return results


# Global instance
correlation_engine = CorrelationEngine()

def get_correlation_engine() -> CorrelationEngine:
    """Get the global correlation engine instance"""
    return correlation_engine