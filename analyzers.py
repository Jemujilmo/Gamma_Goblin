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
        """Generate buy/sell signals based on multiple factors.
        
        Enhanced signal conditions including:
        - Trend alignment and momentum
        - Overbought/oversold reversal detection
        - Momentum divergence and exhaustion
        - Pattern recognition (bear/bull flags)
        - Volume confirmation
        
        Now scans ALL historical candles to show all past signals on chart.
        """
        signals = []
        try:
            # Scan through all candles, starting from candle 10 (need history for calculations)
            for i in range(10, len(data_5m)):
                # Get data up to current candle
                current_data = data_5m.iloc[:i+1]
                current_indicators = indicators_5m.iloc[:i+1]
                
                last_close = float(current_data['Close'].iloc[-1])
                last_timestamp = current_data.index[-1]
                
                # Get indicators for current and recent candles
                last_vwap = float(current_indicators['VWAP'].iloc[-1]) if 'VWAP' in current_indicators else None
                last_ema9 = float(current_indicators['EMA_fast'].iloc[-1]) if 'EMA_fast' in current_indicators else None
                last_ema21 = float(current_indicators['EMA_slow'].iloc[-1]) if 'EMA_slow' in current_indicators else None
                last_rsi = float(current_indicators['RSI'].iloc[-1]) if 'RSI' in current_indicators else None
                
                # Get recent price action for pattern detection
                recent_highs = current_data['High'].iloc[-5:].values if len(current_data) >= 5 else []
                recent_lows = current_data['Low'].iloc[-5:].values if len(current_data) >= 5 else []
                recent_closes = current_data['Close'].iloc[-5:].values if len(current_data) >= 5 else []
                recent_volumes = current_data['Volume'].iloc[-5:].values if len(current_data) >= 5 else []
                
                # Get momentum indicators over time
                rsi_values = current_indicators['RSI'].iloc[-10:].values if len(current_indicators) >= 10 else []

                # Normalize bias strings
                b5 = (bias_5m or '').lower()
                b15 = (bias_15m or '').lower()
                
                # Track signal strength (0-100)
                buy_score = 0
                sell_score = 0
                
                # === IMMEDIATE PRICE ACTION (Most Important) ===
                
                # Factor 1: Recent Price Momentum (30 points) - MOST CRITICAL
                if len(recent_closes) >= 3:
                    # Last 3 candles momentum
                    momentum_3 = recent_closes[-1] - recent_closes[-3]
                    momentum_pct = (momentum_3 / recent_closes[-3]) * 100 if recent_closes[-3] > 0 else 0
                    
                    if momentum_pct > 0.15:  # Rising
                        buy_score += 30
                    elif momentum_pct < -0.15:  # Falling
                        sell_score += 30
                    elif momentum_pct > 0:  # Slightly up
                        buy_score += 15
                    else:  # Slightly down
                        sell_score += 15
                
                # Factor 2: EMA crossover (25 points) - CRITICAL TREND
                if last_ema9 is not None and last_ema21 is not None:
                    if last_ema9 > last_ema21:
                        buy_score += 25
                    else:
                        sell_score += 25
                
                # Factor 3: Price vs VWAP (20 points)
                if last_vwap is not None:
                    if last_close > last_vwap:
                        buy_score += 20
                    else:
                        sell_score += 20
                
                # Factor 4: Bias alignment (10 points - REDUCED, too lagging)
                if 'bull' in b5:
                    buy_score += 5
                if 'bear' in b5:
                    sell_score += 5
                if 'bull' in b15:
                    buy_score += 5
                if 'bear' in b15:
                    sell_score += 5
                
                # === MOMENTUM & REVERSAL FACTORS ===
                
                # Factor 5: Breakdown/Breakout Detection (25 points)
                if len(recent_closes) >= 5 and len(recent_volumes) >= 5:
                    # Check if breaking below recent support or above resistance
                    recent_low = min(recent_lows)
                    recent_high = max(recent_highs)
                    avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
                    
                    # Breakdown: closing below recent low with volume
                    if last_close < recent_low and recent_volumes[-1] > avg_volume * 0.8:
                        sell_score += 25
                        buy_score -= 15
                    # Breakout: closing above recent high with volume  
                    elif last_close > recent_high and recent_volumes[-1] > avg_volume * 0.8:
                        buy_score += 25
                        sell_score -= 15
                
                # Factor 6: RSI regime with REVERSAL logic (25 points)
                if last_rsi is not None:
                    if 45 <= last_rsi <= 65:  # Healthy bullish zone
                        buy_score += 25
                    elif 35 <= last_rsi <= 55:  # Healthy bearish zone
                        sell_score += 25
                    elif last_rsi > 70:  # OVERBOUGHT - STRONG SELL SIGNAL
                        sell_score += 40  # Strong sell opportunity
                        buy_score = 0     # KILL all buy signals - too dangerous
                    elif last_rsi > 65:  # Getting overbought
                        sell_score += 20
                        buy_score -= 30   # Heavy penalty for buying near top
                    elif last_rsi < 30:  # OVERSOLD - STRONG BUY SIGNAL
                        buy_score += 40   # Strong buy opportunity
                        sell_score = 0    # KILL all sell signals - too dangerous
                    elif last_rsi < 35:  # Getting oversold
                        buy_score += 20
                        sell_score -= 30  # Heavy penalty for selling near bottom
                
                # Factor 7: Momentum Divergence (20 points)
                if len(rsi_values) >= 5 and len(recent_closes) >= 5:
                    # Price making higher highs but RSI declining = bearish divergence
                    price_trend = recent_closes[-1] - recent_closes[-5]
                    rsi_trend = rsi_values[-1] - rsi_values[-5]
                    
                    if price_trend > 0 and rsi_trend < -5:  # Bearish divergence
                        sell_score += 20
                        buy_score -= 15
                    elif price_trend < 0 and rsi_trend > 5:  # Bullish divergence
                        buy_score += 20
                        sell_score -= 15
                
                # Factor 8: Volume Confirmation (20 points - increased from 15)
                if len(recent_volumes) >= 5:
                    avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
                    last_volume = recent_volumes[-1]
                    
                    # Volume confirms downside momentum
                    if last_close < recent_closes[-2]:
                        if last_volume > avg_volume * 1.3:
                            sell_score += 20  # Strong selling pressure
                        elif last_volume > avg_volume * 2:
                            buy_score += 10  # Potential capitulation (reversal)
                    # Volume confirms upside momentum
                    elif last_close > recent_closes[-2]:
                        if last_volume > avg_volume * 1.3:
                            buy_score += 20  # Strong buying pressure
                        elif last_volume > avg_volume * 2:
                            sell_score += 10  # Potential exhaustion (reversal)
                
                # Factor 9: Pattern Recognition - Bear/Bull Flags (15 points)
                if len(recent_highs) >= 5 and len(recent_lows) >= 5:
                    # Bear flag: strong down move, then tight consolidation near lows
                    strong_down = recent_closes[0] > recent_closes[2] * 1.005
                    consolidating_low = max(recent_closes[-3:]) < recent_closes[0] * 0.998
                    if strong_down and consolidating_low:
                        sell_score += 15
                        
                    # Bull flag: strong up move, then tight consolidation near highs
                    strong_up = recent_closes[0] < recent_closes[2] * 0.995
                    consolidating_high = min(recent_closes[-3:]) > recent_closes[0] * 1.002
                    if strong_up and consolidating_high:
                        buy_score += 15
                
                # Factor 10: MACD Momentum (30 points) - Critical for trend reversals
                if 'MACD_histogram' in current_indicators.columns:
                    macd_hist = current_indicators['MACD_histogram']
                    macd_line = current_indicators['MACD']
                    signal_line = current_indicators['MACD_signal']
                    
                    if len(macd_hist) >= 3:
                        last_hist = macd_hist.iloc[-1]
                        prev_hist = macd_hist.iloc[-2]
                        
                        # CRITICAL: MACD crossover detection (EARLY signal)
                        # Bullish crossover - histogram crosses from negative to positive
                        if prev_hist < 0 and last_hist > 0:
                            buy_score += 35  # Strong early buy signal
                            sell_score = 0   # Kill all sells on bullish crossover
                        
                        # Bearish crossover - histogram crosses from positive to negative
                        elif prev_hist > 0 and last_hist < 0:
                            sell_score += 35  # Strong early sell signal
                            buy_score = 0     # Kill all buys on bearish crossover
                        
                        # DON'T trade when MACD already deep in one direction (too late!)
                        # If histogram has been negative for 3+ bars, DON'T sell more
                        elif len(macd_hist) >= 5:
                            last_3_hist = macd_hist.iloc[-3:].values
                            
                            # Already been bearish - too late to sell, might reverse soon
                            if all(h < -0.05 for h in last_3_hist):
                                sell_score = max(0, sell_score - 25)  # Penalize late sells
                                buy_score += 10  # Hint at potential reversal
                            
                            # Already been bullish - too late to buy, might reverse soon
                            elif all(h > 0.05 for h in last_3_hist):
                                buy_score = max(0, buy_score - 25)  # Penalize late buys
                                sell_score += 10  # Hint at potential reversal
                        
                        # Momentum acceleration (only if not already extended)
                        elif abs(last_hist) > abs(prev_hist) * 1.3 and abs(last_hist) < 0.3:
                            if last_hist > 0:  # Bullish accelerating
                                buy_score += 12
                            else:  # Bearish accelerating
                                sell_score += 12
                
                # === GENERATE SIGNALS - Always show best guess, even if weak ===
                # Signal if one side dominates by at least 15 points OR score > 45%
                min_threshold = 45  # Raised from 35 - be more conservative
                score_difference = abs(buy_score - sell_score)
                
                # SAFETY CIRCUIT BREAKERS - Block obviously bad signals
                # 1. Never buy if RSI > 68 (too risky)
                if last_rsi and last_rsi > 68:
                    buy_score = 0
                    if sell_score < 35:  # If sell also weak, boost it
                        sell_score = max(sell_score, 50)
                
                # 2. Never sell if RSI < 32 (too risky)
                if last_rsi and last_rsi < 32:
                    sell_score = 0
                    if buy_score < 35:
                        buy_score = max(buy_score, 50)
                
                # 3. Don't buy if recent momentum is strongly negative
                if len(recent_closes) >= 3:
                    recent_momentum = (recent_closes[-1] - recent_closes[-3]) / recent_closes[-3] * 100
                    if recent_momentum < -0.3:  # Falling fast
                        buy_score = max(0, buy_score - 30)
                    elif recent_momentum > 0.3:  # Rising fast
                        sell_score = max(0, sell_score - 30)
                
                # Determine signal strength label
                def get_strength_label(score):
                    if score >= 80:
                        return "STRONG"
                    elif score >= 65:
                        return "MODERATE"
                    elif score >= 45:
                        return "WEAK"
                    else:
                        return "VERY WEAK"
                
                # Generate BUY signal
                if buy_score > sell_score and (buy_score >= min_threshold or score_difference >= 10):
                    strength_label = get_strength_label(buy_score)
                    
                    # Determine signal type
                    if last_rsi and last_rsi < 30:
                        signal_type = f'{strength_label} COUNTER-TREND BUY'
                    elif last_rsi and last_rsi > 70:
                        signal_type = f'{strength_label} RISKY BUY (Overbought)'
                    else:
                        signal_type = f'{strength_label} BUY'
                    
                    signals.append({
                        'timestamp': last_timestamp,
                        'price': last_close,
                        'type': 'buy',
                        'strength': min(100, buy_score),
                        'label': f'{signal_type} ({buy_score}%)'
                    })
                    # Only print latest signal to avoid spam
                    if i == len(data_5m) - 1:
                        print(f"✅ {signal_type}: {buy_score}% at ${last_close:.2f} (SELL: {sell_score}%)")
                    
                # Generate SELL signal
                elif sell_score > buy_score and (sell_score >= min_threshold or score_difference >= 10):
                    strength_label = get_strength_label(sell_score)
                    
                    # Determine signal type
                    if last_rsi and last_rsi > 70:
                        signal_type = f'{strength_label} COUNTER-TREND SELL'
                    elif last_rsi and last_rsi < 30:
                        signal_type = f'{strength_label} RISKY SELL (Oversold)'
                    else:
                        signal_type = f'{strength_label} SELL'
                    
                    signals.append({
                        'timestamp': last_timestamp,
                        'price': last_close,
                        'type': 'sell',
                        'strength': min(100, sell_score),
                        'label': f'{signal_type} ({sell_score}%)'
                    })
                    # Only print latest signal to avoid spam
                    if i == len(data_5m) - 1:
                        print(f"✅ {signal_type}: {sell_score}% at ${last_close:.2f} (BUY: {buy_score}%)")
                    
                # No clear winner - only log for latest candle
                elif i == len(data_5m) - 1:
                    print(f"⚖️ NEUTRAL: BUY={buy_score}%, SELL={sell_score}% (too close to call)")
            
            # Print summary of all signals found
            print(f"📊 Signal scan complete: Found {len(signals)} total signals ({sum(1 for s in signals if s['type']=='buy')} BUY, {sum(1 for s in signals if s['type']=='sell')} SELL)")
                
        except Exception as e:
            # Be tolerant: return empty signals on any failure
            print(f"Signal generation error: {e}")
            import traceback
            traceback.print_exc()
            return []
        return signals
