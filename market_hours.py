"""
Market hours detection and data freshness validation
"""
from datetime import datetime, time, timedelta
import pytz
from typing import Tuple, Optional
import pandas as pd


class MarketHours:
    """
    Utility class to check market hours and data freshness.
    """
    
    # US stock market timezone (market logic always in ET)
    MARKET_TZ = pytz.timezone('America/New_York')
    
    # Display timezone (can be different from market timezone)
    DISPLAY_TZ = None  # Will be set from config
    
    # Regular trading hours (Eastern Time)
    MARKET_OPEN = time(9, 30)   # 9:30 AM ET
    MARKET_CLOSE = time(16, 0)  # 4:00 PM ET
    
    # Pre-market and after-hours
    PREMARKET_OPEN = time(4, 0)   # 4:00 AM ET
    AFTERHOURS_CLOSE = time(20, 0)  # 8:00 PM ET
    
    @classmethod
    def set_display_timezone(cls, tz_name: str):
        """
        Set the display timezone for formatting timestamps.
        
        Args:
            tz_name: Timezone name (e.g., 'America/Chicago' for Central Time)
        """
        cls.DISPLAY_TZ = pytz.timezone(tz_name)
    
    @classmethod
    def to_display_time(cls, dt: datetime) -> datetime:
        """
        Convert a datetime to display timezone.
        
        Args:
            dt: Datetime to convert (should be timezone-aware)
            
        Returns:
            Datetime in display timezone
        """
        if cls.DISPLAY_TZ is None:
            return dt
        if dt.tzinfo is None:
            dt = cls.MARKET_TZ.localize(dt)
        return dt.astimezone(cls.DISPLAY_TZ)
    
    @classmethod
    def get_market_time(cls) -> datetime:
        """
        Get current time in market timezone (Eastern Time).
        
        Returns:
            Current datetime in ET
        """
        return datetime.now(cls.MARKET_TZ)
    
    @classmethod
    def is_market_open(cls, include_extended_hours: bool = False) -> bool:
        """
        Check if the market is currently open.
        
        Args:
            include_extended_hours: If True, includes pre-market and after-hours
        
        Returns:
            True if market is open, False otherwise
        """
        now = cls.get_market_time()
        current_time = now.time()
        
        # Check if it's a weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's a US market holiday (simplified - doesn't account for all holidays)
        if cls._is_market_holiday(now):
            return False
        
        # Check trading hours
        if include_extended_hours:
            return cls.PREMARKET_OPEN <= current_time <= cls.AFTERHOURS_CLOSE
        else:
            return cls.MARKET_OPEN <= current_time <= cls.MARKET_CLOSE
    
    @classmethod
    def _is_market_holiday(cls, dt: datetime) -> bool:
        """
        Check if date is a major US market holiday.
        Note: This is a simplified check. For production, use a proper holiday calendar.
        
        Args:
            dt: Datetime to check
        
        Returns:
            True if it's a known market holiday
        """
        # Major holidays (simplified list)
        year = dt.year
        
        # New Year's Day
        if dt.month == 1 and dt.day == 1:
            return True
        
        # Independence Day
        if dt.month == 7 and dt.day == 4:
            return True
        
        # Christmas
        if dt.month == 12 and dt.day == 25:
            return True
        
        # Add more holidays as needed (MLK Day, Presidents Day, Good Friday, etc.)
        
        return False
    
    @classmethod
    def get_market_status(cls) -> dict:
        """
        Get detailed market status information.
        
        Returns:
            Dictionary with market status details
        """
        now = cls.get_market_time()
        current_time = now.time()
        is_weekend = now.weekday() >= 5
        is_holiday = cls._is_market_holiday(now)
        
        # Determine status
        if is_weekend:
            status = "Weekend"
            next_open = cls._get_next_market_open(now)
        elif is_holiday:
            status = "Holiday"
            next_open = cls._get_next_market_open(now)
        elif cls.MARKET_OPEN <= current_time <= cls.MARKET_CLOSE:
            status = "Open"
            next_open = None
        elif cls.PREMARKET_OPEN <= current_time < cls.MARKET_OPEN:
            status = "Pre-Market"
            next_open = None
        elif cls.MARKET_CLOSE < current_time <= cls.AFTERHOURS_CLOSE:
            status = "After-Hours"
            next_open = None
        else:
            status = "Closed"
            next_open = cls._get_next_market_open(now)
        
        return {
            "status": status,
            "is_open": cls.is_market_open(include_extended_hours=False),
            "is_extended_hours": cls.is_market_open(include_extended_hours=True) and not cls.is_market_open(include_extended_hours=False),
            "current_time_et": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "next_open": next_open.strftime("%Y-%m-%d %H:%M:%S %Z") if next_open else None
        }
    
    @classmethod
    def _get_next_market_open(cls, from_time: datetime) -> datetime:
        """
        Calculate the next market open time.
        
        Args:
            from_time: Starting datetime
        
        Returns:
            Next market open datetime
        """
        # Start with next day
        next_day = from_time + timedelta(days=1)
        next_day = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Skip weekends
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        
        # Skip holidays (simplified)
        while cls._is_market_holiday(next_day):
            next_day += timedelta(days=1)
            # Skip weekends again if we land on one
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
        
        return next_day
    
    @classmethod
    def check_data_freshness(cls, latest_timestamp: pd.Timestamp, max_age_minutes: int = 30) -> Tuple[bool, str]:
        """
        Check if data is fresh enough for real-time analysis.
        
        Args:
            latest_timestamp: Most recent data timestamp
            max_age_minutes: Maximum acceptable age in minutes
        
        Returns:
            Tuple of (is_fresh, warning_message)
        """
        now = cls.get_market_time()
        
        # Convert timestamp to market timezone if needed
        if latest_timestamp.tzinfo is None:
            latest_timestamp = cls.MARKET_TZ.localize(latest_timestamp)
        else:
            latest_timestamp = latest_timestamp.astimezone(cls.MARKET_TZ)
        
        age = now - latest_timestamp
        age_minutes = age.total_seconds() / 60
        
        # If market is closed, we expect stale data
        if not cls.is_market_open(include_extended_hours=True):
            market_status = cls.get_market_status()
            warning = (f"⚠️  Market is currently {market_status['status']}. "
                      f"Data is from {latest_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')} "
                      f"({age_minutes:.0f} minutes old).")
            if market_status['next_open']:
                warning += f" Next open: {market_status['next_open']}"
            return False, warning
        
        # Market is open - check freshness
        if age_minutes > max_age_minutes:
            return False, f"⚠️  Data may be stale. Latest data is {age_minutes:.0f} minutes old (max: {max_age_minutes} minutes)."
        
        return True, f"✓ Data is fresh ({age_minutes:.1f} minutes old)"
