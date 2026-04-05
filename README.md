# Stock Tracking System

Track Taiwan and US markets, analyze and manage investments.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React + TypeScript + Vite
- **Database:** PostgreSQL
- **Cache:** Redis
- **Container:** Docker / Docker Compose

## Features

| Feature | Phase | Status |
|---------|-------|--------|
| Stock Quote & History | Phase 1-7 | ✅ |
| Watchlist | Phase 8-10 | ✅ |
| Price Alerts | Phase 11-14 | ✅ |
| Portfolio Management | Phase 15-19 | ✅ |
| AI Buy/Sell Signal | Phase 20-22 | ✅ |
| Custom Alert System | Phase 23 | ✅ |
| Dividend Growth Tracker | Phase 28 | ✅ |

## Quick Start

```bash
# Clone and start all services
docker-compose up -d

# Or for local development
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

### Core
- `GET /api/v1/stocks/{symbol}/quote` — Real-time stock quote
- `GET /api/v1/stocks/{symbol}/history` — Historical price data
- `GET /api/v1/stocks/{symbol}/indicators` — RSI, MACD, SMA, EMA
- `GET /api/v1/stocks/{symbol}/signal` — AI buy/sell signal

### Portfolio
- `GET /api/v1/portfolio` — Holdings with P&L
- `POST /api/v1/portfolio/holdings` — Add holding
- `GET /api/v1/portfolio/signals` — Portfolio-wide AI signals

### Dividends
- `GET /api/v1/dividends/holdings` — Dividend portfolio
- `GET /api/v1/dividends/dashboard` — Dividend summary
- `GET /api/v1/dividends/growth/{symbol}` — Dividend growth analysis
- `GET /api/v1/dividends/calendar` — Upcoming ex-dividend dates

### Alerts
- `GET /api/v1/alerts` — Active price alerts
- `POST /api/v1/alerts` — Create price alert
- `POST /api/v1/alerts/{id}/trigger` — Trigger alert

## Development

```bash
# Create feature branch from develop
git checkout develop
git checkout -b feature/your-feature-name

# Run tests
pytest tests/

# Push and create PR
git push -u origin feature/your-feature-name
```

## Branch Strategy

- `main` — Production code
- `develop` — Integration branch for features
- `feature/*` — New features (branch from develop)
- `fix/*` — Bug fixes
- `chore/*` — Maintenance tasks

## Deployment

- **Backend:** Render (auto-deploy on merge to develop)
- **Frontend:** Vercel (auto-deploy on merge to develop)
- **Database:** PostgreSQL 16

## Project Phases

See [PROJECT_TASKS.md](./PROJECT_TASKS.md) for full phase history.
