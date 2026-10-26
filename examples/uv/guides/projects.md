# Projects: init, layout, config, run, lock/sync, export, build, workspaces

Source pages: https://docs.astral.sh/uv/concepts/projects/init/, https://docs.astral.sh/uv/concepts/projects/layout/, https://docs.astral.sh/uv/concepts/projects/config/, https://docs.astral.sh/uv/concepts/projects/run/, https://docs.astral.sh/uv/concepts/projects/sync/, https://docs.astral.sh/uv/concepts/projects/export/, https://docs.astral.sh/uv/concepts/projects/build/, https://docs.astral.sh/uv/concepts/projects/workspaces/

Dependency declaration (`uv add`, `tool.uv.sources`, extras, groups) lives in `dependencies.md`.

## Creating projects (`uv init`)

https://docs.astral.sh/uv/concepts/projects/init/

- Two templates: **applications** (default, or `--app`) and **libraries** (`--lib`).
- Both get a build system and a `src/<project_name>/` layout by default. Disable the build system with `--no-package` or `--bare`.
- Prior to v0.12, uv did not define a build system for applications by default.
- Target dir: `uv init` uses the working directory; `uv init foo` creates `foo/`. `--directory` changes the working directory the target path is resolved against. If a `pyproject.toml` already exists in the target, uv exits with an error.

### Which flag

- `uv init example-app` (or `--app`): web servers, scripts, CLIs. Creates `.python-version`, `README.md`, `pyproject.toml`, `src/example_app/__init__.py`, a `[project.scripts]` entry, and a `uv_build` build system. Run with `uv run example-app`.
- `uv init --lib example-lib`: code meant to be built and distributed (e.g. to PyPI). Libraries always require a packaged project. Adds a `py.typed` marker. No `[project.scripts]`.
- `uv init --no-package example-app`: flat project with `main.py`, `README.md`, `.python-version`, `pyproject.toml`; no build system, so the project is **not** installed into the environment. Run with `uv run main.py`.
- `uv init example-bare --bare`: only `pyproject.toml`. Skips `.python-version`, README, source dirs, git init, and extra metadata (`description`, `authors`). Opt back in: `uv init example-bare --bare --description "Hello world" --author-from git --vcs git --pin-python`. Combined with `--lib`/`--build-backend`, it still configures a build system but creates no file structure.
- `uv init --build-backend <name>`: `hatchling`, `uv_build`, `flit-core`, `pdm-backend`, `setuptools`, `maturin`, `scikit-build-core`. `--build-backend` implies `--package`.

Generated application `pyproject.toml`:

```toml
[project]
name = "example-app"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
example-app = "example_app:main"

[build-system]
requires = ["uv_build>=0.13.5,<0.14"]
build-backend = "uv_build"
```

- A `src` layout matters most for libraries: it keeps the library isolated from `python` invocations in the project root and separates distributed code from the rest of the project.

### Extension modules

- Pure-Python is the default. For native code pick a backend that builds extension modules:
  - `maturin` for Rust (`uv init --build-backend maturin example-ext` adds `Cargo.toml`, `src/lib.rs`, `src/example_ext/_core.pyi`).
  - `scikit-build-core` for C, C++, FORTRAN, Cython (adds CMake config and `main.cpp`).
- With maturin or scikit-build-core, uv configures `tool.uv.cache-keys` to include common source file types. To force a rebuild (files outside `cache-keys`, or no `cache-keys`), use `--reinstall`.

## Project structure and files

https://docs.astral.sh/uv/concepts/projects/layout/

- `pyproject.toml`: uv requires it to identify the project root. Minimum is `[project]` with `name` and `version`.
- `.venv`: persistent project environment next to `pyproject.toml`, created as needed. Kept in-project so editors find it. Do not commit it; uv auto-excludes it from git with an internal `.gitignore`.
  - Run things in it with `uv run`, or activate it as a normal venv. `uv sync` creates it explicitly.
  - Do **not** modify it manually (e.g. `uv pip install`). Use `uv add` for project deps; `uvx` or `uv run --with` for one-off requirements.
  - Temporary environments: e.g. `uv run --isolated`.
  - Opt out of uv managing it: `[tool.uv] managed = false` disables automatic locking and syncing.
