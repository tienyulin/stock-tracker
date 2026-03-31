import { describe, it, expect } from 'vitest'

// This test verifies the API base URL is correctly configured
// The VITE_API_BASE_URL must include /api/v1 suffix for backend calls to work
describe('API Configuration', () => {
  it('should have API_BASE_URL ending with /api/v1', () => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string
    expect(apiBaseUrl).toBeDefined()
    expect(apiBaseUrl).toMatch(/\/api\/v1$/)
  })

  it('should have a valid backend URL', () => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string
    expect(apiBaseUrl).toMatch(/^https?:\/\/.+/)
  })
})
