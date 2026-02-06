#!/usr/bin/env python3
"""MCP CLI subcommands for openalex_local."""

import sys

import click

from .. import info

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def mcp():
    """MCP (Model Context Protocol) server commands.

    \b
    Commands:
      start        - Start the MCP server
      doctor       - Diagnose MCP setup
      installation - Show installation instructions
      list-tools   - List available MCP tools
    """
    pass


@mcp.command("start", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t",
    "--transport",
    type=click.Choice(["stdio", "sse", "http"]),
    default="stdio",
    help="Transport protocol (http recommended for remote)",
)
@click.option(
    "--host",
    default="localhost",
    envvar="OPENALEX_LOCAL_MCP_HOST",
    help="Host for HTTP/SSE transport",
)
@click.option(
    "--port",
    default=8083,
    type=int,
    envvar="OPENALEX_LOCAL_MCP_PORT",
    help="Port for HTTP/SSE transport",
)
@click.option(
    "--force",
    is_flag=True,
    help="Kill existing process using the port if any (http/sse only)",
)
def mcp_start(transport: str, host: str, port: int, force: bool):
    """Start the MCP server.

    \b
    Transports:
      stdio  - Standard I/O (default, for Claude Desktop local)
      http   - Streamable HTTP (recommended for remote/persistent)
      sse    - Server-Sent Events (deprecated as of MCP spec 2025-03-26)

    \b
    Local configuration (stdio):
      {
        "mcpServers": {
          "openalex": {
            "command": "openalex-local",
            "args": ["mcp", "start"]
          }
        }
      }

    \b
    Remote configuration (http):
      # Start server:
      openalex-local mcp start -t http --host 0.0.0.0 --port 8083

      # Client config:
      {
        "mcpServers": {
          "openalex-remote": {
            "url": "http://your-server:8083/mcp"
          }
        }
      }
    """
    run_mcp_server(transport, host, port, force)


@mcp.command("doctor", context_settings=CONTEXT_SETTINGS)
def mcp_doctor():
    """Diagnose MCP server setup and dependencies."""
    click.echo("MCP Server Diagnostics")
    click.echo("=" * 50)
    click.echo()

    # Check fastmcp
    click.echo("Dependencies:")
    try:
        import fastmcp

        click.echo(
            f"  [OK] fastmcp installed (v{getattr(fastmcp, '__version__', 'unknown')})"
        )
    except ImportError:
        click.echo("  [FAIL] fastmcp not installed")
        click.echo("         Fix: pip install openalex-local[mcp]")
        sys.exit(1)

    click.echo()

    # Check database
    click.echo("Database:")
    try:
        db_info = info()
        click.echo("  [OK] Database accessible")
        click.echo(f"       Works: {db_info.get('work_count', 0):,}")
        click.echo(f"       FTS indexed: {db_info.get('fts_indexed', 0):,}")
    except Exception as e:
        click.echo(f"  [FAIL] Database error: {e}")
        sys.exit(1)

    click.echo()
    click.echo("All checks passed! MCP server is ready.")
    click.echo()
    click.echo("Start with:")
    click.echo("  openalex-local mcp start              # stdio (Claude Desktop)")
    click.echo("  openalex-local mcp start -t http      # HTTP transport")


@mcp.command("installation", context_settings=CONTEXT_SETTINGS)
def mcp_installation():
    """Show MCP client installation instructions."""
    click.echo("MCP Client Configuration")
    click.echo("=" * 50)
    click.echo()
    click.echo("1. Local (stdio) - Claude Desktop / Claude Code:")
    click.echo()
    click.echo("   Add to your MCP client config (e.g., claude_desktop_config.json):")
    click.echo()
    click.echo("   {")
    click.echo('     "mcpServers": {')
    click.echo('       "openalex-local": {')
    click.echo('         "command": "openalex-local",')
    click.echo('         "args": ["mcp", "start"],')
    click.echo('         "env": {')
    click.echo('           "OPENALEX_LOCAL_DB": "/path/to/openalex.db"')
    click.echo("         }")
    click.echo("       }")
    click.echo("     }")
    click.echo("   }")
    click.echo()
    click.echo("2. Remote (HTTP) - Persistent server:")
    click.echo()
    click.echo("   Server side:")
    click.echo("     openalex-local mcp start -t http --host 0.0.0.0 --port 8083")
    click.echo()
    click.echo("   Client config:")
    click.echo("   {")
    click.echo('     "mcpServers": {')
    click.echo('       "openalex-remote": {')
    click.echo('         "url": "http://your-server:8083/mcp"')
    click.echo("       }")
    click.echo("     }")
    click.echo("   }")


@mcp.command("list-tools", context_settings=CONTEXT_SETTINGS)
def mcp_list_tools():
    """List available MCP tools."""
    click.echo("Available MCP Tools")
    click.echo("=" * 50)
    click.echo()
    click.echo("1. search")
    click.echo("   Search for academic works by title, abstract, or authors.")
    click.echo("   Parameters:")
    click.echo("     - query (str): Search query")
    click.echo("     - limit (int): Max results (default: 10, max: 100)")
    click.echo("     - offset (int): Skip first N results")
    click.echo("     - with_abstracts (bool): Include abstracts")
    click.echo()
    click.echo("2. search_by_id")
    click.echo("   Get detailed information about a work by OpenAlex ID or DOI.")
    click.echo("   Parameters:")
    click.echo("     - identifier (str): OpenAlex ID or DOI")
    click.echo("     - as_citation (bool): Return formatted citation")
    click.echo()
    click.echo("3. status")
    click.echo("   Get database statistics and status.")
    click.echo("   Parameters: none")
    click.echo()
    click.echo("4. enrich_ids")
    click.echo("   Enrich OpenAlex IDs or DOIs with full metadata.")
    click.echo("   Parameters:")
    click.echo("     - identifiers (list[str]): List of OpenAlex IDs or DOIs")


def run_mcp_server(transport: str, host: str, port: int, force: bool = False):
    """Internal function to run MCP server."""
    try:
        from .mcp_server import run_server
    except ImportError:
        click.echo(
            "MCP server requires fastmcp. Install with:\n"
            "  pip install openalex-local[mcp]",
            err=True,
        )
        sys.exit(1)

    run_server(transport=transport, host=host, port=port, force=force)


def register_mcp_commands(cli_group):
    """Register MCP commands with the main CLI group."""
    cli_group.add_command(mcp)
