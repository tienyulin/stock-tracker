---
title: "Beginner-Friendly AI" Pattern
tags: [product-strategy, differentiation, ai, beginner]
created: 2026-04-09
updated: 2026-04-09
---

# "Beginner-Friendly AI" Pattern

**Also known as:** 「菜鳥也能懂」AI 分析介面

---

## Definition

Providing AI-generated insights that explain *why* a recommendation is made, not just *what* to do. Target users: retail investors who are new to the market and lack the mental models to trust a bare buy/sell signal.

---

## Why It Matters

| Without Explanation | With Explanation |
|---------------------|------------------|
| "Buy TSMC" | "TSMAC appears oversold (RSI=28). Historically, RSI < 30 on TWSE stocks rebounds within 2 weeks 70% of the time. This matches your risk tolerance (medium)." |
| User distrusts signal | User understands and trusts signal |
| User ignores recommendation | User acts on recommendation |

---

## Implementation in Our App

### Where Applied
- **AI Portfolio Chat** — explain stock picks in plain language
- **AI Signal Scoring** — confidence score + reasoning
- **Dividend Tracker** — explain why a dividend is good (yield vs. history)

### Key Pattern
```
Signal → Reasoning (plain language) → Confidence → Action
```

---

## Related Concepts

- [synthesis/competitive-landscape.md](../synthesis/competitive-landscape.md)
- [entities/trade-ideas.md](../entities/trade-ideas.md) — competitor lacking this pattern
