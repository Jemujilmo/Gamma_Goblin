"""Flask Web Interface for Market Copilot
Provides interactive charts with:
- Candlestick charts with VWAP, EMA9, EMA21 overlays
- Gamma indicators
- Options walls (support/resistance levels)
- Sentiment-based buy/sell signals

This module builds three independent Plotly figures (1m / 5m / 15m),
serializes them for client-side Plotly.js rendering, and exposes a small
JSON API used by the dashboard front-end.
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
import sys
from datetime import datetime

import pandas as pd

from market_copilot import MarketCopilot
from ticker_list import get_ticker_list
from indicators import calculate_all_indicators
from config import REQUEST_DELAY, INDICATORS
from analyzers import OptionsWallAnalyzer, SentimentAnalyzer
from options_data import OptionsDataFetcher
from plotly.subplots import make_subplots
import plotly.graph_objects as go

app = Flask(__name__)

# Lightweight cache for API payloads
_cache_lock = threading.Lock()
_cached_payload = None
_cached_at = 0
_is_building = False
CACHE_TTL = 5  # seconds


def _serializable_value(v):
    try:
        if isinstance(v, pd.Timestamp):
            return v.strftime('%Y-%m-%dT%H:%M:%S%z')
    except Exception:
        pass
    try:
        from datetime import datetime as _dt
        if isinstance(v, _dt):
            return v.strftime('%Y-%m-%dT%H:%M:%S%z')
    except Exception:
        pass
    try:
        import numpy as _np
        if isinstance(v, (_np.generic,)):
            return v.item()
    except Exception:
        pass
    return v


def _serialize_fig(fig):
    if fig is None:
        return None
    chart_data = []
    for t in fig.data:
        td = t.to_plotly_json()
        for k in ('x', 'y', 'open', 'high', 'low', 'close', 'customdata'):
            if k in td and td[k] is not None:
                try:
                    arr = list(td[k])
                    arr = [
                        [_serializable_value(v2) for v2 in v]
                        if isinstance(v, (list, tuple))
                        else _serializable_value(v)
                        for v in arr
                    ]
                    td[k] = arr
                except Exception:
                    pass
        chart_data.append(td)
    chart_layout = fig.layout.to_plotly_json() if hasattr(fig.layout, 'to_plotly_json') else dict(fig.layout)
    return {'data': chart_data, 'layout': chart_layout}


def _build_price_volume_figure(data, indicators, title, timeframe_label, ticker='SPY', signals=None):
    """Build a two-row (price + volume) Plotly figure for one timeframe.

    Uses ATR and a small baseline to compute a display window so SPY's
    typically-small intraday moves remain visible.
    
    Args:
        ticker: Stock ticker symbol (used in candlestick trace name)
        signals: List of signal dicts with 'timestamp', 'type', 'price', 'strength'
    """
    if data is None or data.empty:
        return None

    price_min = float(data['Low'].min())
    price_max = float(data['High'].max())
    last_close = float(data['Close'].iloc[-1])
    data_range = price_max - price_min if price_max > price_min else 0.0

    atr = None
    try:
        atr = float(indicators['ATR'].iloc[-1]) if 'ATR' in indicators else None
    except Exception:
        atr = None

    # baseline choices tuned for SPY intraday moves
    if timeframe_label == '1m':
        base = 0.8
    elif timeframe_label == '5m':
        base = 2.5
    else:
        base = 4.0

    if atr and atr > 0:
        display_range = max(data_range, atr * 6, base)
    else:
        display_range = max(data_range, base)

    half = display_range / 2.0
    y0 = last_close - half
    y1 = last_close + half

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        row_heights=[0.80, 0.20], subplot_titles=(title, f'{timeframe_label} Volume'))

    # Format times for hover as 12-hour with AM/PM
    try:
        formatted_times = [dt.strftime('%b %d, %Y, %I:%M %p') if hasattr(dt, 'strftime') else str(dt) for dt in data.index]
    except Exception:
        formatted_times = [str(dt) for dt in data.index]

    try:
        custom = list(zip(
            indicators.get('VWAP', [None] * len(data)),
            indicators.get('EMA_fast', [None] * len(data)),
            indicators.get('EMA_slow', [None] * len(data)),
            data['Volume'].tolist(),
        ))
    except Exception:
        custom = [[None, None, None, None] for _ in range(len(data))]

    fig.add_trace(go.Candlestick(
        x=data.index, 
        open=data['Open'], 
        high=data['High'], 
        low=data['Low'], 
        close=data['Close'],
        name=f'{ticker} {timeframe_label}',
        text=formatted_times,
        customdata=custom,
        hovertemplate='<b>%{text}</b><br>' +
                      'Open: $%{open:.2f}<br>' +
                      'High: $%{high:.2f}<br>' +
                      'Low: $%{low:.2f}<br>' +
                      'Close: $%{close:.2f}<extra></extra>'
    ), row=1, col=1)

    if 'VWAP' in indicators:
        fig.add_trace(go.Scatter(x=data.index, y=indicators['VWAP'], name=f'VWAP ({timeframe_label})',
                                  line=dict(color='purple', width=2, dash='dot')), row=1, col=1)
    if 'EMA_fast' in indicators:
        fig.add_trace(go.Scatter(x=data.index, y=indicators['EMA_fast'], name=f'EMA 9 ({timeframe_label})',
                                  line=dict(color='#2196F3', width=1.5)), row=1, col=1)
    if 'EMA_slow' in indicators:
        fig.add_trace(go.Scatter(x=data.index, y=indicators['EMA_slow'], name=f'EMA 21 ({timeframe_label})',
                                  line=dict(color='#FF9800', width=1.5)), row=1, col=1)

    colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=colors, showlegend=False), row=2, col=1)

    # Add buy/sell signals as markers
    if signals:
        buy_signals = [s for s in signals if s['type'] == 'buy']
        sell_signals = [s for s in signals if s['type'] == 'sell']
        
        if buy_signals:
            buy_times = [s['timestamp'] for s in buy_signals]
            buy_prices = [s['price'] for s in buy_signals]
            buy_strength = [s.get('strength', 50) for s in buy_signals]
            
            fig.add_trace(go.Scatter(
                x=buy_times,
                y=buy_prices,
                mode='markers',
                name='Buy Signal',
                marker=dict(
                    symbol='triangle-up',
                    size=14,
                    color='#00E676',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>BUY</b><br>Price: $%{y:.2f}<br>Time: %{x}<extra></extra>',
                showlegend=True
            ), row=1, col=1)
        
        if sell_signals:
            sell_times = [s['timestamp'] for s in sell_signals]
            sell_prices = [s['price'] for s in sell_signals]
            sell_strength = [s.get('strength', 50) for s in sell_signals]
            
            fig.add_trace(go.Scatter(
                x=sell_times,
                y=sell_prices,
                mode='markers',
                name='Sell Signal',
                marker=dict(
                    symbol='triangle-down',
                    size=14,
                    color='#FF1744',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>SELL</b><br>Price: $%{y:.2f}<br>Time: %{x}<extra></extra>',
                showlegend=True
            ), row=1, col=1)

    fig.update_layout(template='plotly_dark', hovermode='closest', showlegend=True,
                      margin=dict(l=60, r=30, t=40, b=40), autosize=True, height=700)
    fig.update_yaxes(range=[y0, y1], row=1, col=1, title_text='Price ($)')
    fig.update_yaxes(title_text='Volume', row=2, col=1)
    fig.update_xaxes(title_text='Time', row=2, col=1, tickformat='%I:%M %p')

    return fig


def create_chart(copilot_data, data_15m, indicators_15m, ticker="SPY", data_1m=None, indicators_1m=None):
    data_5m = copilot_data['data_5m']
    indicators_5m = copilot_data['indicators_5m']
    bias_5m = copilot_data.get('bias_5m')
    bias_15m = copilot_data.get('bias_15m')

    current_price = float(data_5m['Close'].iloc[-1])
    
    # Try real options data first, fallback to synthetic
    try:
        options_fetcher = OptionsDataFetcher(ticker)
        walls = options_fetcher.get_options_walls(current_price)
        iv_metrics = options_fetcher.get_iv_metrics()
        pcr = options_fetcher.get_put_call_ratio()
        gex = options_fetcher.get_gamma_exposure(current_price)
    except Exception as e:
        # Fallback to synthetic data
        print(f"Options data error: {e}, using fallback")
        walls = OptionsWallAnalyzer().get_options_walls(current_price)
        iv_metrics = None
        pcr = None
        gex = None
    
    signals = SentimentAnalyzer().analyze_sentiment(data_5m, indicators_5m, bias_5m, bias_15m)

    fig_1m = None
    if data_1m is not None and indicators_1m is not None:
        fig_1m = _build_price_volume_figure(data_1m, indicators_1m, f'{ticker} 1-Minute Chart', '1m', ticker, signals)

    fig_5m = _build_price_volume_figure(data_5m, indicators_5m, f'{ticker} 5-Minute Chart', '5m', ticker, signals)
    fig_15m = _build_price_volume_figure(data_15m, indicators_15m, f'{ticker} 15-Minute Chart', '15m', ticker, signals)

    return {'1m': fig_1m, '5m': fig_5m, '15m': fig_15m}, walls, signals, iv_metrics, pcr, gex


def build_and_cache_payload(ticker="SPY"):
    global _cached_payload, _cached_at, _is_building
    if _is_building:
        return
    _is_building = True
    try:
        copilot = MarketCopilot(ticker=ticker)
        data_5m = copilot.data_fetcher.fetch_data('5m', '5d')
        time.sleep(REQUEST_DELAY)
        data_15m = copilot.data_fetcher.fetch_data('15m', '1mo')

        if data_5m is None or data_15m is None or data_5m.empty or data_15m.empty:
            return

        data_5m = data_5m.tail(78)
        data_15m = data_15m.tail(100)

        indicators_5m = calculate_all_indicators(data_5m, INDICATORS)
        indicators_15m = calculate_all_indicators(data_15m, INDICATORS)

        bias_5m, conf_5m, _ = copilot.bias_classifier.classify_bias(indicators_5m.iloc[-1])
        bias_15m, conf_15m, _ = copilot.bias_classifier.classify_bias(indicators_15m.iloc[-1])

        copilot_data = {'data_5m': data_5m, 'indicators_5m': indicators_5m, 'bias_5m': bias_5m.value, 'bias_15m': bias_15m.value}

        # optional 1m
        data_1m = None
        indicators_1m = None
        try:
            data_1m = copilot.data_fetcher.fetch_data('1m', '1d')
            time.sleep(REQUEST_DELAY)
            if data_1m is not None and not data_1m.empty:
                data_1m = data_1m.tail(240)
                indicators_1m = calculate_all_indicators(data_1m, INDICATORS)
        except Exception:
            data_1m = None
            indicators_1m = None

        figs, walls, signals, iv_metrics, pcr, gex = create_chart(copilot_data, data_15m, indicators_15m, ticker=ticker, data_1m=data_1m, indicators_1m=indicators_1m)

        # Provide a small indicators summary for the frontend which expects
        # data.indicators.close and data.indicators.rsi (and a gamma_score).
        try:
            current_price = float(data_5m['Close'].iloc[-1])
        except Exception:
            current_price = None

        try:
            rsi_val = float(indicators_5m['RSI'].iloc[-1]) if 'RSI' in indicators_5m else None
        except Exception:
            rsi_val = None

        # Compute a compact gamma_score similar to chart_view.py so the UI can display a gauge
        try:
            recent_volume = data_5m['Volume'].iloc[-5:].mean()
            avg_volume = data_5m['Volume'].mean()
            volume_ratio = (recent_volume / avg_volume) if avg_volume and avg_volume > 0 else 1.0
        except Exception:
            volume_ratio = 1.0

        try:
            if 'ATR' in indicators_5m:
                current_atr = float(indicators_5m['ATR'].iloc[-1])
                avg_atr = float(indicators_5m['ATR'].mean())
                volatility_ratio = (current_atr / avg_atr) if avg_atr and avg_atr > 0 else 1.0
            else:
                volatility_ratio = 1.0
        except Exception:
            volatility_ratio = 1.0

        try:
            price_change_5m = ((data_5m['Close'].iloc[-1] / data_5m['Close'].iloc[-5]) - 1) * 100 if len(data_5m) >= 5 else 0
        except Exception:
            price_change_5m = 0

        try:
            gamma_score = min(100, int((volume_ratio * 30 + volatility_ratio * 30 + abs(price_change_5m) * 10)))
        except Exception:
            gamma_score = 0

        payload = {
            'chart_1m': _serialize_fig(figs.get('1m')) if figs.get('1m') is not None else None,
            'chart_5m': _serialize_fig(figs.get('5m')),
            'chart_15m': _serialize_fig(figs.get('15m')),
            'bias_5m': {'bias': bias_5m.value, 'confidence': conf_5m},
            'bias_15m': {'bias': bias_15m.value, 'confidence': conf_15m},
            'walls': walls[:5],
            'signals': [{'timestamp': s['timestamp'].strftime('%Y-%m-%d %I:%M:%S %p'), 'price': s['price'], 'type': s['type'], 'strength': s['strength']} for s in signals[-10:]],
            'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'indicators': {
                'close': current_price,
                'rsi': rsi_val,
            },
            'gamma_score': gamma_score,
            'iv_metrics': iv_metrics,
            'put_call_ratio': pcr,
            'gamma_exposure': gex,
        }

        with _cache_lock:
            _cached_payload = payload
            _cached_at = time.time()

    finally:
        _is_building = False


def periodic_refresh():
    while True:
        try:
            build_and_cache_payload()
        except Exception:
            pass
        time.sleep(CACHE_TTL)


@app.route('/')
def index():
    """Main dashboard with multi-timeframe charts (1m/5m/15m)"""
    return render_template('index.html')


@app.route('/indicator')
def indicator():
    """Simplified single-chart indicator view with persistent zoom"""
    return render_template('indicator.html')


@app.route('/api/tickers')
def get_tickers():
    """Return list of available tickers for dropdown"""
    tickers = get_ticker_list()
    return jsonify({'tickers': [{'symbol': s, 'name': n} for s, n in tickers]})


@app.route('/api/analysis/debug')
def get_analysis_debug():
    try:
        copilot = MarketCopilot()
        data_5m = copilot.data_fetcher.fetch_data('5m', '5d')
        time.sleep(REQUEST_DELAY)
        if data_5m is None or data_5m.empty:
            return jsonify({'error': 'No 5m data available'}), 500

        data_5m = data_5m.tail(78)
        indicators_5m = calculate_all_indicators(data_5m, INDICATORS)

        N = 10
        rows = []
        start = max(0, len(data_5m) - N)
        for i in range(start, len(data_5m)):
            ts = data_5m.index[i]
            rows.append({
                'timestamp': pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(data_5m['Open'].iloc[i]),
                'high': float(data_5m['High'].iloc[i]),
                'low': float(data_5m['Low'].iloc[i]),
                'close': float(data_5m['Close'].iloc[i]),
                'vwap': float(indicators_5m['VWAP'].iloc[i]) if 'VWAP' in indicators_5m else None,
                'ema9': float(indicators_5m['EMA_fast'].iloc[i]) if 'EMA_fast' in indicators_5m else None,
                'ema21': float(indicators_5m['EMA_slow'].iloc[i]) if 'EMA_slow' in indicators_5m else None,
                'volume': int(data_5m['Volume'].iloc[i])
            })

        return jsonify({'sample': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis')
def get_analysis():
    try:
        # Get ticker from query parameter (default to SPY)
        ticker = request.args.get('ticker', 'SPY').upper()
        
        # If cache is fresh for this ticker, return it
        cache_key = f"{ticker}_cached_payload"
        with _cache_lock:
            if cache_key in globals() and (time.time() - _cached_at) < CACHE_TTL:
                return jsonify(globals()[cache_key])

        # Build on-demand if cache empty or stale
        # Trigger a build; if another thread is already building, wait a short
        # time for it to finish to avoid returning an empty response.
        build_and_cache_payload(ticker)

        # small wait loop to allow background builder to populate cache (race
        # between request and background thread). Wait up to 5 seconds.
        wait_start = time.time()
        while True:
            with _cache_lock:
                if _cached_payload:
                    break
            if time.time() - wait_start > 5:
                break
            time.sleep(0.2)

        with _cache_lock:
            if _cached_payload:
                resp = dict(_cached_payload)
            else:
                # Return a safe, minimal payload to avoid 500s on first-hit
                # (frontend will still show loading/placeholder values).
                resp = {
                    'chart_1m': None,
                    'chart_5m': None,
                    'chart_15m': None,
                    'bias_5m': {'bias': 'Unknown', 'confidence': 0.0},
                    'bias_15m': {'bias': 'Unknown', 'confidence': 0.0},
                    'walls': [],
                    'signals': [],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
                    'indicators': {'close': None, 'rsi': None},
                    'gamma_score': 0,
                }

        # Enrich with market status / latest timestamps
        try:
            from market_hours import MarketHours
            resp['market_status'] = MarketHours.get_market_status()
        except Exception:
            resp['market_status'] = {'status': 'Unknown', 'is_open': False}

        return jsonify(resp)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os

    port = int(os.environ.get('FLASK_RUN_PORT') or os.environ.get('FLASK_PORT') or 5000)
    for arg in sys.argv[1:]:
        if arg.startswith('--port=') or arg.startswith('-p='):
            try:
                port = int(arg.split('=', 1)[1])
            except Exception:
                pass

    print('=' * 80)
    print('  MARKET COPILOT - Web Interface')
    print('  Starting Flask server...')
    print('=' * 80)
    print(f"\n📊 Access the dashboard at: http://localhost:{port}")

    try:
        refresher = threading.Thread(target=periodic_refresh, daemon=True)
        refresher.start()
    except Exception:
        pass

    app.run(debug=True, host='0.0.0.0', port=port)
