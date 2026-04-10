# Wiki Schema — LLM Wiki Maintenance Rules

**Last Updated:** 2026-04-09
**Maintained by:** Athena (CTO Agent)

---

## Overview

This wiki follows the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

**Three layers:**
1. `raw/` — immutable source documents (research, articles, notes)
2. `pages/` — LLM-generated markdown pages (summaries, entities, concepts)
3. `schema.md` / `index.md` / `log.md` — this file + navigation + timeline

---

## Directory Structure

```
wiki/
├── raw/                    # Source documents (NEVER modify)
│   └── YYYY-MM-DD-*.md     # Named with date prefix
├── pages/                  # LLM-generated wiki pages
│   ├── index.md            # Auto-updated on every ingest
│   ├── log.md              # Append-only activity log
│   ├── entities/           # Individual stocks, features, people
│   ├── concepts/           # Patterns, strategies, architectures
│   ├── sources/            # Summary pages for each raw doc
│   └── synthesis/          # High-level cross-cutting analysis
├── schema.md               # This file
└── index.md                # Auto-generated directory
```

---

## Naming Conventions

### Raw Files
- `YYYY-MM-DD-topic-research.md` — e.g., `2026-04-02-dividend-ai-signals-research.md`
- One topic per file

### Wiki Pages
- `entities/{slug}.md` — e.g., `entities/sharesight.md`, `entities/phase-19-ai-portfolio.md`
- `concepts/{slug}.md` — e.g., `concepts/rag-patterns.md`, `concepts/open-finance-taiwan.md`
- `sources/{slug}.md` — one per raw file, e.g., `sources/2026-04-02-dividend-ai-signals-research.md`
- `synthesis/{slug}.md` — e.g., `synthesis/competitive-landscape.md`

---

## Frontmatter

Every wiki page MUST have frontmatter:

```markdown
---
title: Page Title
tags: [research, fintech, open-finance]
sources: [2026-04-02-dividend-ai-signals-research]
created: 2026-04-09
updated: 2026-04-09
---

# Page Title
```

---

## Ingest Workflow

When a new source is added to `raw/`:

1. **Read** the source file completely
2. **Create** `pages/sources/{filename}.md` — summary + key takeaways
3. **Update** `index.md` — add entry for the new source page
4. **Update relevant pages:**
   - Extract entities → update `pages/entities/{entity}.md`
   - Extract concepts → update `pages/concepts/{concept}.md`
5. **Append** to `pages/log.md`: `## [YYYY-MM-DD] ingest | Source Title`
6. **Flag contradictions** if new data conflicts with existing pages

---

## Query Workflow

When Tony or a team member asks a question:

1. **Read** `index.md` to find relevant pages
2. **Read** relevant pages in full
3. **Synthesize** answer
4. **If answer is valuable:** Save as a new page in `pages/synthesis/`

---

## Lint Workflow

Periodically (every 5 ingests or when asked):

1. Check for orphan pages (no inbound links)
2. Check for stale claims superseded by newer sources
3. Check missing cross-references
4. Check for important concepts mentioned but lacking pages
5. Report findings in `pages/log.md`: `## [YYYY-MM-DD] lint | <findings>`

---

## Quality Standards

- **No hallucination** — cite sources explicitly
- **Cross-reference aggressively** — link to related pages
- **Contradictions must be flagged** — use `> ⚠️ Contradicts: [page link]`
- **Summary-first** — first paragraph = key takeaway, no preamble
- **Frontmatter required** — tags, sources, dates

---

## What Goes in Wiki vs. Where

| Content | Place |
|---------|-------|
| Market research, scout results | `raw/` + `pages/sources/` |
| Feature analysis, competitive intel | `pages/synthesis/` |
| Individual entities (stocks, apps) | `pages/entities/` |
| Patterns, architectures, strategies | `pages/concepts/` |
| Meeting notes, decisions | `raw/` (as source) |
| Agent work logs | `pages/log.md` |

---

*This schema is co-evolved with Athena. Update when workflow changes.*
