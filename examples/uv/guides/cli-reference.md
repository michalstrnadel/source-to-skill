# CLI reference

Source pages: https://docs.astral.sh/uv/reference/cli/ · https://docs.astral.sh/uv/reference/installer/ · https://docs.astral.sh/uv/reference/contributing/

Distilled from the generated CLI reference. Every command repeats the same global options (documented once below) and most resolver/installer commands share one large set of resolver options (documented once in "Shared resolver and installer options"). Per-command sections list only what is specific.

## Command tree

```
uv [OPTIONS] <COMMAND>
```

- `uv auth` - manage authentication
  - `login <SERVICE>` - log in to a service (domain or URL)
  - `logout <SERVICE>` - log out of a service
  - `token <SERVICE>` - show the auth token for a service
  - `dir` - show the credentials directory
- `uv run` - run a command or script
- `uv init` - create a new project
- `uv add` - add dependencies to the project
- `uv remove` - remove dependencies from the project
- `uv version` - read or update the project's version
- `uv sync` - update the project's environment
- `uv lock` - update the project's lockfile
- `uv export` - export the lockfile to an alternate format
- `uv tree` - display the project's dependency tree
- `uv format` - format Python code in the project (Ruff)
- `uv check` - run checks on the project (type checking with ty)
- `uv audit` - audit the project's dependencies (vulnerabilities, adverse statuses)
- `uv tool` - run and install commands provided by Python packages
  - `run` (alias `uvx`) - run a command provided by a package
  - `install` - install commands provided by a package
  - `upgrade` - upgrade installed tools
  - `list` - list installed tools
  - `audit` - audit installed tools and their dependencies
  - `uninstall` - uninstall a tool
  - `update-shell` - ensure the tool executable directory is on `PATH`
  - `dir` - show the tools directory
- `uv python` - manage Python versions and installations
  - `list` - list available installations
  - `install` - download and install Python versions
  - `upgrade` - upgrade installed versions to the latest patch
  - `find` - search for a Python installation
  - `pin` - pin to a specific Python version (`.python-version`)
  - `dir` - show the uv Python installation directory
  - `uninstall` - uninstall Python versions
  - `update-shell` - ensure the Python executable directory is on `PATH`
- `uv pip` - pip-compatible interface
  - `compile` - compile `requirements.in` to `requirements.txt` or `pylock.toml`
  - `sync` - sync an environment with a `requirements.txt` / `pylock.toml`
  - `install` - install packages into an environment
  - `uninstall` - uninstall packages
  - `freeze` - list installed packages in requirements format
  - `list` - list installed packages in tabular format
  - `show` - show info about installed packages
  - `tree` - dependency tree of an environment
  - `check` - verify installed packages have compatible dependencies
- `uv venv` - create a virtual environment
- `uv build` - build sdists and wheels
- `uv publish` - upload distributions to an index
- `uv workspace` - inspect workspaces
  - `metadata` - view workspace metadata (output not yet stable)
  - `dir` - path of the workspace root or a member
  - `list` - list workspace members
- `uv cache` - manage uv's cache
  - `clean [PACKAGE]...` - clear all entries or those for specific packages
  - `prune` - remove dangling entries and cached environments
  - `dir` - show the cache directory
  - `size` - show the cache size
- `uv self` - manage the uv executable
  - `update [TARGET_VERSION]` - update uv
  - `version` - display uv's version
- `uv generate-shell-completion <SHELL>` - generate a shell completion script (documented in the reference, not in the top-level command list)
- `uv help [COMMAND]...` - display documentation for a command (`--no-pager`)

## Global options (accepted by every command)

