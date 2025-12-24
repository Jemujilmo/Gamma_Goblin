# Rate Limiting - Visual Guide

## Timeline Diagram

```
Without Rate Limiting (Risk of hitting API limits):
═══════════════════════════════════════════════════════

Request 1 ━━━┫
Request 2 ━━━━━━┫
Request 3 ━━━┫
Request 4 ━━━━┫
Request 5 ━━━┫
...
Request 2000 ━━━┫
Request 2001 ━━━┫  ❌ RATE LIMITED BY YAHOO
═══════════════════════════════════════════════════════
         Too fast! Could hit 2000/hour limit


With Rate Limiting (Safe operation):
═══════════════════════════════════════════════════════

Request 1 ━━━┫........wait 2s........┫
Request 2              ━━━━━━┫........wait 2s........┫
Request 3                       ━━━┫........wait 2s........┫
Request 4                                  ━━━━┫
...
═══════════════════════════════════════════════════════
    2s delay enforced     =     ~1800 requests/hour
                          ✅ Safely under 2000/hour limit
```

## Request Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│         User calls copilot.analyze()                │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   For each timeframe (5m, 15m):                     │
│                                                      │
│   ┌──────────────────────────────────────────┐     │
│   │  Call: data_fetcher.fetch_data()         │     │
│   └──────────────────────────────────────────┘     │
│                       │                              │
│                       ▼                              │
│   ┌──────────────────────────────────────────┐     │
│   │  RATE LIMITING CHECK                     │     │
│   │                                          │     │
│   │  1. Check time since last request        │     │
│   │                                          │     │
│   │  2. If < 2 seconds:                      │     │
│   │     └─> Sleep for remaining time         │     │
│   │                                          │     │
│   │  3. Update request counter               │     │
│   │                                          │     │
│   │  4. Update last request timestamp        │     │
│   └──────────────────────────────────────────┘     │
│                       │                              │
│                       ▼                              │
│   ┌──────────────────────────────────────────┐     │
│   │  Make Yahoo Finance API Call             │     │
│   └──────────────────────────────────────────┘     │
│                       │                              │
│                       ▼                              │
│   ┌──────────────────────────────────────────┐     │
│   │  Return OHLCV data                       │     │
│   └──────────────────────────────────────────┘     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Class-Level State Tracking

```
┌────────────────────────────────────────────────────────┐
│  YahooFinanceDataFetcher Class Variables               │
│  (Shared across all instances)                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  _last_request_time:  1703346120.5  (Unix timestamp)   │
│  _request_count:      47             (this hour)        │
│  _hour_start_time:    1703343600.0   (hour began)      │
│                                                         │
└────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌─────────┐        ┌─────────┐       ┌─────────┐
    │Instance1│        │Instance2│       │Instance3│
    │copilot1 │        │copilot2 │       │copilot3 │
    └─────────┘        └─────────┘       └─────────┘
    
All instances share the same rate limit tracking!
This prevents bypassing limits by creating multiple objects.
```

## Hourly Reset Mechanism

```
Hour 1: 10:00 AM - 11:00 AM
═══════════════════════════════════════════════════════
  
  10:00:00  ┌── Hour starts (_hour_start_time = now)
            │   _request_count = 0
            │
  10:00:02  ├── Request 1 (_request_count = 1)
  10:00:04  ├── Request 2 (_request_count = 2)
  10:00:06  ├── Request 3 (_request_count = 3)
            │   ... more requests ...
  10:59:58  ├── Request 1799 (_request_count = 1799)
            │
  11:00:00  └── Hour elapsed >= 3600 seconds
            
Hour 2: 11:00 AM - 12:00 PM
═══════════════════════════════════════════════════════
            
  11:00:00  ┌── RESET! (_hour_start_time = now)
            │          (_request_count = 0)
            │
  11:00:02  ├── Request 1 (_request_count = 1)
  11:00:04  ├── Request 2 (_request_count = 2)
            │   ... cycle repeats ...
```

## Multi-Instance Safety

```
Scenario: Running multiple analysis scripts simultaneously

Script 1:                    Script 2:
┌──────────────┐            ┌──────────────┐
│ copilot1 =   │            │ copilot2 =   │
│ MarketCopilot│            │ MarketCopilot│
│   ()         │            │   ()         │
└──────────────┘            └──────────────┘
        │                           │
        ▼                           ▼
    Request at                  Request at
    10:00:00                    10:00:01
        │                           │
        └───────────┬───────────────┘
                    ▼
        ┌───────────────────────┐
        │  Shared Class State   │
        │  _last_request_time   │
        └───────────────────────┘
                    │
                    ▼
            Script 2 must wait!
            (Only 1 second since last request,
             needs to wait 1 more second)

Result: Even with multiple scripts/instances,
        rate limiting is enforced globally.
```

## Configuration Impact

```
REQUEST_DELAY = 2.0 seconds
═══════════════════════════════════════════════════════

Requests per minute:  30 (60s / 2s)
Requests per hour:    1800 (3600s / 2s)
Safety margin:        200 requests under limit

Multi-timeframe impact (2 timeframes):
  - 2 API calls per analysis
  - ~4 seconds total per analysis
  - ~450 analyses per hour possible


REQUEST_DELAY = 3.0 seconds
═══════════════════════════════════════════════════════

Requests per minute:  20 (60s / 3s)
Requests per hour:    1200 (3600s / 3s)
Safety margin:        800 requests under limit

Multi-timeframe impact (2 timeframes):
  - 2 API calls per analysis
  - ~6 seconds total per analysis
  - ~300 analyses per hour possible


REQUEST_DELAY = 1.0 seconds (⚠️ RISKY)
═══════════════════════════════════════════════════════

Requests per minute:  60 (60s / 1s)
Requests per hour:    3600 (3600s / 1s)
Safety margin:        -1600 requests OVER limit ❌

⚠️  HIGH RISK OF RATE LIMITING!
```

## Real-World Usage Pattern

```
Typical live monitoring setup:
═══════════════════════════════════════════════════════

┌────────────────────────────────────────────────────┐
│ Run analysis every 5 minutes                       │
│ Each analysis: 2 API requests (5m + 15m data)      │
│ With 2-second delay: ~4 seconds per analysis       │
└────────────────────────────────────────────────────┘

Per hour:
  - 12 analyses (every 5 minutes)
  - 24 API requests total
  - Only 1.3% of hourly limit used! ✅
  
This gives you:
  ✓ Real-time market monitoring
  ✓ Plenty of headroom for manual queries
  ✓ No risk of hitting rate limits
  ✓ Responsive system
```

## Monitoring Dashboard Concept

```
╔════════════════════════════════════════════════════╗
║         API USAGE DASHBOARD                        ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Current Hour Progress:                            ║
║  ▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░ 18% (11 min elapsed)    ║
║                                                    ║
║  Requests Used:       47 / 1800                    ║
║  Usage Rate:          256 req/hour (current)       ║
║  Safety Status:       ✅ SAFE                      ║
║                                                    ║
║  Time Since Last:     23.4 seconds                 ║
║  Next Request:        Ready (no delay needed)      ║
║                                                    ║
║  Projected End-of-Hour:                            ║
║    At current rate:   ~256 requests total          ║
║    Headroom:          1544 requests available      ║
║                                                    ║
╚════════════════════════════════════════════════════╝

(Run: python monitor_requests.py)
```
