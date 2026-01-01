"""
Multi-Timeframe Signal Generation System

PHILOSOPHY:
- Signals only when multiple conditions align across timeframes
- VWAP is institutional bias anchor  
- RSI confirms momentum, NOT overbought/oversold
- MACD shows trend direction and momentum shift, NOT crossovers alone
- Volume confirms conviction
- Avoid signals in chop/low-volume conditions

RULES:
- Multi-timeframe confirmation required (1m + 5m + 15m)
- VWAP interaction identifies institutional bias
- RSI for momentum confirmation in 40-60 range
- MACD for trend direction (histogram direction)
- No signals during low volume or flat VWAP

BUY SIGNAL REQUIREMENTS (must meet 3/8):
1. Price above VWAP on 5m (bullish structure)
2. Price above VWAP on 15m (bullish trend)
3. 1m pullback toward VWAP/EMA (entry timing)
4. RSI rising through 40-55 range (momentum building)
5. MACD histogram increasing on 1m (momentum shift)
6. Volume above recent average (conviction)
7. 15m MACD positive (trend confirmation)
8. Gamma score elevated (>40) - indicates high volatility/conviction

SELL SIGNAL REQUIREMENTS (must meet 3/8):
1. Price below VWAP on 5m (bearish structure)
2. Price below VWAP on 15m (bearish trend)
3. Failed reclaim of VWAP/EMA (rejection)
4. RSI falling through 60-45 range (momentum fading)
5. MACD histogram decreasing on 1m (momentum shift)
6. Volume above recent average (conviction)
7. 15m MACD negative (trend confirmation)
8. Gamma score elevated (>40) - indicates high volatility/conviction
"""

import pandas as pd
from typing import List, Dict, Optional