- `uv.lock`: next to `pyproject.toml`. A **universal / cross-platform** lockfile capturing packages across all Python markers (OS, arch, Python version). Holds exact resolved versions. **Commit it.** Human-readable TOML but managed by uv; do not edit manually; uv-specific format, not usable by other tools. Created/updated automatically by `uv sync` and `uv run`, or explicitly with `uv lock`.

### Centralized project environments (preview)

- With the `centralized-project-envs` preview feature, the default project env lives in uv's cache. uv tries to keep a `.venv` link to it; if that fails it writes the cached env path to `.venv`; if both fail, tools relying on `.venv` may not discover it. Switching interpreters selects separate cached envs.
- Not centralized: `UV_PROJECT_ENVIRONMENT` paths and `--active` envs. No effect with `--no-cache`. Also applies to pathless `uv venv` from a project/workspace root.

### `uv.lock` vs `pylock.toml`

- `pylock.toml` (PEP 751) is a standardized, tool-agnostic resolution format intended to replace `requirements.txt`. Some uv functionality cannot be expressed in it, so the project interface keeps using `uv.lock`.
- `uv export -o pylock.toml` exports a `uv.lock`.
- `uv pip compile requirements.in -o pylock.toml` generates one from requirements.
- `uv pip sync pylock.toml` or `uv pip install -r pylock.toml` installs from one.

## Configuring projects

https://docs.astral.sh/uv/concepts/projects/config/

### Python version requirement

- Set `project.requires-python` (recommended), e.g. `requires-python = ">=3.12"`. It determines allowed syntax and constrains dependency versions (they must support the same Python range).

### Entry points (require a build system)

```toml
[project.scripts]          # CLI: `uv run hello`
hello = "example:hello"

[project.gui-scripts]      # differs from scripts only on Windows (no console)
hello = "example:app"

[project.entry-points.'example.plugins']   # plugin discovery
a = "example_plugin_a"
```

- Load plugins with `importlib.metadata.entry_points(group="example.plugins")`. The group name is arbitrary, but namespace it by package name to avoid collisions.

### Build systems

- uv uses the presence of `[build-system]` to decide if the project is a package to install into the project env. No build system: uv installs only the dependencies, not the project. With one: uv builds and installs the project.
- `uv init` defaults to a packaged project using the uv build backend.
- Other packages don't need `[build-system]`: for legacy reasons `setuptools.build_meta:__legacy__` is used. Local path dependencies and `uv pip` installs are built regardless of a `[build-system]` table.
- Build systems power: file include/exclude in distributions, editable behavior, dynamic metadata, native compilation, vendoring shared libraries. Configure those in the backend's docs.

### Project packaging: do you need a package?

- Probably yes: you add commands, distribute the project, use a `src` + `test` layout, or write a library.
- Probably no: scripts, simple application, flat layout.
- Override with `tool.uv.package`:
  - `package = true`: always build and install the project; with no build system, uses the setuptools legacy backend.
  - `package = false`: never build/install it into the project env, ignoring a declared build system; explicit `uv build` still works.

### Project environment path

- `UV_PROJECT_ENVIRONMENT` sets the project venv path (default `.venv`). Relative paths resolve against the workspace root; absolute paths are used as-is (no child directory). Created if missing.
- Targeting system Python is possible but not recommended: `uv sync` removes extraneous packages and may break the system. E.g. on Debian, `UV_PROJECT_ENVIRONMENT=/usr/local` (the `sysconfig` prefix).
- !!! important: an absolute path shared across projects gets overwritten by each project. Only recommended for a single project in CI or Docker images.
- uv does not read `VIRTUAL_ENV` during project operations by default; it warns if it differs from the project env. `--active` opts in to respecting `VIRTUAL_ENV`; `--no-active` silences the warning.

### Build isolation

- Default: every package is built in an isolated venv with its declared build deps (PEP 517). This breaks packages that must build against the installed `torch` (`flash-attn`, `deepspeed`) or that omit build deps (`cchardet` needs `cython`).
- Decision rule: **prefer augmenting build deps over disabling isolation**. Disabling requires build deps to be installed in the project env first, adding extraneous packages and hurting reproducibility.

Augment build dependencies:

```toml
[tool.uv.extra-build-dependencies]
cchardet = ["cython"]
deepspeed = [{ requirement = "torch", match-runtime = true }]
flash-attn = [{ requirement = "torch", match-runtime = true }]

[tool.uv.extra-build-variables]
flash-attn = { FLASH_ATTENTION_SKIP_CUDA_BUILD = "TRUE" }
```

