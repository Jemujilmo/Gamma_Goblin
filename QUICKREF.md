# Quick Reference Guide

## Project Structure

```
spytradebot/
├── market_copilot.py      # Main entry point - run this
├── data_fetcher.py        # Yahoo Finance data retrieval
├── indicators.py          # Technical indicator calculations
├── bias_classifier.py     # Market bias determination
├── signal_generator.py    # Signal creation and synthesis
├── config.py             # Configuration settings
├── examples.py           # Usage examples
├── requirements.txt      # Python dependencies
├── README.md            # Full documentation
└── INSTALL.md          # Installation instructions
```

## Quick Start

```python
from market_copilot import MarketCopilot

# Run analysis (automatically checks market hours)
copilot = MarketCopilot()
signal = copilot.analyze(verbose=True)

# Skip market hours checking (for backtesting/research)
signal = copilot.analyze(verbose=True, check_market_hours=False)
```

## Key Modules

### MarketCopilot (main)
```python
copilot = MarketCopilot(ticker="SPY", data_source="yahoo")
signal = copilot.analyze(verbose=True)
copilot.export_to_json(signal, "signal.json")

# Custom rate limiting (default is 2.0 seconds)
copilot = MarketCopilot(ticker="SPY", request_delay=3.0)  # Slower
copilot = MarketCopilot(ticker="SPY", request_delay=1.0)  # Faster (risky)
```

### Configuration (config.py)
```python
DEFAULT_TICKER = "SPY"
TIMEFRAMES = {"short": "5m", "medium": "15m"}
INDICATORS = {
    "ema_fast": 9,
    "ema_slow": 21,
    "rsi_period": 14,
    "atr_period": 14
}
BIAS_THRESHOLDS = {
    "rsi_bullish": 55,
    "rsi_bearish": 45
}
```

## Signal Structure

```python
signal = {
    "ticker": "SPY",
    "analysis_timestamp": "2025-12-23 14:30:00",
    "timeframes": {
        "5m": {
            "bias": "Bullish",
            "confidence": 0.833,
            "volatility_regime": "Expansion",
            "indicators": {
                "close": 578.45,
                "vwap": 577.20,
                "ema_9": 578.10,
                "ema_21": 577.50,
                "rsi": 62.3,
                "atr": 1.25
            }
        },
        "15m": {...}
    },
    "synthesis": {
        "overall_bias": "Bullish",
        "average_confidence": 0.750,
        "alignment_strength": "Strong",
        "recommendations": [...]
    }
}
```

## Bias Classification Logic

Three conditions evaluated:
1. **Price vs VWAP**: Above = bullish, Below = bearish
2. **EMA Crossover**: EMA9 > EMA21 = bullish
3. **RSI Regime**: >55 = bullish, <45 = bearish

**Confidence** = (Aligned signals) / (Total signals)

## Volatility Regimes

- **Expansion**: ATR rising → Favor directional trades
- **Compression**: ATR falling → Favor theta strategies
- **Neutral**: ATR flat → Mixed conditions

## Trading Interpretations

### Strong Bullish (Confidence >75%, Strong Alignment)
- ✅ Consider: Long calls, bull call spreads, credit put spreads
- If volatility expanding: Directional plays favored

### Strong Bearish (Confidence >75%, Strong Alignment)
- ❌ Consider: Long puts, bear put spreads, credit call spreads
- If volatility expanding: Directional plays favored

### Neutral or Weak Signals (Confidence <50% or Weak Alignment)
- ⚖️ Consider: Iron condors, strangles, theta strategies
- If volatility compressing: Theta decay strategies favored

### Divergent Timeframes
- ⚠️ Reduce position size or wait for alignment
- Higher risk of whipsaw

## Common Commands

```bash
# Run basic analysis
python market_copilot.py

# Run examples
python examples.py

# View signal as JSON
python -c "from market_copilot import MarketCopilot; import json; c = MarketCopilot(); s = c.analyze(verbose=False); print(json.dumps(s, indent=2))"
```

## Extending the System

### Add a new data source:
1. Create class in `data_fetcher.py` inheriting from `DataFetcher`
2. Implement `fetch_data(interval, period)` method
3. Update `get_data_fetcher()` factory function

### Add a new indicator:
1. Add calculation function in `indicators.py`
2. Add to `calculate_all_indicators()`
3. Update `BiasClassifier` to use it

### Add a new timeframe:
1. Update `config.py` TIMEFRAMES dict
2. System will automatically analyze it

## Performance Tips

- Yahoo Finance has rate limits (~2000 requests/hour)
- **Built-in rate limiting**: System automatically waits 2 seconds between requests (~1800 req/hour)
- Customize delay: `MarketCopilot(request_delay=3.0)` for slower requests
- Cache data locally if running frequent analyses
- Use longer intervals (15m, 1h) for less frequent updates
- Consider paid data sources for production use

## Limitations

- Free Yahoo Finance data may have delays
- Intraday data typically available for last 60 days only
- No after-hours data in free tier
- No options data (IV, Greeks) - would need separate source
- **Works when market is closed but shows warnings about stale data**

## Market Hours Awareness

```python
from market_hours import MarketHours

# Check if market is open
if MarketHours.is_market_open():
    print("Market is open!")

# Get detailed status
status = MarketHours.get_market_status()
print(f"Status: {status['status']}")
print(f"Next Open: {status['next_open']}")

# Only analyze when market is open
from market_copilot import MarketCopilot
copilot = MarketCopilot()

if MarketHours.is_market_open():
    signal = copilot.analyze()
else:
    print("Market closed. Waiting...")
```

See [MARKET_HOURS.md](MARKET_HOURS.md) for full documentation.
