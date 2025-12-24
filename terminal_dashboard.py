"""
Terminal Dashboard - Interactive HUD with live charts and indicators
"""
import plotext as plt
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from datetime import datetime
import time
from typing import Optional
import pandas as pd

from market_copilot import MarketCopilot
from market_hours import MarketHours


class TerminalDashboard:
    """
    Interactive terminal dashboard with charts and HUD display.
    """
    
    def __init__(self):
        self.console = Console()
        self.copilot = MarketCopilot()
        self.last_signal = None
        self.chart_data = {}  # Store DataFrames for chart generation
        
    def create_price_chart(self, signal: dict, timeframe: str) -> str:
        """
        Create an ASCII chart of price action in the terminal.
        """
        plt.clear_figure()
        plt.clf()
        
        # Get data from stored chart_data
        if timeframe not in self.chart_data:
            return "[yellow]Chart data not available[/yellow]"
            
        df = self.chart_data[timeframe]
        
        # Get more data points for better visualization
        lookback = min(100, len(df))
        df = df.tail(lookback)
        
        timestamps = list(range(len(df)))
        closes = df['Close'].tolist()
        
        # Plot the line chart with braille for smooth lines
        plt.plot(timestamps, closes, color="green+", label="Price")
        
        # Add EMAs if available
        if 'EMA_fast' in df.columns:
            ema9 = df['EMA_fast'].tolist()
            plt.plot(timestamps, ema9, color="yellow+", label="EMA9")
        
        if 'EMA_slow' in df.columns:
            ema21 = df['EMA_slow'].tolist()
            plt.plot(timestamps, ema21, color="cyan+", label="EMA21")
        
        # Chart settings
        plt.title(f"SPY {timeframe.upper()} - Last {lookback} Candles")
        plt.xlabel("← Older | Newer →")
        plt.ylabel("Price ($)")
        plt.theme('dark')
        
        # Set canvas size for better rendering
        plt.plotsize(80, 20)
        
        return plt.build()
    
    def create_indicator_panel(self, signal: dict, timeframe: str) -> Table:
        """
        Create a HUD-style panel showing indicators.
        """
        tf_data = signal['timeframes'][timeframe]
        indicators = tf_data['indicators']
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Indicator", style="bold cyan", width=8)
        table.add_column("Value", style="bold white", width=12)
        table.add_column("Info", style="", justify="left")
        
        # Close Price with EMA trend
        close = indicators['close']
        ema9 = indicators['ema_9']
        ema21 = indicators['ema_21']
        
        # Determine trend
        if close > ema9 > ema21:
            trend_symbol = "🟢 ⬆"
            trend_color = "green"
        elif close < ema9 < ema21:
            trend_symbol = "🔴 ⬇"
            trend_color = "red"
        else:
            trend_symbol = "🟡 ↔"
            trend_color = "yellow"
        
        table.add_row(
            "CLOSE",
            f"[bold]{close:.2f}[/]",
            f"[{trend_color}]{trend_symbol}[/]"
        )
        
        # VWAP with difference
        vwap_diff = close - indicators['vwap']
        vwap_color = "green" if vwap_diff > 0 else "red"
        vwap_pct = (vwap_diff / indicators['vwap']) * 100
        table.add_row(
            "VWAP",
            f"{indicators['vwap']:.2f}",
            f"[{vwap_color}]{'▲' if vwap_diff > 0 else '▼'} {abs(vwap_diff):.2f} ({vwap_pct:+.2f}%)[/]"
        )
        
        # EMA 9
        ema9_diff = close - ema9
        ema9_color = "green" if ema9_diff > 0 else "red"
        table.add_row(
            "EMA 9",
            f"{ema9:.2f}",
            f"[{ema9_color}]{'▲' if ema9_diff > 0 else '▼'} {abs(ema9_diff):.2f}[/]"
        )
        
        # EMA 21
        ema21_diff = close - ema21
        ema21_color = "green" if ema21_diff > 0 else "red"
        table.add_row(
            "EMA 21",
            f"{ema21:.2f}",
            f"[{ema21_color}]{'▲' if ema21_diff > 0 else '▼'} {abs(ema21_diff):.2f}[/]"
        )
        
        # RSI with color coding and bar
        rsi = indicators['rsi']
        if rsi > 70:
            rsi_color = "red bold"
            rsi_status = "OVERBOUGHT"
        elif rsi > 55:
            rsi_color = "green"
            rsi_status = "BULLISH"
        elif rsi < 30:
            rsi_color = "red bold"
            rsi_status = "OVERSOLD"
        elif rsi < 45:
            rsi_color = "red"
            rsi_status = "BEARISH"
        else:
            rsi_color = "yellow"
            rsi_status = "NEUTRAL"
        
        rsi_bar = self.create_bar(rsi, 0, 100, width=15)
        table.add_row(
            "RSI",
            f"[{rsi_color}]{rsi:.1f}[/]",
            f"[{rsi_color}]{rsi_bar} {rsi_status}[/]"
        )
        
        # ATR
        table.add_row(
            "ATR",
            f"${indicators['atr']:.2f}",
            ""
        )
        
        return table
    
    def create_bar(self, value: float, min_val: float, max_val: float, width: int = 20) -> str:
        """
        Create a visual bar for indicators.
        """
        normalized = (value - min_val) / (max_val - min_val)
        filled = int(normalized * width)
        return "█" * filled + "░" * (width - filled)
    
    def create_bias_panel(self, signal: dict, timeframe: str) -> Panel:
        """
        Create a panel showing bias and confidence.
        """
        tf_data = signal['timeframes'][timeframe]
        bias = tf_data['bias']
        confidence = tf_data['confidence']
        vol_regime = tf_data['volatility_regime']
        
        # Color coding
        if bias == "Bullish":
            bias_color = "green bold"
            bias_symbol = "🚀"
        elif bias == "Bearish":
            bias_color = "red bold"
            bias_symbol = "📉"
        else:
            bias_color = "yellow bold"
            bias_symbol = "➡️"
        
        # Confidence bar
        conf_bar = self.create_bar(confidence, 0, 1, width=30)
        conf_color = "green" if confidence > 0.75 else "yellow" if confidence > 0.5 else "red"
        
        # Volatility
        vol_color = "red" if vol_regime == "Expansion" else "blue" if vol_regime == "Compression" else "white"
        
        content = Text()
        content.append(f"\n{bias_symbol}  BIAS: ", style="bold white")
        content.append(f"{bias}\n", style=bias_color)
        content.append(f"   CONFIDENCE: ", style="bold white")
        content.append(f"{confidence:.0%}\n", style=conf_color)
        content.append(f"   [{conf_color}]{conf_bar}[/]\n\n", style=conf_color)
        content.append(f"⚡ VOLATILITY: ", style="bold white")
        content.append(f"{vol_regime}\n", style=vol_color)
        
        return Panel(content, title=f"[bold white]{timeframe.upper()} ANALYSIS[/]", border_style=bias_color)
    
    def create_synthesis_panel(self, signal: dict) -> Panel:
        """
        Create synthesis/recommendations panel.
        """
        synthesis = signal['synthesis']
        
        # Overall bias styling
        bias = synthesis['overall_bias']
        if bias == "Bullish":
            style = "green bold"
            emoji = "🟢"
        elif bias == "Bearish":
            style = "red bold"
            emoji = "🔴"
        else:
            style = "yellow bold"
            emoji = "🟡"
        
        content = Text()
        content.append(f"\n{emoji} OVERALL BIAS: ", style="bold white")
        content.append(f"{bias}\n\n", style=style)
        
        content.append(f"📊 AVG CONFIDENCE: ", style="bold white")
        content.append(f"{synthesis['average_confidence']:.0%}\n", style="cyan")
        
        content.append(f"🎯 ALIGNMENT: ", style="bold white")
        content.append(f"{synthesis['timeframe_alignment']} - {synthesis['alignment_strength']}\n\n", style="white")
        
        content.append("💡 RECOMMENDATIONS:\n", style="bold yellow")
        for rec in synthesis['recommendations']:
            content.append(f"  • {rec}\n", style="white")
        
        return Panel(content, title="[bold white]🎯 SYNTHESIS[/]", border_style=style)
    
    def create_market_status_panel(self, signal: dict) -> Panel:
        """
        Create market status panel.
        """
        if 'market_status' in signal:
            status = signal['market_status']
            
            status_text = status['status']
            if status_text == "Open":
                color = "green bold"
                symbol = "🟢"
            elif status_text in ["Pre-Market", "After-Hours"]:
                color = "yellow bold"
                symbol = "🟡"
            else:
                color = "red bold"
                symbol = "🔴"
            
            content = Text()
            content.append(f"\n{symbol} STATUS: ", style="bold white")
            content.append(f"{status_text}\n", style=color)
            content.append(f"🕐 TIME (ET): {status['current_time_et']}\n", style="white")
            
            if status['next_open']:
                content.append(f"⏭️  NEXT OPEN: {status['next_open']}\n", style="cyan")
        else:
            content = Text("\n📊 Live Market Analysis\n", style="bold cyan")
        
        return Panel(content, title="[bold white]MARKET STATUS[/]", border_style="cyan")
    
    def create_dashboard(self, signal: dict) -> Layout:
        """
        Create the complete dashboard layout.
        """
        layout = Layout()
        
        # Split into header, body, footer
        layout.split_column(
            Layout(name="header", size=6),
            Layout(name="body"),
            Layout(name="footer", size=12)
        )
        
        # Header
        header_text = Text()
        header_text.append("╔═══════════════════════════════════════════════════════════════════╗\n", style="cyan")
        header_text.append("║        ", style="cyan")
        header_text.append("🚀 SPY MARKET COPILOT - LIVE TERMINAL DASHBOARD", style="bold white")
        header_text.append("        ║\n", style="cyan")
        header_text.append("╚═══════════════════════════════════════════════════════════════════╝", style="cyan")
        layout["header"].update(Panel(header_text, border_style="cyan"))
        
        # Body - split into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Left side - timeframe panels (indicators + mini chart description)
        layout["left"].split_column(
            Layout(name="tf_5m"),
            Layout(name="tf_15m")
        )
        
        # Right side - analysis panels
        layout["right"].split_column(
            Layout(name="market_status", size=8),
            Layout(name="bias_5m", size=12),
            Layout(name="bias_15m", size=12),
        )
        
        # Populate market status
        layout["market_status"].update(self.create_market_status_panel(signal))
        
        # Populate 5m section - just indicators panel (charts causing layout issues)
        layout["tf_5m"].update(Panel(
            self.create_indicator_panel(signal, "5m"),
            title="[bold cyan]📊 5M INDICATORS[/]",
            border_style="green"
        ))
        layout["bias_5m"].update(self.create_bias_panel(signal, "5m"))
        
        # Populate 15m section - just indicators panel
        layout["tf_15m"].update(Panel(
            self.create_indicator_panel(signal, "15m"),
            title="[bold cyan]📊 15M INDICATORS[/]",
            border_style="green"
        ))
        layout["bias_15m"].update(self.create_bias_panel(signal, "15m"))
        
        # Footer - synthesis
        layout["footer"].update(self.create_synthesis_panel(signal))
        
        return layout
    
    def run_once(self):
        """
        Run the dashboard once (static display).
        """
        self.console.clear()
        
        with self.console.status("[bold cyan]Fetching market data...", spinner="dots"):
            # Fetch data for charts
            from data_fetcher import YahooFinanceDataFetcher
            from indicators import calculate_all_indicators
            from config import INDICATORS
            
            fetcher = YahooFinanceDataFetcher("SPY")
            
            # Fetch 5m data
            df_5m = fetcher.fetch_data("5m", period="5d")
            if df_5m is not None and not df_5m.empty:
                df_5m = calculate_all_indicators(df_5m, INDICATORS)
                self.chart_data["5m"] = df_5m
            
            # Fetch 15m data
            df_15m = fetcher.fetch_data("15m", period="5d")
            if df_15m is not None and not df_15m.empty:
                df_15m = calculate_all_indicators(df_15m, INDICATORS)
                self.chart_data["15m"] = df_15m
            
            # Generate signal
            signal = self.copilot.analyze(verbose=False)
        
        self.last_signal = signal
        
        # Create and display dashboard
        dashboard = self.create_dashboard(signal)
        self.console.print(dashboard)
        
        return signal
    
    def run_live(self, refresh_interval: int = 60):
        """
        Run the dashboard with live updates.
        
        Args:
            refresh_interval: Seconds between updates
        """
        try:
            while True:
                self.run_once()
                
                self.console.print(f"\n[dim]Last update: {datetime.now().strftime('%H:%M:%S')} | Refreshing in {refresh_interval}s | Press Ctrl+C to exit[/dim]")
                
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            self.console.print("\n\n[bold yellow]Dashboard stopped by user[/bold yellow]")


def main():
    """
    Main entry point for terminal dashboard.
    """
    import sys
    
    dashboard = TerminalDashboard()
    
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Live mode with auto-refresh
        refresh = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        dashboard.console.print(f"\n[bold cyan]Starting live dashboard (refresh every {refresh}s)...[/bold cyan]\n")
        dashboard.run_live(refresh_interval=refresh)
    else:
        # Single run mode
        dashboard.run_once()


if __name__ == "__main__":
    main()
