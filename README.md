# OpenAlex Local

Local OpenAlex database with 284M+ scholarly works, abstracts, and semantic search.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

<details>
<summary><strong>Why OpenAlex Local?</strong></summary>

**Built for the LLM era** - features that matter for AI research assistants:

| Feature | Benefit |
|---------|---------|
| 📚 **284M Works** | More coverage than CrossRef |
| 📝 **Abstracts** | ~45-60% availability for semantic search |
| 🏷️ **Concepts & Topics** | Built-in classification |
| 👤 **Author Disambiguation** | Linked to institutions |
| 🔓 **Open Access Info** | OA status and URLs |

Perfect for: RAG systems, research assistants, literature review automation.

</details>

<details>
<summary><strong>Installation</strong></summary>

```bash
pip install openalex-local
```

From source:
```bash
git clone https://github.com/ywatanabe1989/openalex-local
cd openalex-local && make install
```

Database setup (~300 GB, ~1-2 days to build):
```bash
# Check system status
make status

# 1. Download OpenAlex Works snapshot (~300GB)
make download-screen  # runs in background

# 2. Build SQLite database
make build-db

# 3. Build FTS5 index
make build-fts
```

</details>

<details>
<summary><strong>Python API</strong></summary>

```python
from openalex_local import search, get, count

# Full-text search (title + abstract)
results = search("machine learning neural networks")
for work in results:
    print(f"{work.title} ({work.year})")
    print(f"  Abstract: {work.abstract[:200]}...")
    print(f"  Concepts: {[c['name'] for c in work.concepts]}")

# Get by OpenAlex ID or DOI
work = get("W2741809807")
work = get("10.1038/nature12373")

# Count matches
n = count("CRISPR")
```

</details>

<details>
<summary><strong>CLI</strong></summary>

```bash
openalex-local search "CRISPR genome editing" -n 5
openalex-local get W2741809807
openalex-local get 10.1038/nature12373
openalex-local count "machine learning"
```

</details>

<details>
<summary><strong>Related Projects</strong></summary>

**[crossref-local](https://github.com/ywatanabe1989/crossref-local)** - Sister project with CrossRef data:

| Feature | crossref-local | openalex-local |
|---------|----------------|----------------|
| Works | 167M | 284M |
| Abstracts | ~21% | ~45-60% |
| Update frequency | Real-time | Monthly |
| DOI authority | ✓ (source) | Uses CrossRef |
| Citations | Raw references | Linked works |
| Concepts/Topics | ❌ | ✓ |
| Author IDs | ❌ | ✓ |
| Best for | DOI lookup, raw refs | Semantic search |

**When to use CrossRef**: Real-time DOI updates, raw reference parsing, authoritative metadata.
**When to use OpenAlex**: Semantic search, citation analysis, topic discovery.

</details>

<details>
<summary><strong>Data Source</strong></summary>

Data from [OpenAlex](https://openalex.org/), an open catalog of scholarly works.
Updated monthly from their [snapshot](https://docs.openalex.org/download-all-data/openalex-snapshot).

</details>

---

<p align="center">
  <a href="https://scitex.ai"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0 · ywatanabe@scitex.ai
</p>

<!-- EOF -->
