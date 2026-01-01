"""
Signal generator module - Creates structured trading signals

⚠️ DEPRECATED: This file is no longer used in production.
The new signal logic is in new_signal_logic.py which uses multi-timeframe
confirmation with VWAP, EMA crossovers, and MACD momentum.

This file remains for backward compatibility with test files.
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from bias_classifier import BiasClassifier, MarketBias
from indicators import detect_volatility_regime


class SignalGenerator:
    """
    Generates structured trading signals based on technical analysis.
    """
    
    def __init__(self, bias_classifier: BiasClassifier):
        """
        Initialize the signal generator.
        
        Args:
            bias_classifier: BiasClassifier instance for determining market bias
        """
        self.classifier = bias_classifier
    
    def generate_signal(
        self,
        ticker: str,
        timeframe: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive trading signal.
        
        Args:
            ticker: Stock ticker symbol
            timeframe: Timeframe being analyzed (e.g., "5m", "15m")
            df: DataFrame with all calculated indicators
        
        Returns:
            Dictionary containing structured signal information
        """
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Classify bias
        bias, confidence, notes = self.classifier.classify_bias(latest)
        
        # Detect volatility regime
        volatility_regime = detect_volatility_regime(df['ATR'])
        
        # Get current timestamp
        timestamp = latest.name if hasattr(latest.name, 'strftime') else datetime.now()
        
        # Build the signal dictionary
        signal = {
            "ticker": ticker,
            "timeframe": timeframe,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp),
            "bias": bias.value,
            "confidence": round(confidence, 3),
            "confidence_label": self.classifier.get_bias_strength_label(confidence),
            "volatility_regime": volatility_regime,
            "indicators": {
                "close": round(latest['Close'], 2),
                "ema_9": round(latest['EMA_fast'], 2) if pd.notna(latest['EMA_fast']) else None,
                "ema_21": round(latest['EMA_slow'], 2) if pd.notna(latest['EMA_slow']) else None,
                "rsi": round(latest['RSI'], 1) if pd.notna(latest['RSI']) else None,
                "atr": round(latest['ATR'], 2) if pd.notna(latest['ATR']) else None,
                "vwap": round(latest['VWAP'], 2) if pd.notna(latest['VWAP']) else None
            },
            "analysis_notes": notes
        }
        
        return signal
    
    def generate_multi_timeframe_signal(
        self,
        ticker: str,
        timeframe_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Generate a multi-timeframe analysis signal.
        
        Args:
            ticker: Stock ticker symbol
            timeframe_data: Dictionary mapping timeframe names to DataFrames
                           e.g., {"5m": df_5m, "15m": df_15m}
        
        Returns:
            Dictionary containing signals for all timeframes plus synthesis
        """
        signals = {}
        
        # Generate signal for each timeframe
        for tf_name, df in timeframe_data.items():
            signals[tf_name] = self.generate_signal(ticker, tf_name, df)
        
        # Synthesize overall recommendation
        synthesis = self._synthesize_signals(signals)
        
        return {
            "ticker": ticker,
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timeframes": signals,
            "synthesis": synthesis
        }
    
    def _synthesize_signals(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize multiple timeframe signals into overall recommendation.
        
        Args:
            signals: Dictionary of timeframe signals
        
        Returns:
            Dictionary with synthesized analysis
        """
        biases = [s['bias'] for s in signals.values()]
        confidences = [s['confidence'] for s in signals.values()]
        
        # Count bias alignment
        bullish_count = sum(1 for b in biases if b == MarketBias.BULLISH.value)
        bearish_count = sum(1 for b in biases if b == MarketBias.BEARISH.value)
        neutral_count = sum(1 for b in biases if b == MarketBias.NEUTRAL.value)
        
        # Determine overall bias
        if bullish_count > bearish_count:
            overall_bias = MarketBias.BULLISH.value
        elif bearish_count > bullish_count:
            overall_bias = MarketBias.BEARISH.value
        else:
            overall_bias = MarketBias.NEUTRAL.value
        
        # Average confidence (weighted by alignment)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Determine alignment strength
        total_timeframes = len(signals)
        max_alignment = max(bullish_count, bearish_count, neutral_count)
        alignment_ratio = max_alignment / total_timeframes if total_timeframes > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_bias,
            avg_confidence,
            alignment_ratio,
            signals
        )
        
        return {
            "overall_bias": overall_bias,
            "average_confidence": round(avg_confidence, 3),
            "timeframe_alignment": f"{max_alignment}/{total_timeframes} timeframes agree",
            "alignment_strength": "Strong" if alignment_ratio >= 0.8 else "Moderate" if alignment_ratio >= 0.5 else "Weak",
            "recommendations": recommendations
        }
    
    def _generate_recommendations(
        self,
        bias: str,
        confidence: float,
        alignment: float,
        signals: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Generate plain-English trading recommendations.
        
        Args:
            bias: Overall market bias
            confidence: Average confidence score
            alignment: Timeframe alignment ratio
            signals: All timeframe signals
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Get volatility regimes
        vol_regimes = [s['volatility_regime'] for s in signals.values()]
        expansion_count = sum(1 for v in vol_regimes if v == "Expansion")
        
        # Bias-based recommendations
        if bias == MarketBias.BULLISH.value:
            if confidence >= 0.75 and alignment >= 0.8:
                recommendations.append("Strong bullish setup - consider directional call options or bullish spreads")
            elif confidence >= 0.5:
                recommendations.append("Moderate bullish bias - smaller directional positions or credit puts may be appropriate")
            else:
                recommendations.append("Weak bullish signal - consider waiting for stronger confirmation")
        
        elif bias == MarketBias.BEARISH.value:
            if confidence >= 0.75 and alignment >= 0.8:
                recommendations.append("Strong bearish setup - consider directional put options or bearish spreads")
            elif confidence >= 0.5:
                recommendations.append("Moderate bearish bias - smaller directional positions or credit calls may be appropriate")
            else:
                recommendations.append("Weak bearish signal - consider waiting for stronger confirmation")
        
        else:
            recommendations.append("Neutral/mixed signals - theta strategies (iron condors, strangles) may be more appropriate")
        
        # Volatility-based recommendations
        if expansion_count >= len(vol_regimes) * 0.7:
            recommendations.append("Volatility expanding - directional strategies may benefit from increased movement")
        elif expansion_count <= len(vol_regimes) * 0.3:
            recommendations.append("Volatility compressing - theta decay strategies may be favorable")
        
        # Alignment-based recommendations
        if alignment < 0.6:
            recommendations.append("Timeframes show divergence - reduce position size or wait for alignment")
        
        return recommendations
