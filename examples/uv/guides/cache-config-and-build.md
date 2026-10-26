# Cache, configuration, storage, preview features and the uv build backend

Source pages: https://docs.astral.sh/uv/concepts/build-backend/, https://docs.astral.sh/uv/concepts/cache/, https://docs.astral.sh/uv/concepts/configuration-files/, https://docs.astral.sh/uv/concepts/preview/, https://docs.astral.sh/uv/reference/storage/

## The uv build backend (`uv_build`)

A build backend turns a source tree into an sdist or wheel. uv works with any PEP 517 backend but also ships its own, `uv_build`: zero-config defaults, validates metadata and project structure, very fast.

- **Pure Python only.** Extension modules need another backend. If you need build scripts or a more flexible layout, the docs suggest `hatchling`.

```toml
[build-system]
requires = ["uv_build>=0.13.5,<0.14"]
build-backend = "uv_build"
```

- Follows uv's versioning policy. **Keep the upper bound** so the package keeps building as new versions ship.
- `uv init` creates projects that use it, and `uv build` builds the sdist and wheel.
- **Bundled copy**: the `uv` binary includes the backend and uses it for uv-driven builds when it satisfies the `uv_build` requirement. Otherwise it fetches a compatible `uv_build`. Other frontends (`python -m build`) always use the `uv_build` package, usually the latest compatible version.
- Debugging under non-uv frontends: `RUST_LOG=uv=debug` or `RUST_LOG=uv=verbose`. Under uv it shares uv's verbosity.

### Module discovery

- Default: a single root module at `src/<package_name>/__init__.py`. `src/` is the default discovery directory.
- Name normalization: lowercase, with `.` and `-` replaced by `_` (`Foo-Bar` becomes `foo_bar`).
- Override with `module-name` and `module-root`:

```toml
[tool.uv.build-backend]
module-name = "FOO"
module-root = ""        # module directly in project root
```

- **Namespace packages**: a `.` in `module-name`, e.g. `module-name = "foo.bar"` for `src/foo/bar/__init__.py`. Important: `foo` gets **no** `__init__.py`, since it's the shared namespace.
- Several root modules: `module-name = ["foo", "bar"]`. Supported but not recommended; the docs advise a workspace with multiple packages instead.
- `namespace = true` skips declaring every module. **Warning: it disables safety checks.** Prefer an explicit list outside legacy projects. To declare the root explicitly, combine it with `module-name = "foo"`.
- **Stub packages**: a `-stubs` suffix (e.g. `foo-stubs`). The `-` is not normalized, and uv looks for `__init__.pyi` (`src/foo-stubs/__init__.pyi`). Namespace stubs are supported too.

### File inclusion and exclusion

Includes are applied first, then excludes, so **excludes always win**. Default excludes are `__pycache__`, `*.pyc` and `*.pyo`.

Sdist contains:

- `pyproject.toml` rewritten in TOML 1.0-compatible syntax, plus the original as `pyproject.toml.orig`. The preview page lists this rewrite as the `toml-backwards-compatibility` preview feature.
- The module under `tool.uv.build-backend.module-root`.
- Files from `project.license-files` and `project.readme`.
- All directories under `tool.uv.build-backend.data`.
- Files matching `tool.uv.build-backend.source-include`.
- Minus `source-exclude` and the default excludes.

Wheel contains:

- The module, plus license files (into `.dist-info`), the readme (into the metadata) and `data` directories (into `.data`).
- Minus `source-exclude`, `wheel-exclude` and the default excludes. Sdist excludes also apply so a wheel built straight from the tree never has more files than one built via the sdist.
- There are no wheel-specific includes. There must be exactly one top-level module, and data must live under the module root or in a `data` directory. Most packages keep small data next to the source.

Glob syntax (PEP 639 reduced portable glob, plus backslash escaping):

