"""
Flask Web Interface for Market Copilot
Provides interactive charts with:
- Candlestick charts with VWAP, EMA9, EMA21 overlays
- Gamma squeeze indicators
- Options walls (support/resistance levels)
- Sentiment-based buy/sell signals (green/red triangles)
"""

from flask import Flask, render_template, jsonify
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

app = Flask(__name__)

class OptionsWallAnalyzer:
    """Analyzes options data to find support/resistance walls"""
    
    def __init__(self, ticker="SPY"):
        self.ticker = ticker
        
    def get_options_walls(self, current_price):
        """
        Calculate likely options walls based on round numbers and volume
        In production, this would use real options chain data
        """
        # Generate likely strike levels (round numbers near current price)
        strikes = []
        base = int(current_price / 5) * 5  # Round to nearest $5
        
        # Create strikes around current price
        for i in range(-4, 5):
            strikes.append(base + (i * 5))
        
        # Simulate wall strength (in production, use actual open interest)
        walls = []
        for strike in strikes:
            distance = abs(strike - current_price)
            # Stronger walls at round numbers and closer to price
            strength = max(0, 100 - distance * 10) * (1 + (strike % 10 == 0) * 0.5)
            
            if strength > 30:
                walls.append({
                    'strike': strike,
                    'strength': strength,
                    'type': 'resistance' if strike > current_price else 'support'
                })
        
        return sorted(walls, key=lambda x: x['strength'], reverse=True)

class SentimentAnalyzer:
    """Analyzes market sentiment to generate buy/sell signals"""
    
    def __init__(self):
        self.signals = []
        
    def analyze_sentiment(self, data_5m, indicators_5m, bias_5m, bias_15m):
        """
        Generate buy/sell signals based on multi-factor analysis
        Returns list of signal points to display on chart
        """
        signals = []
        
        if len(data_5m) < 10:
            return signals
        
        # Get recent candles
        recent_data = data_5m.tail(20)
        
        for idx in range(5, len(recent_data)):
            timestamp = recent_data.index[idx]
            price = recent_data['Close'].iloc[idx]
            
            # Calculate signal strength based on multiple factors
            signal_score = 0
            
            # Factor 1: Bias alignment
            if bias_5m == bias_15m and bias_5m != 'Neutral':
                signal_score += 30
            
            # Factor 2: Price vs VWAP
            vwap = indicators_5m['VWAP'].iloc[idx] if idx < len(indicators_5m['VWAP']) else None
            if vwap:
                if price > vwap and bias_5m == 'Bullish':
                    signal_score += 20
                elif price < vwap and bias_5m == 'Bearish':
                    signal_score += 20
            
            # Factor 3: EMA crossover
            ema9 = indicators_5m['EMA_fast'].iloc[idx] if idx < len(indicators_5m['EMA_fast']) else None
            ema21 = indicators_5m['EMA_slow'].iloc[idx] if idx < len(indicators_5m['EMA_slow']) else None
            
            if ema9 and ema21:
                prev_ema9 = indicators_5m['EMA_fast'].iloc[idx-1]
                prev_ema21 = indicators_5m['EMA_slow'].iloc[idx-1]
                
                # Bullish crossover
                if prev_ema9 <= prev_ema21 and ema9 > ema21:
                    signal_score += 50
                # Bearish crossover
                elif prev_ema9 >= prev_ema21 and ema9 < ema21:
                    signal_score -= 50
            
            # Factor 4: RSI extremes
            rsi = indicators_5m['RSI'].iloc[idx] if idx < len(indicators_5m['RSI']) else None
            if rsi:
                if rsi < 30 and bias_5m == 'Bullish':  # Oversold + bullish
                    signal_score += 25
                elif rsi > 70 and bias_5m == 'Bearish':  # Overbought + bearish
                    signal_score -= 25
            
            # Generate signal if score is strong enough
            if signal_score >= 60:
                signals.append({
                    'timestamp': timestamp,
                    'price': price,
                    'type': 'buy',
                    'strength': min(100, signal_score),
                    'label': f'BUY {signal_score}%'
                })
            elif signal_score <= -60:
                signals.append({
                    'timestamp': timestamp,
                    'price': price,
                    'type': 'sell',
                    'strength': min(100, abs(signal_score)),
                    'label': f'SELL {abs(signal_score)}%'
                })
        
        return signals

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
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("  MARKET COPILOT - Web Interface")
    print("  Starting Flask server...")
    print("=" * 80)
    print("\n📊 Access the dashboard at: http://localhost:5000")
    print("🔄 Auto-refreshes every 2 seconds")
    print("⚡ Features: Live charts, Options walls, Buy/Sell signals, Gamma indicators")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
