"""
Technical indicators module - Computes all required indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        data: Price series (typically Close prices)
        period: EMA period
    
    Returns:
        Series with EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Args:
        data: Price series (typically Close prices)
        period: RSI period (default 14)
    
    Returns:
        Series with RSI values
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period (default 14)
    
    Returns:
        Series with ATR values
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume Weighted Average Price for the current session.
    Resets at the start of each trading day.
    
    Args:
        df: DataFrame with High, Low, Close, Volume columns
    
    Returns:
        Series with VWAP values
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Get date component for grouping by session
    df_copy = df.copy()
    df_copy['date'] = df_copy.index.date
    
    # Calculate cumulative values within each session
    df_copy['tp_volume'] = typical_price * df['Volume']
    df_copy['cumul_tp_volume'] = df_copy.groupby('date')['tp_volume'].cumsum()
    df_copy['cumul_volume'] = df_copy.groupby('date')['Volume'].cumsum()
    
    # VWAP = cumulative(typical_price * volume) / cumulative(volume)
    vwap = df_copy['cumul_tp_volume'] / df_copy['cumul_volume']
    
    return vwap


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data: Price series (typically Close prices)
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
    
    Returns:
        Dictionary with 'macd', 'signal', and 'histogram' Series
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_all_indicators(df: pd.DataFrame, config: Dict[str, int]) -> pd.DataFrame:
    """
    Calculate all technical indicators and add them to the DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        config: Dictionary with indicator parameters
            - ema_fast: Fast EMA period
            - ema_slow: Slow EMA period
            - rsi_period: RSI period
            - atr_period: ATR period
    
    Returns:
        DataFrame with all indicators added as new columns
    """
    df = df.copy()
    
    # EMAs
    df['EMA_fast'] = calculate_ema(df['Close'], config['ema_fast'])
    df['EMA_slow'] = calculate_ema(df['Close'], config['ema_slow'])
    
    # RSI
    df['RSI'] = calculate_rsi(df['Close'], config['rsi_period'])
    
    # ATR
    df['ATR'] = calculate_atr(df, config['atr_period'])
    
    # VWAP
    df['VWAP'] = calculate_vwap(df)
    
    # MACD
    macd_data = calculate_macd(df['Close'])
    df['MACD'] = macd_data['macd']
    df['MACD_signal'] = macd_data['signal']
    df['MACD_histogram'] = macd_data['histogram']
    
    return df


def detect_volatility_regime(atr_series: pd.Series, lookback: int = 5) -> str:
    """
    Detect whether volatility is expanding or compressing.
    
    Args:
        atr_series: Series of ATR values
        lookback: Number of periods to look back for trend
    
    Returns:
        "Expansion" if ATR is rising, "Compression" if falling, "Neutral" if unclear
    """
    if len(atr_series) < lookback + 1:
        return "Neutral"
    
    recent_atr = atr_series.iloc[-lookback:].values
    
    # Check if ATR is generally rising or falling
    # Simple linear regression slope
    x = np.arange(len(recent_atr))
    slope = np.polyfit(x, recent_atr, 1)[0]
    
    # Threshold for significance (can be tuned)
    threshold = recent_atr.mean() * 0.01  # 1% of average ATR
    
    if slope > threshold:
        return "Expansion"
    elif slope < -threshold:
        return "Compression"
    else:
        return "Neutral"
