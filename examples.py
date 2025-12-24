"""
Example usage demonstrations for Market Copilot
"""
from market_copilot import MarketCopilot
import json


def example_basic():
    """Basic usage example"""
    print("\n=== EXAMPLE 1: Basic Analysis ===\n")
    
    copilot = MarketCopilot()
    signal = copilot.analyze(verbose=True)


def example_json_export():
    """Export signal to JSON"""
    print("\n=== EXAMPLE 2: Export to JSON ===\n")
    
    copilot = MarketCopilot()
    signal = copilot.analyze(verbose=False)
    
    # Export to file
    copilot.export_to_json(signal, "spy_signal.json")
    
    # Also print to console
    print(json.dumps(signal, indent=2))


def example_programmatic_access():
    """Access signal data programmatically"""
    print("\n=== EXAMPLE 3: Programmatic Data Access ===\n")
    
    copilot = MarketCopilot()
    signal = copilot.analyze(verbose=False)
    
    # Extract key information
    overall_bias = signal['synthesis']['overall_bias']
    confidence = signal['synthesis']['average_confidence']
    
    print(f"Overall Bias: {overall_bias}")
    print(f"Confidence: {confidence:.1%}")
    
    # Access specific timeframe
    tf_5m = signal['timeframes']['5m']
    print(f"\n5m Timeframe:")
    print(f"  Bias: {tf_5m['bias']}")
    print(f"  RSI: {tf_5m['indicators']['rsi']}")
    print(f"  Close: ${tf_5m['indicators']['close']}")
    print(f"  VWAP: ${tf_5m['indicators']['vwap']}")
    
    # Print recommendations
    print(f"\nRecommendations:")
    for rec in signal['synthesis']['recommendations']:
        print(f"  • {rec}")


def example_conditional_logic():
    """Example of using signal for conditional decision making"""
    print("\n=== EXAMPLE 4: Conditional Trading Logic ===\n")
    
    copilot = MarketCopilot()
    signal = copilot.analyze(verbose=False)
    
    # Extract synthesis
    synthesis = signal['synthesis']
    bias = synthesis['overall_bias']
    confidence = synthesis['average_confidence']
    alignment = synthesis['alignment_strength']
    
    # Get volatility regime from 5m timeframe
    vol_regime = signal['timeframes']['5m']['volatility_regime']
    
    # Decision logic
    print("TRADING DECISION LOGIC:\n")
    
    if bias == "Bullish" and confidence >= 0.75 and alignment == "Strong":
        print("✅ STRONG BULLISH SIGNAL")
        print("   → Consider: Long calls, bull call spreads, or credit put spreads")
        
        if vol_regime == "Expansion":
            print("   → Volatility expanding: Directional bias supported")
        else:
            print("   → Volatility compressing: Shorter-dated options may be better")
    
    elif bias == "Bearish" and confidence >= 0.75 and alignment == "Strong":
        print("❌ STRONG BEARISH SIGNAL")
        print("   → Consider: Long puts, bear put spreads, or credit call spreads")
        
        if vol_regime == "Expansion":
            print("   → Volatility expanding: Directional bias supported")
    
    elif bias == "Neutral" or confidence < 0.5 or alignment == "Weak":
        print("⚖️ NEUTRAL OR UNCERTAIN SIGNAL")
        print("   → Consider: Iron condors, strangles, or wait for better setup")
        
        if vol_regime == "Compression":
            print("   → Volatility compressing: Theta strategies favored")
    
    else:
        print("⚠️ MODERATE SIGNAL")
        print("   → Consider: Smaller position sizes, tighter risk management")
    
    # Risk considerations
    print(f"\n📊 CURRENT MARKET STATE:")
    print(f"   Timeframe Alignment: {synthesis['timeframe_alignment']}")
    print(f"   5m Volatility: {signal['timeframes']['5m']['volatility_regime']}")
    print(f"   15m Volatility: {signal['timeframes']['15m']['volatility_regime']}")


def example_custom_ticker():
    """Example with a different ticker (if desired)"""
    print("\n=== EXAMPLE 5: Custom Ticker ===\n")
    
    # Note: Yahoo Finance free tier works best with SPY
    # Other tickers may have different data availability
    copilot = MarketCopilot(ticker="SPY")
    signal = copilot.analyze(verbose=True)


def example_custom_rate_limiting():
    """Example with custom rate limiting"""
    print("\n=== EXAMPLE 6: Custom Rate Limiting ===\n")
    
    # Slower rate for extra safety (3 seconds = ~1200 req/hour)
    print("Using 3-second delay between requests (safer)...")
    copilot = MarketCopilot(ticker="SPY", request_delay=3.0)
    signal = copilot.analyze(verbose=False)
    
    print(f"\nAnalysis complete!")
    print(f"Overall Bias: {signal['synthesis']['overall_bias']}")
    print(f"Confidence: {signal['synthesis']['average_confidence']:.1%}")
    
    # Show request statistics
    from data_fetcher import YahooFinanceDataFetcher
    stats = YahooFinanceDataFetcher.get_request_stats()
    print(f"\nAPI Usage:")
    print(f"  Requests made: {stats['requests_this_hour']}")
    print(f"  Current rate: ~{stats['requests_per_hour_rate']:.0f} req/hour")


if __name__ == "__main__":
    # Run all examples
    example_basic()
    
    # Uncomment to run other examples:
    # example_json_export()
    # example_programmatic_access()
    # example_conditional_logic()
    # example_custom_ticker()
    # example_custom_rate_limiting()
