"""CLI commands for cache management."""

import json
import sys

import click


class _CacheAliasedGroup(click.Group):
    """Cache group with backward-compatible aliases."""

    ALIASES = {
        "stats": "show-stats",
        "ids": "show-ids",
    }

    def get_command(self, ctx, cmd_name):
        cmd_name = self.ALIASES.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)


@click.group(
    "cache",
    cls=_CacheAliasedGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def cache_group():
    """Manage local paper caches."""
    pass


@cache_group.command("create")
@click.argument("name")
@click.option("-q", "--query", help="Search query to populate cache")
@click.option("-i", "--ids", multiple=True, help="OpenAlex IDs or DOIs to cache")
@click.option("-l", "--limit", default=1000, help="Maximum papers from query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without writing the cache.",
)
@click.option(
    "-y", "--yes", is_flag=True, help="Skip confirmation prompts (assume yes)."
)
def cache_create(name, query, ids, limit, as_json, dry_run, yes):
    """Create a new cache from search or IDs.

    \b
    Example:
      $ openalex-local cache create my-cache -q "machine learning" -l 500
      $ openalex-local cache create my-cache -i W2741809807 -i W3000000000
      $ openalex-local cache create my-cache -q "CRISPR" --dry-run
    """
    from .. import cache

    if not query and not ids:
        click.secho("Error: Provide --query or --ids", fg="red", err=True)
        sys.exit(1)

    if dry_run:
        click.secho(
            f"[dry-run] would create cache '{name}' (query={query!r}, ids={list(ids) if ids else None}, limit={limit})",
            fg="yellow",
        )
        return

    try:
        info = cache.create(
            name, query=query, ids=list(ids) if ids else None, limit=limit
        )
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        click.echo(
            json.dumps(
                {
                    "name": info.name,
                    "count": info.count,
                    "path": info.path,
                    "queries": info.queries,
                },
                indent=2,
            )
        )
    else:
        click.secho(f"Created cache '{info.name}' with {info.count} papers", fg="green")
        click.echo(f"Path: {info.path}")


@cache_group.command("append")
@click.argument("name")
@click.option("-q", "--query", help="Search query to add papers")
@click.option("-i", "--ids", multiple=True, help="OpenAlex IDs or DOIs to add")
@click.option("-l", "--limit", default=1000, help="Maximum papers from query")
def cache_append(name, query, ids, limit):
    """Append papers to an existing cache.

    \b
    Example:
      $ openalex-local cache append my-cache -q "neural networks"
      $ openalex-local cache append my-cache -i W3000000000
    """
    from .. import cache

    if not query and not ids:
        click.secho("Error: Provide --query or --ids", fg="red", err=True)
        sys.exit(1)

    try:
        info = cache.append(
            name, query=query, ids=list(ids) if ids else None, limit=limit
        )
        click.secho(f"Cache '{info.name}' now has {info.count} papers", fg="green")
    except FileNotFoundError:
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)


@cache_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cache_list(as_json):
    """List all caches.

    \b
    Example:
      $ openalex-local cache list
      $ openalex-local cache list --json
    """
    from .. import cache

    caches = cache.list_caches()

    if as_json:
        click.echo(
            json.dumps(
                [
                    {
                        "name": c.name,
                        "count": c.count,
                        "updated_at": c.updated_at,
                        "size_bytes": c.size_bytes,
                    }
                    for c in caches
                ],
                indent=2,
            )
        )
        return

    if not caches:
        click.echo("No caches found")
        return

    click.secho("Caches:", fg="cyan", bold=True)
    for c in caches:
        size_kb = c.size_bytes / 1024
        click.echo(f"  {c.name}: {c.count} papers ({size_kb:.1f} KB)")


