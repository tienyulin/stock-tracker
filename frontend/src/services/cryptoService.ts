/**
 * Crypto Portfolio Service — API client for crypto/DeFi endpoints.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface CryptoWallet {
  id: string
  name: string
  blockchain: string
  address: string
  balance: number
  usd_value: number
  notes?: string
}

export interface DefiPosition {
  id: string
  protocol_name: string
  position_type: string
  token_symbol: string
  quantity: number
  entry_price: number
  current_price: number
  current_value: number
  pnl: number
  pnl_percentage: number
  apy?: number
}

export interface CryptoSummary {
  total_crypto_value: number
  wallet_count: number
  defi_position_count: number
}

export const cryptoService = {
  async getWallets(): Promise<CryptoWallet[]> {
    const res = await fetch(`${API_BASE}/api/v1/crypto/wallets`)
    if (!res.ok) throw new Error('Failed to fetch wallets')
    return res.json()
  },

  async createWallet(payload: {
    name: string
    blockchain: string
    address: string
    balance?: number
    notes?: string
  }): Promise<{ id: string }> {
    const params = new URLSearchParams({
      name: payload.name,
      blockchain: payload.blockchain,
      address: payload.address,
      ...(payload.balance !== undefined ? { balance: String(payload.balance) } : {}),
      ...(payload.notes ? { notes: payload.notes } : {}),
    })
    const res = await fetch(`${API_BASE}/api/v1/crypto/wallets?${params}`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to create wallet')
    return res.json()
  },

  async deleteWallet(walletId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/crypto/wallets/${walletId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('Failed to delete wallet')
  },

  async getDefiPositions(): Promise<DefiPosition[]> {
    const res = await fetch(`${API_BASE}/api/v1/crypto/defi-positions`)
    if (!res.ok) throw new Error('Failed to fetch DeFi positions')
    return res.json()
  },

  async createDefiPosition(payload: {
    protocol_name: string
    position_type: string
    token_symbol: string
    quantity: number
    entry_price: number
    wallet_id?: string
    apy?: number
    rewards_token?: string
    notes?: string
  }): Promise<{ id: string }> {
    const params = new URLSearchParams({
      protocol_name: payload.protocol_name,
      position_type: payload.position_type,
      token_symbol: payload.token_symbol,
      quantity: String(payload.quantity),
      entry_price: String(payload.entry_price),
      ...(payload.wallet_id ? { wallet_id: payload.wallet_id } : {}),
      ...(payload.apy !== undefined ? { apy: String(payload.apy) } : {}),
      ...(payload.rewards_token ? { rewards_token: payload.rewards_token } : {}),
      ...(payload.notes ? { notes: payload.notes } : {}),
    })
    const res = await fetch(`${API_BASE}/api/v1/crypto/defi-positions?${params}`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to create DeFi position')
    return res.json()
  },

  async deleteDefiPosition(positionId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/crypto/defi-positions/${positionId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('Failed to delete DeFi position')
  },

  async getSummary(): Promise<CryptoSummary> {
    const res = await fetch(`${API_BASE}/api/v1/crypto/summary`)
    if (!res.ok) throw new Error('Failed to fetch crypto summary')
    return res.json()
  },
}
