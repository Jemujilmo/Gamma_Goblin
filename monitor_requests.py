"""
Monitor API request statistics
"""
from data_fetcher import YahooFinanceDataFetcher


def print_request_stats():
    """
    Print current request statistics in a formatted way.
    """
    stats = YahooFinanceDataFetcher.get_request_stats()
    
    print("\n" + "="*60)
    print("  API REQUEST STATISTICS")
    print("="*60)
    print(f"  Requests this hour:     {stats['requests_this_hour']}")
    print(f"  Time elapsed:           {stats['hour_elapsed_minutes']:.1f} minutes")
    print(f"  Current request rate:   {stats['requests_per_hour_rate']:.0f} req/hour")
    print(f"  Time since last:        {stats['time_since_last_request']:.1f} seconds")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_request_stats()