@cache_group.command("query")
@click.argument("name")
@click.option("--fields", help="Comma-separated fields to return")
@click.option("--year-min", type=int, help="Minimum publication year")
@click.option("--year-max", type=int, help="Maximum publication year")
@click.option("--cited-min", type=int, help="Minimum citation count")
@click.option("--has-abstract", is_flag=True, default=None, help="Must have abstract")
@click.option("--is-oa", is_flag=True, default=None, help="Must be open access")
@click.option("--source", help="Filter by source/journal (substring)")
@click.option("-n", "--limit", type=int, help="Maximum results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cache_query(
    name,
    fields,
    year_min,
    year_max,
    cited_min,
    has_abstract,
    is_oa,
    source,
    limit,
    as_json,
):
    """Query a cache with filters.

    \b
    Example:
      $ openalex-local cache query my-cache --year-min 2020
      $ openalex-local cache query my-cache --is-oa --json
      $ openalex-local cache query my-cache --cited-min 100 -n 50
    """
    from .. import cache

    field_list = fields.split(",") if fields else None

    try:
        results = cache.query(
            name,
            fields=field_list,
            year_min=year_min,
            year_max=year_max,
            cited_min=cited_min,
            has_abstract=has_abstract if has_abstract else None,
            is_oa=is_oa if is_oa else None,
            source=source,
            limit=limit,
        )
    except FileNotFoundError:
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(results, indent=2))
        return

    click.secho(f"Found {len(results)} papers", fg="green")
    for i, w in enumerate(results[:20], 1):
        title = w.get("title", "No title")[:60]
        year = w.get("year", "N/A")
        click.echo(f"{i}. {title}... ({year})")

    if len(results) > 20:
        click.echo(f"... and {len(results) - 20} more (use --json for full output)")


@cache_group.command("show-stats")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cache_stats(name, as_json):
    """Show statistics for a cache.

    \b
    Example:
      $ openalex-local cache show-stats my-cache
      $ openalex-local cache show-stats my-cache --json
    """
    from .. import cache

    try:
        s = cache.stats(name)
    except FileNotFoundError:
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(s, indent=2))
        return

    click.secho(f"Cache: {s['name']}", fg="cyan", bold=True)
    click.echo(f"Total papers: {s['total']}")
    click.echo(f"Year range: {s['year_min']} - {s['year_max']}")
    click.echo(
        f"Citations: {s['citations_total']:,} total, {s['citations_mean']:.1f} mean"
    )
    click.echo(f"With abstract: {s['with_abstract']} ({s['with_abstract_pct']}%)")
    click.echo(f"Open access: {s['open_access']} ({s['open_access_pct']}%)")

    if s["sources"]:
        click.secho("\nTop sources:", fg="cyan")
        for src, cnt in s["sources"][:5]:
            click.echo(f"  {src}: {cnt}")


@cache_group.command("export")
@click.argument("name")
@click.argument("output")
@click.option(
    "-f",
    "--format",
    "fmt",
    default="json",
    type=click.Choice(["json", "csv", "bibtex"]),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be exported without writing the file.",
)
@click.option(
    "-y", "--yes", is_flag=True, help="Skip confirmation prompts (assume yes)."
)
def cache_export(name, output, fmt, dry_run, yes):
    """Export cache to file.

    \b
    Example:
      $ openalex-local cache export my-cache out.json
      $ openalex-local cache export my-cache out.bib -f bibtex
      $ openalex-local cache export my-cache out.csv -f csv --dry-run
    """
    from .. import cache

    if dry_run:
        click.secho(
            f"[dry-run] would export cache '{name}' to {output} (format={fmt})",
            fg="yellow",
        )
        return

    try:
        path = cache.export(name, output, format=fmt)
        click.secho(f"Exported to {path}", fg="green")
    except FileNotFoundError:
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)


@cache_group.command("delete")
@click.argument("name")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without removing the cache.",
)
def cache_delete(name, yes, dry_run):
    """Delete a cache.

    \b
    Example:
      $ openalex-local cache delete my-cache
      $ openalex-local cache delete my-cache -y
      $ openalex-local cache delete my-cache --dry-run
    """
    from .. import cache

    if not cache.exists(name):
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)

    if dry_run:
        click.secho(f"[dry-run] would delete cache '{name}'", fg="yellow")
        return

    if not yes:
        if not click.confirm(f"Delete cache '{name}'?"):
            click.echo("Cancelled")
            return

    cache.delete(name)
    click.secho(f"Deleted cache '{name}'", fg="green")


@cache_group.command("show-ids")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON array")
def cache_ids(name, as_json):
    """Print all OpenAlex IDs in a cache.

    \b
    Example:
      $ openalex-local cache show-ids my-cache
      $ openalex-local cache show-ids my-cache --json
      $ openalex-local cache show-ids my-cache > ids.txt
    """
    from .. import cache

    try:
        ids = cache.query_ids(name)
    except FileNotFoundError:
        click.secho(f"Cache not found: {name}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(list(ids), indent=2))
        return

    for oid in ids:
        click.echo(oid)
