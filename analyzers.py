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

    def analyze_sentiment(self, data_1m, data_5m, data_15m, indicators_1m, indicators_5m, indicators_15m):
        """
        Multi-timeframe signal generation with strict quality filters.
        
        PHILOSOPHY:
        - Signals only when multiple conditions align across timeframes
        - VWAP is institutional bias anchor
        - RSI confirms momentum, not overbought/oversold
        - MACD shows trend direction and momentum shift
        - Volume confirms conviction
        - Avoid signals in chop/low-volume conditions
        
        TIMEFRAME HIERARCHY:
        - 15m: Overall trend direction (bullish/bearish bias)
        - 5m: Setup confirmation (price structure)
        - 1m: Entry timing (precise entry/exit)
        
        Args:
            data_1m: 1-minute OHLCV data
            data_5m: 5-minute OHLCV data
            data_15m: 15-minute OHLCV data
            indicators_1m: 1-minute indicators (MACD, RSI, VWAP, EMA)
            indicators_5m: 5-minute indicators
            indicators_15m: 15-minute indicators
        
        Returns:
            List of signal dictionaries with timestamp, price, type, strength
        """
        signals = []
        
        try:
            # Need minimum data to calculate signals
            if len(data_5m) < 20 or len(data_1m) < 20:
                return signals
            
            # Scan through 5m candles (primary timeframe for signal generation)
            # Start at candle 20 to have enough history
            for i in range(20, len(data_5m)):
                # Get current 5m candle data
                current_5m_data = data_5m.iloc[:i+1]
                current_5m_indicators = indicators_5m.iloc[:i+1]
                
                # Extract current 5m values
                timestamp_5m = current_5m_data.index[-1]
                close_5m = float(current_5m_data['Close'].iloc[-1])
                volume_5m = float(current_5m_data['Volume'].iloc[-1])
                
                # Get 5m indicators
                vwap_5m = float(current_5m_indicators['VWAP'].iloc[-1]) if 'VWAP' in current_5m_indicators.columns else None
                ema9_5m = float(current_5m_indicators['EMA_fast'].iloc[-1]) if 'EMA_fast' in current_5m_indicators.columns else None
                ema21_5m = float(current_5m_indicators['EMA_slow'].iloc[-1]) if 'EMA_slow' in current_5m_indicators.columns else None
                rsi_5m = float(current_5m_indicators['RSI'].iloc[-1]) if 'RSI' in current_5m_indicators.columns else None
                
                # Get MACD components (5m)
                macd_5m = None
                macd_signal_5m = None
                macd_hist_5m = None
                if 'MACD' in current_5m_indicators.columns and 'MACD_signal' in current_5m_indicators.columns:
                    macd_5m = float(current_5m_indicators['MACD'].iloc[-1])
                    macd_signal_5m = float(current_5m_indicators['MACD_signal'].iloc[-1])
                    macd_hist_5m = macd_5m - macd_signal_5m
                    
                    # Previous histogram for momentum shift detection
                    if len(current_5m_indicators) >= 2:
                        prev_macd = float(current_5m_indicators['MACD'].iloc[-2])
                        prev_signal = float(current_5m_indicators['MACD_signal'].iloc[-2])
                        prev_hist_5m = prev_macd - prev_signal
                
                # Get corresponding 15m candle (for trend context)
                # Find the 15m candle that contains this 5m timestamp
                mask_15m = data_15m.index <= timestamp_5m
                if mask_15m.any():
                    current_15m_data = data_15m[mask_15m]
                    current_15m_indicators = indicators_15m[mask_15m]
                    
                    if len(current_15m_data) > 0:
                        close_15m = float(current_15m_data['Close'].iloc[-1])
                        vwap_15m = float(current_15m_indicators['VWAP'].iloc[-1]) if 'VWAP' in current_15m_indicators.columns else None
                        ema9_15m = float(current_15m_indicators['EMA_fast'].iloc[-1]) if 'EMA_fast' in current_15m_indicators.columns else None
                        ema21_15m = float(current_15m_indicators['EMA_slow'].iloc[-1]) if 'EMA_slow' in current_15m_indicators.columns else None
                        
                        # MACD 15m for trend
                        macd_hist_15m = None
                        if 'MACD' in current_15m_indicators.columns and 'MACD_signal' in current_15m_indicators.columns:
                            macd_15m = float(current_15m_indicators['MACD'].iloc[-1])
                            signal_15m = float(current_15m_indicators['MACD_signal'].iloc[-1])
                            macd_hist_15m = macd_15m - signal_15m
                else:
                    # No 15m data available, skip this signal
                    continue
                
                # Get corresponding 1m candles (for entry timing)
                # Find 1m candles within the current 5m period
                mask_1m = (data_1m.index > timestamp_5m - pd.Timedelta(minutes=5)) & (data_1m.index <= timestamp_5m)
                if mask_1m.any():
                    recent_1m_data = data_1m[mask_1m]
                    recent_1m_indicators = indicators_1m[mask_1m]
                    
                    if len(recent_1m_data) > 0:
                        # Latest 1m values
                        close_1m = float(recent_1m_data['Close'].iloc[-1])
                        volume_1m = float(recent_1m_data['Volume'].iloc[-1])
                        
                        # 1m indicators
                        vwap_1m = float(recent_1m_indicators['VWAP'].iloc[-1]) if 'VWAP' in recent_1m_indicators.columns else None
                        rsi_1m = float(recent_1m_indicators['RSI'].iloc[-1]) if 'RSI' in recent_1m_indicators.columns else None
                        
                        # MACD 1m for momentum shift
                        macd_hist_1m = None
                        macd_increasing_1m = False
                        if 'MACD' in recent_1m_indicators.columns and 'MACD_signal' in recent_1m_indicators.columns:
                            macd_1m = float(recent_1m_indicators['MACD'].iloc[-1])
                            signal_1m = float(recent_1m_indicators['MACD_signal'].iloc[-1])
                            macd_hist_1m = macd_1m - signal_1m
                            
                            # Check if MACD histogram is increasing (momentum shift)
                            if len(recent_1m_indicators) >= 2:
                                prev_macd_1m = float(recent_1m_indicators['MACD'].iloc[-2])
                                prev_signal_1m = float(recent_1m_indicators['MACD_signal'].iloc[-2])
                                prev_hist_1m = prev_macd_1m - prev_signal_1m
                                macd_increasing_1m = macd_hist_1m > prev_hist_1m
                else:
                    # No 1m data, skip
                    continue
                
                # ==============================================================
                # SIGNAL GENERATION LOGIC - Multi-Timeframe Confirmation
                # ==============================================================
                
                # --- FILTER 1: Volume Check (Avoid Low-Volume Chop) ---
                # WHY: Low volume = no conviction, signals are unreliable
                # THRESHOLD: Volume must be above 70% of recent average
                avg_volume_5m = current_5m_data['Volume'].iloc[-10:].mean()
                if volume_5m < avg_volume_5m * 0.7:
                    continue  # Skip low-volume candles
                
                # --- FILTER 2: VWAP Flatness Check (Avoid Choppy Markets) ---
                # WHY: Flat VWAP = consolidation/chop, not trending
                # THRESHOLD: VWAP must move > 0.1% over last 5 candles
                if vwap_5m is not None and len(current_5m_indicators) >= 5:
                    vwap_5_candles_ago = float(current_5m_indicators['VWAP'].iloc[-5])
                    vwap_movement_pct = abs((vwap_5m - vwap_5_candles_ago) / vwap_5_candles_ago) * 100
                    if vwap_movement_pct < 0.1:
                        continue  # VWAP too flat, skip
                
                # ==============================================================
                # BUY SIGNAL LOGIC
                # ==============================================================
                
                buy_conditions_met = 0
                buy_conditions_required = 5  # Must meet at least 5/7 conditions
                
                # CONDITION 1: 15m Trend - Price above VWAP (Bullish bias)
                # WHY: Higher timeframe sets the trend direction
                if vwap_15m is not None and close_15m > vwap_15m:
                    buy_conditions_met += 1
                
                # CONDITION 2: 5m Setup - Price above VWAP (Setup confirmation)
                # WHY: 5m confirms we're in bullish structure
                if vwap_5m is not None and close_5m > vwap_5m:
                    buy_conditions_met += 1
                
                # CONDITION 3: 1m Entry - Pullback toward VWAP or EMA (Entry timing)
                # WHY: Want to buy on dips, not chase
                    if 'bear' in b5:
                        sell_score += 5
                    if 'bull' in b15:
                        buy_score += 5
                    if 'bear' in b15:
                        sell_score += 5
                
                # === MOMENTUM & REVERSAL FACTORS ===
                
                # Factor 5: Breakdown/Breakout Detection (35 points)
                # KEY: Breakdown detection was crucial for the 14:10 trade
                if len(recent_closes) >= 5 and len(recent_volumes) >= 5:
                    # Check if breaking below recent support or above resistance
                    recent_low = min(recent_lows)
                    recent_high = max(recent_highs)
                    avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
                    
                    # Breakdown: closing below recent low with volume - PROFIT MAKER!
                    if last_close < recent_low and recent_volumes[-1] > avg_volume * 0.8:
                        sell_score += 35  # Increased from 25 - breakdowns are GOLD
                        buy_score -= 25   # Stronger penalty for buying in breakdown
                    # Breakout: closing above recent high with volume  
                    elif last_close > recent_high and recent_volumes[-1] > avg_volume * 0.8:
                        buy_score += 35
                        sell_score -= 25
                
                # Factor 6: RSI regime with LOCAL TREND AWARENESS (25 points)
                if last_rsi is not None:
                    if 45 <= last_rsi <= 65:  # Healthy bullish zone
                        buy_score += 25
                    elif 35 <= last_rsi <= 55:  # Healthy bearish zone
                        sell_score += 25
                    elif last_rsi > 70:  # OVERBOUGHT - but check if in uptrend!
                        if local_bullish:
                            # In uptrend, overbought can stay overbought - don't sell
                            sell_score += 10  # Mild caution only
                        else:
                            # Not in uptrend, overbought is sell signal
                            sell_score += 40
                            buy_score = 0
                    elif last_rsi > 65:  # Getting overbought
                        if not local_bullish:
                            sell_score += 20
                            buy_score -= 30
                        # else: in uptrend, allow it
                    elif last_rsi < 30:  # OVERSOLD - but check trend!
                        if local_bearish:
                            # In downtrend, oversold can get more oversold - don't buy
                            buy_score += 10  # Mild bounce potential only
                        else:
                            # Not in downtrend, oversold is buy signal
                            buy_score += 40
                            sell_score = 0
                    elif last_rsi < 35:  # Getting oversold
                        if not local_bearish:
                            buy_score += 20
                            sell_score -= 30
                        # else: in downtrend, allow it
                
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
                
                # Factor 8: Volume Confirmation (25 points)
                # CRITICAL: Volume surge during downtrend = major profit opportunity
                if len(recent_volumes) >= 5:
                    avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
                    last_volume = recent_volumes[-1]
                    
                    # Volume confirms downside momentum - THIS MADE THE 14:10 TRADE!
                    if last_close < recent_closes[-2]:
                        if last_volume > avg_volume * 1.3:
                            sell_score += 25  # Strong selling pressure = SELL OPPORTUNITIES
                            # BONUS: If price also breaking down with volume
                            if len(recent_lows) >= 5 and last_close < min(recent_lows):
                                sell_score += 15  # Extra confirmation
                        elif last_volume > avg_volume * 2:
                            buy_score += 10  # Potential capitulation (reversal)
                    # Volume confirms upside momentum
                    elif last_close > recent_closes[-2]:
                        if last_volume > avg_volume * 1.3:
                            buy_score += 25  # Strong buying pressure
                            # BONUS: If price also breaking out with volume
                            if len(recent_highs) >= 5 and last_close > max(recent_highs):
                                buy_score += 15  # Extra confirmation
                        elif last_volume > avg_volume * 2:
                            sell_score += 10  # Potential exhaustion (reversal)
                
                # Factor 9: Pattern Recognition - Bear/Bull Flags (15 points)
                if len(recent_highs) >= 5 and len(recent_lows) >= 5:
                    # Bear flag: strong down move, then tight consolidation near lows
                    strong_down = recent_closes[0] > recent_closes[2] * 1.005
                    consolidating_low = max(recent_closes[-3:]) < recent_closes[0] * 0.998
                    if strong_down and consolidating_low:
                        sell_score += 15
                    
                    # CRITICAL: Consecutive lower highs and lower lows (14:10 pattern)
                    # This is characteristic of strong downtrends
                    if len(recent_highs) >= 4 and len(recent_lows) >= 4:
                        lower_highs = recent_highs[-1] < recent_highs[-2] < recent_highs[-3]
                        lower_lows = recent_lows[-1] < recent_lows[-2] < recent_lows[-3]
                        if lower_highs and lower_lows:
                            sell_score += 20  # Strong downtrend pattern
                            buy_score -= 15   # Dangerous to buy here
                        
                    # Bull flag: strong up move, then tight consolidation near highs
                    strong_up = recent_closes[0] < recent_closes[2] * 0.995
                    consolidating_high = min(recent_closes[-3:]) > recent_closes[0] * 1.002
                    if strong_up and consolidating_high:
                        buy_score += 15
                    
                    # Consecutive higher highs and higher lows (bull pattern)
                    if len(recent_highs) >= 4 and len(recent_lows) >= 4:
                        higher_highs = recent_highs[-1] > recent_highs[-2] > recent_highs[-3]
                        higher_lows = recent_lows[-1] > recent_lows[-2] > recent_lows[-3]
                        if higher_highs and higher_lows:
                            buy_score += 20  # Strong uptrend pattern
                            sell_score -= 15
                
                # Factor 10: MACD Momentum (30 points) - Critical for trend reversals
                if 'MACD_histogram' in current_indicators.columns:
                    macd_hist = current_indicators['MACD_histogram']
                    macd_line = current_indicators['MACD']
                    signal_line = current_indicators['MACD_signal']
                    
                    if len(macd_hist) >= 3:
                        last_hist = macd_hist.iloc[-1]
                        prev_hist = macd_hist.iloc[-2]
                        
                        # CRITICAL: Check MACD trend direction (prevent bad signals)
                        if len(macd_hist) >= 5:
                            # Calculate MACD histogram trend over last 5 bars
                            macd_trend = macd_hist.iloc[-1] - macd_hist.iloc[-5]
                            
                            # NEVER BUY if MACD histogram is declining (downtrend)
                            if macd_trend < -0.02:  # Strong downward MACD trend
                                buy_score = max(0, buy_score - 40)  # Heavy penalty
                                sell_score += 15  # Favor sells in downtrend
                            
                            # NEVER SELL if MACD histogram is rising (uptrend)
                            elif macd_trend > 0.02:  # Strong upward MACD trend
                                sell_score = max(0, sell_score - 40)  # Heavy penalty
                                buy_score += 15  # Favor buys in uptrend
                        
                        # CRITICAL: MACD crossover detection (EARLY signal)
                        # Bullish crossover - histogram crosses from negative to positive
                        if prev_hist < 0 and last_hist > 0:
                            buy_score += 35  # Strong early buy signal
                            sell_score = 0   # Kill all sells on bullish crossover
                        
                        # Bearish crossover - histogram crosses from positive to negative
                        # THIS IS THE MONEY MAKER - 14:10 trade example
                        elif prev_hist > 0 and last_hist < 0:
                            sell_score += 45  # MAJOR early sell signal (increased from 35)
                            buy_score = 0     # Kill all buys on bearish crossover
                            print(f"🎯 MACD BEARISH CROSSOVER DETECTED - High probability sell setup!")
                        
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
                
                # 0. MACD + EMA DEFINE IMMEDIATE MARKET STATE (not just overall bias)
                # Follow the CURRENT volume flow and price position
                macd_buying_pressure = False
                macd_selling_pressure = False
                price_above_emas = False
                price_below_emas = False
                
                if 'MACD' in current_indicators and 'MACD_signal' in current_indicators:
                    if len(current_indicators) >= 3:
                        # Current histogram
                        last_macd = float(current_indicators['MACD'].iloc[-1])
                        last_signal = float(current_indicators['MACD_signal'].iloc[-1])
                        curr_histogram = last_macd - last_signal
                        
                        # Previous histogram for trend
                        prev_macd = float(current_indicators['MACD'].iloc[-2])
                        prev_signal = float(current_indicators['MACD_signal'].iloc[-2])
                        prev_histogram = prev_macd - prev_signal
                        
                        # Detect histogram direction (volume flow)
                        macd_buying_pressure = curr_histogram > prev_histogram * 1.05 or (curr_histogram > 0 and prev_histogram < 0)
                        macd_selling_pressure = curr_histogram < prev_histogram * 0.95 or (curr_histogram < 0 and prev_histogram > 0)
                
                # Check price position relative to EMAs (immediate trend)
                if last_ema9 is not None and last_ema21 is not None and last_close is not None:
                    price_above_emas = last_close > last_ema9 and last_ema9 > last_ema21
                    price_below_emas = last_close < last_ema9 and last_ema9 < last_ema21
                
                # 1. MACD STRENGTH CHECK - Kill signals when histogram is too weak (low conviction)
                # Weak MACD = indecisive market, avoid trading
                macd_too_weak = False
                if 'MACD' in current_indicators and 'MACD_signal' in current_indicators:
                    if len(current_indicators) >= 2:
                        last_macd = float(current_indicators['MACD'].iloc[-1])
                        last_signal = float(current_indicators['MACD_signal'].iloc[-1])
                        curr_histogram = abs(last_macd - last_signal)
                        
                        # If histogram magnitude is below 0.15, MACD is too weak
                        # This indicates very low conviction - penalize heavily
                        if curr_histogram < 0.15:
                            macd_too_weak = True
                            buy_score = max(0, buy_score - 30)  # Heavy penalty
                            sell_score = max(0, sell_score - 30)  # Heavy penalty
                
                # 2. LOCAL MARKET STATE takes priority over overall bias
                # If MACD + price action shows uptrend, allow buys even if overall bias is bearish
                local_bullish = macd_buying_pressure or price_above_emas
                local_bearish = macd_selling_pressure or price_below_emas
                
                if local_bearish and not local_bullish:
                    # Currently in downtrend - be cautious with buys
                    buy_score = max(0, buy_score - 30)
                    if sell_score < 50:
                        sell_score = max(sell_score, 55)
                elif local_bullish and not local_bearish:
                    # Currently in uptrend - be cautious with sells
                    sell_score = max(0, sell_score - 30)
                    if buy_score < 50:
                        buy_score = max(buy_score, 55)
                # If both or neither, let normal scoring proceed
                
                # 3. Never buy if RSI > 68 (too risky)
                if last_rsi and last_rsi > 68:
                    buy_score = 0
                    if sell_score < 35:  # If sell also weak, boost it
                        sell_score = max(sell_score, 50)
                
                # 4. Tighter RSI sell blocker - don't sell into deep oversold (changed from 32 to 25)
                # This allows sells when RSI 25-32 during strong downtrends
                if last_rsi and last_rsi < 25:
                    sell_score = 0
                    if buy_score < 35:
                        buy_score = max(buy_score, 50)
                
                # 5. MOMENTUM filter - respect LOCAL market state
                # Allow signals that match current MACD + EMA trend
                if len(recent_closes) >= 5:
                    recent_momentum = (recent_closes[-1] - recent_closes[-3]) / recent_closes[-3] * 100
                    recent_range = max(recent_closes[-5:]) - min(recent_closes[-5:])
                    avg_price = sum(recent_closes[-5:]) / 5
                    range_pct = (recent_range / avg_price) * 100
                    
                    # In consolidation, be permissive
                    if range_pct < 0.2:
                        if recent_momentum < -0.25:
                            buy_score = max(0, buy_score - 20)
                        elif recent_momentum > 0.25:
                            sell_score = max(0, sell_score - 20)
                    # In trending market, check LOCAL state (not overall bias)
                    elif local_bullish and recent_momentum < -0.2:
                        # In local uptrend but momentum turning down - caution
                        buy_score = max(0, buy_score - 25)
                    elif local_bearish and recent_momentum > 0.2:
                        # In local downtrend but momentum turning up - caution
                        sell_score = max(0, sell_score - 25)
                    elif not local_bullish and recent_momentum < -0.15:
                        # No local uptrend and falling - kill buys
                        buy_score = 0
                        if sell_score < 50:
                            sell_score = max(sell_score, 55)
                    elif not local_bearish and recent_momentum > 0.15:
                        # No local downtrend and rising - kill sells
                        sell_score = 0
                        if buy_score < 50:
                            buy_score = max(buy_score, 55)
                
                # 6. EMA trend confirmation - don't fight EMA crossover
                if last_ema9 is not None and last_ema21 is not None and last_close is not None:
                    # Price below both EMAs = strong downtrend
                    if last_close < last_ema9 and last_close < last_ema21 and last_ema9 < last_ema21:
                        buy_score = 0  # KILL all buys when below both EMAs
                        if sell_score < 50:
                            sell_score = max(sell_score, 55)
                    # Price above both EMAs = strong uptrend
                    elif last_close > last_ema9 and last_close > last_ema21 and last_ema9 > last_ema21:
                        sell_score = 0  # KILL all sells when above both EMAs
                        if buy_score < 50:
                            buy_score = max(buy_score, 55)
                
                # 7. SYMMETRICAL: Block buys at breakout highs, block sells at breakout lows
                if len(extended_highs) >= 10 and len(extended_lows) >= 10 and last_close is not None:
                    overall_high = max(extended_highs)  # Last 20 candles
                    overall_low = min(extended_lows)    # Last 20 candles
                    distance_from_high = ((last_close - overall_high) / overall_high) * 100
                    distance_from_low = ((last_close - overall_low) / overall_low) * 100
                    
                    # KILL buys at NEW 20-candle breakout high (prevents buying tops)
                    if distance_from_high > -0.1 and last_close >= overall_high * 0.999:
                        buy_score = 0
                        if sell_score < 45:
                            sell_score = max(sell_score, 50)
                    
                    # KILL sells at NEW 20-candle breakout low (prevents selling bottoms)
                    if distance_from_low < 0.1 and last_close <= overall_low * 1.001:
                        sell_score = 0
                        if buy_score < 45:
                            buy_score = max(buy_score, 50)
                
                # 8. SYMMETRICAL: Avoid exact tops AND bottoms
                if len(recent_closes) >= 3 and last_close is not None:
                    recent_high_3 = max(recent_closes[-3:])
                    recent_low_3 = min(recent_closes[-3:])
                    
                    # At 3-candle high
                    if last_close >= recent_high_3 * 0.9999:
                        if local_bullish:
                            pass  # In uptrend, allow buying strength
                        else:
                            buy_score = max(0, buy_score - 15)
                    
                    # At 3-candle low
                    if last_close <= recent_low_3 * 1.0001:
                        if local_bearish:
                            pass  # In downtrend, allow selling weakness
                        else:
                            sell_score = max(0, sell_score - 15)
                
                # 7. Volume confirmation - relaxed for consolidation
                if len(recent_volumes) >= 5 and buy_score > 0:
                    avg_volume = sum(recent_volumes) / len(recent_volumes)
                    last_volume = recent_volumes[-1]
                    
                    # Only penalize very low volume (not just below average)
                    if last_volume < avg_volume * 0.6:  # Below 60% of average (was 80%)
                        buy_score = max(0, buy_score - 15)  # Reduced penalty (was -20)
                
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
                
                # CERTAINTY FACTOR: Only show quality signals
                # - Minimum score: 55 (was 45) - higher quality threshold
                # - Score difference: 15 (was 10) - wider margin required
                certainty_threshold = 55
                certainty_margin = 15
                
                # FREQUENCY LIMITING: Check if enough time has passed since last signal
                signal_cooldown_minutes = 15  # Minimum 15 min between signals
                allow_signal = True
                
                if signals:  # If there are previous signals
                    last_signal_time = signals[-1]['timestamp']
                    time_diff = (last_timestamp - last_signal_time).total_seconds() / 60
                    
                    # Only allow new signal if cooldown has passed OR it's significantly stronger
                    if time_diff < signal_cooldown_minutes:
                        # During cooldown, only allow STRONG signals (80+) with big margin (25+)
                        max_score = max(buy_score, sell_score)
                        score_gap = abs(buy_score - sell_score)
                        if not (max_score >= 80 and score_gap >= 25):
                            allow_signal = False
                
                # Generate BUY signal
                if allow_signal and buy_score > sell_score and (buy_score >= certainty_threshold and score_difference >= certainty_margin):
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
                elif allow_signal and sell_score > buy_score and (sell_score >= certainty_threshold and score_difference >= certainty_margin):
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
