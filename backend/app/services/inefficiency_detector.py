"""
Market inefficiency detection algorithms for identifying trading opportunities
"""
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InefficiencyDetector:
    """Detects various types of market inefficiencies"""
    
    def __init__(self):
        self.min_zscore = 2.0  # Minimum z-score for statistical significance
        self.lookback_periods = 20  # Default lookback for calculations
        
    def detect_price_deviation(
        self, 
        price_data: List[Dict],
        zscore_threshold: float = 2.0
    ) -> Optional[Dict]:
        """
        Detect when price deviates significantly from moving average
        Returns opportunity if deviation exceeds threshold
        """
        if len(price_data) < self.lookback_periods:
            return None
            
        closes = [p["close"] for p in price_data]
        volumes = [p["volume"] for p in price_data]
        
        # Calculate moving average and standard deviation
        ma = np.mean(closes[-self.lookback_periods:])
        std = np.std(closes[-self.lookback_periods:])
        
        if std == 0:
            return None
            
        current_price = closes[-1]
        zscore = (current_price - ma) / std
        
        if abs(zscore) >= zscore_threshold:
            # Volume confirmation - higher volume on deviation
            avg_volume = np.mean(volumes[-self.lookback_periods:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                "type": "price_deviation",
                "zscore": zscore,
                "current_price": current_price,
                "moving_average": ma,
                "deviation_pct": ((current_price - ma) / ma) * 100,
                "volume_confirmation": volume_ratio > 1.2,
                "volume_ratio": volume_ratio,
                "signal": "oversold" if zscore < 0 else "overbought",
                "strength": min(abs(zscore) / 4.0, 1.0) * 100  # Normalize to 0-100
            }
            
        return None
        
    def detect_volume_spike(
        self,
        volume_data: List[float],
        spike_threshold: float = 3.0
    ) -> Optional[Dict]:
        """
        Detect unusual volume spikes that may indicate institutional activity
        """
        if len(volume_data) < 10:
            return None
            
        recent_volumes = volume_data[-10:]
        avg_volume = np.mean(recent_volumes[:-1])
        current_volume = recent_volumes[-1]
        
        if avg_volume == 0:
            return None
            
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= spike_threshold:
            return {
                "type": "volume_spike",
                "current_volume": current_volume,
                "average_volume": avg_volume,
                "spike_ratio": volume_ratio,
                "strength": min(volume_ratio / 5.0, 1.0) * 100
            }
            
        return None
        
    def detect_momentum_shift(
        self,
        price_data: List[Dict],
        rsi_period: int = 14
    ) -> Optional[Dict]:
        """
        Detect momentum shifts using RSI and price action
        """
        if len(price_data) < rsi_period + 1:
            return None
            
        # Calculate RSI
        rsi = self._calculate_rsi(price_data, rsi_period)
        
        if rsi is None:
            return None
            
        # Detect oversold/overbought conditions
        if rsi < 30 or rsi > 70:
            # Check for divergence
            prices = [p["close"] for p in price_data[-5:]]
            price_trend = "up" if prices[-1] > prices[0] else "down"
            
            if (rsi < 30 and price_trend == "down") or (rsi > 70 and price_trend == "up"):
                return {
                    "type": "momentum_shift",
                    "rsi": rsi,
                    "condition": "oversold" if rsi < 30 else "overbought",
                    "price_trend": price_trend,
                    "divergence": False,
                    "strength": abs(50 - rsi) * 2  # Normalize to 0-100
                }
            elif (rsi < 30 and price_trend == "up") or (rsi > 70 and price_trend == "down"):
                # Bullish or bearish divergence
                return {
                    "type": "momentum_shift",
                    "rsi": rsi,
                    "condition": "oversold" if rsi < 30 else "overbought",
                    "price_trend": price_trend,
                    "divergence": True,
                    "divergence_type": "bullish" if rsi < 30 else "bearish",
                    "strength": abs(50 - rsi) * 2.5  # Higher strength for divergence
                }
                
        return None
        
    def detect_spread_anomaly(
        self,
        bid: float,
        ask: float,
        historical_spreads: List[float]
    ) -> Optional[Dict]:
        """
        Detect unusual bid-ask spread patterns
        """
        if not historical_spreads or len(historical_spreads) < 10:
            return None
            
        current_spread = ask - bid
        spread_pct = (current_spread / bid) * 100 if bid > 0 else 0
        
        avg_spread = np.mean(historical_spreads)
        std_spread = np.std(historical_spreads)
        
        if std_spread == 0:
            return None
            
        zscore = (current_spread - avg_spread) / std_spread
        
        # Detect unusually wide or narrow spreads
        if abs(zscore) >= 2.0:
            return {
                "type": "spread_anomaly",
                "current_spread": current_spread,
                "spread_pct": spread_pct,
                "average_spread": avg_spread,
                "zscore": zscore,
                "anomaly": "wide" if zscore > 0 else "narrow",
                "strength": min(abs(zscore) / 3.0, 1.0) * 100
            }
            
        return None
        
    def detect_support_resistance_break(
        self,
        price_data: List[Dict],
        lookback: int = 50
    ) -> Optional[Dict]:
        """
        Detect breakouts from support/resistance levels
        """
        if len(price_data) < lookback:
            return None
            
        highs = [p["high"] for p in price_data[-lookback:]]
        lows = [p["low"] for p in price_data[-lookback:]]
        closes = [p["close"] for p in price_data[-lookback:]]
        
        # Find recent support and resistance levels
        resistance = max(highs[:-1])  # Exclude current bar
        support = min(lows[:-1])
        current_close = closes[-1]
        
        # Check for breakout
        if current_close > resistance:
            strength = ((current_close - resistance) / resistance) * 100
            return {
                "type": "resistance_break",
                "level": resistance,
                "current_price": current_close,
                "breakout_pct": strength,
                "strength": min(strength * 10, 100)
            }
        elif current_close < support:
            strength = ((support - current_close) / support) * 100
            return {
                "type": "support_break",
                "level": support,
                "current_price": current_close,
                "breakdown_pct": strength,
                "strength": min(strength * 10, 100)
            }
            
        return None
        
    def detect_gap(
        self,
        previous_close: float,
        current_open: float,
        min_gap_pct: float = 1.0
    ) -> Optional[Dict]:
        """
        Detect price gaps between sessions
        """
        if previous_close == 0:
            return None
            
        gap_size = current_open - previous_close
        gap_pct = (gap_size / previous_close) * 100
        
        if abs(gap_pct) >= min_gap_pct:
            return {
                "type": "price_gap",
                "gap_direction": "up" if gap_size > 0 else "down",
                "gap_size": abs(gap_size),
                "gap_pct": abs(gap_pct),
                "previous_close": previous_close,
                "current_open": current_open,
                "strength": min(abs(gap_pct) * 10, 100)
            }
            
        return None
        
    def detect_all_inefficiencies(
        self,
        ticker: str,
        price_data: List[Dict],
        quote_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Run all inefficiency detection algorithms and return findings
        """
        inefficiencies = []
        
        # Price deviation detection
        deviation = self.detect_price_deviation(price_data)
        if deviation:
            deviation["ticker"] = ticker
            inefficiencies.append(deviation)
            
        # Volume spike detection
        if price_data:
            volumes = [p["volume"] for p in price_data]
            volume_spike = self.detect_volume_spike(volumes)
            if volume_spike:
                volume_spike["ticker"] = ticker
                inefficiencies.append(volume_spike)
                
        # Momentum shift detection
        momentum = self.detect_momentum_shift(price_data)
        if momentum:
            momentum["ticker"] = ticker
            inefficiencies.append(momentum)
            
        # Support/Resistance break detection
        sr_break = self.detect_support_resistance_break(price_data)
        if sr_break:
            sr_break["ticker"] = ticker
            inefficiencies.append(sr_break)
            
        # Gap detection (if we have at least 2 days of data)
        if len(price_data) >= 2:
            gap = self.detect_gap(
                price_data[-2]["close"],
                price_data[-1]["open"]
            )
            if gap:
                gap["ticker"] = ticker
                inefficiencies.append(gap)
                
        # Spread anomaly detection (if quote data available)
        if quote_data and "bid" in quote_data and "ask" in quote_data:
            # For now, use a simple historical spread estimate
            historical_spreads = []
            for i in range(min(10, len(price_data))):
                # Estimate spread as percentage of price
                historical_spreads.append(0.01)  # 1 basis point default
                
            spread_anomaly = self.detect_spread_anomaly(
                quote_data["bid"],
                quote_data["ask"],
                historical_spreads
            )
            if spread_anomaly:
                spread_anomaly["ticker"] = ticker
                inefficiencies.append(spread_anomaly)
                
        return inefficiencies
        
    def _calculate_rsi(self, price_data: List[Dict], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index
        """
        if len(price_data) < period + 1:
            return None
            
        closes = [p["close"] for p in price_data]
        
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def rank_inefficiencies(self, inefficiencies: List[Dict]) -> List[Dict]:
        """
        Rank inefficiencies by combined strength and reliability
        """
        for inefficiency in inefficiencies:
            # Base score from strength
            score = inefficiency.get("strength", 50)
            
            # Bonus for volume confirmation
            if inefficiency.get("volume_confirmation"):
                score *= 1.2
                
            # Bonus for divergence patterns
            if inefficiency.get("divergence"):
                score *= 1.3
                
            # Penalty for wide spreads (less liquid)
            if inefficiency.get("type") == "spread_anomaly" and inefficiency.get("anomaly") == "wide":
                score *= 0.8
                
            inefficiency["score"] = min(score, 100)
            
        # Sort by score
        return sorted(inefficiencies, key=lambda x: x.get("score", 0), reverse=True)


# Singleton instance
inefficiency_detector = InefficiencyDetector()