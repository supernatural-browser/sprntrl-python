# Changelog

## 0.1.6

- `__version__` / User-Agent now report the real version. The package version has one source,
  `sprntrl/_version.py`, which `pyproject.toml` reads (`[tool.hatch.version]`). The 0.1.5 wheel
  reported `0.1.3`.
- `sessions.create()` (sync + async): new `country` option. `location` is now optional (pass
  `country` instead).
- `OS` accepts `"android"`.

## 0.1.5

- `sessions.create()`: `cache_pack`, `block_trackers`, `block_trackers_exclude`.
