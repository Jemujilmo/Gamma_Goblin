# Thanks Claude Sonnet for helping me make this ridiculous webapp that may or may not ever amount to anything but we'll see.


# SPY Trading Signal Generator

**A simple web app that shows you when to buy or sell SPY stock options using chart analysis.**
This sort of started as something I wanted to use as a test for my options trading process. what it became is something I am not even sure if it works or not but I am going to try my best to actually use it and refine the data to reflect results. this is for testing purposes only, gambling is an addiction and if you think you suffer from a gambling addiction please seek the proper authorities to help you regain control and get the support you need.

This program looks at stock charts and tells you:
- **Green triangles** = Good time to BUY
- **Red triangles** = Good time to SELL

It's like having an assistant that watches the charts for you 24/7.
again these test results are not %100 accurate and all configurations cloned or forked from github are subject to change over time.
---

## 🚀 How to Start the Program (First Time Ever)

**Follow these steps EXACTLY in order:**

### Step 1: Verify Python and Dependencies are Installed

**Before running the app for the first time, you need to install Python and dependencies.**

If you haven't done this yet:
1. Check if Python is installed: Open PowerShell and type `python --version`
2. If Python is NOT installed, download it from [python.org](https://www.python.org/downloads/) (Python 3.8 or higher)
3. See [INSTALL.md](INSTALL.md) for complete installation instructions

**If you already have the `.venv` folder in the project directory, skip to Step 2.**

### Step 2: Open PowerShell
1. Press the **Windows key** on your keyboard
2. Type **"PowerShell"**
3. Click on **"Windows PowerShell"** (the blue one)
4. A black/blue window will open - this is your command window

### Step 3: Go to the Program Folder
Copy this command and paste it into PowerShell (right-click to paste):

```powershell
cd "C:\Users\Kryst\Code Stuff\spytradebot"
```

Press **Enter**

### Step 4: Start the Program
Copy this command and paste it into PowerShell:

```powershell
.\.venv\Scripts\python.exe flask_app.py
```

Press **Enter**

**Note about ports:** By default, the program runs on port 5000. If you need to use a different port (e.g., if something else is using port 5000), you can specify it:
```powershell
.\.venv\Scripts\python.exe flask_app.py --port=5050
```
Then access the dashboard at http://localhost:5050 instead of http://localhost:5000

You'll see text scroll by. **Watch for these important messages:**
```
Access the dashboard at: http://localhost:5000
* Running on http://127.0.0.1:5000
```

**IMPORTANT: Wait for the startup process to complete!** You'll see:
- `[STARTUP] Pre-caching SPY data...`
- `[SPY] Fetching 5m data...`
- `[SPY] Fetching 15m data...`
- `[SPY] Fetching 1m data...`
- Then a backtest report will appear

**Wait until you see the backtest report (about 10-30 seconds). Don't close this window!**

### Step 5: Open Your Web Browser
**ONLY AFTER the backtest report appears in PowerShell:**

1. Open **Google Chrome** or **Microsoft Edge**
2. In the address bar (where you type websites), copy and paste this:
   ```
   http://localhost:5000
   ```
3. Press **Enter**
4. **Wait 5-10 seconds** for the page to load completely

**You should now see charts with buy/sell signals!**

**If you see "Failed to fetch data":**
- Wait 10 more seconds and refresh the page (press F5)
- Make sure the PowerShell window is still open and running
- Check that you waited for the backtest report before opening the browser

---

## 📊 What You're Looking At

When the page loads, you'll see three charts (1-minute, 5-minute, and 15-minute views):

- **Green upward triangles** = BUY signals (stock might go up)
- **Red downward triangles** = SELL signals (stock might go down)
- **Yellow/Purple lines** = Moving averages (show the trend)
- **Green/Red bars at bottom** = Volume (how much trading is happening)

The charts update automatically every minute - you don't need to refresh the page.

---

## ❌ How to Stop the Program

When you're done:
1. Go back to the PowerShell window (the black/blue window)
2. Press **Ctrl + C** on your keyboard
3. The program will stop
4. You can close the PowerShell window now

---

## 🔧 Troubleshooting (If Something Goes Wrong)

### Problem: "Python was not found"
**Solution:** Python isn't installed. Install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)

### Problem: "No such file or directory: .venv" or ".venv\Scripts\python.exe not found"
**Solution:** Virtual environment not set up. Follow the complete installation guide in [INSTALL.md](INSTALL.md)

### Problem: "No module named 'flask'" or other import errors
**Solution:** Dependencies not installed. Run:
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### Problem: "Port already in use" or "Address already in use"
**Solution:** 
1. The program is already running in another PowerShell window - close it first
2. Or another program is using port 5000. Close the conflicting program or use a different port:
   ```powershell
   .\.venv\Scripts\python.exe flask_app.py --port=5050
   ```

### Problem: "Failed to fetch data" in web browser
**Solution:** 
1. **You opened the browser too quickly!** Wait for the backtest report to appear in PowerShell (10-30 seconds after starting)
2. Refresh the page (press F5) and wait 10 seconds
3. Make sure the PowerShell window is still open and running (you didn't press Ctrl+C)
4. Try closing the browser tab and opening a new one to `http://localhost:5000`

### Problem: Charts aren't showing up or page is blank
**Solution:** 
1. **Wait longer!** The first data fetch takes 10-30 seconds
2. ChWait for the startup messages** - you'll see:
   - `Access the dashboard at: http://localhost:5000`
   - `[STARTUP] Pre-caching SPY data...`
   - Data fetching messages
   - A backtest report with signal accuracy
5. **ONLY AFTER seeing the backtest report**, open your browser and go to: `http://localhost:5000`
6. **Wait 5-10 seconds** for charts to load on first visit
7. **When done:** Press Ctrl+C in PowerShell to stop

**Common Mistake:** Opening the browser too quickly causes "Failed to fetch data" errors. Always wait for the backtest report first!://localhost:5000`
4. Try refreshing the page (press F5) and wait 10 seconds
5. Check your internet connection

### Problem: "Rate limit exceeded" or "429 Too Many Requests"
**Solution:** Yahoo Finance is temporarily blocking requests. Wait 2-5 minutes, then refresh the page.

### Problem: "Failed to fetch data" or blank charts after 1+ minute
**Solution:**
1. Check if the market is closed (data is from last trading session)
2. Press Ctrl+C in PowerShell to stop the program
3. Wait 5 seconds
4. Restart: `.\.venv\Scripts\python.exe flask_app.py`
5. Wait for backtest report, then open browser

---

## 📱 Daily Use (After First Setup)

Every time you want to use the program:

1. **Open PowerShell** (Windows key → type "PowerShell")
2. **Navigate to folder:**
   ```powershell
   cd "C:\Users\Kryst\Code Stuff\spytradebot"
   ```
3. **Start program:**
   ```powershell
   .\.venv\Scripts\python.exe flask_app.py
   ```
4. **Open browser** and go to: `http://localhost:5000`
5. **When done:** Press Ctrl+C in PowerShell to stop

---

## 🤖 Copy-Paste The entirety of this body of text Into Copilot for Help

If you need help, copy the entire text below until line 147 and paste it into Copilot:

```
I'm trying to run a stock trading signal program on Windows. Here's what I need help with:

PROGRAM DETAILS:
- Name: SPY Trading Signal Generator
- Location: C:\Users\Kryst\Code Stuff\spytradebot
- Language: Python
- Purpose: Shows buy/sell signals on stock charts in a web browser

HOW TO RUN IT:
1. Open PowerShell
2. Run: cd "C:\Users\Kryst\Code Stuff\spytradebot"
3. Run: .\.venv\Scripts\python.exe flask_app.py
4. WAIT for backtest report to appear (10-30 seconds)
5. THEN open browser to: http://localhost:5000
6. Wait 5-10 seconds for charts to load

IMPORTANT TIMING:
- Don't open browser until you see the backtest report in PowerShell
- First page load takes 5-10 seconds - be patient
- If you see "Failed to fetch data", you opened browser too quickly - refresh and wait

MY PROBLEM:
[Describe what's happening - for example:]
- "When I run the command, I get an error that says..."
- "The charts show 'Failed to fetch data'..."
- "I see a message about rate limiting..."
- "Python was not found..."
- "The page is blank or won't load..."

WHAT I'VE TRIED:
[List what you've already tried - for example:]
- "I restarted my computer"
- "I closed all PowerShell windows and tried again"
- "I waited for the backtest report before opening browser"
- "I waited 2 minutes and refreshed the page"

Please help me fix this step-by-step in simple terms.
```

---

## 📚 Technical Details (For Advanced Users)

### Current System Capabilities (January 2026)

**✅ Signal Generation Engine:**
- **Multi-Timeframe Analysis**: 1m (entry timing), 5m (setup confirmation), 15m (trend direction)
- **8-Condition Evaluation System**: 3 out of 8 conditions required for signal generation
  - VWAP trend alignment (15m and 5m)
  - EMA9/EMA21 positioning and crossover detection (golden cross/death cross)
  - RSI momentum ranges (35-60 BUY, 40-65 SELL)
  - MACD histogram direction and momentum shifts
  - Volume confirmation (>1.05x average)
  - Gamma score integration (>40 indicates high conviction)
- **Smart Resistance Filter**: Blocks buys near resistance only when MACD shows weakness (<0.05)
- **Mandatory Trend Alignment**: BUY requires price > VWAP, SELL requires price < VWAP
- **Frequency Limiting**: 15-minute cooldown between signals (10 minutes for 6+ condition signals)
- **Real-Time Backtesting**: Automatic accuracy reporting with profit/loss tracking

**📊 Current Performance Metrics:**
- Signal Accuracy: ~68.4% (4 BUY, 15 SELL on recent test data)
- BUY Accuracy: 50% (improving from initial 33.3%)
- SELL Accuracy: 73.3%
- Signal Quality: Filters out low-conviction moves using multi-factor scoring

**🎨 Web Interface Features:**
- Interactive Plotly charts with auto-fit Y-axis (includes indicator values)
- Real-time candlestick charts (1m, 5m, 15m timeframes)
- Market status indicator (🟢 Open / 🔴 Closed / ⏸ Pre/Post Market)
- Live options data: IV Rank, Put/Call Ratio, Options Walls, Gamma Exposure (GEX)
- Signal markers with gamma scores: `BUY (6/8 conditions) [γ=66]`
- Auto-refresh every 2 seconds with connection status
- Multi-ticker support (SPY, QQQ, AAPL, TSLA, 30+ presets, full Nasdaq/NYSE library)
- Volume bars (color-coded green/red)
- MACD histogram and RSI indicators
- Responsive design for desktop and mobile

### What This Program Actually Does

1. **Downloads live stock data** from Yahoo Finance (5m, 15m, 1m intervals)
2. **Calculates indicators**: VWAP, EMA9, EMA21, RSI, MACD, ATR, Volume
3. **Generates signals** using new_signal_logic.py:
   - **BUY Conditions** (need 3/8):
     1. 15m price above VWAP (trend confirmation)
     2. 5m price above VWAP (setup confirmation)
     3. 1m pullback to VWAP/EMA (entry timing)
     4. RSI 35-60 rising (momentum building)
     5. MACD histogram increasing (momentum shift)
     6. Volume >1.05x average (conviction)
     7. 15m MACD positive (trend support)
     8. Gamma score ≥40 (high volatility/conviction)
   - **SELL Conditions** (need 3/8):
     1. 15m price below VWAP
     2. 5m price below VWAP
     3. Failed VWAP/EMA reclaim (rejection)
     4. RSI 40-65 falling (momentum fading)
     5. MACD histogram decreasing
     6. Volume >1.05x average
     7. 15m MACD negative
     8. Gamma score ≥40
   - **Momentum Overrides**: EMA crossovers and MACD zero-crossings trigger immediately
4. **Quality filtering**:
   - Volume must be >50% of 10-candle average
   - Smart resistance filter (blocks buys near highs only when MACD weak)
   - Mandatory VWAP alignment (no counter-trend signals)
5. **Displays results** on interactive charts with zoom/pan/hover details

### Signal Generation Logic

**BUY signals appear when:**
- 3+ standard conditions met OR strong override (golden cross, MACD reversal)
- Price ABOVE VWAP (mandatory trend alignment)
- NOT at resistance with weak MACD (<0.3% from 20-candle high AND MACD <0.05)
- 15 minutes since last signal (or 10 minutes if 6+ conditions)

**SELL signals appear when:**
- 3+ standard conditions met OR strong override (death cross, MACD breakdown)
- Price BELOW VWAP (mandatory trend alignment)
- 15 minutes since last signal (or 10 minutes if 6+ conditions)

**Example Signal Labels:**
- `BUY (6/8 conditions) [γ=66]` - Strong buy with 66% gamma score
- `SELL (4/8 conditions) [γ=41]` - Moderate sell with 41% gamma score
- Higher condition count = higher conviction
- Gamma >70 = Explosive move potential (gamma squeeze territory)

### Gamma Score Calculation

Gamma score (0-100%) combines three factors:
- **Volume Ratio (30%)**: Recent volume / average volume
- **Volatility Ratio (30%)**: Current ATR / average ATR  
- **Price Momentum (40%)**: Absolute price change over last 5 candles

**Interpretation:**
- **70-100%** = ⚡ HIGH GAMMA - Explosive moves likely (institutional activity)
- **40-69%** = ⚠️ ELEVATED - Increased volatility/conviction
- **0-39%** = ✓ NORMAL - Standard market conditions

### Files in This Program

**Production Files (Active):**
- `flask_app.py` - Main web server (starts the program)
- `new_signal_logic.py` - **Primary signal generation** (multi-timeframe with gamma integration)
- `signal_backtester.py` - Real-time accuracy tracking and profit/loss analysis
- `data_fetcher.py` - Downloads stock data from Yahoo Finance
- `indicators.py` - Calculates technical indicators (RSI, MACD, EMA, VWAP, ATR)
- `market_copilot.py` - Analysis orchestration
- `analyzers.py` - Options wall and sentiment analysis
- `options_data.py` - Live options chain data (IV, P/C ratio, GEX)
- `market_hours.py` - Market hours detection and data freshness
- `ticker_list.py` - Multi-ticker support (Nasdaq/NYSE library)
- `config.py` - Settings (timeframes, thresholds, rate limits)
- `requirements.txt` - Required Python packages

**Deprecated Files (Kept for backward compatibility):**
- `bias_classifier.py` - ⚠️ Old bias classification (replaced by new_signal_logic.py)
- `signal_generator.py` - ⚠️ Old signal logic (replaced by new_signal_logic.py)

**Alternative Interfaces (Optional):**
- `chart_view.py` - Standalone ASCII terminal chart viewer
- `terminal_dashboard.py` - Rich terminal UI with HUD display

**Testing & Development:**
- `test_new_signals.py` - Standalone signal testing
- `test_system.py` - System validation
- `test_market_hours.py` - Market hours testing
- `test_rate_limiting.py` - Rate limit testing
- `examples.py` - Usage examples
- `monitor_requests.py` - Rate limiting monitor

**Scripts (Mac/Linux):**
- `scripts/run_dashboard.sh` - Start Flask with auto venv setup
- `scripts/start_dashboard_detach.sh` - Background Flask with health checks

**Documentation:**
- `README.md` - This file
- `WEB_DASHBOARD_GUIDE.md` - Web interface complete reference
- `MARKET_HOURS.md` - Market hours and data freshness
- `RATE_LIMITING.md` - API rate limiting guide
- `ARCHITECTURE.md` - System architecture
- `CHANGELOG.md` - Version history
- `QUICKREF.md` - Quick reference card

### Configuration Settings

Located in `config.py`:

```python
# Ticker
DEFAULT_TICKER = "SPY"

# Timeframes for analysis
TIMEFRAMES = {
    "short": "5m",   # Short-term execution
    "medium": "15m"  # Structural bias
}

# Indicator parameters
INDICATORS = {
    "ema_fast": 9,      # Fast EMA period
    "ema_slow": 21,     # Slow EMA period
    "rsi_period": 14,   # RSI lookback
    "atr_period": 14    # ATR calculation period
}

# Rate limiting (Yahoo Finance API)
REQUEST_DELAY = 2.0              # Seconds between requests (~1800 req/hour)
MAX_REQUESTS_PER_HOUR = 1800     # Safe buffer under Yahoo's ~2000/hour limit
CACHE_DURATION = 60              # Cache data for 60 seconds

# Signal generation thresholds (new_signal_logic.py)
SIGNAL_CONDITIONS_REQUIRED = 3   # Out of 8 total conditions
RSI_BUY_RANGE = (35, 60)        # RSI range for BUY signals
RSI_SELL_RANGE = (40, 65)       # RSI range for SELL signals
VOLUME_THRESHOLD = 1.05          # 1.05x average volume required
GAMMA_THRESHOLD = 40             # Gamma score for elevated conviction
RESISTANCE_PROXIMITY = 0.003     # 0.3% from high triggers resistance check
MACD_WEAKNESS = 0.05            # MACD < 0.05 considered weak momentum
SIGNAL_COOLDOWN_MINUTES = 15     # Minimum time between signals
STRONG_SIGNAL_THRESHOLD = 6      # 6+ conditions = strong signal (10-min cooldown)
```

**Performance Tuning:**
- Increase `REQUEST_DELAY` if hitting rate limits (safer, slower)
- Decrease `SIGNAL_CONDITIONS_REQUIRED` for more signals (less accurate)
- Adjust `GAMMA_THRESHOLD` for sensitivity (lower = more signals)
- Modify `RSI_*_RANGE` to capture different momentum regimes

### Rate Limiting (Why It Sometimes Stops Working)

Yahoo Finance limits how many requests you can make:
- **Limit**: ~2000 requests per hour
- **Our setting**: 1000 requests per hour (safe buffer)
- **What happens if exceeded**: "Rate limit" error, wait 2 minutes

**The program automatically:**
- Waits 3 seconds between data downloads
- Caches data for 60 seconds (reuses instead of re-downloading)
- Backs off exponentially if rate limited (5s → 10s → 20s delays)

### System Requirements

- **Operating System**: Windows 10 or 11
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum
- **Internet**: Stable connection (downloads data every minute)
- **Browser**: Chrome, Edge, or Firefox

### Installed Python Packages

```
yfinance - Downloads stock data
flask - Web server
pandas - Data processing
numpy - Math calculations
plotly - Interactive charts
ta - Technical analysis indicators
```

---

## 🎓 Understanding the Indicators

### What the Lines Mean

- **Purple dotted line (VWAP)**: Average price weighted by volume
  - If price is ABOVE = bullish
  - If price is BELOW = bearish

- **Yellow line (EMA 9)**: 9-period moving average (fast)
  - Shows short-term trend

- **Orange line (EMA 21)**: 21-period moving average (slow)
  - Shows medium-term trend
  - When yellow crosses ABOVE orange = bullish
  - When yellow crosses BELOW orange = bearish

- **MACD Histogram (bottom panel)**: Momentum indicator
  - Green bars = buying pressure
  - Red bars = selling pressure
  - Bigger bars = stronger momentum
  - Small bars (< 0.15) = weak signal, program ignores

### What the Signals Mean

**Signal Strength Labels:**
- **STRONG** (80%+): High confidence, trade these
- **MODERATE** (65-79%): Medium confidence, be cautious
- **WEAK** (45-64%): Low confidence, usually filtered out

**The program only shows MODERATE or STRONG signals** to reduce noise.

---

## ⚠️ Important Warnings

### This is NOT Financial Advice
- Signals are suggestions, not guarantees
- You can lose money trading
- Always do your own research
- Never invest money you can't afford to lose

### Data Limitations
- Data comes from Yahoo Finance (free but limited)
- Sometimes Yahoo blocks us temporarily (rate limiting)
- Market data can be delayed 15-20 minutes
- Signals work best during market hours (9:30 AM - 4:00 PM ET)

### Program Limitations
- Runs on YOUR computer only (not in the cloud)
- Requires internet connection
- Must keep PowerShell window open while using
- Does NOT place trades automatically (you must do it manually)

---

## ⚠️ Common Error Messages

**"Python was not found"**
→ Python isn't installed. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)

**"No such file or directory: .venv" or "cannot find .venv\Scripts\python.exe"**
→ Virtual environment not created. See [INSTALL.md](INSTALL.md) for setup instructions

**"No module named 'flask'"** or **"ModuleNotFoundError"**
→ Dependencies not installed. Run: `.\.venv\Scripts\pip.exe install -r requirements.txt`

**"Address already in use"**
→ Program is already running in another window. Close it first, or use a different port with `--port=5050`

**"Connection refused"** or **"Failed to connect"**
→ Program isn't running. Make sure PowerShell window is open and you see "Running on http://127.0.0.1:5000"

**"Failed to fetch data: Failed to fetch"** (in browser)
→ You opened the browser too quickly! Wait for the backtest report in PowerShell, then refresh the page (F5)

**"Rate limit exceeded"** or **"429 Too Many Requests"**
→ Yahoo Finance blocked requests. Wait 2-5 minutes and try again. The app has built-in rate limiting but Yahoo can still block aggressive usage.

**"Failed to fetch data"** (after waiting)
→ Internet connection issue or Yahoo Finance is down. Check your internet and try restarting the app.

**"Market is closed"** (warning message)
→ Stock market isn't open. Data shows last trading session. This is normal outside market hours (9:30 AM - 4:00 PM ET).

---

## 📞 Getting Help

### Option 1: ChatGPT
Copy the template from the "Copy-Paste This Into ChatGPT" section above and describe your problem.

### Option 2: Check the Logs
If something isn't working:
1. Look at the PowerShell window where the program is running
2. Read the last few lines - they often explain what went wrong
3. Copy any error messages and paste them into ChatGPT

### Option 3: Restart Everything
When in doubt:
1. Press Ctrl+C in PowerShell (stops the program)
2. Close PowerShell
3. Wait 30 seconds
4. Open PowerShell again and restart from Step 1

---

## 🎯 Quick Reference Card

**START PROGRAM:**
```powershell
cd "C:\Users\Kryst\Code Stuff\spytradebot"
.\.venv\Scripts\python.exe flask_app.py
```
**⏱️ Wait for backtest report (10-30 seconds) before opening browser!**

**STOP PROGRAM:**
- Press `Ctrl + C` in PowerShell

**VIEW CHARTS:**
- Open browser: `http://localhost:5000`
- Wait 5-10 seconds for first load
- If you see "Failed to fetch data", refresh (F5) and wait 10 seconds

**IF "FAILED TO FETCH DATA":**
- You opened browser too early → Wait for backtest report, then refresh
- Connection issue → Check PowerShell is still running
- Refresh page (F5) and wait 10 seconds

**IF STUCK:**
- Press Ctrl+C in PowerShell
- Wait 5 seconds
- Close PowerShell
- Restart from beginning
- Remember to wait for backtest report!

**SIGNALS:**
- 🟢 Green triangle = BUY
- 🔴 Red triangle = SELL
- No signals = Wait/Neutral

**TIMING SUMMARY:**
1. Start app → Wait 10-30 sec for backtest report
2. Open browser → Wait 5-10 sec for page load
3. Total: ~20-40 seconds from start to charts visible

---

**Made for absolute beginners. No prior experience required. If you can copy and paste, you can use this program.**

---

### Web Dashboard Features

**Two Dashboard Modes Available:**

1. **Multi-Timeframe View** (Default - http://localhost:5050/)
   - Shows 1-minute, 5-minute, and 15-minute charts simultaneously
   - Best for active trading and quick timeframe comparison
   - All charts update in real-time

2. **Single-Chart Indicator View** (http://localhost:5050/indicator)
   - Focused single chart view with persistent zoom/pan
   - Chart state saved in browser (survives page refresh)
   - Cleaner interface for monitoring one timeframe

Using a virtualenv (recommended):

```bash
# create and activate a venv (unix/mac)
python3 -m venv .venv
source .venv/bin/activate

# install requirements
pip install -r requirements.txt

# run the dashboard on the default port (5000)
python flask_app.py

# or run on a custom port (example 5050)
python flask_app.py --port=5050

# or set via env var
FLASK_RUN_PORT=5050 python flask_app.py
```

If you already have a virtualenv created by the project, run using its python explicitly:

```bash
./.venv/bin/python flask_app.py --port=5050
```

**Web Dashboard Features:**
- ✅ **Multi-ticker support** - Track any US stock or ETF (SPY, QQQ, AAPL, TSLA, etc.)
  - Library of 30+ popular tickers (major ETFs, FAANG+, sector funds)
  - Optional: Fetch complete Nasdaq/NYSE ticker lists (3000+ symbols)
  - Switch tickers without additional API requests
- ✅ **Real-time candlestick charts** with VWAP, EMA9, EMA21 overlays
- ✅ **Volume bars** (color-coded green/red)
- ✅ **Market status indicator** (🟢 Open / 🔴 Closed)
- ✅ **Auto-refresh every 2 seconds** with time-since-update counter
- ✅ **Real options data** from live options chains:
  - Options walls (support/resistance from open interest)
  - IV Rank & IV Percentile
  - Put/Call ratio (volume & open interest based)
  - Gamma exposure levels (GEX)
- ✅ **Algorithmic entry signals** with multi-factor analysis
  - 🟢 BUY signals (call entry points) - green upward triangles
  - 🔴 SELL signals (put entry points) - red downward triangles
  - 4-factor scoring: Bias + VWAP + EMA + RSI (0-100 points)
  - Time-filtered: Only signals during prime hours (9:45 AM - 3:45 PM ET)
  - Strength percentage displayed (60%+ threshold)
- ✅ **Gamma squeeze indicator** (volume + volatility + momentum)
- ✅ **5m and 15m bias** with confidence scoring
- ✅ **Interactive Plotly charts** (zoom, pan, hover for details)
- ✅ **12-hour time format** with AM/PM (standard, not military)

Notes:
- The app prints the full URL it is serving (e.g. http://localhost:5050). If port 5000 is busy on your machine, use --port to choose another port.
- The API endpoints the UI uses are `/api/analysis` and `/test` for quick connectivity checks.

<!-- Important notes callout -->
<div style="background: #fff9db; border-left: 4px solid #ffd54a; padding: 12px; margin: 12px 0;">
    <strong>⚠️ Important notes — things to consider / be aware of</strong>
    <ul>
        <li><strong>Cold-start behaviour</strong>: the server may return a transient HTTP 500 on the very first API request while background data is being built. The UI now uses safe fallbacks, but expect a short delay on the first load.</li>
        <li><strong>Development server only</strong>: this project uses Flask's development server (debug + reloader). It's fine for local use only — do not expose it to production networks.</li>
        <li><strong>Background builder</strong>: a background thread builds cached payloads. Check <code>dashboard.log</code> for any tracebacks; uncaught exceptions will appear there.</li>
        <li><strong>Port & resource conflicts</strong>: if the dashboard cannot start, another process may be using the port. The helper script kills stale listeners on the configured port before starting; you can also use <code>lsof -iTCP:5050 -sTCP:LISTEN</code> to inspect.</li>
        <li><strong>Logs</strong>: <code>dashboard.log</code> captures server output. Rotate or trim the file if you run the dashboard long-term.</li>
        <li><strong>Virtualenv & background starts</strong>: avoid <code>source .venv/bin/activate</code> in backgrounded scripts — use the venv python directly (the project scripts do this for you) to prevent suspended jobs.</li>
        <li><strong>Dependencies & reproducibility</strong>: pin exact versions in <code>requirements.txt</code> for reproducible runs; the helper installs requirements if missing.</li>
        <li><strong>Rate limiting</strong>: the default request delay is 2s (configurable in <code>config.py</code>). Respect external API limits when changing it.</li>
    <li><strong>Automated checks</strong>: a GitHub Actions smoke-test workflow has been added at <code>.github/workflows/smoke-test.yml</code>. It starts the Flask app, waits for <code>/api/analysis</code> to respond, validates basic JSON keys, and then stops the server. To run a local smoke test, use the helper script and then curl the API (example shown below).</li>
    </ul>
</div>

To run the smoke test locally (quick):

```bash
# start the dashboard and wait for the API to be ready
./scripts/start_dashboard_detach.sh 5050

# check the API response
curl -sS http://127.0.0.1:5050/api/analysis | jq . | head -n 40

# stop the dashboard
if [ -f dashboard.pid ]; then kill "$(cat dashboard.pid)" && rm -f dashboard.pid; fi
```


**That's it!** The system will fetch live SPY data and provide bias/confidence signals.

> 💡 **Want more?** See the [How to Use](#-how-to-use) section below for interactive dashboards, live charts, and other interfaces.

---

## 🎯 Purpose

Market Copilot analyzes SPY across multiple timeframes to provide structured signals for options trading decisions. It helps determine whether to use:
- **Directional strategies** (calls/puts, spreads) when bias is strong
- **Theta decay strategies** (iron condors, strangles) when neutral

**This is decision support only** - no automated trading, no broker integration.

## 🏗️ Architecture

### Modular Design
- **data_fetcher.py**: Abstracted data layer (currently Yahoo Finance, easily swappable)
  - **Built-in rate limiting**: Automatic 2-second delays (~1800 req/hour, safely under Yahoo's limit)
- **market_hours.py**: Market hours detection and data freshness validation
  - **Automatic warnings** when market is closed or data is stale
- **indicators.py**: Technical indicator calculations (EMA, RSI, ATR, VWAP)
- **bias_classifier.py**: Market bias determination with confidence scoring
- **signal_generator.py**: Structured signal generation and synthesis
- **options_data.py**: Real options chain analysis (IV Rank, P/C Ratio, GEX, Walls)
- **analyzers.py**: Lightweight fallback analyzers for Flask UI
- **flask_app.py**: Web server with real-time charting API
- **market_copilot.py**: Main orchestration and output formatting
- **config.py**: Centralized configuration

### Analysis Pipeline

1. **Data Fetching**: Pulls OHLCV data for 5m and 15m timeframes
2. **Indicator Calculation**: Computes EMA(9), EMA(21), RSI(14), ATR(14), Session VWAP
3. **Bias Classification**: Analyzes three conditions:
   - Price vs VWAP
   - EMA9 vs EMA21
   - RSI regime (>55 bullish, <45 bearish)
4. **Confidence Scoring**: Based on alignment of conditions (0.0 to 1.0)
5. **Volatility Detection**: ATR trend analysis (Expansion/Compression/Neutral)
6. **Signal Synthesis**: Combines timeframes with plain-English recommendations

## 📦 Installation & Setup

### System Requirements
- **Python 3.8 or higher**
- **Internet connection** (for live market data from Yahoo Finance)
- **Terminal/Command Prompt** (PowerShell, cmd, bash, etc.)

### Step-by-Step Installation

**1. Clone or Download the Repository**
```bash
git clone <your-repo-url>
cd spytradebot
```

**2. Install Required Packages**
```bash
pip install -r requirements.txt
```

This installs:
- `yfinance` - Market data from Yahoo Finance
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `ta` - Technical analysis indicators
- `pytz` - Timezone handling
- `rich` - Terminal UI formatting
- `plotext` - ASCII charts in terminal

**3. Verify Installation (Optional)**
```bash
# Run demo mode to test without live data
python demo_mode.py

# Run system tests
python test_system.py
```

### First Run

```bash
# Simple analysis output
python market_copilot.py
```

You should see output like:
```
================================================================================
  MARKET COPILOT - SPY Analysis
  2025-12-24 14:30:00
================================================================================

📊 5M Timeframe:
   Bias: Bullish (Strong - 83.3%)
   ...
```

---

## 🚀 How to Use

### Available Interfaces

Market Copilot offers **5 different ways** to view your analysis:

#### 1️⃣ **Web Dashboard** (Recommended - Interactive Browser UI)
```bash
python flask_app.py --port=5050
```
**Features:**
- Real-time Plotly candlestick charts (5m, 15m, optional 1m)
- Market status indicator (🟢 Open / 🔴 Closed)
- Live options data: IV Rank, Put/Call Ratio, Options Walls (OI-based)
- Gamma exposure levels and gamma squeeze indicator
- Buy/sell signals with sentiment analysis
- Auto-refresh every 2 seconds
- Interactive zoom, pan, hover details
- Two view modes:
  - **Main Dashboard** (`http://localhost:5050/`) - Multi-timeframe view
  - **Indicator View** (`http://localhost:5050/indicator`) - Single chart with persistent zoom

#### 2️⃣ **Basic Analysis** (Terminal - Quick Snapshot)
```bash
python market_copilot.py
```
- Simple, clean terminal output
- Shows bias, confidence, and indicators
- One-time analysis snapshot

#### 3️⃣ **Terminal Dashboard** (Interactive HUD)
```bash
python terminal_dashboard.py
```
- Live updating dashboard with ASCII charts
- Displays 5m and 15m timeframes
- ASCII candlestick charts
- Auto-refreshes every 60 seconds
- Press `Ctrl+C` to exit

#### 4️⃣ **Chart View** (Live Charts with Auto-Refresh)
```bash
# One-time chart display
python chart_view.py

# Live mode with 60-second refresh
python chart_view.py --live

# Live mode with custom refresh (e.g., 30 seconds)
python chart_view.py --live 30
```
- Full-screen ASCII candlestick charts
- Shows EMA9, EMA21, and VWAP overlays
- Connection and market status indicators
- Gamma squeeze indicators

#### 5️⃣ **Demo Mode** (No installation required!)
```bash
# Random realistic scenario
python demo_mode.py

# Specific scenarios
python demo_mode.py bullish
python demo_mode.py bearish
python demo_mode.py neutral
```
- Uses sample data (no Yahoo Finance needed)
- Great for testing or demonstrations
- Shows how the system works without API calls

---

## 🧪 Testing (No Installation Required!)

**Try the system immediately without installing dependencies:**

```bash
# Run demo mode with sample data
python demo_mode.py

# Test specific scenarios
python demo_mode.py bullish
python demo_mode.py bearish
python demo_mode.py neutral

# Run system tests
python test_system.py
```

The demo mode shows exactly how the system works with realistic sample data - no Yahoo Finance API or packages needed!

---

## 💻 Programmatic Usage (For Developers)

### Basic Python Integration

```python
from market_copilot import MarketCopilot

# Create and run the copilot
copilot = MarketCopilot()
signal = copilot.analyze(verbose=True)

# Automatically warns if market is closed or data is stale
```

**Note**: The system works when the market is closed, but will warn you that the data is from the last trading session.

### Example Output

```
================================================================================
  MARKET COPILOT - SPY Analysis
  2025-12-23 14:30:00
================================================================================

📊 5M Timeframe:
   Bias: Bullish (Strong - 83.3%)
   Volatility: Expansion

   Indicators:
      Close: $578.45
      VWAP:  $577.20
      EMA9:  $578.10  |  EMA21: $577.50
      RSI:   62.3  |  ATR: $1.25

   Analysis:
      • Bias confidence: 3/3 bullish, 0/3 bearish
      • Price above VWAP (578.45 > 577.20)
      • EMA9 above EMA21 (578.10 > 577.50)
      • RSI bullish regime (62.3 > 55)

📊 15M Timeframe:
   Bias: Bullish (Moderate - 66.7%)
   Volatility: Expansion
   ...

--------------------------------------------------------------------------------
📈 SYNTHESIS:
   Overall Bias: Bullish (Avg Confidence: 75.0%)
   Alignment: 2/2 timeframes agree - Strong

💡 RECOMMENDATIONS:
   • Strong bullish setup - consider directional call options or bullish spreads
   • Volatility expanding - directional strategies may benefit from increased movement
```

### Advanced Usage

```python
from market_copilot import MarketCopilot

# Initialize with custom ticker
copilot = MarketCopilot(ticker="SPY")

# Customize rate limiting (default: 2 seconds between requests)
copilot = MarketCopilot(ticker="SPY", request_delay=3.0)  # Slower, safer
copilot = MarketCopilot(ticker="SPY", request_delay=1.0)  # Faster, riskier

# Run analysis
signal = copilot.analyze(verbose=True)

# Export to JSON
copilot.export_to_json(signal, "spy_signal.json")

# Access structured data
print(f"Overall bias: {signal['synthesis']['overall_bias']}")
print(f"Confidence: {signal['synthesis']['average_confidence']}")

# Get specific timeframe data
tf_5m = signal['timeframes']['5m']
print(f"5m RSI: {tf_5m['indicators']['rsi']}")
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Ticker
DEFAULT_TICKER = "SPY"

# Timeframes
TIMEFRAMES = {
    "short": "5m",   # Short-term execution
    "medium": "15m"  # Structural bias
}

# Indicator parameters
INDICATORS = {
    "ema_fast": 9,
    "ema_slow": 21,
    "rsi_period": 14,
    "atr_period": 14
}

# Bias thresholds
BIAS_THRESHOLDS = {
    "rsi_bullish": 55,
    "rsi_bearish": 45
}

# Rate limiting
REQUEST_DELAY = 2.0  # Seconds between API requests (~1800 req/hour)
MAX_REQUESTS_PER_HOUR = 1800
```

## 📊 Signal Structure

Each signal is a dictionary containing:

```python
{
    "ticker": "SPY",
    "analysis_timestamp": "2025-12-23 14:30:00",
    "timeframes": {
        "5m": {
            "bias": "Bullish",
            "confidence": 0.833,
            "confidence_label": "Strong",
            "volatility_regime": "Expansion",
            "indicators": {
                "close": 578.45,
                "ema_9": 578.10,
                "ema_21": 577.50,
                "rsi": 62.3,
                "atr": 1.25,
                "vwap": 577.20
            },
            "analysis_notes": [...]
        },
        "15m": {...}
    },
    "synthesis": {
        "overall_bias": "Bullish",
        "average_confidence": 0.750,
        "timeframe_alignment": "2/2 timeframes agree",
        "alignment_strength": "Strong",
        "recommendations": [...]
    }
}
```

## 🎓 How It Works

### Bias Classification Logic

The system evaluates three conditions:

1. **Price vs VWAP**: Above = bullish signal, Below = bearish signal
2. **EMA Crossover**: EMA9 > EMA21 = bullish, EMA9 < EMA21 = bearish
3. **RSI Regime**: >55 = bullish, <45 = bearish, between = neutral

**Confidence Score** = (Aligned signals) / (Total signals)

### Volatility Regime Detection

Analyzes ATR trend over recent periods:
- **Expansion**: ATR rising (good for directional plays)
- **Compression**: ATR falling (good for theta strategies)
- **Neutral**: Flat ATR

### Multi-Timeframe Synthesis

Combines 5m (execution) and 15m (structure) analysis:
- Strong alignment → Higher conviction trades
- Divergence → Reduce size or wait
- Expansion + Strong bias → Directional options
- Compression + Neutral → Theta strategies

## 🔮 Future Improvements & Roadmap

### 🎨 UI/UX Enhancements (High Priority)

**Modern Framework Migration:**
- **React + TypeScript** frontend with Next.js or Vite
  - Component-based architecture for maintainability
  - Server-side rendering for faster initial load
  - Hot module replacement for development
- **Chart Library Upgrades:**
  - **TradingView Lightweight Charts** - Industry-standard charting with superior performance
  - **Apache ECharts** - Highly customizable with built-in technical indicators
  - **Recharts** - React-native charts with excellent TypeScript support
  - **Chart.js v4** - Lightweight alternative with real-time update optimization
- **State Management**: Redux Toolkit or Zustand for predictable data flow
- **Styling**: Tailwind CSS or Chakra UI for consistent, responsive design
- **Real-time Updates**: WebSocket integration replacing polling (reduce API load)

**Dashboard Enhancements:**
- Multi-monitor layout support (drag-and-drop chart arrangement)
- Dark/light theme toggle with custom color schemes
- Customizable alert system (push notifications, sounds, email/Discord/Telegram)
- Watchlist management (save multiple tickers, quick switch)
- Annotation tools (drawing support/resistance lines, notes on charts)
- Heatmap views (sector performance, correlation matrix)
- Options chain visualizer (3D gamma surface, IV skew)

### 📊 Analytics & Performance

**Backtesting Engine:**
- Historical signal performance analysis (2019-present)
- Win rate by timeframe, market condition, gamma level
- Drawdown analysis and risk metrics (Sharpe ratio, max DD)
- Monte Carlo simulation for strategy validation
- Paper trading mode (track hypothetical trades)

**Machine Learning Integration:**
- LSTM/Transformer models for pattern recognition
- Sentiment analysis from news/social media (Twitter, Reddit WSB)
- Anomaly detection for unusual market behavior
- Reinforcement learning for parameter optimization

**Advanced Metrics:**
- Order flow analysis (time & sales, market depth)
- Dark pool activity indicators
- Institutional positioning (13F filings integration)
- Sector rotation tracking
- Market breadth indicators (advance/decline, new highs/lows)

### 🔧 Technical Improvements

**Data Sources:**
- **Polygon.io** integration (real-time tick data, extended hours)
- **Alpha Vantage** fallback (redundancy if Yahoo fails)
- **IEX Cloud** for fundamental data (P/E, earnings, dividends)
- **CBOE** for official VIX and options data
- Database caching (PostgreSQL/TimescaleDB for historical storage)

**Performance Optimizations:**
- Rust/Go microservices for indicator calculations (10-100x speedup)
- Redis caching layer for sub-second response times
- CDN integration for static assets
- Lazy loading and code splitting (reduce initial bundle size)
- Service worker for offline functionality

**Signal Improvements:**
- Adaptive thresholds based on market volatility (VIX-adjusted)
- Machine learning confidence scoring (random forest/XGBoost)
- Multi-asset correlation signals (SPY + QQQ + VIX combined)
- Regime detection (trending vs mean-reverting markets)
- Support/resistance level calculation (Fibonacci, pivot points)

### 🌐 Platform Expansion

**Multi-Asset Support:**
- Forex pairs (EUR/USD, GBP/USD, etc.)
- Crypto (BTC, ETH via Coinbase/Binance API)
- Futures (ES, NQ, CL)
- International equities (FTSE, DAX, Nikkei)

**Broker Integration:**
- TD Ameritrade API (auto-execute signals)
- Interactive Brokers TWS (advanced order types)
- Robinhood (retail integration)
- Paper trading sandbox for testing

**Mobile Applications:**
- React Native app (iOS + Android)
- Push notification alerts for signals
- Voice commands (Siri/Google Assistant integration)
- Apple Watch complications

**Cloud Deployment:**
- AWS/GCP serverless architecture
- Auto-scaling for multiple users
- Subscription tiers (free, premium, professional)
- API marketplace (sell signals to other traders)

### 🛡️ Risk Management Features

**Position Sizing Calculator:**
- Kelly Criterion optimization
- Risk-per-trade percentage limits
- Account drawdown protection
- Correlation-based exposure limits

**Stop-Loss & Take-Profit:**
- Automatic level calculation based on ATR
- Trailing stops (percentage or ATR-based)
- Time-based exits (close EOD, max holding period)
- Profit target laddering (scale out at 1R, 2R, 3R)

**Portfolio Analytics:**
- Multi-strategy performance tracking
- Beta/alpha calculation vs SPY
- Correlation matrix (avoid over-concentration)
- Tax loss harvesting suggestions

### 📚 Educational Content

**Interactive Tutorials:**
- Guided tours for new users
- Video explanations of each indicator
- Quiz system to test understanding
- Strategy backtesting playground

**Documentation Improvements:**
- API documentation with Swagger/OpenAPI
- Video tutorials (YouTube channel)
- Community Discord server
- Weekly strategy webinars

### 🔐 Security & Compliance

**Enterprise Features:**
- Multi-user authentication (OAuth2, SSO)
- Role-based access control (admin, trader, viewer)
- Audit logging (all trades/signals tracked)
- GDPR compliance for EU users
- SOC 2 Type II certification for enterprise sales

### 🚀 Deployment & DevOps

**CI/CD Pipeline:**
- GitHub Actions for automated testing
- Docker containerization
- Kubernetes orchestration for scaling
- Blue-green deployments (zero downtime updates)
- Automated rollback on errors

**Monitoring & Observability:**
- Prometheus + Grafana for metrics
- Sentry for error tracking
- Log aggregation (ELK stack or Datadog)
- Uptime monitoring with PagerDuty alerts
- Performance profiling (New Relic, Datadog APM)

---

**Priority Matrix:**

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| TradingView Charts | High | Medium | **P0** (Next Sprint) |
| React Frontend | High | High | **P0** (Next Quarter) |
| WebSocket Updates | High | Low | **P1** |
| Backtesting Engine | High | High | **P1** |
| ML Signal Scoring | High | Very High | **P2** |
| Mobile App | Medium | High | **P2** |
| Broker Integration | Medium | Very High | **P3** |
| Multi-Asset Support | Medium | Medium | **P3** |

**Current Status:** Production-ready signal generation with 68.4% accuracy. Focus is on UI modernization and performance optimization before adding new features.

---

## ⚠️ Disclaimers

- **Not financial advice**: This is educational software for decision support only
- **No guarantees**: Past performance does not indicate future results
- **Market data limitations**: Yahoo Finance has rate limits (~2000/hour) - system auto-throttles to ~1800/hour
- **Use at your own risk**: Always validate signals and manage risk appropriately

## 📚 Additional Documentation

- **[WEB_DASHBOARD_GUIDE.md](WEB_DASHBOARD_GUIDE.md)**: Complete web dashboard reference - features, indicators, API endpoints, troubleshooting
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**: Technical summary of latest features (options data, IV metrics, P/C ratio, GEX)
- **[MARKET_HOURS.md](MARKET_HOURS.md)**: Market hours detection, data freshness, and trading session awareness
- **[RATE_LIMITING.md](RATE_LIMITING.md)**: Detailed guide on API rate limiting, monitoring, and customization
- **[QUICKREF.md](QUICKREF.md)**: Quick reference for common operations
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and data flow diagrams
- **[INSTALL.md](INSTALL.md)**: Installation and troubleshooting guide

## 📝 License

MIT License - Feel free to modify and extend for your own use.

## 🤝 Contributing

This is a personal project, but suggestions for improvements are welcome:
- Better indicator calculations
- Additional bias classification rules
- Improved volatility detection
- Performance optimizations

---

**Remember**: This tool provides decision support. Always:
- Validate signals manually
- Manage position sizing
- Use appropriate risk management
- Understand the strategies you're deploying
