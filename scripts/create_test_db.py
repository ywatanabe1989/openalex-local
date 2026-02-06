#!/usr/bin/env python3
"""
Create test database from OpenAlex API samples.

Downloads sample works from OpenAlex API and builds a small test database
with FTS5 index for reproducible testing.

Usage:
    python scripts/create_test_db.py
    python scripts/create_test_db.py --rows 500
"""

import argparse
import json
import sqlite3
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TEST_DB_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_openalex.db"
SAMPLE_JSON_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_works.json"

# OpenAlex API
OPENALEX_API = "https://api.openalex.org/works"
USER_AGENT = (
    "openalex-local-tests/0.1 (https://github.com/ywatanabe1989/openalex-local)"
)


def download_sample_works(rows: int = 500, queries: list = None) -> list:
    """
    Download sample works from OpenAlex API.

    Args:
        rows: Number of records per query
        queries: List of search queries for diversity

    Returns:
        List of work metadata dictionaries
    """
    if queries is None:
        # Diverse queries to get varied content
        queries = [
            "neuroscience",
            "machine learning",
            "climate change",
            "cancer",
            "quantum",
        ]

    all_works = []
    rows_per_query = rows // len(queries)

    for query in queries:
        print(f"Downloading '{query}' ({rows_per_query} records)...")

        url = (
            f"{OPENALEX_API}?search={quote(query)}&per_page={min(rows_per_query, 200)}"
        )
        req = Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode())
                works = data.get("results", [])
                all_works.extend(works)
                print(f"  Got {len(works)} records")
        except HTTPError as e:
            print(f"  Error: {e}")

        # Be nice to the API
        time.sleep(1)

    print(f"Total: {len(all_works)} records")
    return all_works


def save_sample_json(works: list, path: Path):
    """Save works to JSON file for reproducibility."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(works, f)
    print(f"Saved JSON: {path} ({path.stat().st_size / 1024:.1f} KB)")


def load_sample_json(path: Path) -> list:
    """Load works from JSON file."""
    with open(path) as f:
        return json.load(f)


def reconstruct_abstract(inv_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index."""
    if not inv_index:
        return ""
    words = sorted(
        [(pos, word) for word, positions in inv_index.items() for pos in positions]
    )
    return " ".join(word for _, word in words)