- `match-runtime = true` builds against the same version installed in the project env. Changes to `extra-build-dependencies` / `extra-build-variables` are tracked in the cache and trigger rebuilds (e.g. upgrading `torch` rebuilds `flash-attn`).
- `FLASH_ATTENTION_SKIP_CUDA_BUILD = "TRUE"` lets `flash-attn` resolve from a pre-built wheel instead of building (which needs the CUDA toolkit). If the CUDA toolkit is available, omit it: it can produce an incompatible install when no matching pre-built wheel exists.
- `match-runtime` only works for packages with **static metadata**. For packages without it (e.g. `axolotl`), pin the exact runtime version and repeat it in build deps: `dependencies = ["axolotl[deepspeed, flash-attn]", "torch==2.6.0"]` and `axolotl = ["torch==2.6.0"]` etc.
- Alternatively provide metadata upfront so uv need not build during resolution:

```toml
[[tool.uv.dependency-metadata]]
name = "flash-attn"
version = "2.6.3"
requires-dist = ["torch", "einops"]
```

- `version` in `dependency-metadata` is optional for registry deps (applies to all versions) but required for direct URL deps (e.g. Git).

Disable build isolation:

```toml
[project]
dependencies = ["cchardet", "cython", "setuptools"]

[tool.uv]
no-build-isolation-package = ["cchardet"]
```

- CLI equivalent: `--no-build-isolation-package`. uv does a two-phase install: isolation-capable packages first, then the non-isolated ones, so build deps listed as project deps are installed beforehand.
- Fits `flash-attn` (needs `torch` at build and run time, versions guaranteed consistent). For build-only deps like `cchardet`'s `cython`, put them in an extra (`[project.optional-dependencies] build = ["setuptools", "cython"]`), run `uv sync --extra build`, then `uv sync` to remove them.
- If build deps are needed even at **resolution** time, preinstall them with the pip API: `uv venv`, `uv pip install torch setuptools`, `uv sync`. Or use `dependency-metadata` as above.

### Editable mode

- The project is installed editable by default. `uv sync` and `uv run` accept `--no-editable`, intended for deployments (e.g. Docker) where the env must not depend on the source tree.

### Conflicting dependencies

- uv resolves all deps together, including extras and groups; incompatible sections fail resolution unless declared as conflicting:

```toml
[tool.uv]
conflicts = [
    [ { extra = "extra1" }, { extra = "extra2" } ],
    [ { group = "group1" }, { group = "group2" } ],
]
```

### Limited and required environments

- `environments` restricts which platforms/Pythons the lockfile solves for (PEP 508 markers):

```toml
[tool.uv]
environments = ["sys_platform == 'darwin'", "sys_platform == 'linux'"]
```

- `required-environments` marks platforms the project *must* support, e.g. `["sys_platform == 'darwin' and platform_machine == 'x86_64'"]`. Only relevant for packages that publish no source distribution (like PyTorch), since they install only where wheels exist. On Linux, combine with `minimum-libc-version`.

## Running commands (`uv run`)

https://docs.astral.sh/uv/concepts/projects/run/

- The `.venv` is isolated from your shell, so `python -c "import example"` fails; use `uv run python -c "import example"`.
- `uv run` ensures the env is up to date (locks and syncs) before running. The command may come from the env (`uv run example-cli foo`) or from outside (`uv run bash scripts/foo.sh`).
- `--with` adds a dependency for one invocation, overriding the project's requirement: `uv run --with httpx==0.26.0 python -c "..."` uses 0.26.0 even if the project pins `httpx==0.24.0`.
- Scripts with inline metadata (`# /// script` with `dependencies = [...]`) run **isolated from the project**, with only their declared deps: `uv run example.py`.
- Windows legacy setuptools scripts in `.venv\Scripts`: `.ps1`, `.cmd`, `.bat` supported; the extension can be omitted and is searched in that order (`uv run --with nuitka==2.6.7 -- nuitka --version`).
- Signals: uv does not hand over the process. On Unix it forwards most signals except SIGKILL, SIGCHLD, SIGIO, SIGPOLL. SIGINT is forwarded only if sent more than once or if the child's process group differs from uv's. On Windows uv ignores Ctrl-C and lets the child handle it.

