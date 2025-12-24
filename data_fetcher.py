"""
Data fetcher module - Handles market data retrieval
Designed with abstraction for easy data source swapping
"""
import yfinance as yf
import pandas as pd
import time
from typing import Optional, ClassVar
from datetime import datetime, timedelta


class DataFetcher:
    """
    Abstract interface for fetching market data.
    Current implementation uses Yahoo Finance.
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
    
    def fetch_data(self, interval: str, period: str = "5d") -> pd.DataFrame:
        """
        Fetch OHLCV data for the specified interval.
        
        Args:
            interval: Candle interval (e.g., "5m", "15m", "1h", "1d")
            period: How much historical data to fetch (e.g., "5d", "1mo")
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Datetime (index)
        """
        raise NotImplementedError("Subclasses must implement fetch_data()")


class YahooFinanceDataFetcher(DataFetcher):
    """
    Yahoo Finance implementation of data fetcher.
    Includes rate limiting to avoid API throttling.
    """
    
    # Class-level variables for rate limiting
    _last_request_time: ClassVar[float] = 0
    _request_count: ClassVar[int] = 0
    _hour_start_time: ClassVar[float] = time.time()
    
    def __init__(self, ticker: str, request_delay: float = 2.0):
        """
        Initialize the Yahoo Finance data fetcher.
        
        Args:
            ticker: Stock ticker symbol
            request_delay: Minimum seconds between requests (default: 2.0)
        """
        super().__init__(ticker)
        self.request_delay = request_delay
    
    def _rate_limit(self) -> None:
        """
        Enforce rate limiting between API requests.
        Waits if necessary to maintain the configured request delay.
        """
        current_time = time.time()
        
        # Reset counter every hour
        if current_time - YahooFinanceDataFetcher._hour_start_time >= 3600:
            YahooFinanceDataFetcher._request_count = 0
            YahooFinanceDataFetcher._hour_start_time = current_time
        
        # Calculate time since last request
        time_since_last = current_time - YahooFinanceDataFetcher._last_request_time
        
        # Wait if needed to maintain minimum delay
        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            time.sleep(wait_time)
        
        # Update tracking variables
        YahooFinanceDataFetcher._last_request_time = time.time()
        YahooFinanceDataFetcher._request_count += 1
    
    @classmethod
    def get_request_stats(cls) -> dict:
        """
        Get current request statistics for monitoring.
        
        Returns:
            Dictionary with request count and timing info
        """
        current_time = time.time()
        hour_elapsed = current_time - cls._hour_start_time
        
        return {
            "requests_this_hour": cls._request_count,
            "hour_elapsed_seconds": hour_elapsed,
            "hour_elapsed_minutes": hour_elapsed / 60,
            "requests_per_hour_rate": (cls._request_count / hour_elapsed * 3600) if hour_elapsed > 0 else 0,
            "time_since_last_request": current_time - cls._last_request_time if cls._last_request_time > 0 else 0
        }
    
    def fetch_data(self, interval: str, period: str = "5d") -> pd.DataFrame:
        """
        Fetch data from Yahoo Finance with rate limiting.
        
        Args:
            interval: Candle interval (e.g., "5m", "15m", "1h", "1d")
            period: How much historical data to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Apply rate limiting before making request
            self._rate_limit()
            
            ticker_obj = yf.Ticker(self.ticker)
            df = ticker_obj.history(period=period, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data returned for {self.ticker} with interval {interval}")
            
            # Ensure we have the expected columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in data for {self.ticker}")
            
            return df
        
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {self.ticker}: {str(e)}")


def get_data_fetcher(ticker: str, source: str = "yahoo", request_delay: float = 2.0) -> DataFetcher:
    """
    Factory function to get the appropriate data fetcher.
    
    Args:
        ticker: Stock ticker symbol
        source: Data source ("yahoo" for now, expandable later)
        request_delay: Minimum seconds between requests (default: 2.0 for ~1800 req/hour)
    
    Returns:
        DataFetcher instance
    """
    if source.lower() == "yahoo":
        return YahooFinanceDataFetcher(ticker, request_delay=request_delay)
    else:
        raise ValueError(f"Unsupported data source: {source}")