- **Includes are anchored**: `pyproject.toml` means only `<root>/pyproject.toml`. Use `src/**` for recursion. `assets/**/sample.csv` is also anchored.
- Avoid unanchored include patterns like `**/sample.csv` (performance and reproducibility).
- **Excludes are not anchored**: `__pycache__` matches at any depth, and the children of an excluded dir are excluded too. Anchor with a leading `/` (`/dist`).

## Caching

### What gets cached and how

- **Registry deps**: HTTP caching headers.
- **Direct URL deps**: HTTP headers plus the URL itself.
- **Git deps**: the fully resolved commit hash, which is why `uv pip compile` pins Git deps to a commit.
- **Local archives** (`.whl`/`.tar.gz`): file mtime. **Local directories**: mtime of `pyproject.toml`, `setup.py` or `setup.cfg`.
- **Flat indexes** (`--find-links`): contents are treated as immutable and cached by filename. Rebuilding a wheel under the same name isn't picked up until you refresh.
- Special case: local directories passed explicitly on the command line (`uv pip install .`) are always rebuilt and reinstalled.

### Escape hatches

```console
$ uv cache clean                  # everything
$ uv cache clean ruff             # one package
$ uv sync --refresh               # revalidate all cached data (any command)
$ uv sync --refresh-package ruff  # revalidate one package
$ uv sync --reinstall             # ignore installed versions (consider `uv cache clean <pkg>` first)
```

### Cache keys for dynamic metadata: `tool.uv.cache-keys`

By default, local directory deps (e.g. editables) are rebuilt only when `pyproject.toml`, `setup.py` or `setup.cfg` changes, or a `src` dir is added or removed. That heuristic can miss changes. **Setting `cache-keys` replaces the defaults, so include `pyproject.toml` yourself.**

```toml
[tool.uv]
cache-keys = [{ file = "pyproject.toml" }, { git = { commit = true } }]               # setuptools-scm versions
cache-keys = [{ file = "pyproject.toml" }, { git = { commit = true, tags = true } }]  # version from tags
cache-keys = [{ file = "pyproject.toml" }, { file = "requirements.txt" }]            # deps read from a file
cache-keys = [{ file = "**/*.toml" }]                                                # glob (`glob` crate syntax)
cache-keys = [{ file = "pyproject.toml" }, { env = "MY_ENV_VAR" }]                   # env var
cache-keys = [{ file = "pyproject.toml" }, { dir = "src" }]                          # dir created/removed
```

- Globs can be expensive because uv may traverse large trees.
- `dir` only tracks the directory itself (creation/removal), not changes inside it.
- Last resort: `reinstall-package = ["my-package"]` under `[tool.uv]` rebuilds and reinstalls on **every** run.

### Safety

- Concurrent uv commands are safe, even against the same venv. The cache supports multiple readers and writers, and installs take a file lock on the target venv.
- Interrupted or overlapping HTTP cache refreshes are detected and re-downloaded. With `--offline`, an affected entry is unavailable until refreshed online.
- **Never modify the cache directly** (e.g. deleting files).

### Clearing and pruning

- `uv cache clean`: removes all entries. The directory and its lock file stay so other processes can share it.
- `uv cache clean <pkg>`: entries for one package.
- `uv cache prune`: removes **unused** entries (e.g. from older uv versions) and all centralized project environments, which are recreated as needed. Safe to run periodically.
- Cache-modifying commands wait for other uv processes, with a **5 min** default timeout (`UV_LOCK_TIMEOUT`). `--force` ignores the lock when you know nothing else is using the cache.
- Reclaimed-space numbers are estimates. The preview `--preview-features cache-physical-space` measures physical space (hardlinks, CoW clones) on macOS and Linux and reports a lower bound for unmeasurable entries such as compressed Btrfs extents.

### CI caching

- uv caches both built-from-source wheels and downloaded pre-built wheels by default.
- In CI it's often faster to *drop* pre-built wheels (re-downloading is cheap) and keep source-built wheels (building is expensive, especially extension modules).
- **Run `uv cache prune --ci` at the end of the CI job.** It removes pre-built wheels and unzipped sdists but keeps wheels built from source.

