# Database Scripts

Scripts for downloading, building, and maintaining the OpenAlex local database.

## Quick Start

```bash
# Always start here - shows current state and what to do next
make status
```

## Numbering Convention

| Prefix | Category | Description |
|--------|----------|-------------|
| `00_` | Download | Main snapshot download (works) |
| `01_` | Download | Other entities + helpers |
| `02_` | Build | JSON → SQLite database |
| `03_` | Build | FTS5 full-text search index |
| `04_` | Build | Sources/journals table (IF proxy) |
| `05_` | Build | Citations table (accurate IF) |
| `06_` | Build | IF calculation indexes |

## Build Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: DOWNLOAD (~760GB, 1-2 days)                               │
│  make download                                                       │
│    ├── 00_download_safe.sh (works: 698GB)                           │
│    └── 01_download_other_entities.sh (authors+9: 60GB)              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: CORE DATABASE (12-48 hours)                               │
│  make build                                                          │
│    ├── 02_build_database.py (JSON → SQLite)                         │
│    └── 03_build_fts_index.py (full-text search)                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: IMPACT FACTOR (Optional, 50-80 hours)                     │
│  make build-sources      # Journal metadata (~30 sec)               │
│  make build-citations    # Citation graph (~3-4 hours data +        │
│                          #   ~8-10 hours indexes = 50-70h total)    │
│  make build-if-indexes   # Works table indexes (~2-4 hours)         │
└─────────────────────────────────────────────────────────────────────┘
```

## Scripts Reference

### Download Scripts (00_, 01_)

| Script | Description | Duration | Command |
|--------|-------------|----------|---------|
| `00_download_safe.sh` | Download works entity (698GB) | 12-24h | `make download-works` |
| `00_download_all_entities.sh` | Download all entities | 1-2 days | - |
| `01_download_other_entities.sh` | Download non-works (60GB) | 2-4h | `make download-others` |
| `01_download_snapshot.py` | Python download helper | - | - |

### Build Scripts (02_, 03_)

| Script | Description | Duration | Command |
|--------|-------------|----------|---------|
| `02_build_database.py` | Parse JSON → SQLite | 12-48h | `make build-db` |
| `03_build_fts_index.py` | Build FTS5 search index | 1-4h | `make build-fts` |

### Impact Factor Scripts (04_, 05_, 06_)

| Script | Description | Duration | Command |
|--------|-------------|----------|---------|
| `04_build_sources_table.py` | Journal metadata (IF proxy) | ~30 sec | `make build-sources` |
| `05_build_citations_table.py` | Citation relationships (2.9B rows) | ~3-4h | `make build-citations` |
| `06_build_if_indexes.py` | All IF-related indexes | ~8-10h | `make build-if-indexes` |

## Make Targets Summary

```bash
# Status & Help
make status              # Show current state (START HERE)
make help                # List all commands
make check               # Verify prerequisites

# Download
make download            # Download all (parallel)
make download-works      # Download works only (698GB)
make download-others     # Download other entities (60GB)
make download-stop       # Stop downloads (resumable)

# Core Build
make build               # Build database + FTS
make build-db            # Build SQLite from snapshot
make build-fts           # Build full-text search

# Impact Factor Build (Optional)
make build-sources       # Build journal metadata table
make build-citations     # Build citation graph (slow!)
make build-if-indexes    # Build IF calculation indexes

# Utilities
make build-stop          # Stop all builds (resumable)
make db-info             # Show database info
make db-stats            # Detailed statistics
```

## Database Schema

### Core Tables

```sql
-- Works table: 284M+ scholarly works
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openalex_id TEXT UNIQUE NOT NULL,  -- W2741809807
    doi TEXT,
    title TEXT,
    abstract TEXT,
    year INTEGER,
    publication_date TEXT,
    type TEXT,
    language TEXT,
    source TEXT,           -- Journal name
    source_id TEXT,        -- OpenAlex source ID
    issn TEXT,
    volume TEXT,
    issue TEXT,
    first_page TEXT,
    last_page TEXT,
    publisher TEXT,
    cited_by_count INTEGER DEFAULT 0,
    is_oa INTEGER DEFAULT 0,
    oa_status TEXT,
    oa_url TEXT,
    authors_json TEXT,
    concepts_json TEXT,
    topics_json TEXT,
    referenced_works_json TEXT,
    raw_json TEXT,
    created_at TIMESTAMP
);