## Locking and syncing

https://docs.astral.sh/uv/concepts/projects/sync/

- Locking = resolving deps into `uv.lock`. Syncing = installing a subset of the lockfile into the project env.
- Both are **automatic**: `uv run` locks and syncs first; commands that read the lockfile (e.g. `uv tree`) update it first.

### `--locked` vs `--frozen` vs `--no-sync`

- `--locked`: don't update the lockfile; **error** if it is out of date. Use in CI to assert the lock is current. `uv lock --check` is the equivalent check.
- `--frozen`: use the lockfile as-is **without checking** if it is up to date.
- `--no-sync`: run without checking whether the environment is up to date.

```bash
uv run --locked ...
uv run --frozen ...
uv run --no-sync ...
uv lock --check
```

### When is the lockfile outdated?

- Outdated if it no longer matches project metadata: a dependency was added, or constraints changed so the locked version is excluded.
- Still up to date if constraints change but still include the locked version.
- !!! important: new releases on the index never make the lockfile outdated. Upgrades are explicit.

### Syncing

- `uv lock` creates/updates the lockfile explicitly; `uv sync` syncs explicitly (useful so editors see correct versions).
- Project and workspace members are installed **editable**; opt out with `--no-editable`. A project with no build system is not installed.
- `uv sync` is **exact** by default (removes packages not selected); keep extras with `--inexact`. `uv run` is **inexact** by default; force exact with `uv run --exact`.
- Extras (`[project.optional-dependencies]`) are not synced by default: `--extra foo`, `--all-extras`.
- Groups (`[dependency-groups]`, PEP 735): `dev` is synced by default. `--no-dev` excludes it; `--only-dev` installs it without the project and its deps. Also `--all-groups`, `--no-default-groups`, `--group <name>`, `--only-group <name>` (excludes project **and** default groups), `--no-group <name>`.
- Exclusions beat inclusions: `uv sync --no-group foo --group foo` does not install `foo`.

### Upgrading locked versions

- With an existing lock, `uv sync`/`uv lock` prefer locked versions; they change only if constraints exclude them.

```bash
uv lock --upgrade                                  # all packages
uv lock --upgrade-package <package>                # one package, others kept
uv lock --upgrade-package <package>==<version>     # one package to a version
```

- Upgrades stay within declared constraints (an upper bound caps them).
- Git deps: a locked commit SHA is preferred over the latest commit on a referenced branch unless `--upgrade`/`--upgrade-package` is used.
- These flags also work on `uv sync` and `uv run` to update lockfile and environment together.

### Partial installs (e.g. Docker layer caching)

- `uv sync --no-install-project`: skip the current project.
- `--no-install-workspace`: skip all workspace members, including the root.
- `--no-install-package <NO_INSTALL_PACKAGE>`: skip given packages.
- The target's dependencies are still installed. Misuse can leave a package without its deps (broken env).

### Malware checks (preview)

- During sync, uv can check the lockfile against OSV (OpenSSF malicious packages, MAL advisories); a match terminates the sync.
- Enable: `audit.malware-check = true` in settings or `UV_MALWARE_CHECK=1`. Alternative service: `audit.malware-check-url` or `UV_MALWARE_CHECK_URL`.

## Exporting lockfiles (`uv export`)

https://docs.astral.sh/uv/concepts/projects/export/

```bash
uv export --format requirements.txt --output-file requirements.txt
uv export --format pylock.toml --output-file pylock.toml
uv export --format cyclonedx1.5 --output-file sbom.json
```

- Prints to stdout by default; `--output-file` writes a file.
- `requirements.txt`: pip-compatible; install with `uv pip install` or `pip`. The docs recommend against keeping both a `uv.lock` and a `requirements.txt`: `uv.lock` expresses things `requirements.txt` cannot.
- `pylock.toml` (PEP 751): relative local paths are written relative to the output file's directory (relative to the cwd when writing to stdout). Use `--output-file` when writing it into another directory.
- CycloneDX (preview, may change): JSON CycloneDX v1.5 SBOM of the project and all deps, for security auditing, compliance, and SCA tools. Custom component properties: `uv:package:marker` (environment markers) and `uv:workspace:path` (relative path of workspace members).

## Building distributions (`uv build`)

