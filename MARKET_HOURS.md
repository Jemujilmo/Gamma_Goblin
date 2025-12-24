# Market Hours & Data Freshness

## Overview

The Market Copilot now automatically detects whether the market is open and warns you when analyzing stale data.

## Market Status Detection

### When Market is OPEN (9:30 AM - 4:00 PM ET)
```
$ python market_copilot.py

================================================================================
  MARKET COPILOT - SPY Analysis
  2025-12-23 14:30:00
  Market Status: Open
================================================================================

📊 5M Timeframe:
   ✓ Data is fresh (2.3 minutes old)
   ...
```

### When Market is CLOSED
```
$ python market_copilot.py

⚠️  WARNING: Market is currently Closed
   Analysis will use the most recent available data.
   Next market open: 2025-12-24 09:30:00 EST

================================================================================
  MARKET COPILOT - SPY Analysis
  2025-12-23 22:15:00
  Market Status: Closed
================================================================================

   ⚠️  Market is currently Closed. Data is from 2025-12-23 16:00:00 EST (375 minutes old). Next open: 2025-12-24 09:30:00 EST

📊 5M Timeframe:
   ...
```

### Weekend / Holiday
```
⚠️  WARNING: Market is currently Weekend
   Analysis will use the most recent available data.
   Next market open: 2025-12-26 09:30:00 EST
```

## Market Hours

### Regular Trading Hours
- **9:30 AM - 4:00 PM ET** (Monday - Friday)

### Extended Hours
- **Pre-Market**: 4:00 AM - 9:30 AM ET
- **After-Hours**: 4:00 PM - 8:00 PM ET

### Market Closed
- Weekends (Saturday & Sunday)
- US Market Holidays (simplified detection)

## Usage

### Basic Usage (Automatic Checking)
```python
from market_copilot import MarketCopilot

copilot = MarketCopilot()
signal = copilot.analyze(verbose=True)  # Automatically checks market hours
```

### Disable Market Hours Checking
```python
# Skip warnings (not recommended for live trading)
signal = copilot.analyze(verbose=True, check_market_hours=False)
```

### Check Market Status Manually
```python
from market_hours import MarketHours

# Get detailed status
status = MarketHours.get_market_status()
print(f"Status: {status['status']}")
print(f"Is Open: {status['is_open']}")
print(f"Current Time (ET): {status['current_time_et']}")

# Simple check
if MarketHours.is_market_open():
    print("Market is open!")
else:
    print("Market is closed")
```

### Check Data Freshness
```python
import pandas as pd
from market_hours import MarketHours

# After fetching data
latest_timestamp = df.index[-1]
is_fresh, message = MarketHours.check_data_freshness(
    latest_timestamp,
    max_age_minutes=30  # Warn if older than 30 minutes
)

if not is_fresh:
    print(f"Warning: {message}")
```

## Signal Output

When market hours checking is enabled, the signal includes:

```python
signal = {
    "ticker": "SPY",
    "analysis_timestamp": "2025-12-23 22:15:00",
    "market_status": {
        "status": "Closed",  # or "Open", "Weekend", "Holiday", "Pre-Market", "After-Hours"
        "is_open": False,
        "is_extended_hours": False,
        "current_time_et": "2025-12-23 22:15:00 EST",
        "next_open": "2025-12-24 09:30:00 EST"
    },
    "data_freshness_warnings": [
        "5m: ⚠️  Market is currently Closed. Data is from 2025-12-23 16:00:00 EST (375 minutes old).",
        "15m: ⚠️  Market is currently Closed. Data is from 2025-12-23 16:00:00 EST (375 minutes old)."
    ],
    "timeframes": {...},
    "synthesis": {...}
}
```

## Best Practices

### For Live Trading Decisions
```python
from market_copilot import MarketCopilot
from market_hours import MarketHours

copilot = MarketCopilot()

# Only analyze when market is open
if MarketHours.is_market_open():
    signal = copilot.analyze()
    # Make trading decisions...
else:
    print("Market is closed. Waiting for next session...")
```

### For Research/Backtesting
```python
# Disable warnings when analyzing historical data
signal = copilot.analyze(check_market_hours=False)
```

### Monitoring Loop with Market Hours
```python
import time
from market_copilot import MarketCopilot
from market_hours import MarketHours

copilot = MarketCopilot()

while True:
    if MarketHours.is_market_open():
        # Market is open - run analysis
        signal = copilot.analyze(verbose=True)
        
        # Wait 5 minutes before next analysis
        time.sleep(300)
    else:
        # Market is closed - check every 30 minutes
        status = MarketHours.get_market_status()
        print(f"Market is {status['status']}. Next open: {status['next_open']}")
        time.sleep(1800)  # Wait 30 minutes
```

## Data Freshness Thresholds

Default threshold: **30 minutes**

### Customize Threshold
You can modify the freshness check in your own code:

```python
from market_hours import MarketHours
import pandas as pd

# Stricter threshold (10 minutes)
is_fresh, msg = MarketHours.check_data_freshness(
    timestamp,
    max_age_minutes=10
)

# More lenient (1 hour)
is_fresh, msg = MarketHours.check_data_freshness(
    timestamp,
    max_age_minutes=60
)
```

## Holiday Calendar

**Note**: The current implementation includes a simplified holiday check for major holidays:
- New Year's Day (January 1)
- Independence Day (July 4)
- Christmas (December 25)

For production use, consider integrating a comprehensive market calendar library like `pandas_market_calendars`.

### Adding More Holidays
Edit [market_hours.py](market_hours.py) `_is_market_holiday()` method:

```python
@classmethod
def _is_market_holiday(cls, dt: datetime) -> bool:
    year = dt.year
    
    # Add Martin Luther King Jr. Day (3rd Monday in January)
    # Add Presidents' Day (3rd Monday in February)
    # Add Good Friday (calculate based on Easter)
    # Add Memorial Day (last Monday in May)
    # Add Labor Day (1st Monday in September)
    # Add Thanksgiving (4th Thursday in November)
    
    # ... existing code ...
```

## Testing

### Test Market Hours Detection
```bash
python test_market_hours.py
```

This shows:
- Current market status
- Regular vs extended hours
- Data freshness for various timestamps

### Manual Testing
```python
from market_hours import MarketHours

# Get current status
status = MarketHours.get_market_status()
print(status)

# Check if open
print(MarketHours.is_market_open())

# Get market time
print(MarketHours.get_market_time())
```

## Limitations

1. **Holiday Detection**: Simplified - doesn't include all US market holidays
2. **Timezone Handling**: Assumes market timezone is America/New_York
3. **No Early Close Detection**: Doesn't detect early closes (e.g., day before holiday)
4. **Yahoo Finance Delays**: Free tier may have 15-minute delays during market hours

## Future Enhancements

- Integration with `pandas_market_calendars` for complete holiday calendar
- Detection of early close days (1:00 PM ET closes)
- Real-time vs delayed data detection
- Automatic retry when market opens
- Email/SMS alerts when market status changes
