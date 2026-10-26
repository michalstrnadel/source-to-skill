# Settings reference

Source pages: https://docs.astral.sh/uv/reference/settings/

Every setting on the uv settings reference page, grouped as the page groups them: **Project metadata** (`[tool.uv]` keys that describe the project itself, plus `[tool.uv.build-backend]` and `[tool.uv.workspace]`), then **Configuration** (resolver, installer, index, cache, Python, network and publish settings), then the `[tool.uv.audit]` and `[tool.uv.pip]` tables. Format per key: `key` (type, default): what it does.

## Where settings go

- `pyproject.toml`: the keys go under `[tool.uv]`, and sub-tables become `[tool.uv.pip]`, `[tool.uv.audit]`, `[tool.uv.build-backend]`, `[tool.uv.workspace]`, `[tool.uv.sources]`, `[[tool.uv.index]]`.
- `uv.toml`: the same Configuration keys sit at the top level with no `tool.uv` prefix, and sub-tables become `[pip]` and `[audit]`.
- Project metadata keys are shown only with `pyproject.toml` examples. Several are read **only from the workspace root `pyproject.toml`** by `uv lock`, `uv sync` and `uv run`. Declarations in other workspace members or in `uv.toml` files are ignored for: `build-constraint-dependencies`, `constraint-dependencies`, `exclude-dependencies`, `override-dependencies`.
- For these Configuration keys the page shows a `uv.toml` example only: `cache-dir`, `http-proxy`, `https-proxy`, `no-proxy`, `native-tls`, `system-certs`, `python-install-mirror`, `pypy-install-mirror`, `graalpy-install-mirror`, `pyodide-install-mirror`, `python-downloads-json-url`.
- `[tool.uv.pip]` / `[pip]` values are ignored outside the `uv pip` namespace (e.g. by `uv lock` and `uvx`).

```toml
# pyproject.toml
[tool.uv]
resolution = "lowest-direct"

[tool.uv.pip]
all-extras = true
```

```toml
# uv.toml (no tool.uv prefix)
resolution = "lowest-direct"
cache-dir = "./.uv_cache"

[pip]
all-extras = true
```

## Project metadata (`[tool.uv]`)

