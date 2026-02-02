Installation
============

Requirements
------------

- Python 3.10+
- SQLite with FTS5 support (included in most Python installations)
- ~300 GB disk space for full database

Install from PyPI
-----------------

.. code-block:: bash

   pip install openalex-local

With optional dependencies:

.. code-block:: bash

   # Server mode (FastAPI relay)
   pip install openalex-local[server]

   # MCP integration
   pip install openalex-local[mcp]

   # All features
   pip install openalex-local[all]

Install from Source
-------------------

.. code-block:: bash

   git clone https://github.com/ywatanabe1989/openalex-local
   cd openalex-local && pip install -e ".[all]"

Database Setup
--------------

The database can be set up in several ways:

**Option 1: Environment Variable**

.. code-block:: bash

   export OPENALEX_LOCAL_DB=/path/to/openalex.db

**Option 2: Default Locations**

The package searches these locations automatically:

1. ``./openalex.db`` (current directory)
2. ``~/openalex.db`` (home directory)
3. ``~/.openalex/openalex.db``

**Option 3: Build from Scratch**

Building the full database requires ~300 GB disk space:

.. code-block:: bash

   # Check system status
   make status

   # 1. Download OpenAlex Works snapshot (~300GB)
   make download-screen  # runs in background

   # 2. Build SQLite database
   make build-db

   # 3. Build FTS5 index
   make build-fts

HTTP Mode (No Local Database)
-----------------------------

Connect to a remote server instead of using a local database.

**On the server (with database):**

.. code-block:: bash

   openalex-local relay --port 31292

**On your machine:**

.. code-block:: bash

   # Option 1: SSH tunnel
   ssh -L 31292:127.0.0.1:31292 your-server

   # Option 2: Set environment variable
   export OPENALEX_LOCAL_API_URL=http://server-ip:31292
   export OPENALEX_LOCAL_MODE=http

The CLI and Python API work identically in both modes.

Verify Installation
-------------------

.. code-block:: bash

   # Check version
   openalex-local --version

   # Check status and configuration
   openalex-local status

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Description
     - Default
   * - ``OPENALEX_LOCAL_DB``
     - Path to SQLite database
     - Auto-detect
   * - ``OPENALEX_LOCAL_MODE``
     - Force mode: ``db`` or ``http``
     - Auto
   * - ``OPENALEX_LOCAL_API_URL``
     - API URL for HTTP mode
     - ``http://localhost:31292``
   * - ``OPENALEX_LOCAL_PORT``
     - Server port
     - ``31292``
   * - ``OPENALEX_LOCAL_HOST``
     - Server host
     - ``0.0.0.0``