def create_database(works: list, db_path: Path):
    """
    Create SQLite database with same schema as main openalex.db.

    Args:
        works: List of work metadata dictionaries
        db_path: Path to output database
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create works table
    cursor.execute(
        """
        CREATE TABLE works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openalex_id VARCHAR(255) UNIQUE,
            doi VARCHAR(255),
            title TEXT,
            abstract TEXT,
            authors TEXT,
            year INTEGER,
            source VARCHAR(255),
            issn VARCHAR(255),
            volume VARCHAR(255),
            issue VARCHAR(255),
            pages VARCHAR(255),
            publisher TEXT,
            type VARCHAR(255),
            concepts TEXT,
            topics TEXT,
            cited_by_count INTEGER,
            referenced_works TEXT,
            is_oa BOOLEAN,
            oa_url TEXT
        )
    """
    )

    # Create indices
    cursor.execute("CREATE INDEX idx_openalex_id ON works(openalex_id)")
    cursor.execute("CREATE INDEX idx_doi ON works(doi)")
    cursor.execute("CREATE INDEX idx_year ON works(year)")

    # Insert works
    print(f"Inserting {len(works)} works...")
    for work in works:
        openalex_id = work.get("id", "").replace("https://openalex.org/", "")
        doi = (
            work.get("doi", "").replace("https://doi.org/", "")
            if work.get("doi")
            else None
        )

        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        # Reconstruct abstract
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

        # Extract source info
        primary_location = work.get("primary_location") or {}
        source_info = primary_location.get("source") or {}
        source = source_info.get("display_name")
        issns = source_info.get("issn") or []
        issn = issns[0] if issns else None

        # Extract biblio
        biblio = work.get("biblio") or {}

        # Extract concepts (top 5)
        concepts = [
            {"name": c.get("display_name"), "score": c.get("score")}
            for c in (work.get("concepts") or [])[:5]
        ]

        # Extract topics (top 3)
        topics = [
            {
                "name": t.get("display_name"),
                "subfield": t.get("subfield", {}).get("display_name"),
            }
            for t in (work.get("topics") or [])[:3]
        ]

        # Extract OA info
        oa_info = work.get("open_access") or {}

        # Referenced works
        referenced = [
            r.replace("https://openalex.org/", "")
            for r in (work.get("referenced_works") or [])
        ]

        cursor.execute(
            """
            INSERT OR IGNORE INTO works (
                openalex_id, doi, title, abstract, authors, year, source,
                issn, volume, issue, pages, publisher, type, concepts, topics,
                cited_by_count, referenced_works, is_oa, oa_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                openalex_id,
                doi,
                work.get("title") or work.get("display_name"),
                abstract,
                json.dumps(authors),
                work.get("publication_year"),
                source,
                issn,
                biblio.get("volume"),
                biblio.get("issue"),
                biblio.get("first_page"),
                source_info.get("host_organization_name"),
                work.get("type"),
                json.dumps(concepts),
                json.dumps(topics),
                work.get("cited_by_count"),
                json.dumps(referenced),
                oa_info.get("is_oa", False),
                oa_info.get("oa_url"),
            ),
        )

    conn.commit()
    print(f"Inserted {len(works)} works")

    # Create FTS5 index
    print("Building FTS5 index...")
    cursor.execute(
        """
        CREATE VIRTUAL TABLE works_fts USING fts5(
            openalex_id,
            title,
            abstract,
            authors,
            content='',
            tokenize='porter unicode61'
        )
    """
    )

    # Populate FTS index
    cursor.execute(
        """
        INSERT INTO works_fts (rowid, openalex_id, title, abstract, authors)
        SELECT id, openalex_id, title, abstract, authors FROM works
    """
    )

    conn.commit()
    conn.close()

    print(f"Created database: {db_path} ({db_path.stat().st_size / 1024:.1f} KB)")


def verify_database(db_path: Path):
    """Verify the database works correctly."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check counts
    cursor.execute("SELECT COUNT(*) FROM works")
    works_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM works_fts")
    fts_count = cursor.fetchone()[0]

    print(f"\nVerification:")
    print(f"  Works: {works_count}")
    print(f"  FTS indexed: {fts_count}")

    # Test search
    cursor.execute(
        """
        SELECT COUNT(*) FROM works_fts WHERE works_fts MATCH 'neuroscience'
    """
    )
    search_count = cursor.fetchone()[0]
    print(f"  Search 'neuroscience': {search_count} matches")

    conn.close()

    if works_count > 0 and fts_count > 0:
        print("\nTest database ready!")
        return True
    else:
        print("\nError: Database verification failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create test database from OpenAlex API"
    )
    parser.add_argument(
        "--rows", type=int, default=500, help="Number of records to download"
    )
    parser.add_argument(
        "--use-cached", action="store_true", help="Use cached JSON if available"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Creating OpenAlex Test Database")
    print("=" * 60)
    print()

    # Download or load sample works
    if args.use_cached and SAMPLE_JSON_PATH.exists():
        print(f"Using cached JSON: {SAMPLE_JSON_PATH}")
        works = load_sample_json(SAMPLE_JSON_PATH)
    else:
        works = download_sample_works(rows=args.rows)
        save_sample_json(works, SAMPLE_JSON_PATH)

    print()

    # Create database
    create_database(works, TEST_DB_PATH)

    # Verify
    verify_database(TEST_DB_PATH)

    print()
    print("=" * 60)
    print(f"Test database: {TEST_DB_PATH}")
    print("Run tests with: make test")
    print("=" * 60)


if __name__ == "__main__":
    main()
