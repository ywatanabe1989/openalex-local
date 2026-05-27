openalex_local API
==================

The ``openalex_local`` package exposes a small set of functions
(``search``, ``get``, ``count``, ``info``, ``configure``,
``get_mode``) and the ``Work`` / ``SearchResult`` dataclasses, plus
the ``Config`` singleton from ``openalex_local._core.config``. Each
is documented below.

Core Functions
--------------

search
^^^^^^

.. autofunction:: openalex_local.search

get
^^^

.. autofunction:: openalex_local.get

count
^^^^^

.. autofunction:: openalex_local.count

info
^^^^

.. autofunction:: openalex_local.info

Configuration
-------------

configure
^^^^^^^^^

.. autofunction:: openalex_local.configure

get_mode
^^^^^^^^

.. autofunction:: openalex_local.get_mode

Data Classes
------------

Work
^^^^

.. autoclass:: openalex_local.Work
   :members:
   :undoc-members:
   :show-inheritance:

SearchResult
^^^^^^^^^^^^

.. autoclass:: openalex_local.SearchResult
   :members:
   :undoc-members:
   :show-inheritance:

Config
^^^^^^

.. autoclass:: openalex_local._core.config.Config
   :members:
   :undoc-members:
   :show-inheritance:
