"""
Bias classifier module - Determines market bias and confidence

⚠️ DEPRECATED: This file is no longer used in production.
The new signal logic in new_signal_logic.py directly evaluates VWAP positioning,
EMA crossovers, and MACD momentum without separate bias classification.

This file remains for backward compatibility with test files.
"""
import pandas as pd
from typing import Dict, Tuple, List
from enum import Enum


class MarketBias(Enum):
    """Market bias enumeration"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class BiasClassifier:
    """
    Classifies market bias based on technical indicators.
    """
    
    def __init__(self, rsi_bullish_threshold: float = 55, rsi_bearish_threshold: float = 45):
        """
        Initialize the bias classifier.
        
        Args:
            rsi_bullish_threshold: RSI level above which is considered bullish
            rsi_bearish_threshold: RSI level below which is considered bearish
        """
        self.rsi_bullish = rsi_bullish_threshold
        self.rsi_bearish = rsi_bearish_threshold
    
    def classify_bias(self, latest_data: pd.Series) -> Tuple[MarketBias, float, List[str]]:
        """
        Classify market bias based on multiple conditions.
        
        Args:
            latest_data: Series containing the latest indicator values
                Must include: Close, VWAP, EMA_fast, EMA_slow, RSI
        
        Returns:
            Tuple of (bias, confidence_score, notes)
            - bias: MarketBias enum value
            - confidence_score: Float between 0.0 and 1.0
            - notes: List of strings explaining the classification
        """
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        notes = []
        
        # Condition 1: Close vs VWAP
        if pd.notna(latest_data['Close']) and pd.notna(latest_data['VWAP']):
            total_signals += 1
            if latest_data['Close'] > latest_data['VWAP']:
                bullish_signals += 1
                notes.append(f"Price above VWAP ({latest_data['Close']:.2f} > {latest_data['VWAP']:.2f})")
            else:
                bearish_signals += 1
                notes.append(f"Price below VWAP ({latest_data['Close']:.2f} < {latest_data['VWAP']:.2f})")
        
        # Condition 2: EMA9 vs EMA21
        if pd.notna(latest_data['EMA_fast']) and pd.notna(latest_data['EMA_slow']):
            total_signals += 1
            if latest_data['EMA_fast'] > latest_data['EMA_slow']:
                bullish_signals += 1
                notes.append(f"EMA9 above EMA21 ({latest_data['EMA_fast']:.2f} > {latest_data['EMA_slow']:.2f})")
            else:
                bearish_signals += 1
                notes.append(f"EMA9 below EMA21 ({latest_data['EMA_fast']:.2f} < {latest_data['EMA_slow']:.2f})")
        
        # Condition 3: RSI regime
        if pd.notna(latest_data['RSI']):
            total_signals += 1
            rsi_value = latest_data['RSI']
            
            if rsi_value > self.rsi_bullish:
                bullish_signals += 1
                notes.append(f"RSI bullish regime ({rsi_value:.1f} > {self.rsi_bullish})")
            elif rsi_value < self.rsi_bearish:
                bearish_signals += 1
                notes.append(f"RSI bearish regime ({rsi_value:.1f} < {self.rsi_bearish})")
            else:
                notes.append(f"RSI neutral zone ({rsi_value:.1f})")
        
        # Determine bias and confidence
        if total_signals == 0:
            return MarketBias.NEUTRAL, 0.0, ["Insufficient data for bias classification"]
        
        # Calculate confidence based on alignment
        bullish_ratio = bullish_signals / total_signals
        bearish_ratio = bearish_signals / total_signals
        
        # Determine bias
        if bullish_signals > bearish_signals:
            bias = MarketBias.BULLISH
            confidence = bullish_ratio
        elif bearish_signals > bullish_signals:
            bias = MarketBias.BEARISH
            confidence = bearish_ratio
        else:
            bias = MarketBias.NEUTRAL
            confidence = 0.5
        
        # Add summary note
        alignment_note = f"Bias confidence: {bullish_signals}/{total_signals} bullish, {bearish_signals}/{total_signals} bearish"
        notes.insert(0, alignment_note)
        
        return bias, confidence, notes
    
    def get_bias_strength_label(self, confidence: float) -> str:
        """
        Convert confidence score to a human-readable label.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            String label describing bias strength
        """
        if confidence >= 0.9:
            return "Very Strong"
        elif confidence >= 0.75:
            return "Strong"
        elif confidence >= 0.6:
            return "Moderate"
        elif confidence >= 0.4:
            return "Weak"
        else:
            return "Very Weak"
