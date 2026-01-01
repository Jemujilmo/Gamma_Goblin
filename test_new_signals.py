"""
Test the new multi-timeframe signal generation logic
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from new_signal_logic import generate_multi_timeframe_signals
from indicators import calculate_all_indicators
from config import INDICATORS

def test_new_signals():
    print("="*80)
    print("TESTING NEW MULTI-TIMEFRAME SIGNAL LOGIC")
    print("="*80)
    print()
    
    # Fetch data
    print("[FETCH] Downloading SPY data...")
    ticker = "SPY"
    
    # Get 1m data (last day)
    print("  - 1-minute data...")
    data_1m = yf.download(ticker, period='1d', interval='1m', progress=False)
    
    # Get 5m data (last 5 days for context)
    print("  - 5-minute data...")
    data_5m = yf.download(ticker, period='5d', interval='5m', progress=False)
    
    # Get 15m data (last month for context)
    print("  - 15-minute data...")
    data_15m = yf.download(ticker, period='1mo', interval='15m', progress=False)
    
    if data_1m.empty or data_5m.empty or data_15m.empty:
        print("[ERROR] Failed to fetch data")
        return
    
    print("[OK] Data fetched:")
    print(f"   1m:  {len(data_1m)} candles")
    print(f"   5m:  {len(data_5m)} candles")
    print(f"   15m: {len(data_15m)} candles")
    print()
    
    # Calculate indicators
    print("[CALC] Calculating indicators...")
    indicators_1m = calculate_all_indicators(data_1m, INDICATORS)
    indicators_5m = calculate_all_indicators(data_5m, INDICATORS)
    indicators_15m = calculate_all_indicators(data_15m, INDICATORS)
    print("[OK] Indicators calculated")
    print()
    
    # Generate signals
    print("[SIGNAL] Generating signals with new multi-timeframe logic...")
    signals = generate_multi_timeframe_signals(
        data_1m, data_5m, data_15m,
        indicators_1m, indicators_5m, indicators_15m
    )
    print()
    
    # Display results
    print("="*80)
    print("RESULTS")
    print("="*80)
    print()
    
    if not signals:
        print("[X] No signals generated")
        print()
        print("This could mean:")
        print("  - Market is in consolidation/chop (VWAP too flat)")
        print("  - Volume too low")
        print("  - Insufficient multi-timeframe alignment (need 5/7 conditions)")
        return
    
    print(f"[OK] Generated {len(signals)} signals")
    print()
    
    # Separate by type
    buy_signals = [s for s in signals if s['type'] == 'buy']
    sell_signals = [s for s in signals if s['type'] == 'sell']
    
    print(f"[BUY]  signals:  {len(buy_signals)}")
    print(f"[SELL] signals: {len(sell_signals)}")
    print()
    
    # Show each signal with details
    print("-"*80)
    for i, signal in enumerate(signals, 1):
        prefix = "[BUY]" if signal['type'] == 'buy' else "[SELL]"
        signal_type = signal['type'].upper()
        
        print(f"{prefix} Signal #{i}: {signal_type}")
        print(f"   Time:       {signal['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Price:      ${signal['price']:.2f}")
        print(f"   Strength:   {signal['strength']}%")
        print(f"   Conditions: {signal['conditions_met']}/7 met")
        print(f"   Details:")
        for condition in signal['conditions']:
            print(f"      [X] {condition}")
        print()
    
    print("-"*80)
    print()
    
    # Summary statistics
    if signals:
        print("SUMMARY:")
        print(f"   Total signals:     {len(signals)}")
        print(f"   Average strength:  {sum(s['strength'] for s in signals) / len(signals):.1f}%")
        print(f"   Avg conditions:    {sum(s['conditions_met'] for s in signals) / len(signals):.1f}/7")
        print()
        
        # Time distribution
        if len(signals) > 1:
            first_signal = signals[0]['timestamp']
            last_signal = signals[-1]['timestamp']
            time_span = (last_signal - first_signal).total_seconds() / 60
            print(f"   Time span:         {time_span:.0f} minutes")
            print(f"   Signal frequency:  ~{time_span / len(signals):.0f} min between signals")
            print()
    
    # Show latest market state
    print("="*80)
    print("CURRENT MARKET STATE")
    print("="*80)
    print()
    
    latest_5m_close = float(data_5m['Close'].iloc[-1])
    latest_5m_vwap = float(indicators_5m['VWAP'].iloc[-1])
    latest_5m_rsi = float(indicators_5m['RSI'].iloc[-1])
    latest_5m_macd = float(indicators_5m['MACD'].iloc[-1])
    latest_5m_signal = float(indicators_5m['MACD_signal'].iloc[-1])
    
    latest_15m_vwap = float(indicators_15m['VWAP'].iloc[-1])
    latest_15m_macd = float(indicators_15m['MACD'].iloc[-1])
    latest_15m_signal = float(indicators_15m['MACD_signal'].iloc[-1])
    
    print(f"[5M] Timeframe:")
    print(f"   Close:      ${latest_5m_close:.2f}")
    print(f"   VWAP:       ${latest_5m_vwap:.2f}")
    print(f"   Position:   {'ABOVE' if latest_5m_close > latest_5m_vwap else 'BELOW'} VWAP")
    print(f"   RSI:        {latest_5m_rsi:.1f}")
    print(f"   MACD hist:  {latest_5m_macd - latest_5m_signal:.3f}")
    print()
    
    print(f"[15M] Timeframe:")
    print(f"   VWAP:       ${latest_15m_vwap:.2f}")
    print(f"   MACD hist:  {latest_15m_macd - latest_15m_signal:.3f}")
    print(f"   Bias:       {'BULLISH' if latest_15m_macd > latest_15m_signal else 'BEARISH'}")
    print()
    
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_new_signals()
