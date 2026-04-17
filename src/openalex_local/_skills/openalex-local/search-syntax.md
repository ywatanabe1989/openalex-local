---
description: FTS5 full-text search syntax — operators, phrases, async, cache.
---

# Search Syntax

Uses SQLite FTS5 for full-text search across 284M+ works.

```python
from openalex_local import search

# Simple terms
search("neural network")

# Phrase match
search('"deep learning"')

# Boolean operators
search("EEG AND epilepsy")
search("fMRI OR PET")
search("CRISPR NOT bacteria")

# Prefix search
search("neuro*")
```

## Async API

```python
from openalex_local import aio

async def main():
    results = await aio.search("machine learning")
    n = await aio.count("CRISPR")
    work = await aio.get("W2741809807")
    works = await aio.get_many(["W1", "W2"])
```

Available: `aio.search`, `aio.search_many`, `aio.count`, `aio.count_many`,
`aio.get`, `aio.get_many`, `aio.exists`, `aio.info`.

## Local cache

Persist results for offline reuse:

```python
from openalex_local import cache

info = cache.create("ml_papers", query="machine learning", limit=1000)
papers = cache.query("ml_papers", year_min=2020)
ids    = cache.query_ids("ml_papers")
cache.stats("ml_papers")
cache.export("ml_papers", "ml.bib", format="bibtex")
```

Other cache helpers: `append`, `load`, `exists`, `list_caches`, `delete`, `info`.
