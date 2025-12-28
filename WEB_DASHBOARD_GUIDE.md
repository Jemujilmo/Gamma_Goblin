# Web Dashboard Quick Reference

## Accessing the Dashboard

```bash
# Start the server
python flask_app.py --port=5050

# Or with venv
./.venv/bin/python flask_app.py --port=5050
```

## Dashboard URLs

### Main Dashboard (Multi-Timeframe)
**URL:** `http://localhost:5050/`

**Shows:**
- 1-minute chart (when market open)
- 5-minute chart
- 15-minute chart
- All charts update simultaneously
- Ticker search with 7,410+ US stocks (Nasdaq + NYSE)
- Recent search history (last 10 tickers)

**Best For:**
- Active trading
- Quick timeframe comparison
- Seeing full market picture
- Multi-ticker analysis

### Indicator View (Single Chart)
**URL:** `http://localhost:5050/indicator`

**Shows:**
- Single unified chart
- Persistent zoom/pan (saved in browser)
- Cleaner, focused interface

**Best For:**
- Monitoring one timeframe
- Detailed chart analysis
- Presentations

## Status Cards Explained

### 5M Bias & 15M Bias
**Colors:**
- 🟢 Green = Bullish
- 🔴 Red = Bearish
- 🟡 Yellow = Neutral

**Confidence Levels:**
- Strong: 83.3% (3/3 conditions aligned)
- Moderate: 66.7% (2/3 conditions)
- Weak: 33.3% (1/3 conditions)

### Current Price
- Real-time SPY price
- Updated every 2 seconds when market open
- Last known price when market closed

### RSI (14)
**Interpretation:**
- `>70` = Overbought (potential reversal down)
- `55-70` = Bullish
- `45-55` = Neutral
- `30-45` = Bearish
- `<30` = Oversold (potential reversal up)

### IV Rank (NEW)
**What it means:**
- Measures where current IV sits in 52-week range
- `0-30` = 🟢 Low IV - **Buy premium** (calls/puts cheaper)
- `30-50` = 🟡 Moderate
- `50-70` = 🟡 Elevated - **Theta strategies** (sell premium)
- `70-100` = 🔴 Very High - **Strong sell premium** opportunities

