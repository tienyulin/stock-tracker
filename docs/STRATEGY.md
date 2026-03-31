# Stock Tracker - Strategy Document

**Last Updated:** 2026-03-31

---

## 🎯 Product Vision

A **free, real-time stock tracking platform** for retail investors in Taiwan, with:
- US stocks (NYSE/NASDAQ) with live prices
- Taiwan stocks (TWSE) with 20-min delay
- Technical analysis tools (RSI, MACD, MA)
- Personalized watchlists and price alerts

**Target Users:** Retail investors in Taiwan who want a simple, free tool to track their portfolio.

---

## 📍 Current Status

### Deployed ✅
- Frontend: https://frontend-rouge-one-20.vercel.app
- Backend: https://stock-tracker-api-5ht7.onrender.com
- Phase 1, 2, 3 features complete

### Pending
- DNS configuration (stock-tracker.tienyulin.com)
- Full user auth flow testing
- LINE alert integration

---

## 🗺️ Roadmap

### Phase 4: Polish & Growth (Current)
1. **P0:** Full feature testing on live deployment
2. **P1:** LINE notification integration for alerts
3. **P1:** User auth complete flow (login/logout UI)
4. **P2:** PWA/mobile optimizations

### Phase 5: Scale (Future)
1. Add more TWSE stocks
2. Improve chart interactions
3. Export watchlist to PDF/CSV

---

## 💰 Monetization (Future Considerations)

| Option | Notes |
|--------|-------|
| Freemium model | Basic free, premium features paid |
| Affiliate | Stock broker referrals |
| Premium alerts | Push notifications via LINE |

*Decision pending - focus on user growth first.*

---

## 📊 Success Metrics (Track when DNS ready)

| Metric | 30-day Target |
|--------|--------------|
| Unique visitors | 100 |
| Registered users | 20 |
| Watchlists created | 30 |
| Alerts triggered | 50 |

---

## 🔬 Technical Decisions

### Why these providers?
| Provider | Reason |
|----------|--------|
| Vercel | Free via GitHub Student Pack |
| Render | Free tier, FastAPI compatible |
| Neon | Free PostgreSQL |
| Upstash | Free serverless Redis |

### Future considerations
- Move to Vercel Postgres if Neon issues
- Consider Railway if Render sleep issues persist
