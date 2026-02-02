#!/usr/bin/env python3
"""CLI for openalex_local."""

import json
import sys

import click

from .. import __version__


class AliasedGroup(click.Group):
    """Click group with command aliases."""

    ALIASES = {
        "s": "search",
        "doi": "search-by-doi",
        "st": "status",
    }

    def get_command(self, ctx, cmd_name):
        # Check for alias
        cmd_name = self.ALIASES.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)

    def resolve_command(self, ctx, args):
        # Resolve alias before normal command resolution
        _, cmd_name, args = super().resolve_command(ctx, args)
        return _, cmd_name, args


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    def _print_command_help(cmd, prefix: str, parent_ctx):
        """Recursively print help for a command and its subcommands."""
        click.secho(f"\n━━━ {prefix} ━━━", fg="cyan", bold=True)
        sub_ctx = click.Context(cmd, info_name=prefix.split()[-1], parent=parent_ctx)
        click.echo(cmd.get_help(sub_ctx))

        if isinstance(cmd, click.Group):
            for sub_name, sub_cmd in sorted(cmd.commands.items()):
                _print_command_help(sub_cmd, f"{prefix} {sub_name}", sub_ctx)

    # Print main help
    click.secho("━━━ openalex-local ━━━", fg="cyan", bold=True)
    click.echo(ctx.get_help())

    # Print all subcommands recursively
    for name, cmd in sorted(cli.commands.items()):
        _print_command_help(cmd, f"openalex-local {name}", ctx)

    ctx.exit(0)


@click.group(cls=AliasedGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "--version")
@click.option("--http", is_flag=True, help="Use HTTP API instead of direct database")
@click.option("--api-url", help="API URL for http mode (default: auto-detect)")
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_recursive_help,
    help="Show help for all commands recursively.",
)
@click.pass_context
def cli(ctx, http, api_url):
    """
    Local OpenAlex database with 284M+ works and full-text search.

    \b
    Supports both direct database access (db mode) and HTTP API (http mode).

    \b
    DB mode (default if database found):
      openalex-local search "machine learning"

    \b
    HTTP mode (connect to API server):
      openalex-local --http search "machine learning"
    """
    ctx.ensure_object(dict)

    if http or api_url:
        from .._core.api import configure_http

        configure_http(api_url or "http://localhost:31292")


@cli.command("search")
@click.argument("query")
@click.option("-n", "--number", default=10, help="Number of results")
@click.option("-o", "--offset", default=0, help="Skip first N results")
@click.option("-a", "--abstracts", is_flag=True, help="Show abstracts")
@click.option("-A", "--authors", is_flag=True, help="Show authors")
@click.option("--concepts", is_flag=True, help="Show concepts/topics")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_cmd(query, number, offset, abstracts, authors, concepts, as_json):
    """Search for works by title, abstract, or authors."""
    from .. import search

    try:
        results = search(query, limit=number, offset=offset)
    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except ConnectionError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        click.secho(
            "\nHint: Make sure the relay server is running:", fg="yellow", err=True
        )
        click.secho("  1. On NAS: openalex-local relay", fg="yellow", err=True)
        click.secho(
            "  2. SSH tunnel: ssh -L 31292:127.0.0.1:31292 nas", fg="yellow", err=True
        )
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        output = {
            "query": query,
            "total": results.total,
            "elapsed_ms": results.elapsed_ms,
            "works": [w.to_dict() for w in results.works],
        }
        click.echo(json.dumps(output, indent=2))
        return

    click.secho(
        f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms\n",
        fg="green",
    )

    for i, work in enumerate(results.works, 1):
        click.secho(f"{i}. {work.title} ({work.year})", fg="cyan", bold=True)
        click.echo(f"   DOI: {work.doi or 'N/A'}")
        click.echo(f"   Journal: {work.source or 'N/A'}")

        if authors and work.authors:
            author_str = ", ".join(work.authors[:5])
            if len(work.authors) > 5:
                author_str += f" (+{len(work.authors) - 5} more)"
            click.echo(f"   Authors: {author_str}")

        if abstracts and work.abstract:
            abstract = work.abstract[:300]
            if len(work.abstract) > 300:
                abstract += "..."
            click.echo(f"   Abstract: {abstract}")

        if concepts and work.concepts:
            concept_names = [c.get("name", "") for c in work.concepts[:5]]
            click.echo(f"   Concepts: {', '.join(concept_names)}")

        click.echo()


