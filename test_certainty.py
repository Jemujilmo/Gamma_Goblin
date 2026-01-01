"""Test certainty factor and frequency limiting"""
from analyzers import SentimentAnalyzer
import yfinance as yf

print("Downloading Dec 31 data...")
data_1m = yf.download('SPY', period='1d', interval='1m', start='2024-12-31', end='2025-01-01', progress=False)
data_5m = yf.download('SPY', period='1d', interval='5m', start='2024-12-31', end='2025-01-01', progress=False)
data_15m = yf.download('SPY', period='1d', interval='15m', start='2024-12-31', end='2025-01-01', progress=False)

print("Generating signals with CERTAINTY FACTOR...")
analyzer = SentimentAnalyzer()

# Dummy indicators and bias for testing
indicators_5m = {'price': data_5m['Close'].iloc[-1], 'vwap': data_5m['Close'].mean()}
signals = analyzer.analyze_sentiment(data_5m, indicators_5m, 'bullish', 'bullish')

buys = [s for s in signals if s['type'] == 'buy']
sells = [s for s in signals if s['type'] == 'sell']

print(f"\n=== RESULTS ===")
print(f"Total signals: {len(signals)} (was 9 before)")
print(f"Buys: {len(buys)}")
print(f"Sells: {len(sells)}")

print(f"\nSignal breakdown:")
for s in signals:
    time_str = s['timestamp'].strftime("%H:%M")
    price = s['price']
    label = s['label']
    print(f"  {time_str} {s['type'].upper()} ${price:.2f} - {label}")

if buys:
    print(f"\nSafety check - No buys > $685: {all(s['price'] < 685 for s in buys)}")
    
print(f"\nFrequency check:")
if len(signals) > 1:
    for i in range(1, len(signals)):
        prev_time = signals[i-1]['timestamp']
        curr_time = signals[i]['timestamp']
        gap_minutes = (curr_time - prev_time).total_seconds() / 60
        print(f"  Gap between signals {i}: {gap_minutes:.0f} minutes")
