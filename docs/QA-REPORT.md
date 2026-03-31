# Stock Tracker - QA 驗證報告

**日期：** 2026-03-31
**測試環境：** https://stock.tienyulin.com
**Backend API：** https://stock-api.tienyulin.com
**驗證人：** Hermes (PM)

---

## 📋 測試結果總覽

| 功能 | 狀態 |
|------|------|
| Dashboard 首頁 | ✅ PASS |
| 搜尋（US 股） | ✅ PASS |
| 搜尋（TWSE 股） | ✅ PASS |
| 公司名稱顯示 | ✅ PASS |
| 技術指標（API） | ✅ PASS |
| 技術指標（前端 RSI） | ❌ FAIL |
| 股票圖表 | ✅ PASS |
| Watchlist 頁面 | ❌ FAIL |
| Alerts 頁面 | ❌ FAIL |

---

## 🐛 Open Issues

| # | 標題 | 優先 | 狀態 |
|---|------|------|------|
| #66 | DB connection - sslmode argument error | High | 🔴 OPEN |
| #65 | Watchlist/Alerts require user_id auth | High | 🔴 OPEN |
| #64 | RSI shows N/A on frontend | Medium | 🔴 OPEN |

## ✅ Fixed Issues

| # | 標題 | 修復者 |
|---|------|--------|
| #62 | Company name shows UNKNOWN | Athena |
| #63 | VITE_API_BASE_URL 指向舊 URL | Athena |
| #49 | DNS 未正確指向 | Tony |

---

## 🔧 待修正

### Issue #66：DB SSL 連線問題
**Render (Production):**
```
TypeError: connect() got an unexpected keyword argument 'sslmode'
```
**Local Docker:**
```
ConnectionError: PostgreSQL server at "db:5432" rejected SSL upgrade
```
**可能原因：** `DATABASE_URL` 包含 `sslmode=require` 但 asyncpg driver 處理方式不同

### Issue #65：Watchlist/Alerts 需要 auth
- Backend 需要 UUID user_id，前端無 login UI
- 需要實作 JWT auth flow

### Issue #64：RSI 前端顯示 N/A
- API 回傳正確（RSI=31.61），但前端顯示 N/A
- 前端 component 解析問題

---

## 📝 更新記錄

| 日期 | 內容 |
|------|------|
| 2026-03-31 | 初始 QA 報告 |
| 2026-03-31 | 加入 Issue #66 DB SSL 問題 |