- `--allow-insecure-host` / `--trusted-host <host>` (`UV_INSECURE_HOST`): skip TLS verification for a hostname, `host:port`, or URL; repeatable. Only on secure networks with verified sources (MITM risk).
- `--cache-dir <dir>` (`UV_CACHE_DIR`): default `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv` (macOS/Linux), `%LOCALAPPDATA%\uv\cache` (Windows). See `uv cache dir`.
- `--color auto|always|never`: default auto-detects terminal support.
- `--config-file <path>` (`UV_CONFIG_FILE`): use a specific `uv.toml` (a `pyproject.toml` is not allowed here).
- `--directory <dir>` (`UV_WORKING_DIR`): change working directory before running; relative paths resolve against it.
- `--project <dir>` (`UV_PROJECT`): discover the project in the given directory (`pyproject.toml`, `uv.toml`, `.python-version`, `.venv` found by walking up from there) while other relative paths still resolve against the cwd. No effect in `uv pip`.
- `--help`, `-h`.
- `--managed-python` (`UV_MANAGED_PYTHON`): require uv-managed Pythons (by default uv prefers managed but falls back to system). `--no-managed-python` (`UV_NO_MANAGED_PYTHON`): only system Pythons.
- `--no-python-downloads`: disable automatic Python downloads.
- `--no-cache`, `--no-cache-dir`, `-n` (`UV_NO_CACHE`): use a temporary cache for this run.
- `--no-config` (`UV_NO_CONFIG`): don't discover `pyproject.toml` / `uv.toml` config files (normally searched in cwd, parents, and user config dirs).
- `--no-progress` (`UV_NO_PROGRESS`): hide spinners and progress bars.
- `--offline` (`UV_OFFLINE`): no network; only cached data and local files.
- `--quiet`, `-q`: quiet output; `-qq` writes nothing to stdout.
- `--verbose`, `-v`: verbose output; fine-grained logging via `RUST_LOG`.
- `--system-certs` (`UV_SYSTEM_CERTS`): load TLS certs from the platform store. Default is bundled Mozilla roots (portable, faster especially on macOS); use system certs for corporate trust roots / mandatory proxies.

## Shared resolver and installer options

Repeated on `run`, `add`, `remove`, `version`, `sync`, `lock`, `export`, `tree`, `check`, `audit`, `tool run/install/upgrade`, `pip compile/sync/install`, `build`, `workspace metadata` (subsets vary per command).

Indexes and sources
- `--index <url>` (`UV_INDEX`): extra indexes, take priority over `--default-index`; earlier `--index` values win.
- `--default-index <url>` (`UV_DEFAULT_INDEX`): default `https://pypi.org/simple`.
- `--index-url`, `-i` (`UV_INDEX_URL`) and `--extra-index-url` (`UV_EXTRA_INDEX_URL`): deprecated in favor of `--default-index` / `--index`. Extra index URLs take priority over `--index-url`; earlier values win.
- `--find-links`, `-f` (`UV_FIND_LINKS`): extra locations to search for distributions.
- `--no-index`: ignore registries; only direct URLs and `--find-links`.
- `--index-strategy first-index|unsafe-first-match|unsafe-best-match` (`UV_INDEX_STRATEGY`).
- `--keyring-provider disabled|subprocess` (`UV_KEYRING_PROVIDER`): default `disabled`; only `subprocess` (the `keyring` CLI) is supported.
- `--no-sources` (`UV_NO_SOURCES`): ignore `tool.uv.sources`, lock against publishable metadata. `--no-sources-package <pkg>`.

Resolution
- `--resolution highest|lowest|lowest-direct` (`UV_RESOLUTION`): default `highest`.
- `--prerelease disallow|allow|if-necessary|explicit` (`UV_PRERELEASE`): default `if-necessary` (stable first, pre-release only if all stable candidates are rejected). `if-necessary-or-explicit` is a deprecated alias for `if-necessary`. `--prerelease-package` per package.
- `--fork-strategy fewest|requires-python` (`UV_FORK_STRATEGY`): default optimizes for the latest version per supported Python while minimizing versions across platforms.
- `--exclude-newer <date>` (`UV_EXCLUDE_NEWER`): only artifacts uploaded before the date (per-file upload time, not release date). Accepts RFC 3339 timestamps (`2006-12-02T02:07:43Z`), local dates (`2006-12-02`), friendly durations (`24 hours`, `1 week`, `30 days`), ISO 8601 durations (`PT24H`, `P7D`). Durations assume 24h days; months/years not allowed. `false` disables. `--exclude-newer-package PACKAGE=DATE` per package, repeatable.
- `--upgrade`, `-U` (implies `--refresh`); `--upgrade-package`, `-P <pkg>` (implies `--refresh-package`); `--upgrade-group <group>`: ignore existing pins.
- `-c/--constraint` (`UV_CONSTRAINT`), `--override` (`UV_OVERRIDE`), `-b/--build-constraint` (`UV_BUILD_CONSTRAINT`), `--exclude` (`UV_EXCLUDE`): requirements-style files (where supported).

