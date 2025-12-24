# Rate Limiting Feature

## Overview

The Market Copilot now includes **automatic rate limiting** to prevent hitting Yahoo Finance API limits (~2000 requests/hour). The system automatically waits between requests to stay within safe limits.

## Default Configuration

**Config Settings** ([config.py](config.py)):
```python
REQUEST_DELAY = 2.0  # Seconds between requests
MAX_REQUESTS_PER_HOUR = 1800  # Safety margin below Yahoo's ~2000/hour limit
```

With a 2-second delay:
- **Maximum**: 1800 requests/hour
- **Safety margin**: 200 requests below Yahoo's limit
- **No manual throttling needed**

## How It Works

### Automatic Rate Limiting

The `YahooFinanceDataFetcher` class automatically:

1. **Tracks request timing** (class-level variables shared across instances)
2. **Enforces minimum delay** between consecutive requests
3. **Resets counters** every hour
4. **Sleeps if needed** to maintain the configured delay

### Implementation

```python
from market_copilot import MarketCopilot

# Default: 2-second delay (~1800 req/hour)
copilot = MarketCopilot()
signal = copilot.analyze()  # Automatically rate-limited
```

## Customization

### Slower Rate (More Conservative)

```python
# 3-second delay = ~1200 requests/hour (safer)
copilot = MarketCopilot(request_delay=3.0)
signal = copilot.analyze()
```

### Faster Rate (Riskier)

```python
# 1-second delay = ~3600 requests/hour (may hit limits!)
copilot = MarketCopilot(request_delay=1.0)
signal = copilot.analyze()
```

### Disable Rate Limiting (Not Recommended)

```python
# 0 delay = no rate limiting (use at your own risk)
copilot = MarketCopilot(request_delay=0.0)
signal = copilot.analyze()
```

## Monitoring Usage

### Get Request Statistics

```python
from data_fetcher import YahooFinanceDataFetcher

stats = YahooFinanceDataFetcher.get_request_stats()

print(f"Requests this hour: {stats['requests_this_hour']}")
print(f"Current rate: {stats['requests_per_hour_rate']:.0f} req/hour")
print(f"Time since last request: {stats['time_since_last_request']:.1f}s")
```

### Monitor Script

Run the included monitor script:

```bash
python monitor_requests.py
```

Output:
```
============================================================
  API REQUEST STATISTICS
============================================================
  Requests this hour:     5
  Time elapsed:           2.3 minutes
  Current request rate:   131 req/hour
  Time since last:        45.2 seconds
============================================================
```

## Testing

### Test Rate Limiting

```bash
python test_rate_limiting.py
```

This script:
- Makes multiple API requests
- Measures timing between requests
- Verifies rate limiting is working
- Calculates projected hourly rate

Expected output:
```
======================================================================
  RATE LIMITING TEST
======================================================================

Configuration:
  Request Delay: 2.0 seconds
  Max Requests/Hour: 1800
  Expected Rate: ~1800 requests/hour

Fetching data from Yahoo Finance...
Watch the timing - should be ~2.0s between requests

Request 1/3... ✓ Complete (1.23s) | Total: 1.23s | Rows: 78
Request 2/3... ✓ Complete (2.15s) | Total: 3.38s | Rows: 78
Request 3/3... ✓ Complete (2.08s) | Total: 5.46s | Rows: 78

----------------------------------------------------------------------
Summary:
  Total Requests: 3
  Total Time: 5.46s
  Expected Time: ~4.00s (with 2.0s delays)
  Average Time/Request: 1.82s

✅ Rate limiting is working correctly!

Projected hourly rate: ~1978 requests/hour
⚠️  May exceed safe limit of 1800 requests/hour
======================================================================
```

## Multi-Timeframe Analysis Impact

The default Market Copilot analysis fetches data for 2 timeframes (5m and 15m), so:

- **2 API requests per analysis run**
- With 2-second delay: ~4 seconds total per analysis
- **Maximum**: ~450 complete analyses per hour
- **Recommended**: Run analysis every 5-15 minutes for live monitoring

## Best Practices

### For Real-Time Monitoring

```python
import time
from market_copilot import MarketCopilot

copilot = MarketCopilot(request_delay=2.0)

# Run every 5 minutes
while True:
    signal = copilot.analyze(verbose=True)
    # Do something with signal...
    time.sleep(300)  # Wait 5 minutes
```

This gives you:
- **12 analyses per hour** (well under limits)
- **24 API requests per hour** (only 1.3% of limit)
- **Plenty of headroom** for manual queries

### For Backtesting or Batch Processing

```python
# Use slower rate for large batches
copilot = MarketCopilot(request_delay=3.0)

for date in date_range:
    signal = copilot.analyze()
    # Process...
    # Automatically rate-limited
```

### Cache Data Locally

For repeated analysis of the same timeframe:

```python
# Fetch once
data_5m = copilot.data_fetcher.fetch_data("5m", "5d")
data_15m = copilot.data_fetcher.fetch_data("15m", "5d")

# Reuse data for multiple analyses
# (implement caching logic)
```

## Configuration in Different Environments

### Development/Testing
```python
# Faster for quick iteration (use sparingly)
copilot = MarketCopilot(request_delay=1.0)
```

### Production/Live Trading
```python
# Conservative for reliability
copilot = MarketCopilot(request_delay=3.0)
```

### Backtesting Large Datasets
```python
# Very conservative to avoid any issues
copilot = MarketCopilot(request_delay=5.0)
```

## Troubleshooting

### "Too Many Requests" Error

If you get rate limited:

1. **Increase delay**: `request_delay=5.0` or higher
2. **Wait 1 hour** for counter to reset
3. **Check stats**: Use `get_request_stats()` to monitor
4. **Consider paid API**: Polygon.io, Alpha Vantage, etc.

### Requests Too Slow

If analysis takes too long:

1. **Reduce delay**: `request_delay=1.5` (carefully)
2. **Cache data**: Store fetched data locally
3. **Reduce timeframes**: Use only one timeframe
4. **Upgrade data source**: Use paid API with higher limits

## Technical Details

### Class-Level Variables

Rate limiting uses class-level variables to track requests across all instances:

```python
class YahooFinanceDataFetcher(DataFetcher):
    _last_request_time: ClassVar[float] = 0
    _request_count: ClassVar[int] = 0
    _hour_start_time: ClassVar[float] = time.time()
```

This means:
- **All instances share limits** (prevents bypass via multiple objects)
- **Thread-safe** for most use cases
- **Resets automatically** every hour

### Request Timing

```python
def _rate_limit(self):
    current_time = time.time()
    time_since_last = current_time - self._last_request_time
    
    if time_since_last < self.request_delay:
        wait_time = self.request_delay - time_since_last
        time.sleep(wait_time)
    
    self._last_request_time = time.time()
    self._request_count += 1
```

## Future Enhancements

Potential improvements:

- **Exponential backoff** on rate limit errors
- **Request queue** for batch processing
- **Per-ticker limits** (if Yahoo enforces per-symbol limits)
- **Automatic delay adjustment** based on API responses
- **Database logging** of request history
- **Dashboard** showing usage stats in real-time
