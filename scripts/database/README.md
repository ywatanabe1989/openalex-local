# Database Scripts

Scripts for downloading, building, and maintaining the OpenAlex local database.

## Numbering Convention

| Prefix | Category |
|--------|----------|
| `00_` | Download orchestration |
| `01_` | Additional download scripts |
| `02_` | Database build (JSON → SQLite) |
| `03_` | FTS index build |
| `99_` | Utilities (info, maintenance) |

## Build Order

```
┌─────────────────────────────────────────────────────────────┐
│  00_download_safe.sh + 01_download_other_entities.sh        │
│  (download OpenAlex snapshot - ~760GB, 1-2 days)            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  02_build_database.py                                       │
│  (parse JSON Lines → SQLite - 12-48 hours)                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  03_build_fts_index.py                                      │
│  (build FTS5 full-text search - 1-4 hours)                  │
└─────────────────────────────────────────────────────────────┘
```

## Scripts

### Download (00_, 01_)

| Script | Description | Duration |
|--------|-------------|----------|
| `00_download_safe.sh` | Download works entity (698GB) | 12-24h |
| `00_download_all_entities.sh` | Download all entities | 1-2 days |
| `01_download_other_entities.sh` | Download non-works entities (60GB) | 2-4h |
| `01_download_snapshot.py` | Python download helper | - |

### Build (02_, 03_)

| Script | Description | Duration |
|--------|-------------|----------|
| `02_build_database.py` | Parse JSON Lines → SQLite database | 12-48h |
| `03_build_fts_index.py` | Build FTS5 full-text search index | 1-4h |

## Quick Commands

```bash
# Check status
make status

# Download (if not done)
make download

# Build database (after download complete)
make build-db

# Build FTS index (after database built)
make build-fts

# Or build both sequentially
make build

# Monitor progress
make db-info
make db-stats

# Check build sessions
screen -ls
```

## Database Schema

```sql
-- Works table: core metadata
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openalex_id TEXT UNIQUE NOT NULL,  -- e.g., W2741809807
    doi TEXT,                           -- e.g., 10.1234/example
    title TEXT,
    abstract TEXT,                      -- reconstructed from inverted index
    year INTEGER,
    publication_date TEXT,
    type TEXT,                          -- article, book-chapter, etc.
    language TEXT,                      -- ISO 639-1 code
    source TEXT,                        -- journal/venue name
    source_id TEXT,                     -- OpenAlex source ID
    issn TEXT,
    volume TEXT,
    issue TEXT,
    first_page TEXT,
    last_page TEXT,
    publisher TEXT,
    cited_by_count INTEGER DEFAULT 0,
    is_oa INTEGER DEFAULT 0,            -- 1=open access
    oa_status TEXT,                     -- gold, green, bronze, etc.
    oa_url TEXT,
    authors_json TEXT,                  -- JSON array of author names
    concepts_json TEXT,                 -- JSON array of concepts
    topics_json TEXT,                   -- JSON array of topics
    referenced_works_json TEXT,         -- JSON array of referenced work IDs
    raw_json TEXT,                      -- full original JSON (optional)
    created_at TIMESTAMP
);

-- FTS5 full-text search on title + abstract
CREATE VIRTUAL TABLE works_fts USING fts5(
    openalex_id,
    title,
    abstract,
    content='works',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Build progress tracking (for resumable builds)
CREATE TABLE _build_progress (
    file_path TEXT PRIMARY KEY,
    records_processed INTEGER,
    completed_at TIMESTAMP
);

-- Metadata
CREATE TABLE _metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## Indices

```sql
CREATE INDEX idx_works_doi ON works(doi);
CREATE INDEX idx_works_year ON works(year);
CREATE INDEX idx_works_source ON works(source);
CREATE INDEX idx_works_type ON works(type);
CREATE INDEX idx_works_language ON works(language);
CREATE INDEX idx_works_cited_by_count ON works(cited_by_count);
CREATE INDEX idx_works_is_oa ON works(is_oa);
```

## Prerequisites

1. **Downloaded Snapshot** (~760GB)
   - Run: `make download`
   - Wait for completion: `make status`

2. **Disk Space**
   - Snapshot: ~760GB
   - Database: ~1-2TB
   - Total: ~3TB recommended

3. **Python 3.10+**

## Estimated Resources

| Phase | Size | Duration | Notes |
|-------|------|----------|-------|
| Download | 760GB | 1-2 days | At 5-10 MB/s |
| Build DB | ~1.5TB | 12-48h | Depends on I/O |
| Build FTS | +20-50GB | 1-4h | Added to DB |
| **Total** | **~2TB** | **2-4 days** | |

## Output

| Table | Expected Rows | Description |
|-------|---------------|-------------|
| works | ~284M | All OpenAlex works with metadata |
| works_fts | ~284M | Full-text search index |
| _build_progress | ~10K | Files processed (for resume) |
| _metadata | ~5 | Build timestamps, counts |

## Resumability

Both build scripts support resuming:

- `02_build_database.py`: Tracks processed files in `_build_progress` table
- `03_build_fts_index.py`: Checks if FTS is complete before rebuilding

If a build is interrupted, simply run the same command again to continue.

## Troubleshooting

### Build seems stuck
```bash
# Check screen session
screen -r openalex-build-db

# Check log
tail -f logs/build_db.log

# Check database growth
watch -n 60 'du -h data/openalex.db'
```

### Out of disk space
```bash
# Check space
df -h

# The build needs ~2TB total
# Consider using external storage
```

### Slow performance
```bash
# The scripts use optimized SQLite settings:
# - WAL mode for concurrent reads
# - Large cache (2GB)
# - Memory temp store

# If still slow, check I/O:
iostat -x 1
```

## Related Files

- `Makefile` - Build targets
- `src/openalex_local/_core/db.py` - Database connection
- `src/openalex_local/_core/fts.py` - FTS search functions
- `src/openalex_local/_core/models.py` - Work data model