Building
- `--no-build` (`UV_NO_BUILD`), `--no-build-package` (`UV_NO_BUILD_PACKAGE`): never build sdists.
- `--no-binary` (`UV_NO_BINARY`), `--no-binary-package`: build from source; resolver still reads wheel metadata.
- `--no-build-isolation` (`UV_NO_BUILD_ISOLATION`), `--no-build-isolation-package <pkg>` (assumes PEP 518 build deps already installed).
- `--config-setting`, `-C KEY=VALUE`; `--config-settings-package PACKAGE:KEY=VALUE`: PEP 517 backend settings.
- `--require-build-hashes` / `--no-require-build-hashes`.

Installing and caching
- `--reinstall` / `--force-reinstall` (implies `--refresh`), `--reinstall-package`.
- `--refresh`, `--refresh-package`: refresh cached data.
- `--link-mode clone|copy|hardlink|symlink` (`UV_LINK_MODE`): default `clone` (copy-on-write) on macOS/Linux, `hardlink` on Windows. `symlink` is discouraged: `uv cache clean` would break installed packages.
- `--compile-bytecode`, `--compile` (`UV_COMPILE_BYTECODE`): compile `.pyc` after install (default: lazy on first import). Good for CLIs and Docker. Sync-type commands (`uv sync`, `uv run`) process the whole site-packages.
- `--python-platform <target>`: e.g. `windows`, `linux`, `macos`, `x86_64-unknown-linux-gnu` (= `x86_64-manylinux_2_28`), `aarch64-apple-darwin`, `x86_64-manylinux_2_17`..`_2_40`, `aarch64-manylinux_*`, musl, Android, iOS, `wasm32-pyodide2024/2025`. Defaults: macOS min `13.0` (`MACOSX_DEPLOYMENT_TARGET`), iOS `13.0` (`IPHONEOS_DEPLOYMENT_TARGET`), Android API `24` (`ANDROID_API_LEVEL`).
- `--torch-backend auto|cpu|cu126|...|rocm6.4|...|xpu` (`UV_TORCH_BACKEND`, preview; `uv pip` and `uv tool`): ignore configured indexes for PyTorch-ecosystem packages and use the matching PyTorch index; `auto` detects from installed CUDA drivers.

Dependency selection (project commands)
- `--extra`, `--all-extras`, `--no-extra` (applies with `--all-extras`).
- `--group`, `--all-groups`, `--only-group` (implies `--no-default-groups`), `--no-group` (`UV_NO_GROUP`; always wins), `--no-default-groups` (`UV_NO_DEFAULT_GROUPS`; ignore `tool.uv.default-groups`), `--no-dev` (`UV_NO_DEV`, alias for `--no-group dev`), `--only-dev`.
- `--no-install-project` (`UV_NO_INSTALL_PROJECT`), `--no-install-workspace` (`UV_NO_INSTALL_WORKSPACE`), `--no-install-local` (`UV_NO_INSTALL_LOCAL`), `--no-install-package <pkg>` (may break the env).
- `--no-editable` (`UV_NO_EDITABLE`), `--no-editable-package`.
- `--locked` (`UV_LOCKED`): fail if `uv.lock` is missing or would change. `--frozen` (`UV_FROZEN`): use `uv.lock` as-is without checking freshness; fail if missing; un-locked `pyproject.toml` changes are ignored.
- `--active`: prefer the active venv over the project `.venv`.

## Project commands

### `uv run [OPTIONS] [COMMAND]`

