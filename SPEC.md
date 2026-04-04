# Phase 19: AI Portfolio Assistant — SPEC

## Overview
An AI-powered chat interface integrated into the dashboard for natural language portfolio Q&A, insights, and personalized recommendations.

## Tech Stack
- **Backend:** Python/FastAPI (NOT Node.js — existing codebase is Python)
- **Frontend:** React/TypeScript (existing frontend)
- **AI:** OpenAI GPT-4o or Claude-3.5 via existing AI integration

## Backend: `POST /api/v1/ai/chat`

### Request
```json
{
  "message": "string",
  "conversation_id": "string (optional)"
}
```

### Response (streaming)
```json
{
  "conversation_id": "string",
  "message": "string (streaming)",
  "sources": ["array of portfolio data used"],
  "disclaimer": "string"
}
```

### Endpoints
- `POST /api/v1/ai/chat` — Send message, receive streaming response
- `GET /api/v1/ai/conversations` — List user's conversation history
- `GET /api/v1/ai/conversations/{id}` — Get specific conversation
- `DELETE /api/v1/ai/conversations/{id}` — Delete conversation

### Data Stored
- `ai_conversations` — conversation metadata
- `ai_messages` — individual messages with role + content

### RAG Data Sources
- User portfolio holdings + history
- Market data (via existing yfinance service)
- User preferences and alert settings
- Portfolio performance metrics

### Disclaimer
All AI responses MUST include:
> "This is not financial advice. Past performance does not guarantee future results."

## Frontend: Chat Panel

### Component: `<AIChatPanel />`
- Inline chat panel in dashboard
- Streaming responses
- Conversation history sidebar
- Suggested questions

## Out of Scope
- Direct trading execution
- Multi-user collaborative features

## Labels
- needs-ai-api (OpenAI/Claude API key required)
