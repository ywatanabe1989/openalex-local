#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe (with Claude)
# File: 01_download_snapshot.py

"""
Download OpenAlex Works snapshot from AWS S3.

The snapshot is ~200-300 GB compressed and contains 284M+ works.

Usage:
    python 01_download_snapshot.py [--output-dir DIR] [--entity works]

Requirements:
    pip install boto3  # or use AWS CLI
"""

import argparse
import subprocess
import sys
from pathlib import Path

OPENALEX_S3_BASE = "s3://openalex/data"
DEFAULT_OUTPUT_DIR = Path("/home/ywatanabe/proj/openalex-local/data/snapshot")


def download_manifest(entity: str, output_dir: Path) -> Path:
    """Download manifest file for entity."""
    manifest_url = f"{OPENALEX_S3_BASE}/{entity}/manifest"
    manifest_path = output_dir / entity / "manifest"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading manifest for {entity}...")
    cmd = ["aws", "s3", "cp", manifest_url, str(manifest_path), "--no-sign-request"]

    try:
        subprocess.run(cmd, check=True)
        print(f"Manifest saved to: {manifest_path}")
        return manifest_path
    except subprocess.CalledProcessError as e:
        print(f"Error downloading manifest: {e}", file=sys.stderr)
        sys.exit(1)


def download_entity(entity: str, output_dir: Path) -> None:
    """Download all files for an entity."""
    entity_url = f"{OPENALEX_S3_BASE}/{entity}/"
    entity_dir = output_dir / entity
    entity_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {entity} snapshot to {entity_dir}...")
    print("This may take several hours depending on your connection.")

    cmd = [
        "aws", "s3", "sync",
        entity_url,
        str(entity_dir),
        "--no-sign-request",
        "--exclude", "*.gz",  # First pass: get manifest
    ]

    # Get manifest first
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Now download data files
    cmd = [
        "aws", "s3", "sync",
        entity_url,
        str(entity_dir),
        "--no-sign-request",
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Download complete: {entity_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading data: {e}", file=sys.stderr)
        sys.exit(1)


def check_aws_cli() -> bool:
    """Check if AWS CLI is available."""
    try:
        subprocess.run(["aws", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    parser = argparse.ArgumentParser(description="Download OpenAlex snapshot")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--entity",
        type=str,
        default="works",
        choices=["works", "authors", "sources", "institutions", "concepts", "publishers", "topics"],
        help="Entity type to download (default: works)",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only download manifest (to check size)",
    )
    args = parser.parse_args()

    if not check_aws_cli():
        print("Error: AWS CLI not found. Install with: pip install awscli", file=sys.stderr)
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.manifest_only:
        download_manifest(args.entity, args.output_dir)
    else:
        print(f"=" * 60)
        print(f"OpenAlex Snapshot Download")
        print(f"=" * 60)
        print(f"Entity: {args.entity}")
        print(f"Output: {args.output_dir}")
        print(f"")
        print(f"WARNING: The works snapshot is ~200-300 GB compressed!")
        print(f"Make sure you have enough disk space.")
        print(f"=" * 60)

        response = input("Continue? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

        download_entity(args.entity, args.output_dir)


if __name__ == "__main__":
    main()
