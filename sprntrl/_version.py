"""Single source of truth for the package version.

Kept in its own module so ``_base_client`` can build the User-Agent
without importing the package ``__init__`` (which would be circular).
``pyproject.toml`` reads the package version from here (``[tool.hatch.version]``).
"""

__version__ = "0.1.6"