- `build-constraint-dependencies` (`list[str | dict]`, `[]`): constrains build-dependency versions when building packages during resolution or install. A constraint does *not* trigger installation. Read only from the workspace root. To verify downloaded build-dependency archives, give a table with `requirement` and `hashes`; uv records those hashes in `uv.lock`.
- `conflicts` (`list[list[dict]]`, `[]`): declares extras or groups that are mutually exclusive, so uv can still produce a universal resolution when, e.g., extra `foo` needs `numpy==2.0.0` and extra `bar` needs `numpy==2.1.0`. Trade-off: installation fails if a user activates both.
- `constraint-dependencies` (`list[str]`, `[]`): constraints on the project's dependency resolution. Additive, and they don't trigger installation on their own. Read only from the workspace root.
- `default-groups` (`str | list[str]`, `["dev"]`): dependency groups installed by default. `"all"` enables every group.
- `dependency-groups` (`dict`, `[]`): extra settings per group. Currently it can only add `requires-python`, e.g. `[tool.uv.dependency-groups] my-group = {requires-python = ">=3.12"}`. It cannot *define* groups; use the top-level `[dependency-groups]` table for that.
- `dev-dependencies` (`list[str]`, `[]`): legacy dev deps, installed by default by `uv run`/`uv sync` and not published. "Not recommend anymore": use `dependency-groups.dev` instead. The two are combined into the `dev` group.
- `environments` (`str | list[str]`, `[]`): **limits** the environments that `uv lock` resolves for, which improves performance and avoids unsatisfiable branches. `uv pip compile --universal` respects it too. Example: `environments = ["sys_platform == 'darwin'"]`.
- `exclude-dependencies` (`list[str | dict]`, `[]`): never selects a package, even when transitive deps request it. Useful for dropping optional deps or working around broken ones. Scope it with `{ package = { name, version? }, dependencies = [...] }`; a version-specific entry beats an all-versions entry. Read only from the workspace root.
- `index` (`dict`, `[]`): indexes to resolve against (PEP 503 or a local directory in that layout). See [Index settings](#index-settings).
- `managed` (`bool`, `true`): `false` makes `uv run` ignore the project.
- `minimum-libc-version` (`dict[str, str]`, `None`): **preview**. Sets the minimum libc for Linux in universal resolution. With `{ glibc = "2.31" }`, `manylinux_2_17` wheels count as coverage and `manylinux_2_34` wheels do not; both stay in the lockfile. Pair it with `required-environments` for the architectures. Respected by `uv lock` and `uv pip compile --universal`. Enable with `preview-features = ["minimum-libc-version"]`.
- `override-dependencies` (`list[str | dict]`, `[]`): forces a version regardless of what other packages request. Overrides are *absolute* (they replace requirements); constraints are *additive*. They don't trigger installation. The scoped form `{ package = {...}, dependencies = [...] }` replaces same-name deps and adds new ones. Scoped overrides support registry version specifiers only: no URL, path, Git or explicit-index sources. Read only from the workspace root.
- `package` (`bool`, `true`): `false` makes the project virtual, so it is not built or installed and only its deps go into the venv. A package is installed editable and needs a `build-system` plus a layout the backend expects (e.g. `src`).
- `required-environments` (`str | list[str]`, `[]`): **expands** the platforms that must be supported. Any package without an sdist must ship a wheel for each listed environment, or resolution fails. Rule: `environments` limits, `required-environments` requires.
- `sources` (`dict`, `{}`): dev-time sources per dependency (Git, URL, local path, alternative registry). See https://docs.astral.sh/uv/concepts/projects/dependencies/.

```toml
[tool.uv]
override-dependencies = [
    "werkzeug==2.3.0",
    { package = { name = "flask", version = "3.0.0" }, dependencies = ["itsdangerous==2.1.2"] },
]
required-environments = [
    "sys_platform == 'darwin' and platform_machine == 'arm64'",
    "sys_platform == 'linux' and platform_machine == 'x86_64'",
]
conflicts = [[{ extra = "extra1" }, { extra = "extra2" }]]

[tool.uv.sources]
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
pydantic = { path = "/path/to/pydantic", editable = true }
```

## Build backend (`[tool.uv.build-backend]`)

These apply only to the `uv_build` backend. Other backends, such as hatchling, have their own config. Glob options use PEP 639 portable globs.

- `data` (`dict[str, str]`, `{}`): directories copied into `<name>-<version>.data/(purelib|platlib|headers|scripts|data)`.
  - `scripts`: goes to the venv `bin`/`Scripts` directory, which is on `PATH` under `uv run`. Prefer `project.scripts` for Python entrypoints.
  - `data`: installed over the venv root and may override existing files.
  - `headers`: goes to the include directory.
  - `purelib`/`platlib`: go to site-packages and are not recommended.
  - Small data files usually belong inside the module instead.
- `default-excludes` (`bool`, `true`): `false` drops the default excludes `__pycache__`, `*.pyc`, `*.pyo`.
- `module-name` (`str | list[str]`, `None`): module directory inside `module-root`. The default is the package name with `.` and `-` replaced by `_`.
  - The directory needs an `__init__.py`. Exception: `-stubs` packages, which use `__init__.pyi`.
  - Use a dotted path (`foo.bar`) for a namespace package with a single module.
  - Use a list for multiple modules. The page recommends one module per package, with multiple packages split into a workspace.
  - Risk: two packages with the same module name corrupt each other when installed together.
- `module-root` (`str`, `"src"`): directory containing the module. `""` gives a flat layout.
- `namespace` (`bool`, `false`): builds a PEP 420 implicit namespace package with multiple root `__init__.py`. With a single root `__init__.py`, use a dotted `module-name` instead.
- `source-exclude` (`list[str]`, `[]`): globs excluded from the sdist. Also applied to wheels, so a wheel built from the tree matches one built from the sdist.
- `source-include` (`list[str]`, `[]`): extra globs for the sdist. `pyproject.toml` and the module directory are always included.
- `wheel-exclude` (`list[str]`, `[]`): globs excluded from the wheel.

```toml
[tool.uv.build-backend]
module-name = "sklearn"
module-root = ""          # flat layout
source-include = ["tests/**"]
data = { headers = "include/headers", scripts = "bin" }
```

## Workspace (`[tool.uv.workspace]`)

- `members` (`list[str]`, `[]`): workspace members, as globs or explicit paths.
- `exclude` (`list[str]`, `[]`): excluded members. A package matching both `members` and `exclude` is excluded.

```toml
[tool.uv.workspace]
members = ["member1", "path/to/member2", "libs/*"]
# exclude takes the same glob/path forms, e.g. exclude = ["member1", "libs/*"]
```

## Configuration: resolver

- `resolution` (`"highest"` default): also `"lowest"` or `"lowest-direct"` (lowest for direct deps, highest for transitive).
- `prerelease` (`"if-necessary"` default): uses stable versions and falls back to pre-releases only after every stable candidate is rejected. Other values:
  - `"disallow"`
  - `"allow"`
  - `"explicit"`: pre-releases only for first-party packages with explicit pre-release specifiers.
  - `"if-necessary-or-explicit"`: deprecated alias for `if-necessary`.
- `prerelease-package` (`dict`, `{}`): per-package pre-release mode that beats the global `prerelease`, e.g. `{ numpy = "allow", scipy = "disallow" }`.
- `fork-strategy` (`"requires-python"` default): picks the latest version per supported Python while minimizing versions across platforms. `"fewest"` minimizes versions per package and may prefer older, more widely compatible ones.
- `exclude-newer` (`str | false`, `None`): considers only artifacts uploaded before a point in time.
  - Compared against each file's upload time, not the release date.
  - Accepts RFC 3339 (`2006-12-02T02:07:43Z`), a friendly duration (`24 hours`, `1 week`, `30 days`) or ISO 8601 (`PT24H`, `P7D`).
  - Durations assume 24h days (DST is ignored); months and years are not allowed.
  - `false` disables it.
- `exclude-newer-package` (`dict`, `None`): per-package dates, e.g. `{ tqdm = "2022-04-04T00:00:00Z", markupsafe = false }`. `false` exempts a package from the global `exclude-newer`.
- `dependency-metadata` (`list[dict]`, `[]`): static metadata, so uv skips the registry query or source build. Respected fields: `name`, `version` (omitted means all versions), `requires-dist`, `requires-python`, `provides-extra`.
- `no-sources` (`bool`, `false`): ignores `tool.uv.sources` and locks against publishable metadata. `no-sources-package` (`list[str]`, `[]`) does the same per package.
- `upgrade` (`bool`, `false`): ignores pinned versions in existing output. `upgrade-package` (`list[str]`, `[]`) accepts `ruff` or `ruff<0.5.0`.
- `add-bounds` (`"lower"` default, **preview**): the specifier `uv add` writes.
  - `"lower"`: `>=1.2.3`
  - `"major"`: `>=1.2.3, <2.0.0`
  - `"minor"`: `>=1.2.3, <1.3.0`
  - `"exact"`: `==1.2.3`
  - With `--frozen`, deps are added without constraints.
- `required-version` (`str`, `null`): PEP 440 specifier for the uv version, e.g. `">=0.5.0"`. uv exits with an error if unmet.
- `preview-features` (`bool | list[str]`, `false`): enables all (`true`) or named preview features, e.g. `["json-output"]`. Unknown names produce a warning.

## Configuration: indexes and auth

<a id="index-settings"></a>
- `index` (`dict`, `[]`): the `[[tool.uv.index]]` entries.
  - Priority follows definition order (first-defined is highest), and these beat `index-url`/`extra-index-url`.
  - uv uses the first index that has a package, unless `index-strategy` says otherwise.
  - `explicit = true`: the index is used only by deps that select it via `[tool.uv.sources]`.
  - `default = true`: the index moves to lowest priority and disables the PyPI default.
- `index-strategy` (`"first-index"` default): stops at the first index that has the package, which prevents "dependency confusion" attacks. Other values:
  - `"unsafe-first-match"`: searches all indexes, exhausting the first one before moving on.
  - `"unsafe-best-match"`: picks the best version across all indexes; when a version is in several, only the first index's entry is used.
- `index-url` (`str`, `"https://pypi.org/simple"`): **deprecated, use `index`**. Lower priority than `extra-index-url` and `index`.
- `extra-index-url` (`list[str]`, `[]`): **deprecated, use `index`**. Beats `index-url` and any `index` with `default = true`; earlier values win.
- `find-links` (`list[str]`, `[]`): a directory with top-level `.whl`/sdists, or a URL to a flat list of links.
- `no-index` (`bool`, `false`): ignores all registries and uses only direct URLs and `find-links`.
- `keyring-provider` (`str`, `"disabled"`): only `subprocess` is supported, which uses the `keyring` CLI.
- `allow-insecure-host` (`list[str]`, `[]`): hostname, `host:port` or URL that skips certificate verification. "Only use `--allow-insecure-host` in a secure network with verified sources", because it exposes you to MITM attacks.
- `torch-backend` (`str`, `null`, **preview**): `cpu`, `cu126`, or `auto` (detects from installed CUDA drivers). Ignores the configured indexes for PyTorch-ecosystem packages. **Only respected by `uv pip` commands.**

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch" }
```

## Configuration: build and install

- `no-build` (`bool`, `false`): never builds sdists, though cached wheels are reused. First-party/workspace packages and editables are still built, and their backends may run arbitrary code. `no-build-package` (`list[str]`, `[]`) does this per package.
- `no-binary` (`bool`, `false`): installs from source, though the resolver still uses wheels for metadata. `no-binary-package` (`list[str]`, `[]`) does this per package.
- `no-build-isolation` (`bool`, `false`): assumes PEP 518 build deps are already installed. `no-build-isolation-package` (`list[str]`, `[]`) does this per package.
- `config-settings` (`dict`, `{}`): PEP 517 `KEY=VALUE` settings, e.g. `{ editable_mode = "compat" }`. `config-settings-package` (`dict`, `{}`) sets them per package, e.g. `{ numpy = { editable_mode = "compat" } }`.
- `extra-build-dependencies` (`dict`, `[]`): adds packages to a dependency's build environment, for packages that assume e.g. `pip` without declaring it. Example: `{ pytest = ["setuptools"] }`.
- `extra-build-variables` (`dict[str, dict[str, str]]`, `{}`): env vars for specific builds, e.g. `{ flash-attn = { FLASH_ATTENTION_SKIP_CUDA_BUILD = "TRUE" } }`.
- `require-build-hashes` (`bool`, `false`): requires hashes for every build dependency, including transitive ones.
  - Hashes come from `build-constraint-dependencies` or URL fragments in `build-system.requires`. Hashes returned by a backend don't count.
  - Not required for the bundled `uv_build`.
  - Not checked when build isolation is off, nor for already-installed packages or built wheels.
  - Also applies to `uv pip`, where `[tool.uv.pip]` can override it.
- `compile-bytecode` (`bool`, `false`): compiles `.py` to `.pyc` after install instead of lazily on first import. This trades install time for start time (CLIs, Docker). It processes the whole site-packages and, like pip, ignores errors.
- `link-mode` (default `"clone"` on macOS/Linux, `"hardlink"` on Windows): also `"copy"` or `"symlink"`. Symlink is discouraged: `uv cache clean` breaks every installed package.
- `reinstall` (`bool`, `false`): reinstalls everything and implies `refresh`. `reinstall-package` (`list[str]`, `[]`) does this per package and implies `refresh-package`.

## Configuration: cache

- `cache-dir` (`str`, `None`): defaults to `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv` on Linux/macOS, and `%LOCALAPPDATA%\uv\cache` on Windows.
- `cache-keys` (`list[dict]`, default `[{ file = "pyproject.toml" }, { file = "setup.py" }, { file = "setup.cfg" }]`): what triggers a rebuild of the project.
  - By default uv also rebuilds when a `src` dir is added or removed.
  - Supports `{ file = ... }` (globs like `**/*.toml` are allowed but may be expensive), `{ dir = ... }`, `{ git = { commit = true, tags = true } }` and `{ env = "MACOSX_DEPLOYMENT_TARGET" }`.
  - Applies only to the project that declares it; paths are relative to that project.
- `no-cache` (`bool`, `false`): uses a temporary directory for the operation instead of the cache.

```toml
[tool.uv]
# dynamic deps read from requirements.txt, version from setuptools_scm
cache-keys = [{ file = "pyproject.toml" }, { file = "requirements.txt" }, { git = { commit = true } }]
```

## Configuration: concurrency and network

- `concurrent-downloads` (`int`, `50`): maximum in-flight downloads.
- `concurrent-builds` (`int`, default: number of CPU cores): maximum concurrent sdist builds.
- `concurrent-installs` (`int`, default: number of CPU cores): install/unzip threads.
- `offline` (`bool`, `false`): no network; uses only the cache and local files.
- `http-proxy` / `https-proxy` (`str`, `None`): proxy URLs. `no-proxy` (`list[str]`, `None`): hosts to bypass, e.g. `["localhost", "127.0.0.1"]`.
- `system-certs` (`bool`, `false`): uses the platform's native certificate store instead of the bundled Mozilla roots.
- `native-tls` (`bool`, `false`): **deprecated, use `system-certs`**.

## Configuration: Python

- `python-preference` (`"managed"` default): also `"only-managed"`, `"system"` or `"only-system"`.
- `python-downloads` (`"automatic"` default): also `"manual"` (requires explicit install) or `"never"`.
- `python-install-mirror` (`str`, `None`): replaces `https://github.com/astral-sh/python-build-standalone/releases/download`. `file://` is allowed for local dirs.
- `pypy-install-mirror`: replaces `https://downloads.python.org/pypy`.
- `graalpy-install-mirror`: replaces `https://github.com/oracle/graalpython/releases/download`.
- `pyodide-install-mirror`: replaces `https://github.com/pyodide/pyodide/releases/download`.
- `python-downloads-json-url` (`str`, `None`): path or URL to a JSON list of custom Python installations, e.g. `"/etc/uv/python-downloads.json"`.

## Configuration: publish

- `publish-url` (`str`, `"https://upload.pypi.org/legacy/"`): upload endpoint.
- `check-url` (`str`, `None`): index URL checked before and after upload to skip files that already exist.
  - Use it to retry partially failed publishes and to handle parallel uploads of the same file.
  - PyPI accepts identical re-uploads without it; most other indexes error.
  - The index must provide SHA-256, SHA-384 or SHA-512.
- `trusted-publishing` (`str`, `automatic`): by default uv checks for trusted publishing in supported environments (GitHub Actions, GitLab CI/CD) and ignores it if it isn't configured. `"always"` forces it.

## `[tool.uv.audit]` (`[audit]` in uv.toml)

- `ignore` (`list[str]`, `[]`): vulnerability IDs to drop from audit results, aliases included, e.g. `["PYSEC-2022-43017", "GHSA-5239-wwwm-4pmq"]`.
- `ignore-until-fixed` (`list[str]`, `[]`): ignored only while no fix version exists, then reported again.
- `malware-check` (`bool`, `false`): runs the automatic malware check during sync.
- `malware-check-url` (`str`, `"https://api.osv.dev/"`): vulnerability service URL.

## `[tool.uv.pip]` (`[pip]` in uv.toml)

Ignored outside `uv pip`. Keys shared with `[tool.uv]` (same semantics and defaults as above): `compile-bytecode`, `config-settings`, `config-settings-package`, `dependency-metadata`, `exclude-newer`, `exclude-newer-package`, `extra-build-dependencies`, `extra-build-variables`, `extra-index-url`, `find-links`, `fork-strategy`, `index-strategy`, `index-url`, `keyring-provider`, `link-mode`, `no-build-isolation`, `no-build-isolation-package`, `no-index`, `no-sources`, `no-sources-package`, `prerelease`, `reinstall`, `reinstall-package`, `resolution`, `torch-backend`, `upgrade`, `upgrade-package`. Differences from `[tool.uv]`:

- In `[tool.uv.pip]`, `index-url` and `extra-index-url` are not marked deprecated. `extra-index-url` beats `index-url`.
- `no-binary` (`list[str]`, `[]`): unlike the `[tool.uv]` bool, this takes packages. `:all:` disables binaries for everything and `:none:` clears earlier entries.
- `no-build` (`bool`, `false`): alias for `--only-binary :all:`.
- `only-binary` (`list[str]`, `[]`): wheels only for the listed packages (`:all:`, `:none:` supported). Editables may still be built.
- `require-build-hashes` (`bool`, `false`): overrides the `[tool.uv]` value. It does not cover runtime deps; use `require-hashes` for those.

pip-only keys:

- Selecting requirements:
  - `all-extras` (`bool`, `false`): all optional deps. Applies to `pyproject.toml`, `setup.py` and `setup.cfg` sources only.
  - `extra` (`list[str]`, `[]`): named extras (same sources).
  - `no-extra` (`list[str]`, `[]`): excludes extras when `all-extras` is set.
  - `group` (`list[str]`, `None`): dependency groups to include.
  - `no-deps` (`bool`, `false`): only the explicitly listed packages.
- Target environment:
  - `python` (`str`, `None`): interpreter to install into. `3.10` uses the registry on Windows (`py --list-paths`) or `python3.10`; `python3.10`/`python.exe` is looked up on `PATH`; an absolute path is used exactly. Intended for CI.
  - `system` (`bool`, `false`): the first Python on `PATH`. CI only, "can modify the system Python installation".
  - `break-system-packages` (`bool`, `false`): allows modifying an `EXTERNALLY-MANAGED` Python (e.g. one from `apt`). CI only.
  - `target` (`str`, `None`): installs at the top level of a directory.
  - `prefix` (`str`, `None`): installs into `lib`/`bin` under a dir as if it were a venv. Prefer `--python`: scripts installed via `--prefix` reference the installing interpreter and are non-portable.
  - `allow-empty-requirements` (`bool`, `false`): lets `uv pip sync` run with empty input, which clears the environment.
  - `strict` (`bool`, `false`): validates the environment for missing deps.
- Resolution target:
  - `python-version` (`str`, `None`): minimum Python for the resolution. `3.8` means `3.8.0`.
  - `python-platform` (`str`, `None`): a target triple, e.g. `x86_64-unknown-linux-gnu` or `aarch64-apple-darwin`.
  - `universal` (`bool`, `false`): a single `requirements.txt` for all OSes, architectures and implementations. The current or `--python-version` Python becomes a lower bound.
- Hashes:
  - `generate-hashes` (`bool`, `false`): writes hashes into the output.
  - `require-hashes` (`bool`, `false`): all-or-nothing. Every requirement needs a hash and must be pinned `==` or a direct URL. No Git, no editables, and local deps only as a `.whl`/`.zip`/`.tar.gz`, not a directory.
  - `verify-hashes` (`bool`, **`true`**): verifies hashes that are present without requiring them everywhere.
- `uv pip compile` output:
  - `output-file` (`str`, `None`): existing pins are preferred unless `--upgrade` is set.
  - `custom-compile-command` (`str`, `None`): header command for wrapper scripts.
  - `annotation-style`: `"split"` (default) or `"line"`.
  - `no-annotate`, `no-header` (`bool`, `false`).
  - `emit-index-url`, `emit-find-links`, `emit-build-options` (`--no-binary`/`--only-binary`), `emit-index-annotation` (`# from https://pypi.org/simple`), `emit-marker-expression` (`bool`, `false` each).
  - `no-strip-extras` (`bool`, `false`): output with extras can't be used as a constraints file.
  - `no-strip-markers` (`bool`, `false`): by default markers are stripped because the result is only guaranteed for the target environment.
  - `no-emit-package` (`list[str]`, `[]`): omits a package but keeps its deps. Same as pip-compile `--unsafe-package`.

```toml
[tool.uv.pip]
universal = true
python-version = "3.8"
generate-hashes = true
output-file = "requirements.txt"
no-binary = [":all:"]
```
