"""
Test market hours detection and data freshness checking
"""
from market_hours import MarketHours
from datetime import datetime
import pytz


def test_market_status():
    """
    Test market status detection.
    """
    print("\n" + "="*70)
    print("  MARKET STATUS TEST")
    print("="*70)
    
    # Get current market status
    status = MarketHours.get_market_status()
    
    print(f"\nCurrent Market Status:")
    print(f"  Status: {status['status']}")
    print(f"  Market Open: {'Yes' if status['is_open'] else 'No'}")
    print(f"  Extended Hours: {'Yes' if status['is_extended_hours'] else 'No'}")
    print(f"  Current Time (ET): {status['current_time_et']}")
    
    if status['next_open']:
        print(f"  Next Market Open: {status['next_open']}")
    
    # Get market time
    market_time = MarketHours.get_market_time()
    print(f"\nMarket Time: {market_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Day of Week: {market_time.strftime('%A')}")
    
    print("="*70 + "\n")


def test_data_freshness():
    """
    Test data freshness checking with various timestamps.
    """
    print("\n" + "="*70)
    print("  DATA FRESHNESS TEST")
    print("="*70)
    
    market_tz = pytz.timezone('America/New_York')
    now = datetime.now(market_tz)
    
    # Test various ages
    from datetime import timedelta
    import pandas as pd
    
    test_cases = [
        ("5 minutes ago", now - timedelta(minutes=5)),
        ("1 hour ago", now - timedelta(hours=1)),
        ("1 day ago", now - timedelta(days=1)),
        ("Last Friday", now - timedelta(days=now.weekday() + 3) if now.weekday() < 5 else now - timedelta(days=2)),
    ]
    
    print(f"\nTesting data freshness (current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')})\n")
    
    for label, timestamp in test_cases:
        ts = pd.Timestamp(timestamp)
        is_fresh, message = MarketHours.check_data_freshness(ts, max_age_minutes=30)
        
        print(f"{label}:")
        print(f"  Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  Fresh: {is_fresh}")
        print(f"  Message: {message}")
        print()
    
    print("="*70 + "\n")


def test_market_open_check():
    """
    Test is_market_open functionality.
    """
    print("\n" + "="*70)
    print("  MARKET OPEN CHECK TEST")
    print("="*70)
    
    is_open = MarketHours.is_market_open(include_extended_hours=False)
    is_extended = MarketHours.is_market_open(include_extended_hours=True)
    
    print(f"\nRegular Hours (9:30 AM - 4:00 PM ET): {is_open}")
    print(f"Extended Hours (4:00 AM - 8:00 PM ET): {is_extended}")
    
    if is_extended and not is_open:
        market_time = MarketHours.get_market_time()
        current_time = market_time.time()
        
        if current_time < MarketHours.MARKET_OPEN:
            print(f"\n✓ Currently in PRE-MARKET session")
        elif current_time > MarketHours.MARKET_CLOSE:
            print(f"\n✓ Currently in AFTER-HOURS session")
    elif is_open:
        print(f"\n✓ Market is OPEN for regular trading")
    else:
        print(f"\n✗ Market is CLOSED")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    test_market_status()
    test_market_open_check()
    test_data_freshness()