https://docs.astral.sh/uv/concepts/projects/build/

- !!! important: `uv build` is a **build frontend**. It picks the Python version and invokes the backend from `[build-system]`; included files and filenames are decided by the backend.
- Default: builds the project in the current directory into `dist/` (e.g. `example-0.1.0-py3-none-any.whl` and `example-0.1.0.tar.gz`). `uv build path/to/project` builds elsewhere.
- Builds the sdist first, then the wheel **from that sdist**. `--sdist` only, `--wheel` only, `--sdist --wheel` builds both from source.
- Before publishing, run `uv build --no-sources` to check it builds without `tool.uv.sources`, as other build tools would ([dependencies page](https://docs.astral.sh/uv/concepts/projects/dependencies/)).

### Build constraints and hashes

```bash
uv build --build-constraint constraints.txt --require-hashes
# constraints.txt:
# setuptools==68.2.2 --hash=sha256:b454a356...
```

- `--require-build-hashes` requires hashes for every build dep, including transitive ones (experimental; suppress the warning with `--preview-features build-dependency-hashes`).
- Project-level, during resolution and installation:

```toml
[tool.uv]
build-constraint-dependencies = [
    { requirement = "setuptools==68.2.2", hashes = ["sha256:b454a35605876da60632df1a60f736524eb73cc47bbc9f3f1ef1b644de74fd2a"] },
    "wheel<1",
]
require-build-hashes = true   # optional: hash every build dep
```

- Hashed entries must pin an exact version (or a direct URL). Hashes may also come from URL fragments in `build-system.requires`, not from requirements returned by a backend.
- Not hash-checked: deps used when build isolation is disabled, already-installed packages, previously built wheels. The bundled `uv_build` backend needs no hash (it ships in the uv executable).

### Preventing publish to PyPI

```toml
[project]
classifiers = ["Private :: Do Not Upload"]
```

- PyPI rejects the upload. Does not affect alternative registries. The docs also recommend per-project PyPI API tokens.

## Workspaces

https://docs.astral.sh/uv/concepts/projects/workspaces/

- A collection of packages (members) managed together, Cargo-style. Each member has its own `pyproject.toml`; the workspace shares **one lockfile**.
- `uv lock` acts on the whole workspace. `uv run` and `uv sync` act on the workspace root by default; `--package <member>` targets a member from any workspace directory.
- Create one by adding `[tool.uv.workspace]` to a `pyproject.toml` (that package becomes the root). `uv init` inside an existing package adds the new project as a member by default, creating the table if needed.

```toml
[project]
name = "albatross"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["bird-feeder", "tqdm>=4,<5"]

[tool.uv.sources]
bird-feeder = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]          # required, globs
exclude = ["packages/seeds"]      # optional, globs
```

- Every directory matched by `members` (and not `exclude`) must contain a `pyproject.toml`. Members can be applications or libraries. The root is also a member.
- `uv run` == `uv run --package albatross`; `uv run --package bird-feeder` runs in that member.

### Workspace sources

- `{ workspace = true }` means the dependency comes from the workspace, not a registry. `workspace` can also be a path string to an **external** workspace root (resolved relative to the declaring project, or the root for root-level sources); uv selects the member that matches the dependency name.
- Dependencies between members are editable.
- Root `tool.uv.sources` apply to all members unless a member overrides that dependency. A member's source for a dependency fully replaces the root's for it, **even if the member's source has a marker that doesn't match the current platform**.

### Layout

- Common: root project plus libraries under `packages/`, single `uv.lock` at the root. Excluded dirs (`packages/seeds`) are not members.

### When (not) to use workspaces

- Use for multiple interconnected packages in one repo: e.g. core library vs CLI tested independently; library plus a performance-critical extension module; plugin system with each plugin as a member depending on the root.
- Don't use when members have **conflicting requirements** or need **separate venvs**. Use independent projects with path deps instead:

```toml
[tool.uv.sources]
bird-feeder = { path = "packages/bird-feeder" }
```

  This gives finer control over resolution and environments, but `uv run --package` is unavailable; run commands from each package directory.
- A workspace enforces a single `requires-python`: the intersection of all members'. To test one member on a Python the rest doesn't support, use `uv pip` in a separate venv.
- Python has no dependency isolation: uv cannot stop a member importing deps declared by another member.
