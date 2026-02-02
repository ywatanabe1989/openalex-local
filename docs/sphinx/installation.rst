Installation
============

From PyPI
---------

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

From Source
-----------

.. code-block:: bash

   git clone https://github.com/ywatanabe1989/openalex-local
   cd openalex-local && pip install -e ".[all]"

Database Setup
--------------

The database requires ~300 GB disk space and takes 1-2 days to build:

.. code-block:: bash

   # Check system status
   make status

   # 1. Download OpenAlex Works snapshot (~300GB)
   make download-screen  # runs in background

   # 2. Build SQLite database
   make build-db

   # 3. Build FTS5 index
   make build-fts

Remote Mode (HTTP)
------------------

If you have the database on a remote server:

1. Start the relay server on the database server:

   .. code-block:: bash

      openalex-local relay --port 31292

2. On your local machine, connect via SSH tunnel:

   .. code-block:: bash

      ssh -L 31292:127.0.0.1:31292 your-server

3. Use the CLI normally (auto-detects HTTP mode):

   .. code-block:: bash

      openalex-local search "neural networks"

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
