CLI Reference
=============

Main Commands
-------------

openalex-local
^^^^^^^^^^^^^^

.. code-block:: text

   Usage: openalex-local [OPTIONS] COMMAND [ARGS]...

   Local OpenAlex database with 284M+ works and full-text search.

   Options:
     --version         Show the version and exit.
     --http            Use HTTP API instead of direct database
     --api-url TEXT    API URL for http mode (default: auto-detect)
     --help-recursive  Show help for all commands recursively.
     -h, --help        Show this message and exit.

   Commands:
     mcp            MCP (Model Context Protocol) server commands.
     relay          Run HTTP relay server for remote database access.
     search         Search for works by title, abstract, or authors.
     search-by-doi  Search for a work by DOI.
     status         Show status and configuration.

search
^^^^^^

.. code-block:: text

   Usage: openalex-local search [OPTIONS] QUERY

   Search for works by title, abstract, or authors.

   Options:
     -n, --number INTEGER  Number of results  [default: 10]
     -o, --offset INTEGER  Skip first N results  [default: 0]
     -a, --abstracts       Show abstracts
     -A, --authors         Show authors
     --concepts            Show concepts/topics
     --json                Output as JSON
     -h, --help            Show this message and exit.

Examples:

.. code-block:: bash

   # Basic search
   openalex-local search "machine learning"

   # With abstracts and authors
   openalex-local search "CRISPR" -a -A -n 5

   # JSON output for scripting
   openalex-local search "neural networks" --json

search-by-doi
^^^^^^^^^^^^^

.. code-block:: text

   Usage: openalex-local search-by-doi [OPTIONS] DOI

   Search for a work by DOI.

   Options:
     --json     Output as JSON
     -h, --help Show this message and exit.

Examples:

.. code-block:: bash

   # By DOI
   openalex-local search-by-doi 10.1038/nature12373

   # By OpenAlex ID
   openalex-local search-by-doi W2741809807

relay
^^^^^

.. code-block:: text

   Usage: openalex-local relay [OPTIONS]

   Run HTTP relay server for remote database access.

   Options:
     --host TEXT     Host to bind  [env: OPENALEX_LOCAL_HOST]
     --port INTEGER  Port to listen on (default: 31292)  [env: OPENALEX_LOCAL_PORT]
     -h, --help      Show this message and exit.

Example:

.. code-block:: bash

   # Start relay on default port
   openalex-local relay

   # Custom port
   openalex-local relay --port 8080

MCP Commands
------------

mcp start
^^^^^^^^^

.. code-block:: text

   Usage: openalex-local mcp start [OPTIONS]

   Start the MCP server.

   Options:
     -t, --transport [stdio|sse|http]  Transport protocol
     --host TEXT                       Host for HTTP/SSE transport
     --port INTEGER                    Port for HTTP/SSE transport
     -h, --help                        Show this message and exit.

mcp doctor
^^^^^^^^^^

Diagnose MCP server setup and dependencies.

.. code-block:: bash

   openalex-local mcp doctor

mcp installation
^^^^^^^^^^^^^^^^

Show MCP client installation instructions.

.. code-block:: bash

   openalex-local mcp installation

mcp list-tools
^^^^^^^^^^^^^^

List available MCP tools.

.. code-block:: bash

   openalex-local mcp list-tools
