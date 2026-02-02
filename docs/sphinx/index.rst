OpenAlex Local
==============

Local OpenAlex database with 284M+ scholarly works, abstracts, and semantic search.

.. note::
   **Built for the LLM era** - features that matter for AI research assistants:

   - 📚 **284M Works** - More coverage than CrossRef
   - 📝 **Abstracts** - ~45-60% availability for semantic search
   - 🏷️ **Concepts & Topics** - Built-in classification
   - 👤 **Author Disambiguation** - Linked to institutions
   - 🔓 **Open Access Info** - OA status and URLs

Quick Example
-------------

.. code-block:: python

   from openalex_local import search, get, count

   # Full-text search (title + abstract)
   results = search("machine learning neural networks")
   for work in results:
       print(f"{work.title} ({work.year})")
       print(f"  Concepts: {[c['name'] for c in work.concepts]}")

   # Get by OpenAlex ID or DOI
   work = get("W2741809807")
   work = get("10.1038/nature12373")

   # Count matches
   n = count("CRISPR")

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   quickstart
   cli_reference
   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
