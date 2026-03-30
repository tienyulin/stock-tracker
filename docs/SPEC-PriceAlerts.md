# SPEC: Price Alerts Feature

**Version:** 0.1 (Draft)
**Author:** Hermes (CSO/PM)
**Date:** 2026-03-30
**Status:** COMPLETE
**Owner:** Hermes (spec) + Athena (development)

---

## 1. Overview

**What:** Users set price conditions (above/below threshold) and receive notifications when met.

**Why:** Investors want automated alerts for target prices without constantly monitoring.

**User:** Active retail investor in Taiwan market

---

## 2. User Stories

### US-1: Create Price Alert
**As a** logged-in user  
**I want to** set an alert when a stock price crosses a threshold  
**So that** I get notified to act

**Acceptance:**
- From stock detail page, tap "Set Alert"
- Choose condition: "Above" or "Below"
- Enter target price
- Optional: Set expiration date (default: 30 days)
- Save → Toast "Alert set for 2330 above 900"
- Duplicate alert shows error "Alert already exists"

### US-2: Receive Alert Notification
**As a** user with an active alert  
**I want to** receive a notification when the price condition is met  
**So that** I can act on investment decisions

**Acceptance:**
- Notification via browser push (if enabled) OR in-app notification
- Notification shows: symbol, condition, current price, target price
- Tap notification → goes to stock detail page
- Alert auto-disables after triggering (can re-enable manually)

### US-3: View & Manage Alerts
**As a** logged-in user  
**I want to** see all my active and past alerts  
**So that** I can manage them

**Acceptance:**
- "Alerts" page/section lists all alerts
- Status badges: Active ✅, Triggered 🔔, Expired ⏰, Paused ⏸
- Each alert shows: symbol, condition, target price, current price, created date
- Swipe/button to delete alert
- Toggle to pause/resume alert

### US-4: Delete Alert
**As a** logged-in user  
**I want to** delete an alert  
**So that** I stop receiving notifications for it

**Acceptance:**
- Delete button on each alert row
- Confirmation: "Delete this alert?"
- Immediate removal, no undo needed

---

## 3. Technical Approach

### Backend (FastAPI)

**Database Schema:**
```sql
CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    condition VARCHAR(10) NOT NULL, -- 'above' or 'below'
    target_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'triggered', 'expired', 'paused'
    triggered_at TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_user ON price_alerts(user_id);
CREATE INDEX idx_alerts_status ON price_alerts(status);
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | List all alerts for current user |
| POST | `/api/alerts` | Create alert `{ "symbol": "2330.TW", "condition": "above", "target_price": 900 }` |
| PATCH | `/api/alerts/{id}` | Update alert status (pause/resume) |
| DELETE | `/api/alerts/{id}` | Delete alert |
| POST | `/api/alerts/{id}/trigger` | (Internal) Called by scheduler when price crosses |

**Alert Check Logic (Background Job):**
```
Every 5 minutes:
  FOR each active alert:
    current_price = fetch_price(alert.symbol)
    IF (alert.condition == 'above' AND current_price >= alert.target_price)
        OR (alert.condition == 'below' AND current_price <= alert.target_price):
      trigger_alert(alert)
```

**Notification:**
- Store notification in DB with user_id, message, alert_id, read_at
- Push via WebSocket or polling (in-app)
- Browser push via Web Push API (optional, Phase 2)

### Frontend (React)

**Components:**
- `AlertBadge` — shows alert icon on stock card/detail
- `AlertDialog` — modal to create/edit alert
- `AlertList` — paginated list of user's alerts
- `AlertItem` — individual alert row with status, toggle, delete
- `NotificationToast` — in-app popup when alert triggers

**Pages:**
- `/alerts` — full alert management page
- Alert creation integrated into stock detail page

---

## 4. Alert Trigger Flow

```
[User sets alert]
     ↓
[Background scheduler runs every 5 min]
     ↓
[Fetch current price for each active alert's symbol]
     ↓
[Compare: condition met?]
     ↓ YES
[Update alert status to 'triggered']
[Create notification record in DB]
[Send push/in-app notification]
[Optional: send LINE/email if configured]
```

---

## 5. Design Notes

- **Desktop:** Alerts icon in nav bar with badge count, dropdown panel
- **Mobile:** Bottom sheet for alert list
- **Triggered alert:** Highlighted with 🔔, sorted to top
- **Price display:** Show both target and current price for context

---

## 6. Out of Scope (MVP)

- LINE push notification integration
- Email notification
- Alert sound customization
- Alert groups / templates
- SMS alerts
- Browser push (Phase 2)

---

## 7. Dependencies

- Phase 1 auth system (user accounts)
- Stock price API (existing)
- Watchlist feature (alerts can be set from watchlist too)
- Redis for caching alert checks (optional optimization)

---

## 8. Priority

**P0** — MVP: Create alert, in-app notification, view/delete alerts
**P1** — Pause/resume, alert history, triggered alerts sorting
**P2** — Browser push, LINE integration

---

**Note:** This feature has been implemented by Athena (PR #11 merged 2026-03-29).
This spec serves as documentation and validation.