@cli.command("search-by-doi")
@click.argument("doi")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--citation", is_flag=True, help="Output as APA citation")
@click.option("--bibtex", is_flag=True, help="Output as BibTeX entry")
def search_by_doi_cmd(doi, as_json, citation, bibtex):
    """Search for a work by DOI."""
    from .. import get

    try:
        work = get(doi)
    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if work is None:
        click.secho(f"Not found: {doi}", fg="red", err=True)
        sys.exit(1)

    if citation:
        click.echo(work.citation("apa"))
        return

    if bibtex:
        click.echo(work.citation("bibtex"))
        return

    if as_json:
        click.echo(json.dumps(work.to_dict(), indent=2))
        return

    click.secho(work.title, fg="cyan", bold=True)
    click.echo(f"DOI: {work.doi}")
    click.echo(f"OpenAlex ID: {work.openalex_id}")
    click.echo(f"Year: {work.year or 'N/A'}")
    click.echo(f"Journal: {work.source or 'N/A'}")
    click.echo(f"Type: {work.type or 'N/A'}")
    click.echo(f"Citations: {work.cited_by_count or 0}")

    if work.authors:
        click.echo(f"Authors: {', '.join(work.authors)}")

    if work.abstract:
        click.echo(f"\nAbstract:\n{work.abstract}")

    if work.is_oa and work.oa_url:
        click.echo(f"\nOpen Access: {work.oa_url}")


@cli.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status_cmd(as_json):
    """Show status and configuration."""
    from .. import info

    try:
        status = info()
    except FileNotFoundError as e:
        if as_json:
            click.echo(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(status, indent=2))
        return

    click.secho("OpenAlex Local Status", fg="cyan", bold=True)
    click.echo(f"Mode: {status.get('mode', 'unknown')}")
    click.echo(f"Status: {status.get('status', 'unknown')}")

    if "db_path" in status:
        click.echo(f"Database: {status['db_path']}")

    if "work_count" in status:
        click.echo(f"Works: {status['work_count']:,}")

    if "fts_indexed" in status:
        click.echo(f"FTS Indexed: {status['fts_indexed']:,}")


# Register MCP subcommand group
from .mcp import mcp

cli.add_command(mcp)

# Register cache subcommand group
from .cli_cache import cache_group

cli.add_command(cache_group)


@cli.command("relay")
@click.option("--host", default=None, envvar="OPENALEX_LOCAL_HOST", help="Host to bind")
@click.option(
    "--port",
    default=None,
    type=int,
    envvar="OPENALEX_LOCAL_PORT",
    help="Port to listen on (default: 31292)",
)
def relay(host: str, port: int):
    """Run HTTP relay server for remote database access.

    \b
    This runs a FastAPI server that provides proper full-text search
    using FTS5 index across all 284M+ papers.

    \b
    Example:
      openalex-local relay                  # Run on 0.0.0.0:31292
      openalex-local relay --port 8080      # Custom port

    \b
    Then connect with http mode:
      openalex-local --http search "CRISPR"
      curl "http://localhost:31292/works?q=CRISPR&limit=10"
    """
    try:
        from .._server import run_server, DEFAULT_HOST, DEFAULT_PORT
    except ImportError:
        click.echo(
            "API server requires fastapi and uvicorn. Install with:\n"
            "  pip install fastapi uvicorn",
            err=True,
        )
        sys.exit(1)

    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT
    click.echo(f"Starting OpenAlex Local relay server on {host}:{port}")
    click.echo(f"Search endpoint: http://{host}:{port}/works?q=<query>")
    click.echo(f"Docs: http://{host}:{port}/docs")
    run_server(host=host, port=port)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
