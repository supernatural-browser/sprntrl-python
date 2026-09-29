import sys
from importlib import metadata
from pathlib import Path

import pytest

import sprntrl
from sprntrl import _base_client

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    tomllib = pytest.importorskip("tomli")

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_reads_version_from_version_module():
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "version" not in cfg["project"]
    assert "version" in cfg["project"]["dynamic"]
    assert cfg["tool"]["hatch"]["version"]["path"] == "sprntrl/_version.py"


def test_user_agent_reports_package_version():
    assert _base_client._USER_AGENT == f"sprntrl-python/{sprntrl.__version__}"


def test_installed_metadata_matches_version():
    try:
        dist_version = metadata.version("sprntrl")
    except metadata.PackageNotFoundError:
        pytest.skip("sprntrl not installed (pip install -e .)")
    assert dist_version == sprntrl.__version__
