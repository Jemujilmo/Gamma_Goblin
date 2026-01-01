"""
Signal Backtester - Analyzes signal performance and suggests improvements
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class SignalBacktester:
    """Backtests trading signals and suggests algorithm improvements"""
    
    def __init__(self, lookforward_candles: int = 5):
        """
        Args:
            lookforward_candles: How many candles ahead to check profitability
        """
        self.lookforward_candles = lookforward_candles
    
    def evaluate_signals(self, data: pd.DataFrame, signals: List[Dict]) -> Dict:
        """
        Evaluate each signal's performance.
        
        Returns:
            Dictionary with performance metrics and improvement suggestions
        """
        results = {
            'total_signals': len(signals),
            'buy_signals': 0,
            'sell_signals': 0,
            'profitable_buys': 0,
            'profitable_sells': 0,
            'losing_buys': 0,
            'losing_sells': 0,
            'buy_accuracy': 0.0,
            'sell_accuracy': 0.0,
            'signal_details': [],
            'failed_signal_patterns': []
        }
        
        if not signals:
            return results
        
        for signal in signals:
            signal_time = pd.Timestamp(signal['timestamp'])
            signal_price = signal['price']
            signal_type = signal['type']
            
            # Find signal in data
            try:
                signal_idx = data.index.get_loc(signal_time)
            except KeyError:
                # Signal timestamp not in data, skip
                continue
            
            # Look forward to see if signal was profitable
            future_idx = min(signal_idx + self.lookforward_candles, len(data) - 1)
            future_prices = data.iloc[signal_idx:future_idx + 1]
            
            if len(future_prices) < 2:
                continue
            
            # Calculate performance
            max_gain = future_prices['High'].max() - signal_price
            max_loss = signal_price - future_prices['Low'].min()
            final_price = future_prices.iloc[-1]['Close']
            final_pnl = final_price - signal_price if signal_type == 'buy' else signal_price - final_price
            
            # Determine if profitable
            is_profitable = final_pnl > 0
            
            # Track results
            if signal_type == 'buy':
                results['buy_signals'] += 1
                if is_profitable:
                    results['profitable_buys'] += 1
                else:
                    results['losing_buys'] += 1
                    results['failed_signal_patterns'].append({
                        'timestamp': str(signal_time),
                        'type': 'buy',
                        'price': signal_price,
                        'pnl': final_pnl,
                        'strength': signal.get('strength', 0),
                        'label': signal.get('label', '')
                    })
            else:
                results['sell_signals'] += 1
                if is_profitable:
                    results['profitable_sells'] += 1
                else:
                    results['losing_sells'] += 1
                    results['failed_signal_patterns'].append({
                        'timestamp': str(signal_time),
                        'type': 'sell',
                        'price': signal_price,
                        'pnl': final_pnl,
                        'strength': signal.get('strength', 0),
                        'label': signal.get('label', '')
                    })
            
            results['signal_details'].append({
                'timestamp': str(signal_time),
                'type': signal_type,
                'price': signal_price,
                'strength': signal.get('strength', 0),
                'profitable': is_profitable,
                'pnl': final_pnl,
                'max_gain': max_gain,
                'max_loss': max_loss
            })
        
        # Calculate accuracy
        if results['buy_signals'] > 0:
            results['buy_accuracy'] = results['profitable_buys'] / results['buy_signals'] * 100
        if results['sell_signals'] > 0:
            results['sell_accuracy'] = results['profitable_sells'] / results['sell_signals'] * 100
        
        # Overall accuracy
        total_profitable = results['profitable_buys'] + results['profitable_sells']
        results['overall_accuracy'] = total_profitable / len(signals) * 100 if signals else 0
        
        return results
    
    def analyze_failed_signals(self, results: Dict, data: pd.DataFrame, indicators: pd.DataFrame) -> List[str]:
        """
        Analyze failed signals to identify common patterns.
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        if not results['failed_signal_patterns']:
            suggestions.append("✅ All signals were profitable!")
            return suggestions
        
        failed = results['failed_signal_patterns']
        
        # Analyze by signal strength
        weak_failures = [s for s in failed if s['strength'] < 50]
        strong_failures = [s for s in failed if s['strength'] >= 70]
        
        if len(weak_failures) > len(failed) * 0.5:
            suggestions.append(f"⚠️ {len(weak_failures)}/{len(failed)} failed signals were WEAK (<50%). Consider raising minimum threshold to 45-50%.")
        
        if strong_failures:
            suggestions.append(f"⚠️ {len(strong_failures)} STRONG signals (>70%) failed. These need investigation:")
            for sig in strong_failures[:3]:  # Show top 3
                suggestions.append(f"   - {sig['type'].upper()} at ${sig['price']:.2f} ({sig['label']}) → Lost ${abs(sig['pnl']):.2f}")
        
        # Analyze counter-trend vs trend-following
        counter_trend_failures = [s for s in failed if 'COUNTER-TREND' in s.get('label', '')]
        risky_failures = [s for s in failed if 'RISKY' in s.get('label', '')]
        
        if len(counter_trend_failures) > len(failed) * 0.4:
            suggestions.append(f"⚠️ Counter-trend signals have {len(counter_trend_failures)}/{len(failed)} failures. Consider reducing RSI reversal weight.")
        
        if len(risky_failures) > len(failed) * 0.3:
            suggestions.append(f"⚠️ RISKY signals (against RSI) failing frequently. Consider blocking signals against extreme RSI.")
        
        # Accuracy-based suggestions
        if results['buy_accuracy'] < 40:
            suggestions.append(f"⚠️ BUY accuracy is only {results['buy_accuracy']:.1f}%. Consider:")
            suggestions.append("   - Increase weight on upward momentum factor")
            suggestions.append("   - Require EMA9 > EMA21 for all buys")
            suggestions.append("   - Add pullback detection (don't buy into resistance)")
        
        if results['sell_accuracy'] < 40:
            suggestions.append(f"⚠️ SELL accuracy is only {results['sell_accuracy']:.1f}%. Consider:")
            suggestions.append("   - Increase weight on downward momentum factor")
            suggestions.append("   - Require EMA9 < EMA21 for all sells")
            suggestions.append("   - Add bounce detection (don't sell into support)")
        
        return suggestions
    
    def generate_report(self, data: pd.DataFrame, indicators: pd.DataFrame, signals: List[Dict]) -> str:
        """Generate a comprehensive backtest report"""
        
        results = self.evaluate_signals(data, signals)
        suggestions = self.analyze_failed_signals(results, data, indicators)
        
        report = []
        report.append("=" * 70)
        report.append("📊 SIGNAL BACKTEST REPORT")
        report.append("=" * 70)
        report.append("")
        report.append("OVERALL PERFORMANCE:")
        report.append(f"  Total Signals: {results['total_signals']}")
        report.append(f"  Overall Accuracy: {results.get('overall_accuracy', 0):.1f}%")
        report.append("")
        report.append("BUY SIGNALS:")
        report.append(f"  Total: {results['buy_signals']}")
        report.append(f"  Profitable: {results['profitable_buys']} ({results['buy_accuracy']:.1f}%)")
        report.append(f"  Losing: {results['losing_buys']}")
        report.append("")
        report.append("SELL SIGNALS:")
        report.append(f"  Total: {results['sell_signals']}")
        report.append(f"  Profitable: {results['profitable_sells']} ({results['sell_accuracy']:.1f}%)")
        report.append(f"  Losing: {results['losing_sells']}")
        report.append("")
        report.append("=" * 70)
        report.append("🔧 IMPROVEMENT SUGGESTIONS:")
        report.append("=" * 70)
        for suggestion in suggestions:
            report.append(suggestion)
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
