"""
Chart View - Standalone ASCII charts for SPY Market Copilot
Displays price action charts separately from the main dashboard.
"""

import plotext as plt
import time
import os
import sys
from colorama import init
from data_fetcher import YahooFinanceDataFetcher
from indicators import calculate_all_indicators
from config import INDICATORS
from market_copilot import MarketCopilot
from market_hours import MarketHours

# Initialize colorama for Windows ANSI support
init(wrap=False)

# ANSI escape codes
HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'


def get_spinner_frame(counter: int) -> str:
    """Get rotating spinner animation frame."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    return frames[counter % len(frames)]


def create_status_widget(is_connected: bool, counter: int = 0) -> str:
    """Create connection status widget with animation."""
    if is_connected:
        spinner = get_spinner_frame(counter)
        return f"[green bold]{spinner} CONNECTED[/green bold]"
    else:
        return f"[red bold]✖ DISCONNECTED[/red bold]"


def create_market_status_widget(is_open: bool, counter: int = 0) -> str:
    """Create market status widget with animation."""
    if is_open:
        spinner = get_spinner_frame(counter)
        return f"[green bold]{spinner} MARKET OPEN[/green bold]"
    else:
        return f"[yellow bold]● MARKET CLOSED[/yellow bold]"


def create_bias_panel(bias: str, confidence: float, timeframe: str) -> str:
    """Create bias indicator panel."""
    if bias == "Bullish":
        bias_color = "green bold"
        bias_symbol = "🚀"
    elif bias == "Bearish":
        bias_color = "red bold"
        bias_symbol = "📉"
    else:
        bias_color = "yellow bold"
        bias_symbol = "➡️"
    
    conf_pct = int(confidence * 100)
    conf_bar = "█" * (conf_pct // 5) + "░" * (20 - (conf_pct // 5))
    
    return f"[{bias_color}]{bias_symbol} {bias.upper()}[/{bias_color}] [{timeframe.upper()}] {conf_bar} {conf_pct}%"


def create_chart(df, timeframe: str = "5m"):
    """
    Create an ASCII candlestick chart with EMAs and VWAP.
    Plot trend lines first, then candlesticks on top to avoid visual intersection.
    """
    plt.clear_figure()
    plt.clf()
    
    # Use last 30 candles for better visibility
    if len(df) > 30:
        df = df.tail(30)
    
    # Prepare data for candlestick chart
    # Use numeric indices for plotting, but we'll customize labels
    indices = list(range(len(df)))
    time_labels = [dt.strftime('%I:%M %p') for dt in df.index]
    
    # Plot trend lines FIRST (so they appear behind candlesticks)
    if 'EMA_fast' in df.columns:
        plt.plot(indices, df['EMA_fast'].tolist(), label="EMA9", color="yellow", marker="braille")
    if 'EMA_slow' in df.columns:
        plt.plot(indices, df['EMA_slow'].tolist(), label="EMA21", color="cyan", marker="braille")
    if 'VWAP' in df.columns:
        plt.plot(indices, df['VWAP'].tolist(), label="VWAP", color="magenta", marker="braille")
    
    # Plot candlesticks SECOND (on top of trend lines)
    candlestick_data = {
        'Open': df['Open'].tolist(),
        'High': df['High'].tolist(),
        'Low': df['Low'].tolist(),
        'Close': df['Close'].tolist()
    }
    plt.candlestick(indices, candlestick_data, colors=['green+', 'red+'])
    
    # Set custom x-axis labels with actual times
    # For 5m: show every 3rd candle (15 min intervals)
    # For 15m: show every 2nd candle (30 min intervals)
    label_step = 3 if timeframe == "5m" else 2
    label_indices = list(range(0, len(df), label_step))
    label_times = [time_labels[i] for i in label_indices]
    plt.xticks(label_indices, label_times)
    
    # Chart configuration
    candle_interval = "5 Minutes" if timeframe == "5m" else "15 Minutes"
    plt.title(f"SPY {timeframe.upper()} Chart - {candle_interval} per Candle (Green=Bullish, Red=Bearish)")
    plt.xlabel("Market Time (ET)")
    plt.ylabel("Price ($)")
    plt.theme('dark')
    
    plt.show()


def main():
    """Display charts for all configured timeframes."""
    print("\n*** SPY MARKET COPILOT - CHART VIEW ***\n")
    print("Fetching data from Yahoo Finance...\n")
    
    fetcher = YahooFinanceDataFetcher("SPY")
    
    # Fetch and display 5m chart
    print("=" * 80)
    print("5-MINUTE TIMEFRAME")
    print("=" * 80)
    df_5m = fetcher.fetch_data("5m", period="5d")
    if df_5m is not None and not df_5m.empty:
        df_5m = calculate_all_indicators(df_5m, INDICATORS)
        create_chart(df_5m, "5m")
    else:
        print("Failed to fetch 5m data")
    
    print("\n")
    
    # Fetch and display 15m chart
    print("=" * 80)
    print("15-MINUTE TIMEFRAME")
    print("=" * 80)
    df_15m = fetcher.fetch_data("15m", period="5d")
    if df_15m is not None and not df_15m.empty:
        df_15m = calculate_all_indicators(df_15m, INDICATORS)
        create_chart(df_15m, "15m")
    else:
        print("Failed to fetch 15m data")
    
    print("\nChart display complete")


def live_mode(refresh_interval=60):
    """
    Live mode - continuously update charts at specified interval with status widgets.
    Uses simple cls command for Windows clearing.
    
    Args:
        refresh_interval: Seconds between updates (default 60)
    """
    copilot = MarketCopilot()
    market_hours = MarketHours()
    fetcher = YahooFinanceDataFetcher("SPY")
    counter = 0
    
    # Initial data
    market_open = market_hours.is_market_open()
    is_connected = False
    signal_5m = None
    signal_15m = None
    df_5m = None
    df_15m = None
    last_update_time = None
    last_update_timestamp = None
    is_fetching = False
    
    def fetch_fresh_data():
        """Fetch new data and return updated variables"""
        nonlocal is_connected, signal_5m, signal_15m, df_5m, df_15m, market_open, last_update_time, last_update_timestamp
        
        market_open = market_hours.is_market_open()
        temp_connected = False
        temp_signal_5m = None
        temp_signal_15m = None
        temp_df_5m = None
        temp_df_15m = None
        
        try:
            result = copilot.analyze(verbose=False, check_market_hours=False)
            df_5m_raw = fetcher.fetch_data("5m", period="1d")
            df_15m_raw = fetcher.fetch_data("15m", period="1d")
            
            if df_5m_raw is not None and not df_5m_raw.empty:
                temp_df_5m = calculate_all_indicators(df_5m_raw, INDICATORS)
                temp_connected = True
            
            if df_15m_raw is not None and not df_15m_raw.empty:
                temp_df_15m = calculate_all_indicators(df_15m_raw, INDICATORS)
                temp_connected = True
            
            if result and 'timeframes' in result:
                temp_signal_5m = result['timeframes'].get('5m')
                temp_signal_15m = result['timeframes'].get('15m')
        except Exception as e:
            temp_connected = False
        
        # Update the outer scope variables
        is_connected = temp_connected
        signal_5m = temp_signal_5m
        signal_15m = temp_signal_15m
        df_5m = temp_df_5m
        df_15m = temp_df_15m
        last_update_time = time.strftime('%I:%M:%S %p ET')
        last_update_timestamp = time.time()
    
    # Initial data fetch
    print("\nFetching initial data...")
    fetch_fresh_data()
    
    # Hide cursor for cleaner display
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()
    
    try:
        while True:
            # Start fetching new data in background (for next cycle)
            next_fetch_at = refresh_interval
            
            # Display and countdown loop
            for countdown in range(refresh_interval, 0, -1):
                # Trigger background fetch when countdown starts
                if countdown == refresh_interval and countdown > 0:
                    # After first iteration, fetch new data immediately
                    if last_update_time is not None:  # Not first run
                        is_fetching = True
                        import threading
                        fetch_thread = threading.Thread(target=fetch_fresh_data, daemon=True)
                        fetch_thread.start()
                
                # Clear screen - cls works reliably in PowerShell despite flicker
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Display header with status widgets
                print(f"\n*** SPY MARKET COPILOT - LIVE CHART VIEW ***")
                
                # Calculate elapsed time since last update
                if last_update_timestamp:
                    elapsed = int(time.time() - last_update_timestamp)
                    status_line = f"Last Update: {last_update_time} ({elapsed}s ago)"
                else:
                    status_line = "Last Update: Fetching..."
                
                if is_fetching:
                    status_line += " | Updating..."
                print(f"{status_line}  |  ", end="")
                
                # Status widgets
                if is_connected:
                    spinner = get_spinner_frame(counter)
                    print(f"{spinner} CONNECTED  |  ", end="")
                else:
                    print("X DISCONNECTED  |  ", end="")
                
                if market_open:
                    spinner = get_spinner_frame(counter)
                    print(f"{spinner} MARKET OPEN")
                else:
                    print("O MARKET CLOSED")
                
                print(f"Auto-refresh: every {refresh_interval}s (Ctrl+C to stop)\n")
                
                # Display bias indicators if connected
                if is_connected and signal_5m and signal_15m:
                    bias_5m = signal_5m['bias']
                    conf_5m = int(signal_5m['confidence'] * 100)
                    bias_15m = signal_15m['bias']
                    conf_15m = int(signal_15m['confidence'] * 100)
                    
                    # Create visual bars
                    bar_length = 10
                    filled_5m = int((conf_5m / 100) * bar_length)
                    filled_15m = int((conf_15m / 100) * bar_length)
                    bar_5m = "█" * filled_5m + "░" * (bar_length - filled_5m)
                    bar_15m = "█" * filled_15m + "░" * (bar_length - filled_15m)
                    
                    # Emoji symbols
                    if bias_5m == "Bullish":
                        emoji_5m = "🚀"
                    elif bias_5m == "Bearish":
                        emoji_5m = "📉"
                    else:
                        emoji_5m = "➡️"
                    
                    if bias_15m == "Bullish":
                        emoji_15m = "🚀"
                    elif bias_15m == "Bearish":
                        emoji_15m = "📉"
                    else:
                        emoji_15m = "➡️"
                    
                    print(f"{emoji_5m} {bias_5m.upper()} [5M]  {bar_5m} {conf_5m}%")
                    print(f"{emoji_15m} {bias_15m.upper()} [15M] {bar_15m} {conf_15m}%")
                    
                    # Add gamma squeeze indicators if we have 5m data
                    if df_5m is not None and len(df_5m) > 20:
                        # Calculate volume metrics
                        recent_volume = df_5m['Volume'].iloc[-5:].mean()
                        avg_volume = df_5m['Volume'].mean()
                        volume_ratio = (recent_volume / avg_volume) if avg_volume > 0 else 1.0
                        
                        # Calculate volatility (ATR-based)
                        if 'ATR' in df_5m.columns:
                            current_atr = df_5m['ATR'].iloc[-1]
                            avg_atr = df_5m['ATR'].mean()
                            volatility_ratio = (current_atr / avg_atr) if avg_atr > 0 else 1.0
                        else:
                            volatility_ratio = 1.0
                        
                        # Calculate price momentum
                        price_change_5m = ((df_5m['Close'].iloc[-1] / df_5m['Close'].iloc[-5]) - 1) * 100 if len(df_5m) >= 5 else 0
                        
                        # Gamma squeeze score (0-100)
                        gamma_score = min(100, int((volume_ratio * 30 + volatility_ratio * 30 + abs(price_change_5m) * 10)))
                        
                        # Visual bar for gamma
                        gamma_filled = int((gamma_score / 100) * bar_length)
                        gamma_bar = "█" * gamma_filled + "░" * (bar_length - gamma_filled)
                        
                        # Determine gamma status
                        if gamma_score >= 70:
                            gamma_status = "⚡ HIGH GAMMA"
                            gamma_emoji = "⚡"
                        elif gamma_score >= 40:
                            gamma_status = "⚠️  ELEVATED"
                            gamma_emoji = "⚠️"
                        else:
                            gamma_status = "✓ NORMAL"
                            gamma_emoji = "✓"
                        
                        print(f"\n{gamma_emoji} {gamma_status:12} {gamma_bar} {gamma_score}%  |  Vol: {volume_ratio:.1f}x  |  Momentum: {price_change_5m:+.2f}%")
                    
                    print()
                
                # Fetch and display 5m chart
                print("=" * 80)
                print("5-MINUTE TIMEFRAME")
                print("=" * 80)
                
                if is_connected and df_5m is not None:
                    create_chart(df_5m, "5m")
                else:
                    print("Failed to fetch 5m data or no connection")
                
                print("\n")
                
                # Fetch and display 15m chart
                print("=" * 80)
                print("15-MINUTE TIMEFRAME")
                print("=" * 80)
                
                if is_connected and df_15m is not None:
                    create_chart(df_15m, "15m")
                else:
                    print("Failed to fetch 15m data or no connection")
                
                # Increment animation counter
                counter += 1
                
                # Wait 1 second before next countdown update
                time.sleep(1)
                
                # Check if background fetch completed
                if is_fetching and countdown > 1:
                    if not fetch_thread.is_alive():
                        is_fetching = False
            
    except KeyboardInterrupt:
        # Show cursor again on exit
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        print("\n\nLive mode stopped by user")


if __name__ == "__main__":
    import sys
    
    # Check for live mode flag
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        # Optional: custom refresh interval
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        live_mode(interval)
    else:
        main()
