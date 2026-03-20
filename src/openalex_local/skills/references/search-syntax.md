---
name: search-syntax
description: FTS5 search query syntax, operators, and patterns for effective literature search.
---

# Search Syntax Guide

openalex-local uses SQLite FTS5 for full-text search across titles and abstracts.

## Basic Queries

```
machine learning                  # Both words (implicit AND)
"neural network"                  # Exact phrase
machine OR learning               # Either word
machine NOT reinforcement         # Exclude term
```

## Phrase and Proximity

```
"deep learning"                   # Exact phrase match
NEAR(neural network, 5)           # Words within 5 tokens
"convolutional neural network"    # Multi-word phrase
```

## Column Filters

```
title:CRISPR                      # Search title only
abstract:genome editing           # Search abstract only
```

## Combining Operators

```
CRISPR AND "genome editing"       # Both required
(neural OR deep) AND learning     # Grouped logic
"machine learning" NOT survey     # Exclude surveys
```

## Practical Patterns

| Goal | Query |
|------|-------|
| Find review papers | `"systematic review" AND <topic>` |
| Find methodological papers | `"we propose" AND <method>` |
| Narrow to a subfield | `"<broad topic>" AND "<narrow topic>"` |
| Exclude certain work types | `<topic> NOT "meta-analysis"` |

## Tips

- FTS5 is case-insensitive
- Stemming is not applied; use variations (`neural networks` vs `neural network`)
- Use `count()` first to gauge result volume before fetching
- Use `limit` and `offset` for pagination on large result sets

## Python Examples

```python
from openalex_local import search, count

# Check volume first
n = count("CRISPR")
print(f"{n:,} papers")  # e.g., 45,231 papers

# Narrow search
results = search('"CRISPR" AND "gene therapy"', limit=50)

# Title-only search
results = search("title:transformer", limit=20)
```
