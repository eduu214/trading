"""
Backtesting Engine Service
Comprehensive strategy backtesting using Vectorbt
Part of F002-US001: Real Strategy Engine with Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import asyncio
import time
import vectorbt as vbt
from app.services.technical_indicators import TechnicalIndicatorService
from app.services.strategy_engine import StrategyEngine, SignalType
from app.core.logging_config import structured_logger

@dataclass
class BacktestResult:
    """Backtesting results with performance metrics"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float
    equity_curve: pd.Series
    trades: pd.DataFrame
    execution_time: float

class BacktestingTimeoutError(Exception):
    """Raised when backtesting operation times out"""
    pass

class BacktestingEngine:
    """
    Comprehensive backtesting engine using Vectorbt
    F002-US001 Slice 3 Task 15: Enhanced with timeout handling and progress tracking
    Implements F002-US001 requirements for strategy validation
    """
    
    def __init__(self):
        """Initialize the backtesting engine with timeout configuration"""
        self.indicators = TechnicalIndicatorService()
        self.strategy_engine = StrategyEngine()
        self.default_capital = 10000  # $10,000 starting capital
        self.commission = 0.001  # 0.1% commission
        self.slippage = 0.001  # 0.1% slippage
        
        # Timeout configuration (Task 15 requirement)
        self.max_timeout = 300  # 5 minutes maximum
        self.soft_timeout = 240  # 4 minutes soft warning
        self.progress_callbacks = []  # For progress tracking
        
        # Performance tracking
        self.backtest_stats = {
            'total_backtests': 0,
            'completed_backtests': 0,
            'timeout_errors': 0,
            'avg_execution_time': 0.0
        }
        
        # Structured logging (Task 18)
        self.logger = structured_logger
    
    async def _run_with_timeout(
        self,
        coro,
        operation_name: str = "backtest",
        timeout: Optional[float] = None
    ):
        """
        Run a coroutine with timeout protection
        F002-US001 Slice 3 Task 15: 5-minute timeout with progress tracking
        """
        timeout = timeout or self.max_timeout
        start_time = time.time()
        
        try:
            self.backtest_stats['total_backtests'] += 1
            
            # Create timeout task
            result = await asyncio.wait_for(coro, timeout=timeout)
            
            # Update success stats
            execution_time = time.time() - start_time
            self.backtest_stats['completed_backtests'] += 1
            self._update_avg_execution_time(execution_time)
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.backtest_stats['timeout_errors'] += 1
            
            # Log timeout error with structured logging (Task 18)
            self.logger.log_timeout_error(
                correlation_id="timeout_" + str(int(start_time)),
                operation=operation_name,
                timeout_seconds=timeout,
                elapsed_seconds=execution_time,
                context={
                    "total_backtests": self.backtest_stats['total_backtests'],
                    "timeout_errors": self.backtest_stats['timeout_errors']
                }
            )
            
            error_msg = (
                f"{operation_name} operation timed out after {execution_time:.1f}s "
                f"(limit: {timeout}s). This may indicate insufficient computational resources "
                f"or extremely complex strategy parameters."
            )
            logger.error(error_msg)
            raise BacktestingTimeoutError(error_msg)
    
    def _update_avg_execution_time(self, execution_time: float):
        """Update rolling average execution time"""
        current_avg = self.backtest_stats['avg_execution_time']
        completed = self.backtest_stats['completed_backtests']
        
        self.backtest_stats['avg_execution_time'] = (
            (current_avg * (completed - 1) + execution_time) / completed
        )
    
    async def _notify_progress(self, stage: str, progress: float, details: str = ""):
        """Notify progress callbacks of current status"""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(stage, progress, details)
                else:
                    callback(stage, progress, details)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def add_progress_callback(self, callback):
        """Add a progress tracking callback"""
        self.progress_callbacks.append(callback)
    
    async def get_backtest_stats(self) -> Dict:
        """Get current backtesting performance statistics"""
        total = self.backtest_stats['total_backtests']
        completed = self.backtest_stats['completed_backtests']
        
        return {
            **self.backtest_stats,
            'success_rate': (completed / max(1, total)) * 100,
            'timeout_rate': (self.backtest_stats['timeout_errors'] / max(1, total)) * 100,
            'avg_execution_time_formatted': f"{self.backtest_stats['avg_execution_time']:.2f}s"
        }
        
    async def backtest_rsi_strategy(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        rsi_period: int = 14,
        oversold_level: float = 30,
        overbought_level: float = 70,
        initial_capital: float = None
    ) -> BacktestResult:
        """
        Backtest RSI mean reversion strategy with timeout protection
        F002-US001 Slice 3 Task 15: Enhanced with timeout and progress tracking
        """
        return await self._run_with_timeout(
            self._backtest_rsi_strategy_impl(
                symbol, price_data, rsi_period, oversold_level, overbought_level, initial_capital
            ),
            f"RSI backtest for {symbol}"
        )
    
    async def _backtest_rsi_strategy_impl(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        rsi_period: int = 14,
        oversold_level: float = 30,
        overbought_level: float = 70,
        initial_capital: float = None
    ) -> BacktestResult:
        """
        Backtest RSI mean reversion strategy
        
        Args:
            symbol: Trading symbol
            price_data: OHLCV DataFrame with datetime index
            rsi_period: RSI calculation period
            oversold_level: RSI level to trigger buy
            overbought_level: RSI level to trigger sell
            initial_capital: Starting capital (default $10,000)
            
        Returns:
            BacktestResult with performance metrics
        """
        try:
            start_time = datetime.now()
            capital = initial_capital or self.default_capital
            
            # Generate correlation ID for this backtest operation (Task 18)
            correlation_id = self.logger.generate_correlation_id()
            
            # Log backtest start with context (Task 18)
            self.logger.log_backtest_start(
                correlation_id=correlation_id,
                symbol=symbol,
                strategy="RSI_MEAN_REVERSION",
                parameters={
                    "rsi_period": rsi_period,
                    "oversold_level": oversold_level,
                    "overbought_level": overbought_level,
                    "initial_capital": capital
                },
                data_period={
                    "start": price_data.index[0].isoformat(),
                    "end": price_data.index[-1].isoformat(),
                    "data_points": len(price_data)
                }
            )
            
            # Progress: Starting backtest
            await self._notify_progress("initialization", 0.1, f"Starting RSI backtest for {symbol}")
            
            # Calculate RSI with logging (Task 18)
            await self._notify_progress("indicators", 0.3, "Calculating RSI indicator")
            
            indicator_start = time.time()
            try:
                rsi = await self.indicators.calculate_rsi(price_data['close'], period=rsi_period)
                indicator_time = time.time() - indicator_start
                
                # Log successful indicator calculation (Task 18)
                self.logger.log_indicator_calculation(
                    correlation_id=correlation_id,
                    indicator_name="RSI",
                    symbol=symbol,
                    parameters={"period": rsi_period},
                    data_points=len(price_data),
                    execution_time=indicator_time
                )
            except Exception as e:
                # Log indicator calculation error (Task 18)
                self.logger.log_indicator_error(
                    correlation_id=correlation_id,
                    indicator_name="RSI",
                    symbol=symbol,
                    error=e,
                    parameters={"period": rsi_period},
                    data_points=len(price_data)
                )
                raise
            
            # Generate entry and exit signals
            await self._notify_progress("signals", 0.5, "Generating buy/sell signals")
            entries = (rsi < oversold_level).astype(int)  # Buy when oversold
            exits = (rsi > overbought_level).astype(int)   # Sell when overbought
            
            # Run vectorized backtest
            await self._notify_progress("backtesting", 0.7, "Running vectorized backtest")
            portfolio = vbt.Portfolio.from_signals(
                price_data['close'],
                entries=entries,
                exits=exits,
                init_cash=capital,
                fees=self.commission,
                slippage=self.slippage,
                freq='D'
            )
            
            # Calculate performance metrics
            await self._notify_progress("metrics", 0.9, "Calculating performance metrics")
            result = await self._calculate_metrics(
                portfolio,
                "RSI_MEAN_REVERSION",
                symbol,
                price_data.index[0],
                price_data.index[-1],
                capital,
                start_time
            )
            
            # Progress: Completion
            await self._notify_progress("completed", 1.0, f"RSI backtest completed successfully")
            
            # Log successful backtest completion (Task 18)
            self.logger.log_backtest_success(
                correlation_id=correlation_id,
                symbol=symbol,
                strategy="RSI_MEAN_REVERSION",
                performance_metrics={
                    "sharpe_ratio": result.sharpe_ratio,
                    "total_return_pct": result.total_return_pct,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades
                },
                execution_time=result.execution_time
            )
            
            return result
            
        except Exception as e:
            # Log backtest error with context (Task 18)
            error_context = {
                "rsi_period": rsi_period,
                "oversold_level": oversold_level,
                "overbought_level": overbought_level,
                "data_points": len(price_data) if 'price_data' in locals() else None,
                "execution_time": (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else None
            }
            
            self.logger.log_backtest_error(
                correlation_id=correlation_id if 'correlation_id' in locals() else "unknown",
                symbol=symbol,
                strategy="RSI_MEAN_REVERSION",
                error=e,
                context=error_context
            )
            
            logger.error(f"Error in RSI backtest for {symbol}: {e}")
            raise
    
    async def backtest_macd_strategy(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        initial_capital: float = None
    ) -> BacktestResult:
        """
        Backtest MACD momentum strategy
        
        Args:
            symbol: Trading symbol
            price_data: OHLCV DataFrame
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            initial_capital: Starting capital
            
        Returns:
            BacktestResult with performance metrics
        """
        try:
            start_time = datetime.now()
            capital = initial_capital or self.default_capital
            
            # Calculate MACD
            macd_data = await self.indicators.calculate_macd(
                price_data['close'],
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period
            )
            
            macd = macd_data['macd']
            signal = macd_data['signal']
            
            # Generate crossover signals
            macd_above = (macd > signal).fillna(False)
            entries = macd_above & ~macd_above.shift(1).fillna(False)  # Crossover up
            exits = ~macd_above & macd_above.shift(1).fillna(False)     # Crossover down
            
            # Run vectorized backtest
            portfolio = vbt.Portfolio.from_signals(
                price_data['close'],
                entries=entries.fillna(False),
                exits=exits.fillna(False),
                init_cash=capital,
                fees=self.commission,
                slippage=self.slippage,
                freq='D'
            )
            
            # Calculate performance metrics
            result = await self._calculate_metrics(
                portfolio,
                "MACD_MOMENTUM",
                symbol,
                price_data.index[0],
                price_data.index[-1],
                capital,
                start_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in MACD backtest for {symbol}: {e}")
            raise
    
    async def backtest_bollinger_strategy(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        initial_capital: float = None
    ) -> BacktestResult:
        """
        Backtest Bollinger Band breakout strategy
        
        Args:
            symbol: Trading symbol
            price_data: OHLCV DataFrame
            period: BB period
            std_dev: Number of standard deviations
            initial_capital: Starting capital
            
        Returns:
            BacktestResult with performance metrics
        """
        try:
            start_time = datetime.now()
            capital = initial_capital or self.default_capital
            
            # Calculate Bollinger Bands
            bb_data = await self.indicators.calculate_bollinger_bands(
                price_data['close'],
                period=period,
                std_dev=std_dev
            )
            
            upper = bb_data['upper']
            lower = bb_data['lower']
            close = price_data['close']
            
            # Generate breakout signals
            entries = close > upper  # Buy on upper band breakout
            exits = close < lower     # Sell on lower band breakdown
            
            # Run vectorized backtest
            portfolio = vbt.Portfolio.from_signals(
                close,
                entries=entries.fillna(False),
                exits=exits.fillna(False),
                init_cash=capital,
                fees=self.commission,
                slippage=self.slippage,
                freq='D'
            )
            
            # Calculate performance metrics
            result = await self._calculate_metrics(
                portfolio,
                "BOLLINGER_BREAKOUT",
                symbol,
                price_data.index[0],
                price_data.index[-1],
                capital,
                start_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Bollinger backtest for {symbol}: {e}")
            raise
    
    async def _calculate_metrics(
        self,
        portfolio: vbt.Portfolio,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        start_time: datetime
    ) -> BacktestResult:
        """
        Calculate comprehensive performance metrics
        
        Args:
            portfolio: Vectorbt Portfolio object
            strategy_name: Name of the strategy
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            start_time: Backtest start time for execution timing
            
        Returns:
            BacktestResult with all metrics
        """
        try:
            # Get basic stats
            stats = portfolio.stats()
            
            # Calculate returns
            returns = portfolio.returns()
            total_return = portfolio.total_return()
            
            # Calculate Sharpe ratio (annualized)
            # Using 252 trading days for annualization
            sharpe_ratio = 0.0
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
            
            # Calculate max drawdown
            drawdown = portfolio.drawdown()
            max_drawdown = portfolio.max_drawdown() if len(drawdown) > 0 else 0
            
            # Get trade statistics
            trades = portfolio.trades.records_readable
            total_trades = len(trades)
            
            if total_trades > 0:
                winning_trades = len(trades[trades['PnL'] > 0])
                losing_trades = len(trades[trades['PnL'] < 0])
                win_rate = winning_trades / total_trades if total_trades > 0 else 0
                
                # Calculate profit factor
                total_wins = trades[trades['PnL'] > 0]['PnL'].sum() if winning_trades > 0 else 0
                total_losses = abs(trades[trades['PnL'] < 0]['PnL'].sum()) if losing_trades > 0 else 0
                profit_factor = total_wins / total_losses if total_losses > 0 else 0
                
                # Average win/loss
                avg_win = trades[trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
                avg_loss = trades[trades['PnL'] < 0]['PnL'].mean() if losing_trades > 0 else 0
                
                # Best/worst trades
                best_trade = trades['PnL'].max()
                worst_trade = trades['PnL'].min()
                
                # Average trade duration (in days)
                if 'Duration' in trades.columns:
                    avg_duration = trades['Duration'].mean()
                else:
                    avg_duration = 0
            else:
                winning_trades = losing_trades = 0
                win_rate = profit_factor = 0
                avg_win = avg_loss = best_trade = worst_trade = avg_duration = 0
            
            # Calculate final capital
            final_capital = initial_capital * (1 + total_return)
            
            # Get equity curve
            equity_curve = portfolio.value()
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                total_return_pct=total_return * 100,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown * 100,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                avg_win=avg_win,
                avg_loss=avg_loss,
                best_trade=best_trade,
                worst_trade=worst_trade,
                avg_trade_duration=avg_duration,
                equity_curve=equity_curve,
                trades=trades if total_trades > 0 else pd.DataFrame(),
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            # Return a default result on error
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=initial_capital,
                total_return=0,
                total_return_pct=0,
                sharpe_ratio=0,
                max_drawdown=0,
                max_drawdown_pct=0,
                win_rate=0,
                profit_factor=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0,
                avg_loss=0,
                best_trade=0,
                worst_trade=0,
                avg_trade_duration=0,
                equity_curve=pd.Series([initial_capital]),
                trades=pd.DataFrame(),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def compare_strategies(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        strategies: List[str] = None
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies on the same data
        
        Args:
            symbol: Trading symbol
            price_data: OHLCV DataFrame
            strategies: List of strategy names to test (default: all)
            
        Returns:
            Dictionary of strategy results
        """
        try:
            if strategies is None:
                strategies = ["RSI", "MACD", "BOLLINGER"]
            
            results = {}
            
            for strategy in strategies:
                if strategy.upper() == "RSI":
                    result = await self.backtest_rsi_strategy(symbol, price_data)
                    results["RSI_MEAN_REVERSION"] = result
                elif strategy.upper() == "MACD":
                    result = await self.backtest_macd_strategy(symbol, price_data)
                    results["MACD_MOMENTUM"] = result
                elif strategy.upper() == "BOLLINGER":
                    result = await self.backtest_bollinger_strategy(symbol, price_data)
                    results["BOLLINGER_BREAKOUT"] = result
            
            # Log comparison summary
            logger.info(f"Strategy comparison for {symbol}:")
            for name, result in results.items():
                logger.info(f"  {name}: Sharpe={result.sharpe_ratio:.2f}, "
                          f"Return={result.total_return_pct:.2f}%, "
                          f"MaxDD={result.max_drawdown_pct:.2f}%")
            
            return results
            
        except Exception as e:
            logger.error(f"Error comparing strategies for {symbol}: {e}")
            return {}