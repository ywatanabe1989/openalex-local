#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-06 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/11_abstract_coverage.py

"""Calculate abstract coverage statistics for OpenAlex Local database.

This script calculates:
1. Global abstract availability ratio
2. Per-publisher coverage (Elsevier, Springer, Wiley, etc.)
3. Per-journal coverage for major journals (Nature, Science, Cell, etc.)
"""

import scitex as stx
from openalex_local._core.db import get_db


@stx.session
def main(
    top_n: int = 20,
    CONFIG=stx.session.INJECTED,
    plt=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Calculate abstract coverage statistics.

    Args:
        top_n: Number of top journals/publishers to show
    """
    db = get_db()

    # =========================================================================
    # 1. Global Coverage
    # =========================================================================
    logger.info("=" * 70)
    logger.info("ABSTRACT COVERAGE STATISTICS")
    logger.info("=" * 70)

    result = db.fetchone("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
    """)

    total = result['total']
    with_abstract = result['with_abstract']
    ratio = (with_abstract / total) * 100

    logger.info(f"\nGlobal Statistics:")
    logger.info(f"  Total works: {total:,}")
    logger.info(f"  With abstract: {with_abstract:,}")
    logger.info(f"  Coverage: {ratio:.1f}%")

    # =========================================================================
    # 2. Per-Publisher Coverage
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info("Coverage by Publisher (Top {})".format(top_n))
    logger.info("-" * 70)

    publishers = db.fetchall("""
        SELECT
            publisher,
            COUNT(*) as total,
            SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as with_abstract,
            ROUND(100.0 * SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) / COUNT(*), 1) as coverage
        FROM works
        WHERE publisher IS NOT NULL AND publisher != ''
        GROUP BY publisher
        HAVING total > 10000
        ORDER BY total DESC
        LIMIT ?
    """, (top_n,))

    logger.info(f"\n{'Publisher':<40} {'Total':>12} {'Abstract':>12} {'Coverage':>10}")
    logger.info("-" * 76)
    for row in publishers:
        logger.info(f"{row['publisher'][:39]:<40} {row['total']:>12,} {row['with_abstract']:>12,} {row['coverage']:>9.1f}%")

    # =========================================================================
    # 3. Major Journals Coverage
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info("Coverage by Major Journal")
    logger.info("-" * 70)

    # List of major journals to check
    major_journals = [
        # High-impact general
        "Nature", "Science", "Cell", "The Lancet",
        "New England Journal of Medicine", "JAMA",
        # Nature family
        "Nature Medicine", "Nature Genetics", "Nature Neuroscience",
        "Nature Communications", "Scientific Reports",
        # Cell Press
        "Cell Reports", "Neuron", "Immunity",
        # Other major
        "PNAS", "PLoS ONE", "eLife",
        # Physics/Chemistry
        "Physical Review Letters", "Journal of the American Chemical Society",
        # Computing
        "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    ]

    logger.info(f"\n{'Journal':<55} {'Total':>10} {'Abstract':>10} {'Coverage':>10}")
    logger.info("-" * 87)

    for journal in major_journals:
        result = db.fetchone("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as with_abstract
            FROM works
            WHERE source = ?
        """, (journal,))

        if result and result['total'] > 0:
            coverage = (result['with_abstract'] / result['total']) * 100
            logger.info(f"{journal[:54]:<55} {result['total']:>10,} {result['with_abstract']:>10,} {coverage:>9.1f}%")
        else:
            logger.info(f"{journal[:54]:<55} {'N/A':>10} {'N/A':>10} {'N/A':>10}")

    # =========================================================================
    # 4. Coverage by Year
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info("Coverage by Publication Year (Recent 10 Years)")
    logger.info("-" * 70)

    years = db.fetchall("""
        SELECT
            year,
            COUNT(*) as total,
            SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as with_abstract,
            ROUND(100.0 * SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) / COUNT(*), 1) as coverage
        FROM works
        WHERE year >= 2014 AND year <= 2024
        GROUP BY year
        ORDER BY year DESC
    """)

    logger.info(f"\n{'Year':<10} {'Total':>15} {'Abstract':>15} {'Coverage':>10}")
    logger.info("-" * 52)
    for row in years:
        logger.info(f"{row['year']:<10} {row['total']:>15,} {row['with_abstract']:>15,} {row['coverage']:>9.1f}%")

    # =========================================================================
    # 5. Summary for README
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY (for documentation)")
    logger.info("=" * 70)
    logger.info(f"\nGlobal abstract coverage: {ratio:.1f}%")
    logger.info(f"Total indexed works: {total:,}")

    # Save summary to CSV
    import pandas as pd

    # Publisher coverage
    pub_data = [dict(row) for row in publishers]
    df_pub = pd.DataFrame(pub_data)
    stx.io.save(df_pub, "publisher_coverage.csv")

    # Year coverage
    year_data = [dict(row) for row in years]
    df_year = pd.DataFrame(year_data)
    stx.io.save(df_year, "year_coverage.csv")

    logger.info("\nSaved: publisher_coverage.csv, year_coverage.csv")

    return 0


if __name__ == "__main__":
    main()

# EOF
