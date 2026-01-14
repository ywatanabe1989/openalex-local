# OpenAlex Local

Local OpenAlex database with 284M+ scholarly works, abstracts, and semantic search.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

## Why OpenAlex Local?

| Feature | Benefit |
|---------|---------|
| 284M Works | More coverage than CrossRef |
| Abstracts | High availability for semantic search |
| Concepts & Topics | Built-in classification |
| Author Disambiguation | Linked to institutions |
| Open Access Info | OA status and URLs |

## Installation

```bash
pip install openalex-local
```

From source:
```bash
git clone https://github.com/ywatanabe1989/openalex-local
cd openalex-local && pip install -e .
```

## Database Setup

The database requires downloading the OpenAlex snapshot (~330 GB compressed).

```bash
# 1. Download OpenAlex Works snapshot
python scripts/database/01_download_snapshot.py

# 2. Build SQLite database
python scripts/database/02_build_database.py

# 3. Build FTS5 index
python scripts/database/03_build_fts_index.py
```

## Usage

### Python API

```python
from openalex_local import search, get

# Full-text search (title + abstract)
results = search("machine learning neural networks")
for work in results:
    print(f"{work.title} ({work.year})")
    print(f"  Abstract: {work.abstract[:200]}...")
    print(f"  Concepts: {[c['name'] for c in work.concepts]}")

# Get by OpenAlex ID or DOI
work = get("W2741809807")
work = get("10.1038/nature12373")
```

### CLI

```bash
openalex-local search "CRISPR genome editing" -n 5
openalex-local get W2741809807
openalex-local get 10.1038/nature12373
```

## Comparison with CrossRef Local

| Feature | crossref-local | openalex-local |
|---------|---------------|----------------|
| Works | 167M | 284M |
| Abstracts | ~22% | ~70%+ |
| Citations | Raw references | Linked works |
| Impact Factor | Calculated | Pre-computed |
| Concepts | ❌ | ✓ |
| Author IDs | ❌ | ✓ |
| Best for | Citation analysis | Semantic search |

## Data Source

Data from [OpenAlex](https://openalex.org/), an open catalog of scholarly works.
Updated monthly from their [snapshot](https://docs.openalex.org/download-all-data/openalex-snapshot).

## License

AGPL-3.0 - see [LICENSE](LICENSE) for details.