**Trading Implications:**
- Low IV Rank → Buy options (they're cheap)
- High IV Rank → Sell options (they're expensive)
- Use for credit spreads, iron condors, strangles

### Put/Call Ratio (NEW)
**What it measures:**
- Ratio of put volume to call volume
- `< 0.8` = 🟢 Bullish (more calls being bought)
- `0.8 - 1.2` = 🟡 Neutral
- `> 1.2` = 🔴 Bearish (more puts being bought)

**Contrarian Indicator:**
- Extremely high P/C can signal bottom (excessive fear)
- Extremely low P/C can signal top (excessive greed)

## Gamma Squeeze Indicator

**Score Components:**
- Volume Ratio (30%): Recent volume vs average
- Volatility Ratio (30%): Current ATR vs average ATR
- Momentum (40%): Price change momentum

**Levels:**
- `0-40%` = ✓ Normal - Standard conditions
- `40-70%` = ⚠️ Elevated - Increased volatility expected
- `70-100%` = ⚡ HIGH GAMMA - Explosive moves likely

**When to Act:**
- High gamma + bullish bias → Consider directional calls
- High gamma + bearish bias → Consider directional puts
- Low gamma + neutral → Consider theta strategies

## Options Walls (Support/Resistance)

**What they show:**
- Strike prices with high open interest
- Support levels (below current price - puts)
- Resistance levels (above current price - calls)

**How to use:**
- Walls act as magnets - price often gravitates toward them
- Strong walls (>80% strength) are harder to break
- Combine with technical analysis for entry/exit points

**Data Source:**
- Real open interest from live SPY options chains
- Updates with each API call (every 2 seconds when active)

## Recent Signals

**Signal Types:**
- 🟢 **BUY** = Bullish setup detected
- 🔴 **SELL** = Bearish setup detected

**Strength:**
- Based on multi-factor sentiment scoring
- Higher % = stronger conviction
- Consider >= 60% strength for trading

**Factors Analyzed:**
1. Bias alignment (5m vs 15m)
2. Price vs VWAP
3. EMA crossovers (9 vs 21)
4. RSI regimes
5. Volatility context

## API Endpoints

### Main Data Endpoint
```
GET /api/analysis
```

**Returns:**
```json
{
  "timestamp": "2025-12-28 12:00:00",
  "chart_5m": { ... },        // Plotly chart data
  "chart_15m": { ... },
  "bias_5m": {
    "bias": "Bullish",
    "confidence": 0.833
  },
  "indicators": {
    "close": 690.31,
    "rsi": 58.2
  },
  "iv_metrics": {              // NEW
    "iv_rank": 22.5,
    "current_iv": 14.2,
    "iv_percentile": 22.5
  },
  "put_call_ratio": {          // NEW
    "volume_pcr": 0.85,
    "sentiment": "neutral"
  },
  "gamma_exposure": {          // NEW
    "total_gamma": 240513,
    "net_gex": -19863,
    "gex_level": "neutral"
  },
  "walls": [                   // NOW REAL DATA
    {
      "strike": 695.0,
      "type": "resistance",
      "strength": 81,
      "open_interest": 8189
    }
  ],
  "signals": [ ... ],
  "market_status": {
    "is_open": true,
    "status": "Regular Trading"
  }
}
```

### Debug Endpoint
```
GET /api/analysis/debug
```

Returns last 10 candles with all indicator values for troubleshooting.

## Auto-Refresh Behavior

**When Market Open:**
- Fetches new data every 2 seconds
- Charts update smoothly without flickering
- Status cards animate changes

**When Market Closed:**
- Still refreshes every 2 seconds
- Shows last available data
- Market status shows "🔴 Market Closed"

## Chart Interactions

**Ticker Search & Selection:**
- Click search box to see recent searches (last 10 tickers)
- Type to filter from 7,410+ available tickers
- Recent searches shown with blue highlight (📌 RECENT SEARCHES)
- Live search results shown with green highlight
- Press Enter or click to select any ticker
- Manual entry supported for unlisted symbols
- Recent searches persist across browser sessions

**Zoom:**
- Click and drag on chart to zoom
- Double-click to reset zoom
- Scroll wheel for fine zoom control

**Pan:**
- Hold shift + drag to pan left/right
- Useful for historical data review

**Hover:**
- Hover over candles for details:
  - OHLC values
  - VWAP, EMA9, EMA21 at that time
  - Volume

**Persistent State (Indicator View Only):**
- Zoom/pan state saved to browser localStorage
- Survives page refresh
- Clear browser cache to reset

## Keyboard Shortcuts

**Browser:**
- `Ctrl+R` / `F5` - Refresh page
- `Ctrl+Shift+R` - Hard refresh (clears cache)
- `F11` - Fullscreen mode
- `Ctrl+0` - Reset zoom level

**Dashboard:**
- Auto-refresh runs continuously
- No manual shortcuts needed
- Use browser refresh for forced update

## Troubleshooting

**Charts not loading:**
1. Check browser console (F12)
2. Verify API endpoint: `http://localhost:5050/api/analysis`
3. Restart Flask server
4. Clear browser cache

**Data seems stale:**
- Check "Time since update" indicator
- Verify market status (may be closed)
- Check terminal for API errors

**Server won't start:**
```bash
# Check if port in use
lsof -i :5050  # Linux/Mac
netstat -ano | findstr :5050  # Windows

# Kill process using port
kill <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Restart on different port
python flask_app.py --port=5051
```

**Options data missing:**
- Options data fetcher falls back to synthetic on errors
- Check terminal output for "Options data error" messages
- Verify yfinance is installed: `pip install yfinance`

## Performance Tips

1. **Adjust refresh rate** - Edit `templates/index.html` line ~669:
   ```javascript
   refreshInterval = setInterval(fetchAnalysis, 2000); // Change 2000 to 5000 for 5s
   ```

2. **Reduce timeframes** - Comment out 1m chart if not needed

3. **Limit history** - Reduce `.tail()` values in `flask_app.py`:
   ```python
   data_5m = data_5m.tail(50)  # Instead of 78
   data_15m = data_15m.tail(60)  # Instead of 100
   ```

4. **Disable options data** - Comment out options fetcher in `create_chart()` to use only synthetic walls

## Best Practices

✅ **DO:**
- Use Multi-Timeframe view for trading decisions
- Use Indicator view for presentations/monitoring
- Check market status before acting on signals
- Combine IV Rank with P/C Ratio for options strategy
- Use walls as reference points, not absolute barriers
- Search for any US stock (7,410+ tickers available)
- Use recent searches for quick ticker switching

❌ **DON'T:**
- Trade based on single indicator alone
- Ignore market status (don't trade on stale data)
- Over-leverage on high gamma conditions
- Chase signals without confirming bias alignment
- Use in production without proper WSGI server
- Clear browser cache unnecessarily (loses recent searches & chart state)

## Multi-Ticker Usage

**Switching Tickers:**
1. Click the ticker search box at top of dashboard
2. See your recent searches (last 10, saved in browser)
3. Type to search from 7,410+ US stocks
4. Click any ticker or press Enter to switch

**Available Tickers:**
- All Nasdaq stocks (~6,990 tickers)
- All NYSE stocks (~2,763 tickers)
- Total: 7,410+ unique symbols
- Includes: ETFs, stocks, major indices

**Ticker List Sources:**
- Fetched from Nasdaq official API
- Fetched from NYSE public datasets
- **Does NOT use Yahoo Finance API** (0 requests)
- Updates automatically on server startup

**API Request Usage:**
- Ticker list = 0 Yahoo Finance requests
- Each ticker switch = 3-4 requests per refresh
- Same request count regardless of ticker chosen
- Auto-refresh every 2 seconds = ~1,800-2,160 req/hour
- Within Yahoo Finance free tier limits (2,000/hour)

## Example Trading Workflow

1. **Morning Setup:**
   - Open Multi-Timeframe dashboard
   - Search for your watchlist tickers (AAPL, TSLA, SPY, etc.)
   - Check market status (wait for 🟢 Open)
   - Note options walls for the day

2. **Strategy Selection:**
   - Check IV Rank:
     - Low (<30) → Plan to buy options
     - High (>70) → Plan to sell premium
   - Check P/C Ratio for sentiment
   - Check Gamma score for volatility expectations

3. **Entry Timing:**
   - Wait for 5m and 15m bias alignment
   - Look for buy/sell signals at support/resistance
   - Confirm with RSI (avoid overbought/oversold extremes)

4. **Position Management:**
   - Set stops at nearest options wall
   - Take profits at opposite wall
   - Adjust based on gamma squeeze indicator

5. **Exit Strategy:**
   - Close positions when bias flips
   - Take profits on high-strength signals
   - Scale out at resistance/support levels

---

**Remember:** This is a decision support tool, not financial advice. Always manage risk appropriately and validate signals before trading.
