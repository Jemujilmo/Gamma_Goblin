"""Real options chain data fetcher for SPY using yfinance.

Provides:
- IV Rank and IV Percentile calculations
- Put/Call ratio from real options volume
- Gamma exposure levels
- Strike-based support/resistance from actual open interest
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class OptionsDataFetcher:
    """Fetch and analyze real options chain data for SPY"""
    
    def __init__(self, ticker: str = "SPY"):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        
    def get_options_walls(self, current_price: float, min_oi: int = 1000) -> List[Dict]:
        """Get support/resistance levels from actual options open interest.
        
        Args:
            current_price: Current stock price
            min_oi: Minimum open interest to consider a strike significant
            
        Returns:
            List of dicts with strike, type, strength, open_interest
        """
        try:
            # Get nearest expiration (typically 0-7 DTE for max gamma)
            expirations = self.stock.options
            if not expirations or len(expirations) == 0:
                return self._fallback_walls(current_price)
            
            # Use nearest expiration for highest gamma impact
            nearest_exp = expirations[0]
            chain = self.stock.option_chain(nearest_exp)
            
            calls = chain.calls
            puts = chain.puts
            
            # Combine calls and puts, focusing on near-the-money strikes
            price_range = current_price * 0.03  # ±3% range
            lower_bound = current_price - price_range
            upper_bound = current_price + price_range
            
            walls = []
            
            # Process calls (resistance above current price)
            call_strikes = calls[
                (calls['strike'] >= current_price) & 
                (calls['strike'] <= upper_bound) &
                (calls['openInterest'] >= min_oi)
            ].sort_values('openInterest', ascending=False).head(3)
            
            for _, row in call_strikes.iterrows():
                walls.append({
                    'strike': float(row['strike']),
                    'type': 'resistance',
                    'strength': min(100, int((row['openInterest'] / 10000) * 100)),
                    'open_interest': int(row['openInterest']),
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0
                })
            
            # Process puts (support below current price)
            put_strikes = puts[
                (puts['strike'] <= current_price) & 
                (puts['strike'] >= lower_bound) &
                (puts['openInterest'] >= min_oi)
            ].sort_values('openInterest', ascending=False).head(3)
            
            for _, row in put_strikes.iterrows():
                walls.append({
                    'strike': float(row['strike']),
                    'type': 'support',
                    'strength': min(100, int((row['openInterest'] / 10000) * 100)),
                    'open_interest': int(row['openInterest']),
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0
                })
            
            # Sort by distance from current price
            walls.sort(key=lambda x: abs(x['strike'] - current_price))
            
            return walls[:6] if walls else self._fallback_walls(current_price)
            
        except Exception as e:
            print(f"Options walls error: {e}")
            return self._fallback_walls(current_price)
    
    def get_iv_metrics(self) -> Dict:
        """Calculate IV Rank and IV Percentile from options chain.
        
        Returns:
            Dict with iv_rank, iv_percentile, current_iv, iv_high, iv_low
        """
        try:
            expirations = self.stock.options
            if not expirations or len(expirations) == 0:
                return self._fallback_iv_metrics()
            
            # Get ATM implied volatility from nearest expiration
            nearest_exp = expirations[0]
            chain = self.stock.option_chain(nearest_exp)
            
            # Get current stock price
            hist = self.stock.history(period='1d')
            if hist.empty:
                return self._fallback_iv_metrics()
            
            current_price = float(hist['Close'].iloc[-1])
            
            # Find ATM option (closest to current price)
            calls = chain.calls
            atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
            
            if atm_call.empty or pd.isna(atm_call['impliedVolatility'].iloc[0]):
                return self._fallback_iv_metrics()
            
            current_iv = float(atm_call['impliedVolatility'].iloc[0])
            
            # Get historical volatility for comparison
            # Calculate IV rank using 52-week historical range
            hist_52w = self.stock.history(period='1y')
            if not hist_52w.empty:
                returns = hist_52w['Close'].pct_change().dropna()
                hist_vol = returns.std() * np.sqrt(252)  # Annualized
                
                # For IV rank, we need historical IV data
                # As approximation, use historical volatility range
                iv_high = hist_vol * 1.5  # Approximate high IV
                iv_low = hist_vol * 0.5   # Approximate low IV
                
                # IV Rank = (Current IV - 52w Low IV) / (52w High IV - 52w Low IV)
                iv_rank = ((current_iv - iv_low) / (iv_high - iv_low)) * 100 if (iv_high - iv_low) > 0 else 50
                iv_rank = max(0, min(100, iv_rank))
                
                # IV Percentile (simplified - what % of time IV was below current)
                iv_percentile = iv_rank  # Simplified approximation
                
                return {
                    'iv_rank': round(iv_rank, 1),
                    'iv_percentile': round(iv_percentile, 1),
                    'current_iv': round(current_iv * 100, 2),  # Convert to percentage
                    'iv_high': round(iv_high * 100, 2),
                    'iv_low': round(iv_low * 100, 2),
                    'hist_vol': round(hist_vol * 100, 2)
                }
            else:
                return {
                    'iv_rank': 50.0,
                    'iv_percentile': 50.0,
                    'current_iv': round(current_iv * 100, 2),
                    'iv_high': None,
                    'iv_low': None,
                    'hist_vol': None
                }
                
        except Exception as e:
            print(f"IV metrics error: {e}")
            return self._fallback_iv_metrics()
    
    def get_put_call_ratio(self) -> Dict:
        """Calculate Put/Call ratio from options volume and open interest.
        
        Returns:
            Dict with volume_pcr, oi_pcr, sentiment
        """
        try:
            expirations = self.stock.options
            if not expirations or len(expirations) < 2:
                return {'volume_pcr': 1.0, 'oi_pcr': 1.0, 'sentiment': 'neutral'}
            
            # Use first 2 expirations for broader picture
            total_put_volume = 0
            total_call_volume = 0
            total_put_oi = 0
            total_call_oi = 0
            
            for exp in expirations[:2]:
                chain = self.stock.option_chain(exp)
                
                put_vol = chain.puts['volume'].sum()
                call_vol = chain.calls['volume'].sum()
                put_oi = chain.puts['openInterest'].sum()
                call_oi = chain.calls['openInterest'].sum()
                
                if pd.notna(put_vol):
                    total_put_volume += put_vol
                if pd.notna(call_vol):
                    total_call_volume += call_vol
                if pd.notna(put_oi):
                    total_put_oi += put_oi
                if pd.notna(call_oi):
                    total_call_oi += call_oi
            
            volume_pcr = total_put_volume / total_call_volume if total_call_volume > 0 else 1.0
            oi_pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
            
            # Interpret sentiment
            avg_pcr = (volume_pcr + oi_pcr) / 2
            if avg_pcr > 1.2:
                sentiment = 'bearish'
            elif avg_pcr < 0.8:
                sentiment = 'bullish'
            else:
                sentiment = 'neutral'
            
            return {
                'volume_pcr': round(volume_pcr, 2),
                'oi_pcr': round(oi_pcr, 2),
                'sentiment': sentiment,
                'put_volume': int(total_put_volume),
                'call_volume': int(total_call_volume)
            }
            
        except Exception as e:
            print(f"PCR error: {e}")
            return {'volume_pcr': 1.0, 'oi_pcr': 1.0, 'sentiment': 'neutral'}
    
    def get_gamma_exposure(self, current_price: float) -> Dict:
        """Estimate total gamma exposure levels.
        
        Returns:
            Dict with total_gamma, net_gamma_exposure, gex_level
        """
        try:
            expirations = self.stock.options
            if not expirations:
                return {'total_gamma': 0, 'net_gex': 0, 'gex_level': 'low'}
            
            # Focus on nearest expiration for max gamma impact
            nearest_exp = expirations[0]
            chain = self.stock.option_chain(nearest_exp)
            
            # Simplified GEX calculation
            # Dealers are short gamma when price is below call walls, long gamma above put walls
            call_gamma = chain.calls['openInterest'].sum()
            put_gamma = chain.puts['openInterest'].sum()
            
            total_gamma = call_gamma + put_gamma
            
            # Net GEX (positive = dealers long gamma = low volatility)
            # (negative = dealers short gamma = high volatility)
            net_gex = put_gamma - call_gamma
            
            # Categorize GEX level
            if abs(net_gex) < total_gamma * 0.2:
                gex_level = 'neutral'
            elif net_gex > 0:
                gex_level = 'high'  # Dealers long gamma, suppresses volatility
            else:
                gex_level = 'low'   # Dealers short gamma, amplifies volatility
            
            return {
                'total_gamma': int(total_gamma),
                'net_gex': int(net_gex),
                'gex_level': gex_level,
                'call_oi': int(call_gamma),
                'put_oi': int(put_gamma)
            }
            
        except Exception as e:
            print(f"GEX error: {e}")
            return {'total_gamma': 0, 'net_gex': 0, 'gex_level': 'neutral'}
    
    def _fallback_walls(self, price: float) -> List[Dict]:
        """Fallback synthetic walls when real data unavailable"""
        base = round(price)
        walls = []
        for i, off in enumerate([-2, -1, 1, 2]):
            walls.append({
                'strike': float(base + off),
                'type': 'resistance' if off > 0 else 'support',
                'strength': max(20, 80 - i * 15),
                'open_interest': 0,
                'volume': 0
            })
        return walls
    
    def _fallback_iv_metrics(self) -> Dict:
        """Fallback IV metrics when real data unavailable"""
        return {
            'iv_rank': 50.0,
            'iv_percentile': 50.0,
            'current_iv': 15.0,
            'iv_high': None,
            'iv_low': None,
            'hist_vol': None
        }


if __name__ == '__main__':
    # Test the options data fetcher
    print("Testing Options Data Fetcher for SPY...")
    print("=" * 60)
    
    fetcher = OptionsDataFetcher("SPY")
    
    # Get current price
    hist = yf.Ticker("SPY").history(period='1d')
    current_price = float(hist['Close'].iloc[-1])
    print(f"\nCurrent SPY Price: ${current_price:.2f}")
    
    print("\n1. Options Walls (Support/Resistance):")
    print("-" * 60)
    walls = fetcher.get_options_walls(current_price)
    for wall in walls:
        print(f"  ${wall['strike']:.2f} - {wall['type'].upper():11} | "
              f"Strength: {wall['strength']:3}% | OI: {wall['open_interest']:,}")
    
    print("\n2. IV Metrics:")
    print("-" * 60)
    iv = fetcher.get_iv_metrics()
    print(f"  Current IV:     {iv['current_iv']}%")
    print(f"  IV Rank:        {iv['iv_rank']}")
    print(f"  IV Percentile:  {iv['iv_percentile']}")
    if iv['hist_vol']:
        print(f"  Historical Vol: {iv['hist_vol']}%")
    
    print("\n3. Put/Call Ratio:")
    print("-" * 60)
    pcr = fetcher.get_put_call_ratio()
    print(f"  Volume P/C:     {pcr['volume_pcr']}")
    print(f"  OI P/C:         {pcr['oi_pcr']}")
    print(f"  Sentiment:      {pcr['sentiment'].upper()}")
    
    print("\n4. Gamma Exposure:")
    print("-" * 60)
    gex = fetcher.get_gamma_exposure(current_price)
    print(f"  Total Gamma:    {gex['total_gamma']:,}")
    print(f"  Net GEX:        {gex['net_gex']:,}")
    print(f"  GEX Level:      {gex['gex_level'].upper()}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