-- FTS5 full-text search
CREATE VIRTUAL TABLE works_fts USING fts5(
    openalex_id, title, abstract,
    content='works', content_rowid='id',
    tokenize='porter unicode61'
);
```

### Impact Factor Tables (Optional)

```sql
-- Sources: 255K journals with metrics
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    openalex_id TEXT UNIQUE,
    issn_l TEXT,
    issns TEXT,              -- JSON array
    display_name TEXT,
    type TEXT,
    works_count INTEGER,
    cited_by_count INTEGER,
    two_year_mean_citedness REAL,  -- Impact Factor proxy
    h_index INTEGER,
    i10_index INTEGER,
    is_oa INTEGER,
    is_in_doaj INTEGER
);

-- ISSN lookup for fast journal identification
CREATE TABLE issn_lookup (
    issn TEXT PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id)
);

-- Citations: 2.9B citation relationships
CREATE TABLE citations (
    citing_id TEXT NOT NULL,   -- Work that cites
    cited_id TEXT NOT NULL,    -- Work being cited
    citing_year INTEGER        -- Year of citation
);
```

### Indexes for IF Calculation

```sql
-- Works table (for finding articles by journal+year)
CREATE INDEX idx_works_issn ON works(issn);
CREATE INDEX idx_works_issn_year ON works(issn, year);  -- KEY for IF
CREATE INDEX idx_works_source_id ON works(source_id);
CREATE INDEX idx_works_source_id_year ON works(source_id, year);

-- Citations table (for counting citations)
CREATE INDEX idx_citations_cited_year ON citations(cited_id, citing_year);  -- KEY for IF
CREATE INDEX idx_citations_citing ON citations(citing_id);
CREATE INDEX idx_citations_year ON citations(citing_year);
```

## Impact Factor Calculation

### Formula
```
IF(2023) = Citations in 2023 to articles from 2021-2022
           ─────────────────────────────────────────────
           Citable articles published in 2021-2022
```

### Data Flow
```
1. Find articles: SELECT openalex_id FROM works
                  WHERE issn = ? AND year BETWEEN 2021 AND 2022

2. Count citations: SELECT COUNT(*) FROM citations
                    WHERE cited_id IN (...) AND citing_year = 2023

3. Calculate: IF = citations / articles
```

### Two IF Sources

| Source | Table | Speed | Accuracy |
|--------|-------|-------|----------|
| OpenAlex proxy | `sources.two_year_mean_citedness` | Fast | Good proxy |
| Calculated | `citations` table | Slower | JCR-like |

## Resource Requirements

| Phase | Disk | Duration | Notes |
|-------|------|----------|-------|
| Download | 760GB | 1-2 days | At 5-10 MB/s |
| Core Build | +1TB | 12-48h | DB + FTS |
| IF Build | +300GB | 50-70h | Citations + indexes |
| **Total** | **~2TB** | **3-5 days** | |

## Monitoring Progress

```bash
# Check overall status
make status

# Watch specific builds
tail -f logs/build_db.log
tail -f logs/build_fts.log
tail -f logs/build_citations.log
tail -f logs/build_if_indexes.log

# Check screen sessions
screen -ls

# Attach to session
screen -r openalex-build-db

# Database growth
watch -n 60 'du -h data/openalex.db'
```

## Resumability

All scripts support resuming after interruption:

| Script | Resume Mechanism |
|--------|------------------|
| `02_build_database.py` | Tracks files in `_build_progress` table |
| `03_build_fts_index.py` | Checks if FTS complete |
| `05_build_citations_table.py` | Tracks rowid in `_citations_build_progress` |
| `06_build_if_indexes.py` | Uses `CREATE INDEX IF NOT EXISTS` |

## Troubleshooting

### Build seems stuck
```bash
screen -r openalex-build-db     # Attach to session
tail -f logs/build_db.log       # Check log
watch -n 60 'du -h data/openalex.db'  # Watch growth
```

### Out of disk space
```bash
df -h                           # Check space
# Need ~2TB total for full build
```

### Database locked during index creation
```bash
# Wait for index to complete, or use a new connection
sqlite3 data/openalex.db ".indices"  # Check existing indexes
```

## Related Files

- `Makefile` - Build orchestration
- `scripts/utils/status.sh` - Status reporter
- `src/openalex_local/_core/db.py` - Database connection
- `src/openalex_local/_core/fts.py` - FTS search
- `src/openalex_local/_core/models.py` - Work model