### Cache directory resolution

1. A temporary dir if `--no-cache` (uv *always* needs a cache; this one lasts for the invocation only).
2. `--cache-dir`, `UV_CACHE_DIR`, or `tool.uv.cache-dir`.
3. System default: `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv` (Unix), `%LOCALAPPDATA%\uv\cache` (Windows).

- **Prefer `--refresh` over `--no-cache`**: it skips reading the cache but still updates it for later runs.
- **Keep the cache on the same filesystem as your environments**, or uv can't link files and falls back to slower copies.
- `uv cache dir` prints the path.

### Versioning

- The cache is split into buckets (wheels, sdists, Git, ...), each versioned. A breaking format change bumps the bucket version (e.g. uv 0.4.13 bumped core metadata from v12 to v13), and uv never touches incompatible buckets.
- Multiple uv versions can safely share one cache dir. Across a bucket bump they just won't share entries (you may get duplicates).

## Configuration files

### Discovery

- Project level: uv looks for `pyproject.toml` or `uv.toml` in the cwd, then the nearest parent.
  - `pyproject.toml` counts only if it has a `[tool.uv]` table; otherwise uv keeps searching upward.
  - `uv.toml` has the same structure without the `tool.uv` prefix (`[[index]]` instead of `[[tool.uv.index]]`).
  - **If both are in one directory, `uv.toml` wins and `[tool.uv]` in `pyproject.toml` is ignored.**
- Workspaces: the search starts at the workspace root. Member configs are ignored, because the workspace is locked as one unit.
- `uv tool` commands ignore local config and read only user- and system-level config.
- User level: `~/.config/uv/uv.toml` (macOS/Linux) or `%APPDATA%\uv\uv.toml` (Windows). System level: `/etc/uv/uv.toml` or `%PROGRAMDATA%\uv\uv.toml`.
- **User and system configs must be `uv.toml`. The `pyproject.toml` format isn't allowed there.**

```toml
# pyproject.toml
[[tool.uv.index]]
url = "https://test.pypi.org/simple"
default = true
```

### Precedence and merging

- Order: **CLI > environment variables > project > user > system**.
- Scalars (string, number, bool): the higher-priority value wins. Arrays are concatenated, with project entries first.
- With multiple system configs (e.g. `/etc/uv/uv.toml` and `$XDG_CONFIG_DIRS/uv/uv.toml`), only the first found is used, and XDG takes priority.
- `--no-config`: skip all persistent config discovery (this also disables `.python-version` discovery).
- `--config-file <path/uv.toml>`: use only this file. All discovered files, including user-level, are ignored.

### `[tool.uv.pip]`

Applies **only** to `uv pip` subcommands. Many settings have top-level equivalents that also apply to `uv pip` unless `[tool.uv.pip]` overrides them. Kept separate to stay pip-compatible while top-level settings can use different designs (e.g. `--no-build`).

```toml
[tool.uv.pip]
index-url = "https://test.pypi.org/simple"   # affects `uv pip install`, not `uv sync`/`uv lock`/`uv run`
```

### `.env` files (`uv run`)

- dotenv files (`.env`, `.env.local`, `.env.development`, ...), loaded via the `dotenvy` crate.
- Load with `--env-file <path>` or `UV_ENV_FILE`. Repeat `--env-file`, and later files override earlier ones. In `UV_ENV_FILE`, separate paths with spaces (`"/path/to/file1 /path/to/file2"`).
- Disable with `--no-env-file` or `UV_NO_ENV_FILE=1`, which overrides both of the above.
- **Real environment variables win over `.env` values.**

```console
$ echo "MY_VAR='Hello, world!'" > .env
$ uv run --env-file .env -- python -c 'import os; print(os.getenv("MY_VAR"))'
```

## Storage directories

For each location uv uses the first path that exists in the order below. It follows XDG on Linux and macOS and Known Folders on Windows.

