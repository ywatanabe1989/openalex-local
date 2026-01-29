#!/usr/bin/env python3
"""Example: Batch processing with jobs module.

Demonstrates:
- Creating batch jobs
- Processing multiple DOIs
- Tracking progress
"""

from openalex_local import jobs, get

# List of DOIs to process
dois = [
    "10.1038/nature14539",  # Deep learning paper
    "10.1126/science.aaa8415",  # AlphaGo paper
    "10.1038/s41586-021-03819-2",  # AlphaFold paper
]

# Create a job
job = jobs.create(dois, name="example_batch")
print(f"Created job: {job.id}")
print(f"Items to process: {len(job.items)}")


# Define processor function
def process_doi(doi: str):
    """Process a single DOI."""
    work = get(doi)
    if work:
        print(f"  Found: {work.title[:50]}...")
    else:
        raise ValueError(f"Not found: {doi}")


# Run the job (if database is available)
try:
    print("\nProcessing...")
    result = jobs.run(job.id, process_doi)
    print(f"\nCompleted: {len(result.completed)}/{len(result.items)}")
    if result.failed:
        print(f"Failed: {list(result.failed.keys())}")
except FileNotFoundError as e:
    print(f"\nSkipped (no database): {e}")
