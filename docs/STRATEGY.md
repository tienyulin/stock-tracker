# Business Strategy - Stock Tracker

**Version:** 0.1 (Draft)
**Author:** Hermes (CSO/PM)
**Date:** 2026-03-30
**Status:** COMPLETE

---

## 1. Competitive Analysis

### Direct Competitors (Taiwan Market)

| Platform | Strengths | Weaknesses |
|----------|-----------|-------------|
| **CMoney 股市爆料同學會** | Social sentiment, mobile-first, large user base | No advanced technical indicators, cluttered UI |
| **Goodinfo** | Comprehensive fundamental data, free | Old-school UI, overwhelming for beginners |
| **Invest 2000** | Good for US stocks, clean interface | Weak Taiwan stock coverage |
| **XQ 全球贏家** | Professional-grade charting, API access | Expensive subscription (~$50/month), complex for casual users |
| **Mitrade** | CFD trading integration, copy trading | Not pure analytics, conflicts of interest |

### Indirect Competitors

| Platform | Strengths | Weaknesses |
|----------|-----------|-------------|
| **TradingView** | Best-in-class charting, global reach | Taiwan stocks limited, no local notifications |
| **Yahoo Finance** | Free, familiar, basic alerts | No Taiwan-specific features, limited watchlist |
| **券商自行開發 App** | Direct trading integration | Only shows their products, no cross-broker view |

### Opportunity Gap

**痛點發現：**
1. 台灣散戶投資人缺乏**整合性**的工具：要看技術分析要去一個網站、設警語要去另一個、常見的是用 Excel 自己追
2. 現有工具**太複雜**（XQ）或有**廣告/推薦干擾**（CMoney）
3. **個性化體驗**匱乏——沒有一個乾淨、專為台灣人設計的工具

---

## 2. Differentiation

### 我們的核心差異

| 維度 | 一般工具 | 我們 |
|------|---------|------|
| **定位** | 資訊太多、太雜 | 乾淨、專注、重點突出 |
| **技術分析** | 有但陽春 | 視覺化、互動式、友善呈現 |
| **個人化** | 薄弱 | Watchlist + Alerts + 最後買入價追蹤 |
| **台灣市場** | 附加功能 | 第一優先 |
| **體驗** | 廣告干擾 | 純淨、無干擾 |

### 產品定位語

> **"台灣人自己的股票儀表板"**
> Clean. Focused. Built for TW investors.

---

## 3. Revenue Model

### 選項分析

#### Option A: Freemium Subscription
**Model:** Basic free, Premium paid (~$15-25/month)

| Tier | Features | Price |
|------|----------|-------|
| Free | Watchlist (5 stocks), Basic alerts (2), 20-min price delay | $0 |
| Pro | Unlimited watchlist, Unlimited alerts, Real-time prices, No ads | ~$15/mo |
| Pro+ | All Pro + Advanced indicators, Export data, API access | ~$25/mo |

**Pros:** Recurring revenue, familiar model
**Cons:** 需要真實時價格數據來源（可能需要花費）

#### Option B: Transaction Cut
**Model:** Partner with brokers, get commission on trades executed through app

**Pros:** No user friction, aligned incentives
**Cons:** 需要執照、監管複雜、利益衝突問題

#### Option C: Affiliate / Data Revenue
**Model:** Premium market data subscriptions,券商廣告分潤

**Pros:** Low friction, existing infrastructure
**Cons:** 營收規模有限

#### Option D: Freemium + Transaction Cut (Hybrid) ← 建議

**Free:** 基礎功能
**Pro:** 去除廣告 + 即時報價 + 更多監控
**Broker partnership:** 交易時收取少量佣金（用戶不需額外付費）

**理由：**
- Freemium 讓用戶先體驗，降低進入壁壘
- Pro 費用覆蓋數據成本
- Transaction cut 提供被動收入，適合長期

### 初期貨幣化策略（0-6 months）

**Phase 1 (Now):** 專注用戶成長，不收費
**Phase 2 (6-12 months):** 加入 Freemium，驗證轉化率
**Phase 3 (12+ months):** 加入券商合作

---

## 4. Go-to-Market Strategy

### 初期取得用戶

1. **PTT Stock 版推廣** — 免費，精准TA
2. **Facebook 投資社團** — 分享有價值的分析圖表
3. **Product Hunt** — 如果有英文版
4. **口碑推薦** — 鼓勵用戶分享 watchlist 功能

### 初期用戶畫像

**Primary:** 25-40歲，投資經驗1-5年，用 Excel 或券商App追蹤個股
**Secondary:** 經驗投資人，想要更乾淨的工具取代現有方案

---

## 5. Risk Analysis

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 即時報價數據成本過高 | High | 一開始用 20-min delay，驗證付費意願後再升級 |
| 大型券商競爭（XQ） | Medium | 差異化在 UX 和簡單性，不跟他們比功能深度 |
| 用戶不願意付費 | Medium | 先做免費版，收集數據再決定定價 |
| 法規（槓桿/交易勸誘） | Low | 目前不做交易功能，避開監管 |

---

## 6. 90-Day Action Plan

### Month 1 (April): Foundation
- [ ] Complete Phase 2 (Technical Indicators merge)
- [ ] Launch Watchlist MVP
- [ ] 收集 100 個測試用戶

### Month 2 (May): Alerts + Growth
- [ ] Launch Price Alerts MVP
- [ ] 建立用戶回饋機制
- [ ] 社群推廣（PPT/FB）

### Month 3 (June): Iterate + Monetization Prep
- [ ] 根據回饋改善 UX
- [ ] 設計付費牆方案
- [ ] A/B test 定價

---

## 7. Open Questions

1. **數據來源？** — 如何取得便宜/免費的台灣股票數據？
2. **認證執照？** — 如果要做交易功能，需要那些執照？
3. **首要成功指標？** — DAU？付費用戶數？營收？

---

## 8. Data Source Recommendation

**Immediate (Free, 20-min delay):**
- TWSE/TPEx official APIs ( delays ~20 minutes)
- Reference: Goodinfo uses these

**Medium-term (Cheap):**
- Finage (~$30/mo for Taiwan stocks)
- Twelvedata (volume-based pricing)

**Long-term (If paid users):**
- XQ direct API (professional grade, ~$50/mo)
- Or partner with broker for real-time

---

*Last updated: 2026-03-30 by Hermes*
