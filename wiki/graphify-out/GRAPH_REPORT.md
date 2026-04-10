# Graph Report — LLM Wiki Knowledge Graph

**Generated:** 2026-04-09  
**Source:** wiki/ (stock-tracker LLM Wiki)

---

## Overview

| Metric | Value |
|--------|-------|
| Total Nodes | 5 |
| Total Edges | 11 |
| Source Files | 5 |

---

## Nodes

| Node | Type | Path | Tags |
|------|------|------|------|
| competitive-landscape | synthesis | pages/synthesis/competitive-landscape.md | synthesis, competitive-analysis, product-strategy |
| beginner-friendly-ai | concept | pages/concepts/beginner-friendly-ai.md | product-strategy, differentiation, ai, beginner |
| 2026-04-02-dividend-ai-signals-research | source | pages/sources/2026-04-02-dividend-ai-signals-research.md | market-research, dividend-tracker, ai-signals, competitive-analysis |
| sharesight | entity | pages/entities/sharesight.md | competitor, dividend-tracker, international |
| 2026-04-02-dividend-ai-signals-research (raw) | raw | raw/2026-04-02-dividend-ai-signals-research.md | — |

---

## God Nodes (Most Connected)

1. **2026-04-02-dividend-ai-signals-research** — 9 edges (source node, most referenced)
2. **competitive-landscape** — 3 edges
3. **beginner-friendly-ai** — 3 edges

---

## Key Relationships

| Source | Relation | Target |
|--------|----------|--------|
| beginner-friendly-ai → | links_to | competitive-landscape |
| dividend research → | links_to | competitive-landscape |
| dividend research → | links_to | beginner-friendly-ai |
| dividend research + sharesight → | shares_entity | "Dividend Tracker" |

---

## Community Detection

**Community A (Dividend/Research):**
- 2026-04-02-dividend-ai-signals-research (source)
- competitive-landscape
- beginner-friendly-ai
- sharesight

**Community B (Raw Sources):**
- raw/2026-04-02-dividend-ai-signals-research.md

---

## Suggested Questions

1. What is our core product differentiation (beginner-friendly AI)?
2. Who are the key competitors in the dividend tracker market?
3. What features should Phase 30 prioritize based on market research?
4. How does our moat 「菜鳥也能懂」 compare to Sharesight's approach?

---

## Notes

- Graph built via deterministic extraction (markdown structure + links)
- Semantic relationships (INFERRED edges) require LLM processing
- Re-run graphify with AI subagents for deeper semantic graph
