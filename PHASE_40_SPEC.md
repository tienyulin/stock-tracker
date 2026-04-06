# Phase 40: Real-Time Market Data & Streaming Alerts — SPEC

## Overview
提供即時市場數據串流和即時價格警報，取代目前 polling 方式，實現真正的即時通知體驗。

## Current State
- ✅ WebSocket endpoint exists (`/ws/stocks/{symbol}`)
- ✅ ConnectionManager handles subscriptions
- ✅ AlertCheckerService (polling-based, 60s interval)
- ✅ CacheService with TTL
- ⚠️  current `_send_periodic_updates` polls every 60s — not truly real-time

## Target State
- 🔄 Replace 60s polling with event-driven streaming
- 🔄 Alert trigger latency < 2 seconds
- ✅ Redis pub/sub for multi-instance scaling
- ✅ Real-time portfolio P&L updates

## Tech Stack
- **Backend:** Python/FastAPI + Redis (Upstash)
- **Streaming:** WebSocket + Redis pub/sub
- **Data Sources:** Yahoo Finance WebSocket / Alpha Vantage / Polygon.io

## Architecture

### Components
1. **StreamingPriceService** — Redis pub/sub publisher for price events
2. **AlertStreamProcessor** — Subscribes to price channel, triggers alerts <2s
3. **PortfolioRealtimeUpdater** — Recalculates P&L on price change

### Redis Channels
- `price:{symbol}` — tick-by-tick price updates
- `alert:{user_id}` — per-user alert notifications

### WebSocket Flow
```
Client → WS /ws/stocks/{symbol} → ConnectionManager
                                   ↓
                              Redis PubSub ← StreamingPriceService
                                   ↓
                           AlertStreamProcessor → notify
```

## Acceptance Criteria
- [ ] WebSocket connects and receives first price < 1s
- [ ] Alert trigger latency < 2 seconds (from price change to notification)
- [ ] Multiple WebSocket instances share state via Redis
- [ ] Alert history recorded in DB
- [ ] Portfolio P&L updates in real-time

## Out of Scope
- Apple Watch / iOS Widget (separate phase)
- Multi-user collaborative features
