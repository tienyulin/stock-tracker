# Stock Tracker API Architecture

## Overview

FastAPI backend with PostgreSQL database for the Stock Tracking System.

## Technology Stack

- **Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL + SQLAlchemy 2.0 (async)
- **ORM:** SQLAlchemy with async support
- **Validation:** Pydantic v2
- **Migration:** Alembic

## Database Schema

### Tables

```
users
├── id (UUID, PK)
├── username (VARCHAR, unique)
├── email (VARCHAR, unique)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

watchlists
├── id (UUID, PK)
├── user_id (UUID, FK → users.id)
├── name (VARCHAR)
├── is_default (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

watchlist_items
├── id (UUID, PK)
├── watchlist_id (UUID, FK → watchlists.id)
├── symbol (VARCHAR) — e.g., "AAPL", "2330.TW"
├── added_at (TIMESTAMP)
└── notes (TEXT, nullable)

alerts
├── id (UUID, PK)
├── user_id (UUID, FK → users.id)
├── symbol (VARCHAR)
├── condition_type (ENUM: 'above', 'below', 'change_pct')
├── threshold (DECIMAL)
├── is_active (BOOLEAN)
├── triggered_at (TIMESTAMP, nullable)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

alert_notifications
├── id (UUID, PK)
├── alert_id (UUID, FK → alerts.id)
├── channel (ENUM: 'telegram', 'email', 'push')
├── status (ENUM: 'pending', 'sent', 'failed')
├── sent_at (TIMESTAMP, nullable)
└── error_message (TEXT, nullable)
```

## API Endpoints

### Stocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stocks/{symbol}/quote` | Get real-time quote |
| GET | `/api/v1/stocks/{symbol}/history` | Get historical data |
| GET | `/api/v1/stocks/search?q={query}` | Search symbols |
| GET | `/api/v1/stocks/{symbol}/info` | Get company info |

### Watchlists

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/watchlists` | List user's watchlists |
| POST | `/api/v1/watchlists` | Create watchlist |
| GET | `/api/v1/watchlists/{id}` | Get watchlist with items |
| PUT | `/api/v1/watchlists/{id}` | Update watchlist |
| DELETE | `/api/v1/watchlists/{id}` | Delete watchlist |
| POST | `/api/v1/watchlists/{id}/items` | Add stock to watchlist |
| DELETE | `/api/v1/watchlists/{id}/items/{item_id}` | Remove stock |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/alerts` | List user's alerts |
| POST | `/api/v1/alerts` | Create alert |
| GET | `/api/v1/alerts/{id}` | Get alert details |
| PUT | `/api/v1/alerts/{id}` | Update alert |
| DELETE | `/api/v1/alerts/{id}` | Delete alert |
| POST | `/api/v1/alerts/{id}/trigger` | Manually trigger alert |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── router.py          # Main router
│       ├── stocks.py           # Stock endpoints
│       ├── watchlists.py       # Watchlist endpoints
│       └── alerts.py           # Alert endpoints
├── core/
│   ├── __init__.py
│   ├── config.py              # Settings
│   ├── database.py            # Async SQLAlchemy
│   └── security.py            # Auth utilities
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── watchlist.py
│   └── alert.py
├── schemas/
│   ├── __init__.py
│   ├── stock.py
│   ├── watchlist.py
│   └── alert.py
├── services/
│   ├── __init__.py
│   ├── yfinance_service.py    # Existing
│   ├── stock_service.py       # Existing
│   ├── watchlist_service.py   # Existing
│   └── alert_service.py       # Existing
├── __init__.py
└── main.py                    # Existing
migrations/                    # Alembic
tests/
├── __init__.py
├── conftest.py
├── api/
│   └── v1/
│       ├── test_stocks.py
│       ├── test_watchlists.py
│       └── test_alerts.py
└── services/
    └── test_*.py
```

## Implementation Order

1. **Database Setup** — PostgreSQL + Alembic migrations
2. **Models** — SQLAlchemy models for all tables
3. **Core Config** — Environment-based settings
4. **Stock API** — Connect existing yfinance_service to routes
5. **Watchlist API** — Full CRUD with DB persistence
6. **Alert API** — CRUD + background task for checking
7. **Authentication** — Simple API key auth (optional)

## Example API Usage

### Create Watchlist
```bash
POST /api/v1/watchlists
{
  "name": "Tech Stocks",
  "is_default": true
}
```

### Add to Watchlist
```bash
POST /api/v1/watchlists/{id}/items
{
  "symbol": "AAPL"
}
```

### Create Alert
```bash
POST /api/v1/alerts
{
  "symbol": "AAPL",
  "condition_type": "above",
  "threshold": 200.00
}
```

### Get Quote
```bash
GET /api/v1/stocks/AAPL/quote
```
