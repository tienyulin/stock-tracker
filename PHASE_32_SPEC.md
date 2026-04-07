# Phase 32: Crypto Portfolio Integration (DeFi + CEX) — SPEC

## Overview
将加密货币投资组合整合进 Stock Tracker，支持中心化交易所（CEX）和去中心化金融（DeFi）钱包，成为真正的全资产管理平台。

## Target State
- 🔄 `CryptoWallet` model — 链上钱包余额追踪
- 🔄 `DefiPosition` model — DeFi 仓位移除、Staking、LP
- 🔄 `CexAccount` model — CEX API 密钥管理
- 🔄 `CryptoService` — 价格同步、持仓计算
- 🔄 `DefiService` — DeFi 仓位与收益计算
- 🔄 API: `/api/v1/crypto/*`
- 🔄 Frontend: `CryptoDashboard`

## Data Models

### CryptoWallet
```
- id, user_id, name, blockchain (ethereum/bsc/polygon/solana)
- address, balance, usd_value, notes
```

### DefiPosition
```
- id, user_id, wallet_id, protocol_name, position_type (lp/staking/lending)
- token_symbol, token_address, quantity, entry_price
- current_price, current_value, pnl, pnl_percentage
- apy, rewards_token, estimated_rewards
```

### CexAccount
```
- id, user_id, exchange (coinbase/binance/kraken), api_key_encrypted
- api_secret_encrypted, label, is_active, last_sync_at
```

### CryptoPrice (cache table)
```
- symbol, price_usd, market_cap, volume_24h, price_change_24h
- last_updated
```

## Services

### CryptoService
- `get_wallet_balance()` — 通过 Etherscan API 获取 ETH/ERC20 余额
- `sync_portfolio_prices()` — CoinGecko 价格同步
- `get_portfolio_summary()` — 总览（CEX + DeFi + 钱包）
- `calculate_pnl()` — 损益计算

### DefiService
- `get_defi_positions()` — 从钱包地址读取 DeFi 仓位
- `calculate_apy_rewards()` — APY 收益计算
- `get_liquidity_pool_value()` — LP 池子价值

## API Endpoints
- `GET /api/v1/crypto/wallets` — 钱包列表
- `POST /api/v1/crypto/wallets` — 新增钱包
- `DELETE /api/v1/crypto/wallets/{id}` — 删除钱包
- `GET /api/v1/crypto/defi-positions` — DeFi 仓位移除
- `POST /api/v1/crypto/defi-positions` — 新增 DeFi 仓位
- `GET /api/v1/crypto/cex-accounts` — CEX 账户列表
- `POST /api/v1/crypto/cex-accounts` — 添加 CEX 账户
- `GET /api/v1/crypto/summary` — 总加密资产总览

## Acceptance Criteria
- [ ] 用户可新增钱包地址
- [ ] ETH 钱包余额同步（Etherscan）
- [ ] DeFi 仓位移除可用
- [ ] CoinGecko 价格实时更新
- [ ] 加密资产总和在仪表板显示
- [ ] 单元测试覆盖
