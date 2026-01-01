"""
Configuration settings for Market Copilot
"""

# Ticker configuration
DEFAULT_TICKER = "SPY"

# Timeframe settings
TIMEFRAMES = {
    "short": "5m",   # Short-term execution bias
    "medium": "15m"  # Higher-timeframe structural bias
}

# Indicator parameters
INDICATORS = {
    "ema_fast": 9,
    "ema_slow": 21,
    "rsi_period": 14,
    "atr_period": 14
}

# Bias classification thresholds
BIAS_THRESHOLDS = {
    "rsi_bullish": 55,
    "rsi_bearish": 45
}

# Data fetching settings
DATA_PERIOD = "5d"  # Fetch last 5 days to ensure enough data for calculations

# Timezone settings
DISPLAY_TIMEZONE = "America/Chicago"  # Central Time for display (market logic stays in ET)

# Rate limiting (to avoid Yahoo Finance API limits)
REQUEST_DELAY = 3.0  # Seconds between requests (increased to avoid rate limiting)
MAX_REQUESTS_PER_HOUR = 1000  # Conservative limit - Yahoo enforces strict rate limits
MAX_RETRIES = 3  # Maximum retry attempts for failed requests
RETRY_BACKOFF_BASE = 5  # Base seconds for exponential backoff (5, 10, 20...)
CACHE_DURATION = 60  # Cache data for 60 seconds to reduce API calls
