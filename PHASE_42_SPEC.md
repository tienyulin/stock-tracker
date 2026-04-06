# Phase 42: Family Office & Multi-Entity Management

## 概述
支援家庭理財和多重實體管理，讓用戶能夠管理多個家庭成員的資產、公司帳戶和Trust。

## 用戶故事
- 作為家族決策者，我想在一個儀表板看到所有家族成員的資產
- 作為公司財務，我需要管理公司帳戶和個人帳戶分開
- 作為受托人，我想管理 Trust 帳戶並向受益人報告

## 資料模型

### family_members
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| user_id | UUID | 所屬用戶(FK) |
| name | str | 成員姓名 |
| role | enum | ADMIN/VIEWER/MINOR |
| relationship | str | 關係 |
| date_of_birth | date | 生日 |
| created_at | datetime | 建立時間 |

### entities
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| user_id | UUID | 所屬用戶(FK) |
| entity_type | enum | COMPANY/TRUST/PARTNERSHIP/INDIVIDUAL |
| name | str | 實體名稱 |
| registration_number | str | 登記號碼 |
| jurisdiction | str | 司法管轄區 |
| created_at | datetime | 建立時間 |

### entity_members (多對多)
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| entity_id | UUID | 實體(FK) |
| family_member_id | UUID | 成員(FK) |
| role | str | 在實體中的角色 |
| ownership_percentage | float | 所有權比例 |

### entity_accounts
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| entity_id | UUID | 實體(FK) |
| account_type | enum | BROKERAGE/BANK/CRYPTO/OTHER |
| institution | str | 金融機構 |
| account_number_masked | str | 帳號(遮罩) |
| current_value | Decimal | 目前市值 |

## API Endpoints

### family_members
- `GET /api/v1/family/members` - 取得家庭成員列表
- `POST /api/v1/family/members` - 新增家庭成員
- `GET /api/v1/family/members/{id}` - 取得成員詳情
- `PUT /api/v1/family/members/{id}` - 更新成員
- `DELETE /api/v1/family/members/{id}` - 刪除成員

### entities
- `GET /api/v1/family/entities` - 取得實體列表
- `POST /api/v1/family/entities` - 新增實體
- `GET /api/v1/family/entities/{id}` - 取得實體詳情
- `PUT /api/v1/family/entities/{id}` - 更新實體
- `DELETE /api/v1/family/entities/{id}` - 刪除實體

### entity_accounts
- `GET /api/v1/family/entities/{entity_id}/accounts` - 取得帳戶列表
- `POST /api/v1/family/entities/{entity_id}/accounts` - 新增帳戶
- `PUT /api/v1/family/accounts/{id}` - 更新帳戶
- `DELETE /api/v1/family/accounts/{id}` - 刪除帳戶

### analytics
- `GET /api/v1/family/analytics/overview` - 家族整體概覽
- `GET /api/v1/family/analytics/net-worth` - 跨實體淨資產

## 前端頁面

### 家庭總覽 (FamilyDashboard)
- 家庭成員列表卡片
- 各實體淨資產概覽
- 跨實體配置圖表

### 多實體設定 (EntitiesSettings)
- 實體 CRUD
- 成員-實體關聯管理
- 權限設定

## 驗收標準
- [ ] 可新增家庭成員
- [ ] 可新增實體(COMPANY/TRUST/PARTNERSHIP)
- [ ] 各實體資料隔離
- [ ] 跨實體報表正確
- [ ] 權限控制正常(ADMIN/VIEWER/MINOR)