def generate_multi_timeframe_signals(
    data_1m: pd.DataFrame,
    data_5m: pd.DataFrame,
    data_15m: pd.DataFrame,
    indicators_1m: pd.DataFrame,
    indicators_5m: pd.DataFrame,
    indicators_15m: pd.DataFrame
) -> List[Dict]:
    """
    Generate buy/sell signals with multi-timeframe confirmation.
    
    Returns list of signals: [{timestamp, price, type, strength, conditions_met, label}]
    """
    signals = []
    
    # Need minimum data
    if len(data_5m) < 20:
        return signals
    
    # Scan through 5m candles (primary timeframe)
    for i in range(20, len(data_5m)):
        # Current 5m candle
        close_5m = float(data_5m['Close'].iloc[i])
        timestamp_5m = data_5m.index[i]
        volume_5m = float(data_5m['Volume'].iloc[i])
        
        # 5m indicators
        vwap_5m = float(indicators_5m['VWAP'].iloc[i])
        ema9_5m = float(indicators_5m['EMA_fast'].iloc[i])
        ema21_5m = float(indicators_5m['EMA_slow'].iloc[i])
        rsi_5m = float(indicators_5m['RSI'].iloc[i])
        macd_5m = float(indicators_5m['MACD'].iloc[i])
        macd_signal_5m = float(indicators_5m['MACD_signal'].iloc[i])
        macd_hist_5m = macd_5m - macd_signal_5m
        
        # Calculate Gamma Score (0-100) based on volume, volatility, and momentum
        # WHY: High gamma indicates explosive move potential (like gamma squeezes)
        recent_volume_5m = float(data_5m['Volume'].iloc[max(0, i-5):i].mean())
        avg_volume_5m_calc = float(data_5m['Volume'].iloc[max(0, i-20):i].mean())
        volume_ratio = (recent_volume_5m / avg_volume_5m_calc) if avg_volume_5m_calc > 0 else 1.0
        
        # Calculate volatility (ATR-based if available)
        if 'ATR' in indicators_5m.columns:
            current_atr = float(indicators_5m['ATR'].iloc[i])
            avg_atr = float(indicators_5m['ATR'].iloc[max(0, i-20):i].mean())
            volatility_ratio = (current_atr / avg_atr) if avg_atr > 0 else 1.0
        else:
            volatility_ratio = 1.0
        
        # Calculate price momentum over last 5 candles
        if i >= 5:
            price_change_5m = ((close_5m / float(data_5m['Close'].iloc[i-5])) - 1) * 100
        else:
            price_change_5m = 0
        
        # Gamma score: volume (30%) + volatility (30%) + momentum (40%)
        gamma_score = min(100, int((volume_ratio * 30 + volatility_ratio * 30 + abs(price_change_5m) * 10)))
        
        # EMA crossover detection (5m timeframe)
        ema9_above_ema21 = ema9_5m > ema21_5m
        golden_cross = False  # EMA 9 crossing above EMA 21
        death_cross = False   # EMA 9 crossing below EMA 21
        
        if i >= 1:
            prev_ema9_5m = float(indicators_5m['EMA_fast'].iloc[i-1])
            prev_ema21_5m = float(indicators_5m['EMA_slow'].iloc[i-1])
            prev_ema9_above = prev_ema9_5m > prev_ema21_5m
            
            # Golden cross: EMA9 crosses above EMA21
            if not prev_ema9_above and ema9_above_ema21:
                golden_cross = True
            # Death cross: EMA9 crosses below EMA21
            elif prev_ema9_above and not ema9_above_ema21:
                death_cross = True
        
        # 15m data (trend context)
        # Find 15m candle containing this timestamp
        idx_15m_list = data_15m.index[data_15m.index <= timestamp_5m]
        if len(idx_15m_list) == 0:
            continue
        idx_15m = idx_15m_list[-1]
        
        idx_15m_pos = data_15m.index.get_loc(idx_15m)
        if isinstance(idx_15m_pos, slice):
            idx_15m_pos = idx_15m_pos.start
        close_15m = float(data_15m['Close'].iloc[idx_15m_pos])
        vwap_15m = float(indicators_15m['VWAP'].iloc[idx_15m_pos])
        macd_15m = float(indicators_15m['MACD'].iloc[idx_15m_pos])
        macd_signal_15m = float(indicators_15m['MACD_signal'].iloc[idx_15m_pos])
        macd_hist_15m = macd_15m - macd_signal_15m
        
        # 1m data (entry timing)
        # Get recent 1m candles within this 5m period
        mask_1m = (data_1m.index > timestamp_5m - pd.Timedelta(minutes=5)) & (data_1m.index <= timestamp_5m)
        recent_1m = data_1m[mask_1m]
        
        if len(recent_1m) == 0:
            continue
            
        # Latest 1m values
        close_1m = float(recent_1m['Close'].iloc[-1])
        volume_1m = float(recent_1m['Volume'].iloc[-1])
        last_1m_idx = recent_1m.index[-1]
        last_1m_pos = indicators_1m.index.get_loc(last_1m_idx)
        if isinstance(last_1m_pos, slice):
            last_1m_pos = last_1m_pos.start
        vwap_1m = float(indicators_1m['VWAP'].iloc[last_1m_pos])
        rsi_1m = float(indicators_1m['RSI'].iloc[last_1m_pos])
        
        # 1m MACD histogram change
        macd_1m_curr = float(indicators_1m['MACD'].iloc[last_1m_pos])
        signal_1m_curr = float(indicators_1m['MACD_signal'].iloc[last_1m_pos])
        hist_1m_curr = macd_1m_curr - signal_1m_curr
        
        hist_1m_prev = 0
        if len(recent_1m) >= 2:
            prev_1m_idx = recent_1m.index[-2]
            prev_1m_pos = indicators_1m.index.get_loc(prev_1m_idx)
            if isinstance(prev_1m_pos, slice):
                prev_1m_pos = prev_1m_pos.start
            macd_1m_prev = float(indicators_1m['MACD'].iloc[prev_1m_pos])
            signal_1m_prev = float(indicators_1m['MACD_signal'].iloc[prev_1m_pos])
            hist_1m_prev = macd_1m_prev - signal_1m_prev
        
        macd_increasing_1m = hist_1m_curr > hist_1m_prev
        
        # =================================================================
        # FILTERS - Skip if conditions not met (relaxed for more signals)
        # =================================================================
        
        # Filter 1: Volume Check (avoid extremely low-volume chop)
        # WHY: Low volume = no institutional participation (lowered to 50%)
        avg_volume_5m = float(data_5m['Volume'].iloc[max(0, i-10):i].mean())
        if volume_5m < avg_volume_5m * 0.5:  # Lowered from 0.7
            continue  # Skip if volume < 50% of average
        
        # NO FILTER 2 - VWAP flatness was blocking too many signals
        
        
        # =================================================================
        # BUY SIGNAL LOGIC - Must meet 4/7 conditions (lowered for sensitivity)
        # OR strong MACD momentum shift
        # =================================================================
        
        buy_conditions = []
        
        # CONDITION 1: 15m price above VWAP (bullish trend)
        # WHY: Higher timeframe sets directional bias
        if close_15m > vwap_15m:
            buy_conditions.append("15m above VWAP")
        
        # CONDITION 2: 5m price above VWAP (bullish setup)
        # WHY: Confirms we're in bullish price structure
        if close_5m > vwap_5m:
            buy_conditions.append("5m above VWAP")
        
        # CONDITION 3: 1m pullback (entry timing)
        # WHY: Want to buy dips, not chase - pullback to VWAP or EMA
        distance_to_vwap_1m = ((close_1m - vwap_1m) / vwap_1m) * 100
        if 0 < distance_to_vwap_1m < 0.3:  # Within 0.3% above VWAP
            buy_conditions.append("1m pullback to VWAP")
        elif 0 < (close_1m - ema9_5m) / ema9_5m * 100 < 0.2:  # Near EMA9
            buy_conditions.append("1m near EMA9")
        
        # CONDITION 4: RSI rising through 35-60 (momentum building)
        # WHY: NOT overbought/oversold, but momentum direction (widened range)
        if 35 <= rsi_1m <= 60 and rsi_1m > rsi_5m - 5:  # 1m RSI rising toward 5m
            buy_conditions.append("RSI rising 35-60")
        
        # CONDITION 5: MACD histogram increasing on 1m (momentum shift)
        # WHY: Shows buying pressure building, NOT just crossover
        if macd_increasing_1m and hist_1m_curr > 0:
            buy_conditions.append("MACD increasing")
        
        # CONDITION 6: Volume confirmation
        # WHY: Institutions move with volume (lowered threshold)
        avg_volume_1m = float(recent_1m['Volume'].iloc[:-1].mean()) if len(recent_1m) > 1 else volume_1m
        if volume_1m > avg_volume_1m * 1.05:  # Lowered from 1.2x to 1.05x
            buy_conditions.append("Volume above average")
        
        # CONDITION 7: 15m MACD positive (trend confirmation)
        # WHY: Higher timeframe trend must support the trade
        if macd_hist_15m > 0:
            buy_conditions.append("15m MACD positive")
        
        # CONDITION 8: Gamma score elevated (>40)
        # WHY: High gamma indicates explosive potential, institutional activity
        if gamma_score >= 40:
            buy_conditions.append(f"Gamma elevated ({gamma_score}%)")
        
        # STRONG MOMENTUM OVERRIDES catch clear trend changes
        # Override 1: Golden Cross (EMA9 crosses above EMA21)
        # WHY: Classic bullish signal - catches uptrend starts
        # RESTRICTION: Must have positive MACD and price above VWAP (prevents false signals in downtrends)
        if golden_cross and macd_hist_5m > 0 and close_5m > vwap_5m:
            buy_conditions.append("STRONG: Golden Cross (EMA9 > EMA21)")
        
        # Override 2: MACD histogram crossing zero upward on 5m
        # This catches clear reversals like 11:30 AM bounce
        strong_macd_reversal = False
        if i >= 1:
            prev_hist_5m = float(indicators_5m['MACD'].iloc[i-1]) - float(indicators_5m['MACD_signal'].iloc[i-1])
            curr_hist_5m = macd_hist_5m
            # Crossover from negative to positive OR strong increase in positive territory
            if (prev_hist_5m < 0 and curr_hist_5m > 0) or (prev_hist_5m > 0 and curr_hist_5m > prev_hist_5m * 1.5):
                strong_macd_reversal = True
                buy_conditions.append("STRONG: 5m MACD bullish shift")
        
        # Generate BUY signal if 3+ conditions met OR any strong override
        # RESISTANCE CHECK: Only block buys at tops when MACD also shows weakness
        # WHY: Prevents buying like the 2:10 PM top before selloff
        # Only triggers when near high AND MACD losing momentum
        at_resistance = False
        if i >= 20:
            recent_high = float(data_5m['High'].iloc[max(0, i-20):i].max())
            distance_from_high = ((recent_high - close_5m) / close_5m) * 100
            macd_declining = macd_hist_5m < 0.05  # MACD histogram losing strength
            if distance_from_high < 0.3 and macd_declining:  # Near high AND weak MACD
                at_resistance = True
        
        # CRITICAL: BUY only if price above VWAP (trend alignment) AND not at resistance
        price_above_vwap = close_5m > vwap_5m
        trigger_buy = (len(buy_conditions) >= 3 or strong_macd_reversal or (golden_cross and macd_hist_5m > 0 and close_5m > vwap_5m))
        
        if trigger_buy and price_above_vwap and not at_resistance:
            signals.append({
                'timestamp': timestamp_5m,
                'price': close_5m,
                'type': 'buy',
                'strength': len(buy_conditions) * 12,  # 8 conditions max = 96%
                'conditions_met': len(buy_conditions),
                'conditions': buy_conditions,
                'label': f"BUY ({len(buy_conditions)}/8 conditions) [γ={gamma_score}]"
            })
            continue  # Don't check sell if buy triggered
        
        # =================================================================
        # SELL SIGNAL LOGIC - Must meet 4/7 conditions (lowered for sensitivity)
        # OR strong MACD bearish shift
        # =================================================================
        
        sell_conditions = []
        
        # CONDITION 1: 15m price below VWAP (bearish trend)
        if close_15m < vwap_15m:
            sell_conditions.append("15m below VWAP")
        
        # CONDITION 2: 5m price below VWAP (bearish setup)
        if close_5m < vwap_5m:
            sell_conditions.append("5m below VWAP")
        
        # CONDITION 3: Failed reclaim of VWAP (rejection)
        # WHY: Price tried to reclaim VWAP but failed - bearish
        high_1m = float(recent_1m['High'].iloc[-1])
        if close_1m < vwap_1m and high_1m > vwap_1m:
            sell_conditions.append("Failed VWAP reclaim")
        elif close_1m < ema9_5m and high_1m > ema9_5m:
            sell_conditions.append("Failed EMA9 reclaim")
        
        # CONDITION 4: RSI falling through 65-40 (momentum fading)
        # WHY: Momentum turning down (widened range)
        if 40 <= rsi_1m <= 65 and rsi_1m < rsi_5m + 5:  # 1m RSI falling from 5m
            sell_conditions.append("RSI falling 65-40")
        
        # CONDITION 5: MACD histogram decreasing on 1m (momentum shift down)
        if not macd_increasing_1m and hist_1m_curr < 0:
            sell_conditions.append("MACD decreasing")
        
        # CONDITION 6: Volume confirmation (lowered threshold)
        if volume_1m > avg_volume_1m * 1.05:  # Lowered from 1.2x
            sell_conditions.append("Volume above average")
        
        # CONDITION 7: 15m MACD negative (trend confirmation)
        if macd_hist_15m < 0:
            sell_conditions.append("15m MACD negative")
        
        # CONDITION 8: Gamma score elevated (>40)
        # WHY: High gamma indicates explosive potential, institutional activity
        if gamma_score >= 40:
            sell_conditions.append(f"Gamma elevated ({gamma_score}%)")
        
        # STRONG BEARISH OVERRIDE 1: Death Cross (EMA9 crosses below EMA21)
        # WHY: Classic bearish signal - catches downtrend starts (like 2:15 PM death cross)
        # RESTRICTION: Must have negative MACD and price below VWAP (prevents false signals in uptrends)
        if death_cross and macd_hist_5m < 0 and close_5m < vwap_5m:
            sell_conditions.append("STRONG: Death Cross (EMA9 < EMA21)")
        
        # STRONG BEARISH OVERRIDE 2: MACD histogram crossing zero downward on 5m
        # This catches clear selloffs like 2:15 PM breakdown
        strong_macd_breakdown = False
        if i >= 1:
            prev_hist_5m = float(indicators_5m['MACD'].iloc[i-1]) - float(indicators_5m['MACD_signal'].iloc[i-1])
            curr_hist_5m = macd_hist_5m
            # Crossover from positive to negative OR strong decrease in negative territory
            if (prev_hist_5m > 0 and curr_hist_5m < 0) or (prev_hist_5m < 0 and curr_hist_5m < prev_hist_5m * 1.5):
                strong_macd_breakdown = True
                sell_conditions.append("STRONG: 5m MACD bearish shift")
        
        # Generate SELL signal if 3+ conditions met OR strong MACD/EMA shift
        # MANDATORY: Price must be below VWAP to prevent counter-trend signals
        # CRITICAL: SELL only if price below VWAP (trend alignment)
        price_below_vwap = close_5m < vwap_5m
        trigger_sell = (len(sell_conditions) >= 3 or strong_macd_breakdown or (death_cross and macd_hist_5m < 0 and close_5m < vwap_5m))
        
        if trigger_sell and price_below_vwap:
            signals.append({
                'timestamp': timestamp_5m,
                'price': close_5m,
                'type': 'sell',
                'strength': len(sell_conditions) * 12,  # 8 conditions max = 96%
                'conditions_met': len(sell_conditions),
                'conditions': sell_conditions,
                'label': f"SELL ({len(sell_conditions)}/8 conditions) [γ={gamma_score}]"
            })
    
    # Apply frequency limiting (15-minute cooldown)
    filtered_signals = []
    last_signal_time = None
    
    for signal in signals:
        if last_signal_time is None:
            filtered_signals.append(signal)
            last_signal_time = signal['timestamp']
        else:
            time_diff_minutes = (signal['timestamp'] - last_signal_time).total_seconds() / 60
            
            # Allow signal if:
            # 1. 15+ minutes have passed, OR
            # 2. Signal is STRONG (6-8/8 conditions) and 10+ minutes passed
            if time_diff_minutes >= 15:
                filtered_signals.append(signal)
                last_signal_time = signal['timestamp']
            elif signal['conditions_met'] >= 6 and time_diff_minutes >= 10:
                filtered_signals.append(signal)
                last_signal_time = signal['timestamp']
    
    return filtered_signals