- **Temporary**: `$TMPDIR`, `/tmp`, `%TMP%`, `%TEMP%`, `%USERPROFILE%`
- **Cache** (disposable): `$XDG_CACHE_HOME/uv`, `$HOME/.cache/uv`, `%LOCALAPPDATA%\uv\cache`, `uv\cache` in `FOLDERID_LocalAppData`
- **Persistent data**: `$XDG_DATA_HOME/uv`, `$HOME/.local/share/uv`, `$CWD/.uv`, `%APPDATA%\uv\data`, `.\.uv`
- **User config**: `$XDG_CONFIG_HOME/uv`, `$HOME/.config/uv`, `%APPDATA%\uv`, `uv` in `FOLDERID_RoamingAppData`
- **System config**: `$XDG_CONFIG_DIRS/uv`, `/etc/uv`, `%PROGRAMDATA%\uv`, `uv` in `FOLDERID_AppDataProgramData`
- **Executables** (should be on `PATH`): `$XDG_BIN_HOME`, `$XDG_DATA_HOME/../bin`, `$HOME/.local/bin`, `%XDG_BIN_HOME%`, `%XDG_DATA_HOME%\..\bin`, `%USERPROFILE%\.local\bin`

Where each kind of data lives:

| Data | Default | Show | Override |
| --- | --- | --- | --- |
| Dependency cache | cache dir (temp dir if disabled) | `uv cache dir` | `--cache-dir`, `UV_CACHE_DIR`, `cache-dir` |
| Managed Pythons | `<data>/python` | `uv python dir` | `UV_PYTHON_INSTALL_DIR` |
| Python executables | executable dir | `uv python dir --bin` | `UV_PYTHON_BIN_DIR` |
| Tools | `<data>/tools` | `uv tool dir` | `UV_TOOL_DIR` |
| Tool executables | executable dir | `uv tool dir --bin` | `UV_TOOL_BIN_DIR` |
| `uv`/`uvx` (standalone installer) | executable dir | | `UV_INSTALL_DIR` |
| Project venv | `.venv` in project/workspace root | | `UV_PROJECT_ENVIRONMENT` |
| Script venvs (inline metadata) | cache dir | | |

- Changing `UV_PYTHON_INSTALL_DIR` doesn't update existing venvs; recreate them.
- With the `centralized-project-envs` preview, default project venvs live in the cache dir (`.venv` links to them). `uv cache clean` or `uv cache prune` removes them, and they're recreated when needed.

## Preview features

### Enabling

```console
$ uv run --preview ...                                # all
$ UV_PREVIEW=1 uv run ...
$ uv run --preview-features foo --preview-features bar ...
$ uv run --preview-features foo,bar ...
$ UV_PREVIEW_FEATURES=foo,bar uv run ...
$ uv run --no-preview ...                             # disable
```

```toml
# uv.toml, [tool.uv] in pyproject.toml, or PEP 723 script metadata
preview-features = ["foo", "bar"]   # or `true` for all
```

- Some features act **before config is loaded**, so they only work via CLI or env var (`project-directory-must-exist`, `target-workspace-discovery`).
- Unknown feature names warn but don't error, whatever the source.
- Features that are gated by user action work without opt-in but print a warning, e.g. `uv pip install -r pylock.toml`. Enabling the feature silences the warning.

### Available features (one line each)

