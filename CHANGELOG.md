# Changelog

All notable changes to `openalex-local` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.7.9]

- Back-merge `main` into `develop` (reconcile divergence; keep `develop`'s
  source-fix #40, sphinx dedup #41, and the `10_quickstart` example +
  test).
- Standardize CI to the canonical SciTeX workflow set
  (`pytest-matrix`, `import-smoke`, `rtd-sphinx-build`,
  `<pkg>-quality-audit`, `newb-docs-quality`, `auto-merge-to-develop`);
  drop the legacy `CI` / `Tests` / `Docs` / `Newb` workflows.
- `v0.7.7` and `v0.7.8` tags were burned (publish/version mismatch);
  this is the next valid release.

## [0.7.5]

- Initial CHANGELOG entry — see git log for prior history.
