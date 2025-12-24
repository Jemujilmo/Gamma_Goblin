"""
Test script to demonstrate rate limiting functionality
"""
import time
from data_fetcher import YahooFinanceDataFetcher
import config


def test_rate_limiting():
    """
    Test the rate limiting mechanism with multiple requests.
    """
    print("\n" + "="*70)
    print("  RATE LIMITING TEST")
    print("="*70)
    
    print(f"\nConfiguration:")
    print(f"  Request Delay: {config.REQUEST_DELAY} seconds")
    print(f"  Max Requests/Hour: {config.MAX_REQUESTS_PER_HOUR}")
    print(f"  Expected Rate: ~{3600 / config.REQUEST_DELAY:.0f} requests/hour")
    
    # Create fetcher
    fetcher = YahooFinanceDataFetcher("SPY", request_delay=config.REQUEST_DELAY)
    
    print(f"\nFetching data from Yahoo Finance...")
    print(f"Watch the timing - should be ~{config.REQUEST_DELAY}s between requests\n")
    
    # Make multiple requests
    num_requests = 3
    start_time = time.time()
    
    for i in range(num_requests):
        request_start = time.time()
        print(f"Request {i+1}/{num_requests}...", end=" ", flush=True)
        
        try:
            # Fetch data (this will trigger rate limiting)
            df = fetcher.fetch_data(interval="5m", period="1d")
            request_end = time.time()
            
            elapsed = request_end - request_start
            total_elapsed = request_end - start_time
            
            print(f"✓ Complete ({elapsed:.2f}s) | Total: {total_elapsed:.2f}s | Rows: {len(df)}")
            
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
    
    total_time = time.time() - start_time
    expected_time = config.REQUEST_DELAY * (num_requests - 1)  # First request is immediate
    
    print(f"\n" + "-"*70)
    print(f"Summary:")
    print(f"  Total Requests: {num_requests}")
    print(f"  Total Time: {total_time:.2f}s")
    print(f"  Expected Time: ~{expected_time:.2f}s (with {config.REQUEST_DELAY}s delays)")
    print(f"  Average Time/Request: {total_time/num_requests:.2f}s")
    
    if total_time >= expected_time * 0.9:
        print(f"\n✅ Rate limiting is working correctly!")
    else:
        print(f"\n⚠️  Requests completed faster than expected")
    
    # Calculate projected hourly rate
    avg_time = total_time / num_requests
    projected_hourly = 3600 / avg_time
    print(f"\nProjected hourly rate: ~{projected_hourly:.0f} requests/hour")
    
    if projected_hourly <= config.MAX_REQUESTS_PER_HOUR:
        print(f"✅ Within safe limit of {config.MAX_REQUESTS_PER_HOUR} requests/hour")
    else:
        print(f"⚠️  May exceed safe limit of {config.MAX_REQUESTS_PER_HOUR} requests/hour")
    
    print("="*70 + "\n")


def test_custom_delay():
    """
    Test with a custom delay setting.
    """
    print("\n" + "="*70)
    print("  CUSTOM DELAY TEST (1 second)")
    print("="*70)
    
    # Create fetcher with faster delay (more risky)
    custom_delay = 1.0
    fetcher = YahooFinanceDataFetcher("SPY", request_delay=custom_delay)
    
    print(f"\nUsing custom delay: {custom_delay}s")
    print(f"Expected rate: ~{3600 / custom_delay:.0f} requests/hour")
    
    num_requests = 2
    start_time = time.time()
    
    for i in range(num_requests):
        print(f"Request {i+1}/{num_requests}...", end=" ", flush=True)
        try:
            df = fetcher.fetch_data(interval="15m", period="1d")
            elapsed = time.time() - start_time
            print(f"✓ Complete | Total: {elapsed:.2f}s")
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
    
    total_time = time.time() - start_time
    print(f"\nTotal time: {total_time:.2f}s for {num_requests} requests")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run standard rate limiting test
    test_rate_limiting()
    
    # Optionally test custom delay
    # test_custom_delay()
