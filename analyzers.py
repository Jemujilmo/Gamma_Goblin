"""Lightweight analyzers used by the Flask dashboard.

This file provides minimal, safe implementations for:
- OptionsWallAnalyzer.get_options_walls(price)
- SentimentAnalyzer.analyze_sentiment(...)

They are intentionally simple so the web UI won't crash when the
full production analyzers are not available.
"""
from datetime import datetime
from typing import List, Dict


class OptionsWallAnalyzer:
    """Return a small set of synthetic options walls (support/resistance).

    This is a fallback implementation to avoid NameError in the dashboard.
    It creates a few strikes around the current price with decreasing strength.
    """
    def __init__(self):
        pass

    def get_options_walls(self, price: float) -> List[Dict]:
        try:
            base = round(float(price))
        except Exception:
            base = 0

        offsets = [-3, -2, -1, 1, 2]
        walls = []
        for i, off in enumerate(offsets):
            strike = float(base + off)
            walls.append({
                'strike': strike,
                'type': 'resistance' if off > 0 else 'support',
                'strength': max(10, 90 - i * 15)
            })
        return walls


class SentimentAnalyzer:
    """Simple sentiment/signal generator used by the UI.

    It emits a single weak buy/sell signal based on price vs VWAP and
    the provided bias strings. This keeps the visualization meaningful
    without depending on heavier ML or external services.
    """
    def __init__(self):
        pass

    def analyze_sentiment(self, data_5m, indicators_5m, bias_5m, bias_15m):
        signals = []
        try:
            last_close = float(data_5m['Close'].iloc[-1])
            last_vwap = float(indicators_5m['VWAP'].iloc[-1]) if 'VWAP' in indicators_5m else None

            # Normalize bias strings
            b5 = (bias_5m or '').lower()
            if last_vwap is not None:
                if last_close > last_vwap and 'bull' in b5:
                    signals.append({
                        'timestamp': data_5m.index[-1],
                        'price': last_close,
                        'type': 'buy',
                        'strength': 60,
                        'label': 'Auto BUY'
                    })
                elif last_close < last_vwap and 'bear' in b5:
                    signals.append({
                        'timestamp': data_5m.index[-1],
                        'price': last_close,
                        'type': 'sell',
                        'strength': 60,
                        'label': 'Auto SELL'
                    })
        except Exception:
            # Be tolerant: return empty signals on any failure
            return []
        return signals
