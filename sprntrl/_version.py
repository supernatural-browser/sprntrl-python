"""Single source of truth for the package version.

Kept in its own module so ``_base_client`` can build the User-Agent
without importing the package ``__init__`` (which would be circular).
Keep in sync with ``pyproject.toml``.
"""

__version__ = "0.1.2"
