"""
Simple Flask Web Interface - Guaranteed Working Version
"""
from flask import Flask, render_template_string
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SPY Live Chart</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { 
            margin: 0; 
            padding: 20px; 
            background: #1e1e1e; 
            color: white; 
            font-family: Arial;
        }
        #chart { width: 100%; height: 90vh; }
        .header { text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 SPY Live Chart</h1>
        <p id="status">Loading...</p>
    </div>
    <div id="chart"></div>
    <script>
        async function loadChart() {
            try {
                const response = await fetch('/chart_data');
                const chartData = await response.json();
                Plotly.newPlot('chart', chartData.data, chartData.layout, {responsive: true});
                document.getElementById('status').textContent = 'Updated: ' + new Date().toLocaleTimeString();
            } catch (e) {
                document.getElementById('status').textContent = 'Error: ' + e.message;
            }
        }
        
        loadChart();
        setInterval(loadChart, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chart_data')
def chart_data():
    # Fetch data
    ticker = yf.Ticker("SPY")
    data_5m = ticker.history(period="1d", interval="5m")
    data_15m = ticker.history(period="5d", interval="15m")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.5, 0.5],
        subplot_titles=('5-Minute Chart', '15-Minute Chart'),
        vertical_spacing=0.1
    )
    
    # 5-minute candlesticks
    fig.add_trace(
        go.Candlestick(
            x=data_5m.index,
            open=data_5m['Open'],
            high=data_5m['High'],
            low=data_5m['Low'],
            close=data_5m['Close'],
            name='5m'
        ),
        row=1, col=1
    )
    
    # 15-minute candlesticks
    fig.add_trace(
        go.Candlestick(
            x=data_15m.index,
            open=data_15m['Open'],
            high=data_15m['High'],
            low=data_15m['Low'],
            close=data_15m['Close'],
            name='15m'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=800,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        showlegend=True
    )
    
    return fig.to_json()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SIMPLE SPY CHART - http://localhost:5001")
    print("="*60 + "\n")
    app.run(debug=True, port=5001)