- Runs a command in a Python environment. `.py` files and HTTP(S) URLs are run as scripts (`uv run file.py` = `uv run python file.py`); URLs are downloaded temporarily; `-` reads a script from stdin. Scripts with inline metadata get an isolated ephemeral environment.
- In a project: creates/updates the project env first. Outside a project: uses a venv found in cwd/parents, else the discovered interpreter. For scripts, the project is discovered from the script's directory.
- All uv options go *before* the command; use `--` to separate: `uv run --python 3.12 -- python`.
- Specific options:
  - `--with`, `-w <pkg>` / `--with-editable` / `--with-requirements <file>`: extra packages layered in a separate ephemeral env on top of the project env; may conflict with project deps.
  - `--isolated` (`UV_ISOLATED`): fresh env instead of reusing the project env (project still editable; `--with` deps still layered).
  - `--no-project` (`UV_NO_PROJECT`): skip project discovery; run in ephemeral env from `--with`, or a found venv.
  - `--no-sync` (`UV_NO_SYNC`): don't sync; implies `--frozen`.
  - `--exact`: remove extraneous packages (default: minimal changes).
  - `--module`, `-m`: `python -m <module>`. `--script`, `-s`: parse as PEP 723 script regardless of extension. `--gui-script`: Windows-only, runs with `pythonw.exe`.
  - `--env-file <file>` (`UV_ENV_FILE`, repeatable, later files override); `--no-env-file` (`UV_NO_ENV_FILE`).
  - `--package <pkg>` (run in a workspace member), `--all-packages`.
  - `--python`, `-p` (`UV_PYTHON`).

### `uv init [OPTIONS] [PATH]`

- Errors if `pyproject.toml` already exists at the target. If a parent directory has a `pyproject.toml`, the new project becomes a workspace member (unless `--no-workspace`). `.venv` and `uv.lock` are created lazily on first sync.
- `--app` (applications are packaged by default; `--no-package` for unpackaged), `--lib`, `--script` (PATH required; adds a requirement on the system Python version unless `--python`), `--bare` (only `pyproject.toml`).
- `--package` (default) / `--no-package`; `--build-backend uv|hatch|flit|pdm|poetry|setuptools|maturin|scikit` (`UV_INIT_BUILD_BACKEND`).
- `--name`, `--description` / `--no-description`, `--no-readme`, `--author-from auto|git|none` (default `auto`).
- `--vcs git|none` (default `git`), `--no-pin-python` (by default writes `.python-version` with the discovered minor version), `--python` (sets minimum supported version), `--no-workspace` / `--no-project`.

### `uv add [OPTIONS] <PACKAGES|--requirements <REQUIREMENTS>>`

- Adds PEP 508 requirements to `pyproject.toml`, then updates lockfile and env (`--frozen` skips locking and adds deps verbatim without checking they exist; `--no-sync` skips env update). An existing entry is updated unless markers differ, in which case another entry is added.
- `--bounds lower|major|minor|exact`: default `lower` (`>=1.2.3`); `major` = `>=1.2.3, <2.0.0`; `minor` = `>=1.2.3, <1.3.0`; `exact` = `==1.2.3`. `--raw` / `--raw-sources`: add as given, no bounds.
- `--dev` (`UV_DEV`), `--group <g>`, `--optional <extra>`, `--extra <e>` (extras to enable for the dependency), `--marker`, `-m`.
- Git: `--branch`, `--tag`, `--rev`, `--lfs`. `--editable`.
- Workspace: `--package <member>`, `--workspace` (add local path as workspace member; default for paths inside the workspace), `--no-workspace` (plain path dep).
- `--script <file>`: add to a PEP 723 script instead. `-r/--requirements <file>`, `-c/--constraints`.

### `uv remove [OPTIONS] <PACKAGES>...`

- Removes all entries for the package (all marker variants); errors if not present. Packages installed manually with `uv pip install` are not removed.
- `--dev`, `--group`, `--optional <extra>`, `--package`, `--script`, `--frozen`, `--no-sync`.

### `uv version [OPTIONS] [VALUE]`

- Read, or set to `VALUE`. `--bump major|minor|patch|stable|alpha|beta|rc|post|dev` (e.g. `stable`: `1.2.3b4.post5.dev6 => 1.2.3`; `dev`: `1.2.3a4.dev6 => 1.2.3.dev7`).
- `--dry-run`, `--short` (version only), `--output-format text|json`, `--package`, `--frozen`.

### `uv sync [OPTIONS]`

