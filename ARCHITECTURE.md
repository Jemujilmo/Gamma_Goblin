# Market Copilot - System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Market Copilot System                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          USER LAYER                             │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ market_copilot │  │  examples.py   │  │  Custom Scripts │  │
│  │     .py        │  │                │  │                 │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MarketCopilot Class                         │  │
│  │  - Manages data flow                                     │  │
│  │  - Coordinates analysis pipeline                         │  │
│  │  - Formats output                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   DATA LAYER    │  │ ANALYSIS LAYER  │  │  OUTPUT LAYER   │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              data_fetcher.py                             │  │
│  │                                                          │  │
│  │  ┌─────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │  DataFetcher    │  │  YahooFinanceDataFetcher     │  │  │
│  │  │  (Abstract)     │  │  - fetch_data()              │  │  │
│  │  └─────────────────┘  │  - Returns OHLCV DataFrame   │  │  │
│  │                       └──────────────────────────────┘  │  │
│  │                                                          │  │
│  │  Future: AlphaVantageDataFetcher, PolygonDataFetcher    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ANALYSIS LAYER                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              indicators.py                               │  │
│  │  - calculate_ema()                                       │  │
│  │  - calculate_rsi()                                       │  │
│  │  - calculate_atr()                                       │  │
│  │  - calculate_vwap()                                      │  │
│  │  - detect_volatility_regime()                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          bias_classifier.py                              │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         BiasClassifier                             │  │  │
│  │  │  - classify_bias()                                 │  │  │
│  │  │    • Price vs VWAP                                 │  │  │
│  │  │    • EMA9 vs EMA21                                 │  │  │
│  │  │    • RSI regime                                    │  │  │
│  │  │  - Returns: (Bias, Confidence, Notes)              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          signal_generator.py                             │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         SignalGenerator                            │  │  │
│  │  │  - generate_signal()                               │  │  │
│  │  │  - generate_multi_timeframe_signal()               │  │  │
│  │  │  - _synthesize_signals()                           │  │  │
│  │  │  - _generate_recommendations()                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              config.py                                   │  │
│  │  - DEFAULT_TICKER = "SPY"                                │  │
│  │  - TIMEFRAMES = {"short": "5m", "medium": "15m"}         │  │
│  │  - INDICATORS = {ema_fast: 9, ema_slow: 21, ...}         │  │
│  │  - BIAS_THRESHOLDS = {rsi_bullish: 55, ...}              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW DIAGRAM                         │
└─────────────────────────────────────────────────────────────────┘

1. USER calls MarketCopilot.analyze()
          │
          ▼
2. For each timeframe (5m, 15m):
   ┌──────────────────────────────────────────────┐
   │ a. DataFetcher.fetch_data()                  │
   │    → Returns OHLCV DataFrame                 │
   │                                              │
   │ b. calculate_all_indicators()                │
   │    → Adds EMA, RSI, ATR, VWAP columns        │
   │                                              │
   │ c. BiasClassifier.classify_bias()            │
   │    → Returns (Bias, Confidence, Notes)       │
   │                                              │
   │ d. detect_volatility_regime()                │
   │    → Returns regime (Expansion/Compression)  │
   │                                              │
   │ e. SignalGenerator.generate_signal()         │
   │    → Creates structured signal dict          │
   └──────────────────────────────────────────────┘
          │
          ▼
3. SignalGenerator.generate_multi_timeframe_signal()
   ┌──────────────────────────────────────────────┐
   │ - Combines all timeframe signals             │
   │ - Synthesizes overall bias                   │
   │ - Generates recommendations                  │
   └──────────────────────────────────────────────┘
          │
          ▼
4. OUTPUT:
   ┌──────────────────────────────────────────────┐
   │ {                                            │
   │   "ticker": "SPY",                           │
   │   "timeframes": {                            │
   │     "5m": {...},                             │
   │     "15m": {...}                             │
   │   },                                         │
   │   "synthesis": {                             │
   │     "overall_bias": "Bullish",               │
   │     "recommendations": [...]                 │
   │   }                                          │
   │ }                                            │
   └──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     EXTENSIBILITY POINTS                        │
└─────────────────────────────────────────────────────────────────┘

1. DATA SOURCES (data_fetcher.py)
   - Add new DataFetcher subclasses
   - Update get_data_fetcher() factory

2. INDICATORS (indicators.py)
   - Add new calculation functions
   - Update calculate_all_indicators()

3. BIAS LOGIC (bias_classifier.py)
   - Modify classification rules
   - Add new condition checks
   - Adjust thresholds

4. TIMEFRAMES (config.py)
   - Add more timeframes to TIMEFRAMES dict
   - System automatically processes all

5. RECOMMENDATIONS (signal_generator.py)
   - Customize _generate_recommendations()
   - Add options-specific logic
   - Include IV metrics

6. OUTPUT FORMATS
   - Add export_to_csv()
   - Add export_to_database()
   - Create dashboard/UI layer

┌─────────────────────────────────────────────────────────────────┐
│                      FUTURE ENHANCEMENTS                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   ALERTS        │  │  OPTIONS DATA   │  │  BACKTESTING    │
│                 │  │                 │  │                 │
│ - Discord       │  │ - IV Rank       │  │ - Historical    │
│ - Telegram      │  │ - IV Percentile │  │   signals       │
│ - Email         │  │ - Put/Call      │  │ - Performance   │
│ - SMS           │  │ - Greeks        │  │   metrics       │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   DASHBOARD     │  │  MORE TICKERS   │  │  ADVANCED       │
│                 │  │                 │  │  INDICATORS     │
│ - Terminal UI   │  │ - QQQ           │  │                 │
│ - Web API       │  │ - IWM           │  │ - MACD          │
│                 │  │ - Sector ETFs   │  │ - Bollinger     │
│                 │  │ - Custom lists  │  │ - Volume Profile│
└─────────────────┘  └─────────────────┘  └─────────────────┘
