"""
Market Copilot - Main orchestration script
Analyzes SPY across multiple timeframes for options trading decisions
"""
import json
from typing import Dict, Any
from data_fetcher import get_data_fetcher
from indicators import calculate_all_indicators
from bias_classifier import BiasClassifier
from signal_generator import SignalGenerator
from market_hours import MarketHours
import config


class MarketCopilot:
    """
    Main Market Copilot class - orchestrates the entire analysis pipeline.
    """
    
    def __init__(
        self,
        ticker: str = config.DEFAULT_TICKER,
        data_source: str = "yahoo",
        request_delay: float = None
    ):
        """
        Initialize the Market Copilot.
        
        Args:
            ticker: Stock ticker to analyze (default: SPY)
            data_source: Data source to use (default: yahoo)
            request_delay: Seconds between API requests (default: from config)
        """
        self.ticker = ticker
        
        # Use config default if not specified
        if request_delay is None:
            request_delay = config.REQUEST_DELAY
        
        self.data_fetcher = get_data_fetcher(ticker, data_source, request_delay)
        self.bias_classifier = BiasClassifier(
            rsi_bullish_threshold=config.BIAS_THRESHOLDS['rsi_bullish'],
            rsi_bearish_threshold=config.BIAS_THRESHOLDS['rsi_bearish']
        )
        self.signal_generator = SignalGenerator(self.bias_classifier)
    
    def analyze(self, verbose: bool = True, check_market_hours: bool = True) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.
        
        Args:
            verbose: If True, print formatted output to console
            check_market_hours: If True, warn when market is closed or data is stale
        
        Returns:
            Dictionary containing the complete multi-timeframe signal
        """
        try:
            # Check market status
            market_status = None
            data_freshness_warnings = []
            
            if check_market_hours:
                market_status = MarketHours.get_market_status()
                if verbose and not market_status['is_open']:
                    print(f"\n⚠️  WARNING: Market is currently {market_status['status']}")
                    print(f"   Analysis will use the most recent available data.")
                    if market_status['next_open']:
                        print(f"   Next market open: {market_status['next_open']}\n")
            
            # Fetch data for both timeframes
            timeframe_data = {}
            
            for tf_name, tf_interval in config.TIMEFRAMES.items():
                # Fetch raw data
                raw_data = self.data_fetcher.fetch_data(
                    interval=tf_interval,
                    period=config.DATA_PERIOD
                )
                
                # Check data freshness
                if check_market_hours and not raw_data.empty:
                    latest_timestamp = raw_data.index[-1]
                    is_fresh, freshness_msg = MarketHours.check_data_freshness(latest_timestamp)
                    
                    if not is_fresh:
                        data_freshness_warnings.append(f"{tf_interval}: {freshness_msg}")
                        if verbose:
                            print(f"   {freshness_msg}")
                
                # Calculate indicators
                enriched_data = calculate_all_indicators(
                    raw_data,
                    config.INDICATORS
                )
                
                timeframe_data[tf_interval] = enriched_data
            
            # Generate multi-timeframe signal
            signal = self.signal_generator.generate_multi_timeframe_signal(
                self.ticker,
                timeframe_data
            )
            
            # Add market status to signal
            if check_market_hours:
                signal['market_status'] = market_status
                if data_freshness_warnings:
                    signal['data_freshness_warnings'] = data_freshness_warnings
            
            # Print formatted output if verbose
            if verbose:
                self._print_signal(signal)
            
            return signal
        
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            if verbose:
                print(f"\n❌ {error_msg}\n")
            return {"error": error_msg}
    
    def _print_signal(self, signal: Dict[str, Any]) -> None:
        """
        Print the signal in a formatted, human-readable way.
        
        Args:
            signal: The complete signal dictionary
        """
        print("\n" + "="*80)
        print(f"  MARKET COPILOT - {signal['ticker']} Analysis")
        print(f"  {signal['analysis_timestamp']}")
        
        # Show market status if available
        if 'market_status' in signal:
            status = signal['market_status']['status']
            print(f"  Market Status: {status}")
        
        print("="*80)
        
        # Print each timeframe
        for tf_name, tf_signal in signal['timeframes'].items():
            print(f"\n📊 {tf_name.upper()} Timeframe:")
            print(f"   Bias: {tf_signal['bias']} ({tf_signal['confidence_label']} - {tf_signal['confidence']:.1%})")
            print(f"   Volatility: {tf_signal['volatility_regime']}")
            
            # Indicators
            ind = tf_signal['indicators']
            print(f"\n   Indicators:")
            print(f"      Close: ${ind['close']}")
            print(f"      VWAP:  ${ind['vwap']}")
            print(f"      EMA9:  ${ind['ema_9']}  |  EMA21: ${ind['ema_21']}")
            print(f"      RSI:   {ind['rsi']}  |  ATR: ${ind['atr']}")
            
            # Analysis notes
            print(f"\n   Analysis:")
            for note in tf_signal['analysis_notes']:
                print(f"      • {note}")
        
        # Synthesis
        print("\n" + "-"*80)
        print("📈 SYNTHESIS:")
        synthesis = signal['synthesis']
        print(f"   Overall Bias: {synthesis['overall_bias']} (Avg Confidence: {synthesis['average_confidence']:.1%})")
        print(f"   Alignment: {synthesis['timeframe_alignment']} - {synthesis['alignment_strength']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in synthesis['recommendations']:
            print(f"   • {rec}")
        
        print("\n" + "="*80 + "\n")
    
    def export_to_json(self, signal: Dict[str, Any], filepath: str) -> None:
        """
        Export signal to JSON file.
        
        Args:
            signal: The signal dictionary to export
            filepath: Path to save the JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(signal, f, indent=2)
        print(f"Signal exported to {filepath}")


def main():
    """
    Main entry point for the Market Copilot.
    """
    # Create and run the copilot
    copilot = MarketCopilot()
    signal = copilot.analyze(verbose=True)
    
    # Optionally export to JSON
    # copilot.export_to_json(signal, "spy_signal.json")
    
    return signal


if __name__ == "__main__":
    main()