- Exact sync by default: removes packages not declared. `--inexact` / `--no-exact` keeps extraneous ones (conflicting ones still removed; with `--no-build-isolation` extraneous packages are not removed). Creates `.venv` if missing. Re-locks first unless `--locked` / `--frozen`. No yanked-version warnings when installing from a lockfile.
- `--check` (exit with error if env out of date), `--dry-run`, `--active`, `--all-packages`, `--package`, `--script <file>`, `--output-format text|json` (JSON on stdout, schema experimental), `--python` (if given a venv interpreter, uv uses it to create the project env rather than syncing into it).

### `uv lock [OPTIONS]`

- Creates `uv.lock` or re-resolves using the existing one as preferences; no effect without dependency changes unless `--upgrade`.
- `--check` (= `--locked`: error if missing or would change), `--check-exists` (= `--frozen`), `--dry-run`, `--script <file>`, `--python`.

### `uv export [OPTIONS]`

- Formats: `requirements.txt` (default), `pylock.toml`, `cyclonedx1.5` (CycloneDX v1.5 JSON); `--format`, or inferred from `-o/--output-file` extension. Re-locks first unless `--locked` / `--frozen`. Exports the workspace root by default.
- `--package`, `--all-packages`, `--prune <pkg>`, `--script`.
- `--no-hashes`, `--no-header`, `--no-annotate`, `--emit-index-url`, `--emit-find-links`.
- `--no-emit-project`, `--no-emit-workspace`, `--no-emit-local`, `--no-emit-package <pkg>` (aliases `--no-install-*`), `--no-editable`.

### `uv tree [OPTIONS]`

- `--depth`, `-d` (default `255`), `--format text|json` (default `text`), `--invert` / `--reverse`, `--no-dedupe` (duplicates otherwise marked `(*)`), `--outdated`, `--show-sizes` (compressed wheel sizes), `--package`, `--prune`, `--universal`, `--python-version`, `--python-platform`, `--script`, `--frozen`.

### `uv format [OPTIONS] [-- <EXTRA_ARGS>...]`

- Runs the Ruff formatter on all project Python files (same as `ruff format` in the project root). `--check`, `--diff`, `--version <ruff>` (default a constrained range, e.g. `>=0.15,<0.16`), `--exclude-newer`, `--no-project`.
- Pass Ruff args after `--`: `uv format -- --line-length 100`, `uv format -- src/module/foo.py`.

### `uv check [OPTIONS]`

