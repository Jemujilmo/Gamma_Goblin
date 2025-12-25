"""
Flask Web Interface for Market Copilot
Provides interactive charts with:
- Candlestick charts with VWAP, EMA9, EMA21 overlays
- Gamma squeeze indicators
- Options walls (support/resistance levels)
- Sentiment-based buy/sell signals (green/red triangles)
"""

from flask import Flask, render_template, jsonify
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time

from market_copilot import MarketCopilot
from indicators import calculate_all_indicators
from config import DEFAULT_TICKER, REQUEST_DELAY, INDICATORS
import threading
from analyzers import OptionsWallAnalyzer, SentimentAnalyzer

app = Flask(__name__)

# --- Simple in-memory cache for API payload to avoid blocking on-demand rebuilds ---
_cache_lock = threading.Lock()
_cached_payload = None
_cached_at = None
_is_building = False
CACHE_TTL = 5  # seconds - how long cached payload is considered fresh
REFRESH_INTERVAL = 5  # seconds - background refresh interval

def build_and_cache_payload():
    global _cached_payload, _cached_at, _is_building
    # Prevent concurrent builds
    if _is_building:
        return
    _is_building = True
    try:
        # Run the analysis logic and cache a lightweight payload for quick serving
        copilot = MarketCopilot()
        data_5m = copilot.data_fetcher.fetch_data("5m", "5d")
        time.sleep(REQUEST_DELAY)
        data_15m = copilot.data_fetcher.fetch_data("15m", "1mo")

        if data_5m is None or data_15m is None or data_5m.empty or data_15m.empty:
            return

        data_5m_local = data_5m.tail(78)
        data_15m_local = data_15m.tail(100)

        indicators_5m = calculate_all_indicators(data_5m_local, INDICATORS)
        indicators_15m = calculate_all_indicators(data_15m_local, INDICATORS)

        bias_5m, conf_5m, notes_5m = copilot.bias_classifier.classify_bias(indicators_5m.iloc[-1])
        bias_15m, conf_15m, notes_15m = copilot.bias_classifier.classify_bias(indicators_15m.iloc[-1])

        copilot_data = {
            'data_5m': data_5m_local,
            'indicators_5m': indicators_5m,
            'bias_5m': bias_5m.value,
            'bias_15m': bias_15m.value
        }

        fig, walls, signals = create_chart(copilot_data, data_15m_local, indicators_15m)

        current_volume = data_5m_local['Volume'].iloc[-1]
        avg_volume = data_5m_local['Volume'].rolling(20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        current_atr = indicators_5m['ATR'].iloc[-1]
        avg_atr = indicators_5m['ATR'].rolling(20).mean().iloc[-1]
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

        price_change = ((data_5m_local['Close'].iloc[-1] - data_5m_local['Close'].iloc[-5]) /
                       data_5m_local['Close'].iloc[-5] * 100) if len(data_5m_local) >= 5 else 0

        gamma_score = min(100, int((volume_ratio * 30 + volatility_ratio * 30 + abs(price_change) * 10)))

        # Build a minimal payload to cache (avoid serializing full Plotly figure here)
        try:
            from market_hours import MarketHours
            market_status = MarketHours.get_market_status()
        except Exception:
            market_status = {'status': 'Unknown', 'is_open': False}

        payload = {
            'bias_5m': {'bias': bias_5m.value, 'confidence': conf_5m},
            'bias_15m': {'bias': bias_15m.value, 'confidence': conf_15m},
            'indicators': {
                'close': float(data_5m_local['Close'].iloc[-1]) if pd.notna(data_5m_local['Close'].iloc[-1]) else 0.0,
                'vwap': float(indicators_5m['VWAP'].iloc[-1]) if pd.notna(indicators_5m['VWAP'].iloc[-1]) else 0.0,
            },
            'gamma_score': gamma_score,
            'walls': walls[:5],
            'signals': [{'timestamp': s['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 'price': s['price'], 'type': s['type'], 'strength': s['strength']} for s in signals[-10:]],
            'market_status': market_status,
            'latest': {
                '5m': pd.Timestamp(data_5m_local.index[-1]).strftime('%Y-%m-%d %H:%M:%S'),
                '15m': pd.Timestamp(data_15m_local.index[-1]).strftime('%Y-%m-%d %H:%M:%S')
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        with _cache_lock:
            _cached_payload = payload
            _cached_at = time.time()

    except Exception:
        # Don't raise cache thread errors - leave cache as-is
        pass
    finally:
        _is_building = False

def create_chart(copilot_data, data_15m, indicators_15m):
    """Create interactive Plotly charts with all indicators and signals"""
    
    # Extract 5m data
    data_5m = copilot_data['data_5m']
    indicators_5m = copilot_data['indicators_5m']
    bias_5m = copilot_data['bias_5m']
    bias_15m = copilot_data['bias_15m']
    
    # Calculate current price
    current_price = data_5m['Close'].iloc[-1]
    
    # Calculate price ranges for proper y-axis scaling
    price_5m_min = data_5m['Low'].min()
    price_5m_max = data_5m['High'].max()
    price_5m_range = price_5m_max - price_5m_min
    price_5m_padding = price_5m_range * 0.05  # 5% padding
    
    price_15m_min = data_15m['Low'].min()
    price_15m_max = data_15m['High'].max()
    price_15m_range = price_15m_max - price_15m_min
    price_15m_padding = price_15m_range * 0.05
    
    # Get options walls
    wall_analyzer = OptionsWallAnalyzer()
    walls = wall_analyzer.get_options_walls(current_price)
    
    # Get sentiment signals
    sentiment_analyzer = SentimentAnalyzer()
    signals = sentiment_analyzer.analyze_sentiment(data_5m, indicators_5m, bias_5m, bias_15m)
    
    # Create figure with 2 charts (5m and 15m) and volume subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12,
        row_heights=[0.33, 0.14, 0.33, 0.14],
        subplot_titles=('SPY 5-Minute Chart', '5m Volume', 'SPY 15-Minute Chart', '15m Volume')
    )
    
    # ===== 5-MINUTE CHART =====
    # Candlestick chart
    # Prepare per-candle extra data for hover (VWAP, EMA9, EMA21, Volume)
    try:
        custom_5m = list(zip(
            indicators_5m['VWAP'].tolist(),
            indicators_5m['EMA_fast'].tolist(),
            indicators_5m['EMA_slow'].tolist(),
            data_5m['Volume'].tolist()
        ))
    except Exception:
        custom_5m = [[None, None, None, None] for _ in range(len(data_5m))]

    fig.add_trace(
        go.Candlestick(
            x=data_5m.index,
            open=data_5m['Open'],
            high=data_5m['High'],
            low=data_5m['Low'],
            close=data_5m['Close'],
            name='SPY 5m',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350',
            increasing_fillcolor='#26a69a',
            decreasing_fillcolor='#ef5350',
            customdata=custom_5m,
            hovertemplate=(
                'Time: %{x}<br>'
                'Open: $%{open:.2f}<br>'
                'High: $%{high:.2f}<br>'
                'Low: $%{low:.2f}<br>'
                'Close: $%{close:.2f}<br><br>'
                'VWAP: $%{customdata[0]:.2f}<br>'
                'EMA9: $%{customdata[1]:.2f}<br>'
                'EMA21: $%{customdata[2]:.2f}<br>'
                'Volume: %{customdata[3]:,}<extra></extra>'
            ),
            showlegend=True,
            visible=True
        ),
        row=1, col=1
    )
    
    # VWAP
    fig.add_trace(
        go.Scatter(
            x=data_5m.index,
            y=indicators_5m['VWAP'],
            name='VWAP (5m)',
            line=dict(color='purple', width=2, dash='dot'),
            hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # EMA 9
    fig.add_trace(
        go.Scatter(
            x=data_5m.index,
            y=indicators_5m['EMA_fast'],
            name='EMA 9 (5m)',
            line=dict(color='#2196F3', width=1.5),
            hovertemplate='EMA 9: $%{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # EMA 21
    fig.add_trace(
        go.Scatter(
            x=data_5m.index,
            y=indicators_5m['EMA_slow'],
            name='EMA 21 (5m)',
            line=dict(color='#FF9800', width=1.5),
            hovertemplate='EMA 21: $%{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Options Walls on 5m chart
    for wall in walls[:5]:  # Top 5 walls
        color = '#FF5252' if wall['type'] == 'resistance' else '#4CAF50'
        fig.add_hline(
            y=wall['strike'],
            line=dict(color=color, width=2, dash='dash'),
            opacity=min(1.0, wall['strength'] / 100),
            annotation_text=f"${wall['strike']} ({wall['type'][:3].upper()})",
            annotation_position="right",
            row=1, col=1
        )
    
    # Buy/Sell Signals on 5m chart
    buy_signals = [s for s in signals if s['type'] == 'buy']
    sell_signals = [s for s in signals if s['type'] == 'sell']
    
    if buy_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['timestamp'] for s in buy_signals],
                y=[s['price'] for s in buy_signals],
                mode='markers+text',
                name='BUY Signal',
                marker=dict(
                    symbol='triangle-up',
                    size=15,
                    color='#00E676',
                    line=dict(color='#00C853', width=2)
                ),
                text=[s['label'] for s in buy_signals],
                textposition='top center',
                textfont=dict(size=9, color='#00E676'),
                hovertemplate='BUY: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    if sell_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['timestamp'] for s in sell_signals],
                y=[s['price'] for s in sell_signals],
                mode='markers+text',
                name='SELL Signal',
                marker=dict(
                    symbol='triangle-down',
                    size=15,
                    color='#FF1744',
                    line=dict(color='#D50000', width=2)
                ),
                text=[s['label'] for s in sell_signals],
                textposition='bottom center',
                textfont=dict(size=9, color='#FF1744'),
                hovertemplate='SELL: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 5m Volume bars
    colors_5m = ['#26a69a' if close >= open else '#ef5350' 
                 for close, open in zip(data_5m['Close'], data_5m['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data_5m.index,
            y=data_5m['Volume'],
            name='Volume (5m)',
            marker_color=colors_5m,
            showlegend=False,
            hovertemplate='Volume: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # ===== 15-MINUTE CHART =====
    # Candlestick chart
    try:
        custom_15m = list(zip(
            indicators_15m['VWAP'].tolist(),
            indicators_15m['EMA_fast'].tolist(),
            indicators_15m['EMA_slow'].tolist(),
            data_15m['Volume'].tolist()
        ))
    except Exception:
        custom_15m = [[None, None, None, None] for _ in range(len(data_15m))]

    fig.add_trace(
        go.Candlestick(
            x=data_15m.index,
            open=data_15m['Open'],
            high=data_15m['High'],
            low=data_15m['Low'],
            close=data_15m['Close'],
            name='SPY 15m',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350',
            increasing_fillcolor='#26a69a',
            decreasing_fillcolor='#ef5350',
            customdata=custom_15m,
            hovertemplate=(
                'Time: %{x}<br>'
                'Open: $%{open:.2f}<br>'
                'High: $%{high:.2f}<br>'
                'Low: $%{low:.2f}<br>'
                'Close: $%{close:.2f}<br><br>'
                'VWAP: $%{customdata[0]:.2f}<br>'
                'EMA9: $%{customdata[1]:.2f}<br>'
                'EMA21: $%{customdata[2]:.2f}<br>'
                'Volume: %{customdata[3]:,}<extra></extra>'
            ),
            showlegend=True,
            visible=True
        ),
        row=3, col=1
    )
    
    # VWAP
    fig.add_trace(
        go.Scatter(
            x=data_15m.index,
            y=indicators_15m['VWAP'],
            name='VWAP (15m)',
            line=dict(color='purple', width=2, dash='dot'),
            hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # EMA 9
    fig.add_trace(
        go.Scatter(
            x=data_15m.index,
            y=indicators_15m['EMA_fast'],
            name='EMA 9 (15m)',
            line=dict(color='#2196F3', width=1.5),
            hovertemplate='EMA 9: $%{y:.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # EMA 21
    fig.add_trace(
        go.Scatter(
            x=data_15m.index,
            y=indicators_15m['EMA_slow'],
            name='EMA 21 (15m)',
            line=dict(color='#FF9800', width=1.5),
            hovertemplate='EMA 21: $%{y:.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Options Walls on 15m chart
    for wall in walls[:5]:  # Top 5 walls
        color = '#FF5252' if wall['type'] == 'resistance' else '#4CAF50'
        fig.add_hline(
            y=wall['strike'],
            line=dict(color=color, width=2, dash='dash'),
            opacity=min(1.0, wall['strength'] / 100),
            annotation_text=f"${wall['strike']}",
            annotation_position="right",
            row=3, col=1
        )
    
    # 15m Volume bars
    colors_15m = ['#26a69a' if close >= open else '#ef5350' 
                  for close, open in zip(data_15m['Close'], data_15m['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data_15m.index,
            y=data_15m['Volume'],
            name='Volume (15m)',
            marker_color=colors_15m,
            showlegend=False,
            hovertemplate='Volume: %{y:,.0f}<extra></extra>'
        ),
        row=4, col=1
    )
    
    # Update layout with proper config for interactivity
    fig.update_layout(
        title=f'Market Copilot - SPY Analysis | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        xaxis_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        width=None,
        height=1400,
        template='plotly_dark',
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        dragmode='zoom',
        margin=dict(l=60, r=30, t=80, b=40),
        autosize=True
    )
    
    # Update axes with proper ranges
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=4, col=1)
    
    # Set y-axis ranges for price charts
    fig.update_yaxes(
        title_text="Price ($)", 
        row=1, col=1, 
        fixedrange=False,
        range=[price_5m_min - price_5m_padding, price_5m_max + price_5m_padding]
    )
    fig.update_yaxes(title_text="Volume", row=2, col=1, fixedrange=False)
    fig.update_yaxes(
        title_text="Price ($)", 
        row=3, col=1, 
        fixedrange=False,
        range=[price_15m_min - price_15m_padding, price_15m_max + price_15m_padding]
    )
    fig.update_yaxes(title_text="Volume", row=4, col=1, fixedrange=False)
    
    # Add horizontal separator line between 5m and 15m sections
    fig.add_shape(
        type="line",
        x0=0, x1=1, xref="paper",
        y0=0.47, y1=0.47, yref="paper",
        line=dict(color="rgba(255, 255, 255, 0.3)", width=3, dash="solid")
    )
    
    return fig, walls, signals

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test endpoint to verify data fetching works"""
    import yfinance as yf
    spy = yf.Ticker("SPY")
    data = spy.history(period="5d", interval="5m")
    return f"Data fetched: {len(data)} candles. Latest close: ${data['Close'].iloc[-1]:.2f} at {data.index[-1]}"

@app.route('/api/analysis')
def get_analysis():
    """API endpoint to get current market analysis"""
    try:
        # Run Market Copilot analysis
        copilot = MarketCopilot()
        
        # Get data with longer periods to ensure we have data even when market is closed
        data_5m = copilot.data_fetcher.fetch_data("5m", "5d")  # Last 5 days
        time.sleep(REQUEST_DELAY)
        data_15m = copilot.data_fetcher.fetch_data("15m", "1mo")  # Last month
        
        if data_5m.empty or data_15m.empty:
            return jsonify({'error': 'Failed to fetch market data - market may be closed'}), 500
        
        # Take only last 78 periods for 5m (1 day of trading) and last 100 for 15m
        data_5m = data_5m.tail(78)
        data_15m = data_15m.tail(100)
        
        print(f"✓ 5m data: {len(data_5m)} candles, Latest: ${data_5m['Close'].iloc[-1]:.2f}")
        print(f"✓ 15m data: {len(data_15m)} candles, Latest: ${data_15m['Close'].iloc[-1]:.2f}")
        
        # Calculate indicators
        indicators_5m = calculate_all_indicators(data_5m, INDICATORS)
        indicators_15m = calculate_all_indicators(data_15m, INDICATORS)
        
        # Get bias (classify_bias takes a single Series with all indicators)
        bias_5m, conf_5m, notes_5m = copilot.bias_classifier.classify_bias(indicators_5m.iloc[-1])
        bias_15m, conf_15m, notes_15m = copilot.bias_classifier.classify_bias(indicators_15m.iloc[-1])
        
        # Prepare data for chart
        copilot_data = {
            'data_5m': data_5m,
            'indicators_5m': indicators_5m,
            'bias_5m': bias_5m.value,
            'bias_15m': bias_15m.value
        }
        
        # Create chart
        fig, walls, signals = create_chart(copilot_data, data_15m, indicators_15m)
        
        # Debug: Check what traces are in the figure
        print(f"Chart has {len(fig.data)} traces")
        for i, trace in enumerate(fig.data):
            print(f"  Trace {i}: {trace.type} - {trace.name}")
        
        # Calculate gamma squeeze indicator
        current_volume = data_5m['Volume'].iloc[-1]
        avg_volume = data_5m['Volume'].rolling(20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        current_atr = indicators_5m['ATR'].iloc[-1]
        avg_atr = indicators_5m['ATR'].rolling(20).mean().iloc[-1]
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
        
        price_change = ((data_5m['Close'].iloc[-1] - data_5m['Close'].iloc[-5]) / 
                       data_5m['Close'].iloc[-5] * 100) if len(data_5m) >= 5 else 0
        
        gamma_score = min(100, int((volume_ratio * 30 + volatility_ratio * 30 + abs(price_change) * 10)))
        
        # Prepare response
        response = {
            'chart': fig.to_json(),
            'bias_5m': {
                'bias': bias_5m.value,
                'confidence': conf_5m,
                'label': copilot.bias_classifier.get_bias_strength_label(conf_5m)
            },
            'bias_15m': {
                'bias': bias_15m.value,
                'confidence': conf_15m,
                'label': copilot.bias_classifier.get_bias_strength_label(conf_15m)
            },
            'indicators': {
                'close': float(data_5m['Close'].iloc[-1]) if pd.notna(data_5m['Close'].iloc[-1]) else 0.0,
                'vwap': float(indicators_5m['VWAP'].iloc[-1]) if pd.notna(indicators_5m['VWAP'].iloc[-1]) else 0.0,
                'ema_9': float(indicators_5m['EMA_fast'].iloc[-1]) if pd.notna(indicators_5m['EMA_fast'].iloc[-1]) else 0.0,
                'ema_21': float(indicators_5m['EMA_slow'].iloc[-1]) if pd.notna(indicators_5m['EMA_slow'].iloc[-1]) else 0.0,
                'rsi': float(indicators_5m['RSI'].iloc[-1]) if pd.notna(indicators_5m['RSI'].iloc[-1]) else 50.0,
                'atr': float(indicators_5m['ATR'].iloc[-1]) if pd.notna(indicators_5m['ATR'].iloc[-1]) else 0.0
            },
            'gamma_score': gamma_score,
            'walls': walls[:5],  # Top 5 walls
            'signals': [{'timestamp': s['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 
                        'price': s['price'], 
                        'type': s['type'],
                        'strength': s['strength']} for s in signals[-10:]],  # Last 10 signals
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # Attach market status and latest candle timestamps for client-side freshness control
        try:
            from market_hours import MarketHours
            market_status = MarketHours.get_market_status()
            latest_5m = data_5m.index[-1]
            latest_15m = data_15m.index[-1]
            response['market_status'] = market_status
            response['latest'] = {
                '5m': pd.Timestamp(latest_5m).strftime('%Y-%m-%d %H:%M:%S'),
                '15m': pd.Timestamp(latest_15m).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception:
            response['market_status'] = {'status': 'Unknown', 'is_open': False}
            response['latest'] = {'5m': None, '15m': None}
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os

    # Determine port from env vars or command-line before printing
    port = int(os.environ.get('FLASK_RUN_PORT') or os.environ.get('FLASK_PORT') or 5000)
    for arg in sys.argv[1:]:
        if arg.startswith('--port=') or arg.startswith('-p='):
            try:
                port = int(arg.split('=', 1)[1])
            except Exception:
                pass

    print("=" * 80)
    print("  MARKET COPILOT - Web Interface")
    print("  Starting Flask server...")
    print("=" * 80)
    print(f"\n📊 Access the dashboard at: http://localhost:{port}")
    print("🔄 Auto-refreshes every 2 seconds")
    print("⚡ Features: Live charts, Options walls, Buy/Sell signals, Gamma indicators")
    print("\nPress Ctrl+C to stop\n")

    # Start background cache refresher
    try:
        refresher = threading.Thread(target=periodic_refresh, daemon=True)
        refresher.start()
    except Exception:
        pass

    app.run(debug=True, host='0.0.0.0', port=port)
