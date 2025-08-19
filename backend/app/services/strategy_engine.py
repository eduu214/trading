"""
Strategy Engine Service
Implements and executes trading strategies with technical indicators
Part of F002-US001: Real Strategy Engine with Backtesting
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from app.services.technical_indicators import TechnicalIndicatorService
from app.models.strategy import Strategy
from app.core.database import AsyncSessionLocal

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradingSignal:
    """Trading signal with metadata"""
    symbol: str
    signal_type: SignalType
    signal_strength: float  # 0-100
    price: float
    timestamp: datetime
    strategy_name: str
    reason: str
    indicators: Dict[str, float]

class StrategyEngine:
    """Implement and execute trading strategies"""
    
    def __init__(self):
        """Initialize the strategy engine"""
        self.indicators = TechnicalIndicatorService()
        self.min_data_points = 50  # Minimum data points for strategy execution
        
    async def rsi_mean_reversion(
        self,
        symbol: str,
        data: pd.DataFrame,
        rsi_period: int = 14,
        oversold_level: float = 30,
        overbought_level: float = 70,
        exit_level: float = 50
    ) -> List[TradingSignal]:
        """
        RSI-based mean reversion strategy
        
        Buy when RSI < oversold_level (30)
        Sell when RSI > overbought_level (70)
        Exit positions when RSI crosses 50
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            rsi_period: RSI calculation period
            oversold_level: RSI level to trigger buy (default 30)
            overbought_level: RSI level to trigger sell (default 70)
            exit_level: RSI level to exit positions (default 50)
            
        Returns:
            List of trading signals
        """
        try:
            signals = []
            
            # Calculate RSI
            rsi = await self.indicators.calculate_rsi(data['close'], period=rsi_period)
            
            if rsi.empty or len(rsi.dropna()) < 10:
                logger.warning(f"Insufficient RSI data for {symbol}")
                return signals
            
            # Get latest RSI value
            current_rsi = rsi.iloc[-1]
            prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
            current_price = data['close'].iloc[-1]
            
            # Generate signals based on RSI levels
            signal_type = SignalType.HOLD
            signal_strength = 0.0
            reason = ""
            
            if current_rsi < oversold_level:
                # Oversold - potential buy signal
                signal_type = SignalType.BUY
                signal_strength = min(100, (oversold_level - current_rsi) * 3)
                reason = f"RSI oversold at {current_rsi:.2f} (below {oversold_level})"
                
            elif current_rsi > overbought_level:
                # Overbought - potential sell signal
                signal_type = SignalType.SELL
                signal_strength = min(100, (current_rsi - overbought_level) * 3)
                reason = f"RSI overbought at {current_rsi:.2f} (above {overbought_level})"
                
            elif prev_rsi < exit_level <= current_rsi:
                # RSI crossing above exit level - close short positions
                signal_type = SignalType.SELL
                signal_strength = 50
                reason = f"RSI crossed above exit level {exit_level}"
                
            elif prev_rsi > exit_level >= current_rsi:
                # RSI crossing below exit level - close long positions
                signal_type = SignalType.BUY
                signal_strength = 50
                reason = f"RSI crossed below exit level {exit_level}"
            
            # Create signal if not HOLD
            if signal_type != SignalType.HOLD:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    signal_strength=signal_strength,
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    strategy_name="RSI_MEAN_REVERSION",
                    reason=reason,
                    indicators={
                        'rsi': current_rsi,
                        'rsi_prev': prev_rsi,
                        'oversold_level': oversold_level,
                        'overbought_level': overbought_level
                    }
                )
                signals.append(signal)
                logger.info(f"Generated {signal_type.value} signal for {symbol}: {reason}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in RSI mean reversion strategy for {symbol}: {e}")
            return []
    
    async def macd_momentum(
        self,
        symbol: str,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> List[TradingSignal]:
        """
        MACD momentum strategy
        
        Buy when MACD crosses above signal line
        Sell when MACD crosses below signal line
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            
        Returns:
            List of trading signals
        """
        try:
            signals = []
            
            # Calculate MACD
            macd_data = await self.indicators.calculate_macd(
                data['close'],
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period
            )
            
            macd = macd_data['macd']
            signal_line = macd_data['signal']
            histogram = macd_data['histogram']
            
            if macd.empty or len(macd.dropna()) < 10:
                logger.warning(f"Insufficient MACD data for {symbol}")
                return signals
            
            # Get current and previous values
            current_macd = macd.iloc[-1]
            prev_macd = macd.iloc[-2] if len(macd) > 1 else current_macd
            current_signal = signal_line.iloc[-1]
            prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else current_signal
            current_histogram = histogram.iloc[-1]
            current_price = data['close'].iloc[-1]
            
            # Generate signals based on MACD crossovers
            signal_type = SignalType.HOLD
            signal_strength = 0.0
            reason = ""
            
            # Check for crossovers
            if prev_macd <= prev_signal and current_macd > current_signal:
                # MACD crossed above signal line - bullish
                signal_type = SignalType.BUY
                signal_strength = min(100, abs(current_histogram) * 10)
                reason = f"MACD bullish crossover: MACD {current_macd:.4f} > Signal {current_signal:.4f}"
                
            elif prev_macd >= prev_signal and current_macd < current_signal:
                # MACD crossed below signal line - bearish
                signal_type = SignalType.SELL
                signal_strength = min(100, abs(current_histogram) * 10)
                reason = f"MACD bearish crossover: MACD {current_macd:.4f} < Signal {current_signal:.4f}"
            
            # Create signal if not HOLD
            if signal_type != SignalType.HOLD:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    signal_strength=signal_strength,
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    strategy_name="MACD_MOMENTUM",
                    reason=reason,
                    indicators={
                        'macd': current_macd,
                        'signal': current_signal,
                        'histogram': current_histogram,
                        'macd_prev': prev_macd,
                        'signal_prev': prev_signal
                    }
                )
                signals.append(signal)
                logger.info(f"Generated {signal_type.value} signal for {symbol}: {reason}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in MACD momentum strategy for {symbol}: {e}")
            return []
    
    async def bollinger_breakout(
        self,
        symbol: str,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        volume_factor: float = 1.5
    ) -> List[TradingSignal]:
        """
        Bollinger Band breakout strategy
        
        Buy when price breaks above upper band with volume
        Sell when price breaks below lower band with volume
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            period: BB period (default 20)
            std_dev: Number of standard deviations (default 2.0)
            volume_factor: Volume must be this factor above average (default 1.5)
            
        Returns:
            List of trading signals
        """
        try:
            signals = []
            
            # Calculate Bollinger Bands
            bb_data = await self.indicators.calculate_bollinger_bands(
                data['close'],
                period=period,
                std_dev=std_dev
            )
            
            upper_band = bb_data['upper']
            middle_band = bb_data['middle']
            lower_band = bb_data['lower']
            
            if upper_band.empty or len(upper_band.dropna()) < 10:
                logger.warning(f"Insufficient Bollinger Band data for {symbol}")
                return signals
            
            # Calculate average volume
            avg_volume = data['volume'].rolling(window=period).mean()
            
            # Get current values
            current_price = data['close'].iloc[-1]
            prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_volume = data['volume'].iloc[-1]
            current_avg_volume = avg_volume.iloc[-1]
            
            # Generate signals based on band breakouts
            signal_type = SignalType.HOLD
            signal_strength = 0.0
            reason = ""
            
            # Check for breakouts with volume confirmation
            volume_confirmed = current_volume > (current_avg_volume * volume_factor)
            
            if prev_price <= current_upper and current_price > current_upper and volume_confirmed:
                # Price broke above upper band with volume - potential breakout
                signal_type = SignalType.BUY
                signal_strength = min(100, ((current_price - current_upper) / current_upper) * 1000)
                reason = f"Breakout above upper band {current_upper:.2f} with {volume_factor}x volume"
                
            elif prev_price >= current_lower and current_price < current_lower and volume_confirmed:
                # Price broke below lower band with volume - potential breakdown
                signal_type = SignalType.SELL
                signal_strength = min(100, ((current_lower - current_price) / current_lower) * 1000)
                reason = f"Breakdown below lower band {current_lower:.2f} with {volume_factor}x volume"
                
            elif current_price > current_middle and prev_price <= current_middle:
                # Price crossed above middle band - mild bullish
                signal_type = SignalType.BUY
                signal_strength = 30
                reason = f"Price crossed above middle band {current_middle:.2f}"
                
            elif current_price < current_middle and prev_price >= current_middle:
                # Price crossed below middle band - mild bearish
                signal_type = SignalType.SELL
                signal_strength = 30
                reason = f"Price crossed below middle band {current_middle:.2f}"
            
            # Create signal if not HOLD
            if signal_type != SignalType.HOLD:
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    signal_strength=signal_strength,
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    strategy_name="BOLLINGER_BREAKOUT",
                    reason=reason,
                    indicators={
                        'upper_band': current_upper,
                        'middle_band': current_middle,
                        'lower_band': current_lower,
                        'band_width': current_upper - current_lower,
                        'volume_ratio': current_volume / current_avg_volume if current_avg_volume > 0 else 0
                    }
                )
                signals.append(signal)
                logger.info(f"Generated {signal_type.value} signal for {symbol}: {reason}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in Bollinger breakout strategy for {symbol}: {e}")
            return []
    
    async def execute_all_strategies(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> Dict[str, List[TradingSignal]]:
        """
        Execute all available strategies for a symbol
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of strategy names to signals
        """
        try:
            if len(data) < self.min_data_points:
                logger.warning(f"Insufficient data for {symbol}. Need {self.min_data_points} points, got {len(data)}")
                return {}
            
            results = {}
            
            # Execute RSI Mean Reversion
            rsi_signals = await self.rsi_mean_reversion(symbol, data)
            if rsi_signals:
                results['RSI_MEAN_REVERSION'] = rsi_signals
            
            # Execute MACD Momentum
            macd_signals = await self.macd_momentum(symbol, data)
            if macd_signals:
                results['MACD_MOMENTUM'] = macd_signals
            
            # Execute Bollinger Breakout
            bb_signals = await self.bollinger_breakout(symbol, data)
            if bb_signals:
                results['BOLLINGER_BREAKOUT'] = bb_signals
            
            logger.info(f"Executed all strategies for {symbol}. Generated {sum(len(s) for s in results.values())} signals")
            return results
            
        except Exception as e:
            logger.error(f"Error executing strategies for {symbol}: {e}")
            return {}
    
    async def get_consensus_signal(
        self,
        signals: Dict[str, List[TradingSignal]]
    ) -> Optional[TradingSignal]:
        """
        Get consensus signal from multiple strategies
        
        Args:
            signals: Dictionary of strategy signals
            
        Returns:
            Consensus signal or None if no consensus
        """
        try:
            if not signals:
                return None
            
            # Collect all signals
            all_signals = []
            for strategy_signals in signals.values():
                all_signals.extend(strategy_signals)
            
            if not all_signals:
                return None
            
            # Count buy vs sell signals
            buy_signals = [s for s in all_signals if s.signal_type == SignalType.BUY]
            sell_signals = [s for s in all_signals if s.signal_type == SignalType.SELL]
            
            # Calculate weighted consensus
            buy_strength = sum(s.signal_strength for s in buy_signals) / max(1, len(buy_signals))
            sell_strength = sum(s.signal_strength for s in sell_signals) / max(1, len(sell_signals))
            
            # Determine consensus
            if len(buy_signals) > len(sell_signals) and buy_strength > 50:
                # Bullish consensus
                return TradingSignal(
                    symbol=all_signals[0].symbol,
                    signal_type=SignalType.BUY,
                    signal_strength=buy_strength,
                    price=all_signals[0].price,
                    timestamp=datetime.utcnow(),
                    strategy_name="CONSENSUS",
                    reason=f"Bullish consensus from {len(buy_signals)} strategies",
                    indicators={'strategies_count': len(buy_signals)}
                )
            elif len(sell_signals) > len(buy_signals) and sell_strength > 50:
                # Bearish consensus
                return TradingSignal(
                    symbol=all_signals[0].symbol,
                    signal_type=SignalType.SELL,
                    signal_strength=sell_strength,
                    price=all_signals[0].price,
                    timestamp=datetime.utcnow(),
                    strategy_name="CONSENSUS",
                    reason=f"Bearish consensus from {len(sell_signals)} strategies",
                    indicators={'strategies_count': len(sell_signals)}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating consensus signal: {e}")
            return None