- `add-bounds`: `add-bounds` setting picks the bounds `uv add` writes (major, minor, exact pin instead of a lower bound).
- `adjust-ulimit`: on Unix, raises the soft open-file limit to the hard limit at startup.
- `artifact-hash-filtering`: `uv pip compile --generate-hashes` only hashes artifacts allowed by binary/build policies.
- `audit-command`: `uv audit` / `uv tool audit` check dependencies for known vulnerabilities.
- `auth-helper`: `uv auth helper` serves credentials to external tools (Bazel credential helper protocol).
- `azure-endpoint`, `gcs-endpoint`, `s3-endpoint`: authenticate to Azure Blob, GCS or S3-compatible endpoints (`UV_AZURE_ENDPOINT_URL`, `UV_GCS_ENDPOINT_URL`, `UV_S3_ENDPOINT_URL`).
- `batch-export`: `uv export --batch` reads a TOML manifest of `[[export]]` entries.
- `build-dependency-check`: checks build requirements before a non-isolated `uv build` (`--skip-dependency-check` skips it).
- `build-dependency-hashes`: `--require-build-hashes` requires hashes for all (transitive) build deps.
- `build-lazy-imports`: lazy imports for build backends on CPython 3.15+.
- `cache-physical-space`: accurate reclaimed-space reporting (macOS/Linux).
- `cache-size`: `uv cache size` command.
- `centralized-project-envs`: project venvs stored in the cache, with `.venv` linked. Not applied to explicit paths or `--active`.
- `check-command`: `uv check` type-checks with ty.
- `content-addressed-cache`: wheel archives cached by content digest, which deduplicates.
- `detect-module-conflicts`: warns when packages install conflicting modules.
- `extra-build-dependencies`: adds build deps without disabling isolation (`match-runtime = true` available).
- `format-command`: `uv format` runs Ruff (`--check`, `--diff`).
- `frozen-lockfile`: frozen commands work from `uv.lock` without `pyproject.toml`. Needs lockfile revision 5+.
- `index-by-name`: `--index` / `--default-index` accept configured names.
- `index-exclude-newer`: per-index `exclude-newer`.
- `index-hash-algorithm`: per-index required `hash-algorithm`.
- `init-project-flag`: `uv init` rejects the deprecated `--project`; pass the directory positionally.
- `json-output`: `--output-format json` (e.g. `uv tree`). Schemas are experimental.
- `lock-without-metadata`: drops `package.metadata` from `uv.lock` except for remote URL and Git deps.
- `lockfile-format-check`: `--locked` / `--check` reject non-canonical lockfile formatting.
- `lockfile-normalization`: merges equivalent declarations in lockfiles.
- `malware-check`: checks packages against OSV for malware before installing.
- `metadata-json`: build backend adds `METADATA.json` / `WHEEL.json` to wheels.
- `minimum-libc-version`: minimum glibc/musl for `required-environments`.
- `missing-exclude-newer-package-lock`: omits `exclude-newer-package` entries for packages not in the resolution.
- `native-auth`: `uv auth` uses the OS credential store.
- `package-conflicts`: package-level conflicts between workspace members.
- `packaged-init`: `uv init` defaults to a packaged app (`src/` layout, build system, entry point).
- `project-directory-must-exist`: `--project` errors on invalid paths (CLI/env only).
- `publish-require-normalized`: `uv publish` skips non-normalized filenames.
- `pylock`: `uv pip install -r pylock.toml` / `uv pip sync pylock.toml`.
- `python-install-default`: `uv python install --default` also installs `python`/`python3`.
- `relocatable-envs-default`: relocatable venvs by default (`uv venv --no-relocatable` opts out).
- `resolution-inputs`: records only the settings that were consulted in resolution in the lockfile.
- `sbom-export`: `uv export --format cyclonedx1.5`.
- `special-conda-env-names`: Conda envs named `base`/`root` are classified by path.
- `target-workspace-discovery`: `uv run <target>` discovers the project from the target's directory (CLI/env only).
- `toml-backwards-compatibility`: sdist `pyproject.toml` rewritten as TOML 1.0, original kept as `.orig`.
- `tool-install-locks`: stores a `uv.lock` per installed tool (used by `uv tool audit`).
- `venv-safe-clear`: `uv venv --clear` refuses dirs without `pyvenv.cfg` unless `--force`.
- `wheel-variants`: experimental PEP 825 wheel variants.
- `workspace-dir`, `workspace-list`, `workspace-list-scripts`, `workspace-metadata`: `uv workspace dir` / `list` (`--paths`, `--scripts`) / `metadata` (`--sync`).