- Type-checks with ty. `--fix` (apply safe fixes), `--ty-version` (default: the locked version if `ty` is a project or `dev`-group dependency, else a constrained range e.g. `>=0.0,<0.1`), `--isolated` (don't mutate project state), `--package`, `--all-packages`, `--script`.

### `uv audit [OPTIONS]`

- Audits for known vulnerabilities and adverse statuses (deprecation, quarantine). By default audits *all* extras and groups regardless of `tool.uv.default-groups`. Requires network (not in offline mode).
- `--ignore <ID>`, `--ignore-until-fixed <ID>` (only while no fix is available), `--output-format text|json|sarif`, `--service-format osv` (default) with `--service-url`, `--no-default-groups`, `--no-group`, `--no-extra`, `--only-group`, `--only-dev`, `--no-dev`, `--python-version`, `--python-platform`, `--script`, `--frozen`.

### `uv workspace`

- `metadata`: `--sync` adds module ownership metadata (env synced inexactly), `--locked`, `--frozen`, `--script`.
- `dir`: root by default, `--package <member>` for a member; errors outside a workspace.
- `list`: newline-separated member names; `--paths`, `--scripts` (standalone scripts with inline metadata).

## Tools

- `uv tool run` / `uvx`: package assumed to match the command name; `uvx ruff@0.3.0` for an exact version; `--from <pkg>` when the command comes from another package or needs a complex spec. `uvx python` / `uvx python@<version>` starts an isolated interpreter. Previously installed tools are reused unless a version is requested or `--isolated` (`UV_ISOLATED`). Envs are ephemeral, in the uv cache. No command: lists installed tools. Options: `--with`, `--with-editable`, `--with-requirements`, `--python`, `--build-constraint`, `--override`, `--constraint`, `--torch-backend`, `--env-file`, `--lfs`.
- `uv tool install <PACKAGE>`: isolated env in the tools dir; executables linked into the tool bin dir (`uv tool dir --bin`). Reinstalling generally replaces. `-e/--editable`, `--with`, `--with-editable`, `--with-executables-from <pkg>`, `--exclude`, `--force` (recreate env, replace same-named entry points), `--python`.
- `uv tool upgrade <NAME>... | --all`: respects original version constraints and settings (e.g. `--prerelease allow`); to go beyond constraints, `uv tool install` again. `--python` (with `--all` applies to all), `--config-setting-package`.
- `uv tool list`: `--outdated`, `--show-paths`, `--show-version-specifiers`, `--show-with`, `--show-extras`, `--show-python`.
- `uv tool audit <NAME>... | --all` (network required; takes `--ignore`, `--ignore-until-fixed`, `--output-format`, `--service-format`, `--service-url`).
- `uv tool uninstall <NAME>... | --all`.
- `uv tool update-shell`: adds the bin dir to shell config files; errors if the blurb exists but the dir is still not on `PATH`.
- `uv tool dir`: default `$XDG_DATA_HOME/uv/tools` or `$HOME/.local/share/uv/tools` (Unix), `%APPDATA%\uv\data\tools` (Windows); override `$UV_TOOL_DIR`. `--bin` order: `$UV_TOOL_BIN_DIR`, `$XDG_BIN_HOME`, `$XDG_DATA_HOME/../bin`, `$HOME/.local/bin`.

## Python management

Discovery: venv first (active or `.venv` in cwd/parents), then interpreters on `PATH` (plus the registry on Windows). Missing versions are downloaded unless `--no-python-downloads` / the `python-downloads` setting. Supports CPython, PyPy, GraalPy discovery.

Request formats for `--python` / `uv python *`:
- `3`, `3.12`, `3.12.3`; `>=3.12,<3.13`; `3.13t`, `3.12.0d`; `3.13+freethreaded`, `3.12.0+debug`
- `cpython` / `cp`; `cpython@3.12`; `cpython3.12` / `cp312`; `cpython>=3.12,<3.13`; `cpython-3.12.3-macos-aarch64-none`
- `/opt/homebrew/bin/python3` (path), `mypython3` (executable name), `/some/environment/` (install dir)

Commands:
- `uv python list [REQUEST]`: installed + latest patch downloads per supported version. `--all-versions`, `--only-installed`, `--only-downloads`, `--all-platforms`, `--all-arches`, `--show-urls`, `--managed-python` / `--no-managed-python`, `--output-format`.
- `uv python install [TARGETS]...`: CPython from Astral `python-build-standalone`, PyPy from python.org; available versions are bundled per uv release (upgrade uv for new ones). Without targets: `UV_PYTHON`, then `.python-versions` / `.python-version`, else latest stable if none installed. Installs `python3.13`-style executables; `--default` also installs `python3` and `python` (variants keep tags: `python3t`, `pythont`). `--upgrade`, `-U` (latest patch), `--reinstall`, `-r`, `--force`, `-f` (replace unmanaged executables), `--install-dir`, `-i` (`UV_PYTHON_INSTALL_DIR`), `--no-bin`, `--no-registry` (Windows), `--mirror`, `--pypy-mirror`, `--graalpy-mirror`, `--pyodide-mirror`, `--python-downloads-json-url`, `--compile-bytecode` (stdlib).
- `uv python upgrade [TARGETS]...`: latest patch for given minors, or all managed CPython versions; old patches kept; uv-created venvs follow automatically (venvs created before this feature must be recreated). Not for PyPy etc. `--reinstall`, `--install-dir`.
- `uv python find [REQUEST]`: prints interpreter path. `--system` (`UV_SYSTEM_PYTHON`, only system interpreters), `--show-version`, `--resolve-links`, `--script`, `--no-project`.
- `uv python pin [REQUEST]`: writes `.python-version`; no request shows the current pin. `--global` (user config dir: `XDG_CONFIG_HOME/uv` or `%APPDATA%/uv`, used when no local pin), `--resolved` (write interpreter path), `--rm`, `--no-project` (skip validation against `requires-python`). Use plain version numbers if pyenv compatibility matters.
- `uv python dir`: default `$XDG_DATA_HOME/uv/python` / `$HOME/.local/share/uv/python` / `%APPDATA%\uv\data\python`; override `$UV_PYTHON_INSTALL_DIR`. `--bin` (override `$UV_PYTHON_BIN_DIR`; then `$XDG_BIN_HOME`, `$XDG_DATA_HOME/../bin`, `$HOME/.local/bin`).
- `uv python uninstall <TARGETS>... | --all`, `--install-dir`.
- `uv python update-shell`: like `uv tool update-shell` for the Python bin dir.

## pip interface (see pip-interface.md for behavior)

- `uv pip compile <SRC_FILE|--group>`: `-o`, `--format requirements.txt|pylock.toml`, `--universal`, `--python-version`, `--python-platform`, `--generate-hashes`, `--no-strip-extras`, `--no-strip-markers`, `--no-deps`, `--no-emit-package` / `--unsafe-package`, `--annotation-style line|split`, `--custom-compile-command`, `--emit-index-annotation`, `--emit-build-options`, `--emit-index-url`, `--emit-find-links`, `--no-header`, `--no-annotate`, `--only-binary`, `--no-binary`, `--cert <PEM>`, `--system`, `--torch-backend`. Input order sets resolution priority.
- `uv pip sync <SRC_FILE>...`: removes unlisted packages; `--strict`, `--check`, `--dry-run`, `--require-hashes` (`UV_REQUIRE_HASHES`), `--no-verify-hashes` (`UV_NO_VERIFY_HASHES`), `--allow-empty-requirements`, `--break-system-packages`, `--target`, `-t`, `--prefix`, `--python` (alternative interpreter only recommended in CI), `--python-version`, `--group`.
- `uv pip install`: `-r`, `-e`, `--group`, `--no-deps`, `--exact`, `--check`, `--strict`, `--no-editable`, `--require-hashes`, `--target`, `--prefix`, `--system`, `--break-system-packages`, `--overrides`, `--excludes`, `--torch-backend`. `--user` is listed without a description.
- `uv pip uninstall`: `-r`, `--dry-run`, `--system`, `--target`, `--prefix`, `--python`, `--keyring-provider` (for remote requirements files).
- `uv pip freeze`: `--exclude`, `--exclude-editable`, `--path` (repeatable), `--strict`, `--system`, `--target`, `--prefix`.
- `uv pip list`: `--format columns|freeze|json` (default `columns`), `--outdated`, `-e/--editable`, plus freeze filters.
- `uv pip show [PACKAGE]...`: `--files`, `-f`.
- `uv pip tree`: `--show-version-specifiers`, plus `--depth`, `--invert`, `--no-dedupe`, `--outdated`, `--package`, `--prune`, `--show-sizes`.
- `uv pip check`: `--python-version`, `--python-platform` (default: current interpreter's).

## Environments, build, publish

### `uv venv [OPTIONS] [PATH]`

- Default `.venv` in the working directory; in a project, `UV_PROJECT_ENVIRONMENT` changes the default name (only from the project root). No activation needed for uv commands.
- Existing target: the description says it is replaced with a fresh empty venv, while the `--clear` / `--allow-existing` option help says a non-empty path is an error by default; `--clear`, `-c` (`UV_VENV_CLEAR`) clears it first, `--allow-existing` writes into it without clearing, `--force` lets `--clear` remove a non-venv directory.
- `--python`, `-p`; `--seed` (`UV_VENV_SEED`: pip, setuptools, wheel; no setuptools/wheel on 3.12+); `--prompt` (default: directory name; `.` = current dir name); `--relocatable` (`UV_VENV_RELOCATABLE`: relative paths, so entrypoints/scripts cannot be copied outside the env); `--system-site-packages` (runtime only, ignored by uv commands); `--no-project`.

### `uv build [OPTIONS] [SRC]`

- Default (directory): build sdist, then wheel *from the sdist*. `--sdist`, `--wheel`, `--sdist --wheel` (both from source). Given an sdist, `--wheel` builds a wheel from it.
- `--out-dir`, `-o`; `--clear` (remove stale artifacts); `--no-create-gitignore` (default writes a `.gitignore` in the output dir); `--package`, `--all-packages` / `--all`; `-b/--build-constraint`; `--no-build-logs`; `--force-pep517` (skip the fast path that calls the uv build backend directly); `--python` (builds run in isolated venvs created from the discovered interpreter); `--require-hashes`, `--no-verify-hashes`.

### `uv publish [OPTIONS] [FILES]...`

- Default files: `dist/` (globs allowed); only wheels, sdists, and their attestations.
- `--publish-url` (`UV_PUBLISH_URL`; upload endpoint, not the index URL), `--index <name>` (`UV_PUBLISH_INDEX`; an index from config).
- Auth: `--token`, `-t` (`UV_PUBLISH_TOKEN`), `--username`, `-u` / `--password`, `-p` (`UV_PUBLISH_USERNAME` / `UV_PUBLISH_PASSWORD`), `--keyring-provider`, `--trusted-publishing automatic|always|never` (default automatic; supported on GitHub Actions and GitLab CI/CD).
- `--check-url` (`UV_PUBLISH_CHECK_URL`): skip files already on the index; makes retries of partial uploads safe. PyPI accepts identical re-uploads anyway; most other indexes error. Index must expose SHA-256/384/512.
- `--no-attestations` (`UV_PUBLISH_NO_ATTESTATIONS`; PEP 740 attestations are uploaded by default), `--dry-run`.

## Auth, cache, self

- `uv auth login <SERVICE>`: `--token`, `-t` (username becomes `__token__`), `--username`, `-u`, `--password`; `-` reads token/password from stdin. `uv auth logout`, `uv auth token` take `--username`.
- `uv auth dir`: `$XDG_DATA_HOME/uv/credentials` or `$HOME/.local/share/uv/credentials` (Unix), `%APPDATA%\uv\data\credentials` (Windows); override `$UV_CREDENTIALS_DIR`. Only used by the plaintext backend (the native backend uses the system keyring).
- `uv cache clean [PACKAGE]...`: blocks until no process reads the cache; `--force` skips the lock.
- `uv cache prune`: `--ci` removes pre-built (downloaded) wheels but keeps wheels built from source, which suits CI caches like GitHub Actions.
- `uv cache dir`: `$XDG_CACHE_HOME/uv` / `$HOME/.cache/uv` / `%LOCALAPPDATA%\uv\cache`; override with `cache-dir` setting, `--cache-dir`, `$UV_CACHE_DIR`. Keep the cache on the same filesystem as your environments for performance.
- `uv cache size`: `--human`, `-H`.
- `uv self update [TARGET_VERSION]`: `--dry-run`, `--token` (`UV_GITHUB_TOKEN`, reduces GitHub rate limiting). `uv self version`: `--short`, `--output-format`.

## Installer options

https://docs.astral.sh/uv/reference/installer/

```bash
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/custom/path" sh
curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="/custom/path" sh
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --help
```

```powershell
powershell -ExecutionPolicy ByPass -c {$env:UV_INSTALL_DIR = "C:\Custom\Path";irm https://astral.sh/uv/install.ps1 | iex}
```

- Default location: the user executable directory. `UV_INSTALL_DIR` moves only the binary; cache, Pythons, tools stay in default locations.
- `UV_NO_MODIFY_PATH`: don't edit shell profiles (also respected by later `uv self update`).
- `UV_UNMANAGED_INSTALL=<path>`: for ephemeral environments like CI; no profile/env changes and disables `uv self update`.
- Env vars are preferred over script flags because they work the same across platforms.

## Contributing (for users building uv from source)

https://docs.astral.sh/uv/reference/contributing/
- Needs Rust and a C compiler (`build-essential` / `gcc`); on Windows NASM for `aws-lc-sys` (else a prebuilt blob is used).
- Run the dev build with `cargo run -- <args>` (e.g. `cargo run -- pip install requests`); tests via `cargo nextest`, snapshots via `cargo insta`.
- Debug logging: `RUST_LOG=trace uv`.
- Untrusted dependency trees: resolve inside the provided Docker builder (`crates/uv-dev/builder.dockerfile`), since sdists can run arbitrary code even during resolution.
- Policy: no feature PRs without prior discussion; `help wanted` and `bug` issues are the best candidates; AI use must follow Astral's AI Policy.
