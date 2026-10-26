# Managing dependencies

Source pages: https://docs.astral.sh/uv/concepts/projects/dependencies/

## Dependency fields

- `project.dependencies`: published dependencies (used when uploading to PyPI or building a wheel; PEP 621, dependency-specifier syntax).
- `project.optional-dependencies`: published optional dependencies ("extras").
- `dependency-groups`: local-only development dependencies (PEP 735).
- `tool.uv.sources`: alternative sources used during development.
- The `project.*` fields are fine even if the project is never published. `dependency-groups` is recently standardized and may not be supported by all tools.
- Edit via `uv add` / `uv remove`, or edit `pyproject.toml` directly.

## Adding, removing, changing

```bash
uv add httpx                       # -> dependencies = ["httpx>=0.27.2"]
uv add "httpx>=0.20"               # explicit constraint
uv add "httpx @ git+https://github.com/encode/httpx"   # adds a tool.uv.sources entry
uv add -r requirements.txt         # import from a requirements file
uv remove httpx
```

- `uv add` writes a lower bound for the most recent compatible version; change the bound kind with `--bounds` (setting `add-bounds`).
- `--dev`, `--group <name>`, `--optional <extra>` target other tables, for both `uv add` and `uv remove`.
- `uv remove` also drops the dependency's source if nothing else references it.
- Unsatisfiable requests error out (`× No solution found when resolving dependencies`).
- Changing a constraint (`uv add "httpx>0.1.0"`) only changes the locked version if needed. Force the newest allowed version: `uv add "httpx>0.1.0" --upgrade-package httpx`.
- Changing the source updates `tool.uv.sources`, e.g. `uv add "httpx @ ../httpx"` for a local checkout.

## Platform-specific dependencies

- Use PEP 508 environment markers:

```bash
uv add "jax; sys_platform == 'linux'"
uv add "numpy; python_version >= '3.11'"
```

```toml
dependencies = ["jax; sys_platform == 'linux'"]
```

- Sources can also vary per platform (see Platform-specific sources).

## Project dependencies example

```toml
[project]
name = "albatross"
version = "0.1.0"
dependencies = [
  "tqdm >=4.66.2,<5",                                      # range
  "torch ==2.2.2",                                         # exact
  "transformers[torch] >=4.39.3,<5",                       # with extra
  "importlib_metadata >=7.1.0,<8; python_version < '3.10'", # marker
  "mollymawk ==0.1.0"
]
```

## Dependency sources (`tool.uv.sources`)

- Adds what the standard can't express, like editable installs and relative paths. Kinds: **index**, **git**, **url**, **path**, **workspace**.
- !!! important: sources are respected **only by uv**. Other tools see only the standard tables; re-specify source metadata in their format if you develop with another tool.

```toml
[tool.uv.sources]
foo = { path = "./packages/foo" }
```

### Index

```bash
uv add torch --index pytorch=https://download.pytorch.org/whl/cpu
uv add --preview-features index-by-name torch --index pytorch   # select an already-configured index by name (preview)
```

```toml
[tool.uv.sources]
torch = { index = "pytorch" }

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

- An `index` source **pins** the package to that index; it won't be fetched from other indexes.
- `explicit = true`: the index is used *only* for packages that name it in `tool.uv.sources`. Without it, other packages may resolve from it if not found elsewhere.
- The example PyTorch CPU index only works on x86-64 Linux (see the PyTorch guide).

### Git

```bash
uv add git+https://github.com/encode/httpx
uv add git+ssh://git@github.com/encode/httpx
uv add git+https://github.com/encode/httpx --tag 0.27.0
uv add git+https://github.com/encode/httpx --branch main
uv add git+https://github.com/encode/httpx --rev 326b9431c761e1ef1e00b9f760d1f654c8db48c6
uv add git+https://github.com/langchain-ai/langchain#subdirectory=libs/langchain
uv add --lfs git+https://github.com/astral-sh/lfs-cowsay
```

```toml
[tool.uv.sources]
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }   # or branch = "main" / rev = "<sha>"
langchain = { git = "https://github.com/langchain-ai/langchain", subdirectory = "libs/langchain" }
lfs-cowsay = { git = "https://github.com/astral-sh/lfs-cowsay", lfs = true }
```

- Git LFS objects are not fetched by default. `lfs = true` always fetches, `lfs = false` never; omitted means the `UV_GIT_LFS` env var decides. Git LFS must be installed and configured or the build can fail.
- A locked commit SHA is preferred over a branch's latest commit until you pass `--upgrade`/`--upgrade-package` (https://docs.astral.sh/uv/concepts/projects/sync/).

### URL

- An `https://` URL to a wheel (`.whl`) or sdist (typically `.tar.gz` or `.zip`):

```bash
uv add "https://files.pythonhosted.org/packages/.../httpx-0.27.0.tar.gz"
```

```toml
[tool.uv.sources]
httpx = { url = "https://files.pythonhosted.org/packages/.../httpx-0.27.0.tar.gz" }
```

- `subdirectory` is allowed if the sdist isn't in the archive root.

### Path

- A local wheel, sdist, or directory with a `pyproject.toml`; absolute or relative:

```bash
uv add /example/foo-0.1.0-py3-none-any.whl
uv add ./foo-0.1.0-py3-none-any.whl
uv add ~/projects/bar/
uv add --editable ../projects/bar/
```

```toml
[tool.uv.sources]
foo = { path = "/example/foo-0.1.0-py3-none-any.whl" }
bar = { path = "../projects/bar", editable = true }
```

- !!! important: a directory path dep is built and installed as a package by default (see Virtual dependencies).
- Path deps are **not editable by default**; request it with `--editable` (project directories only).
- For multiple packages in the same repo, workspaces may fit better.

### Workspace member

```toml
[project]
dependencies = ["foo==0.1.0"]

[tool.uv.sources]
foo = { workspace = true }
# or from another workspace: foo = { workspace = "../other-workspace" }

[tool.uv.workspace]
members = ["packages/foo"]
```

- Every workspace member dependency must be stated explicitly. Workspace members are always editable.

### Platform-specific and multiple sources

```toml
[tool.uv.sources]
# GitHub on macOS only; PyPI everywhere else (httpx is still installed on all platforms)
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.2", marker = "sys_platform == 'darwin'" }
```

```toml
[tool.uv.sources]
httpx = [
  { git = "https://github.com/encode/httpx", tag = "0.27.2", marker = "sys_platform == 'darwin'" },
  { git = "https://github.com/encode/httpx", tag = "0.24.1", marker = "sys_platform == 'linux'" },
]
torch = [
  { index = "torch-cpu", marker = "platform_system == 'Darwin'"},
  { index = "torch-gpu", marker = "platform_system == 'Linux'"},
]

[[tool.uv.index]]
name = "torch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "torch-gpu"
url = "https://download.pytorch.org/whl/cu130"
explicit = true
```

- Multiple sources for one dependency are disambiguated by PEP 508 markers.

### Disabling sources

- `uv lock --no-sources` ignores `tool.uv.sources` (simulates resolving with published metadata). It also stops workspace member discovery for satisfying dependencies.

## Optional dependencies (extras)

- For libraries that keep features optional (e.g. `pandas[plot, excel]`). Declared in `[project.optional-dependencies]`, extra name -> list of specifiers. They can have `tool.uv.sources` entries like normal deps.

```bash
uv add httpx --optional network
```

```toml
[project.optional-dependencies]
plot = ["matplotlib>=3.6.3"]
excel = ["odfpy>=1.4.1", "openpyxl>=3.1.0"]
```

- Conflicting extras fail resolution unless declared in `tool.uv.conflicts` (https://docs.astral.sh/uv/concepts/projects/config/).
- Sources can apply to a specific extra, e.g. CPU vs GPU torch:

```toml
[project.optional-dependencies]
cpu = ["torch"]
gpu = ["torch"]

[tool.uv.sources]
torch = [
  { index = "torch-cpu", extra = "cpu" },
  { index = "torch-gpu", extra = "gpu" },
]
```

- Extras are not synced by default: `uv sync --extra foo` / `--all-extras` (https://docs.astral.sh/uv/concepts/projects/sync/).

## Development dependencies and groups

- Local-only: **not** included in published requirements and not in `[project]`. Can use `tool.uv.sources`.

```bash
uv add --dev pytest          # -> [dependency-groups] dev = ["pytest >=8.1.1,<9"]
uv add --group lint ruff     # -> lint = ["ruff"]
```

- `dev` is special-cased: `--dev`, `--only-dev`, `--no-dev` equal `--group dev`, `--only-group dev`, `--no-group dev`. It is synced by default.
- Other group flags: `--all-groups`, `--no-default-groups`, `--group`, `--only-group`, `--no-group`.
- All groups are resolved together into the lockfile and must be compatible with each other; conflicting groups fail unless declared in `conflicts`.

### Nesting groups

```toml
[dependency-groups]
dev = [
  {include-group = "lint"},
  {include-group = "test"}
]
lint = ["ruff"]
test = ["pytest"]
```

- An included group's dependencies cannot conflict with the group's other dependencies.

### Default groups

```toml
[tool.uv]
default-groups = ["dev", "foo"]
# or: default-groups = "all"
```

- Default is `dev` only. Turn off for one `uv run`/`uv sync` with `--no-default-groups`; drop one with `--no-group <name>`.

### Group `requires-python`

- Groups must fit the project's `requires-python` by default. Override per group:

```toml
[project]
requires-python = ">=3.10"

[dependency-groups]
dev = ["pytest"]

[tool.uv.dependency-groups]
dev = {requires-python = ">=3.12"}
```

### Legacy `dev-dependencies`

- `tool.uv.dev-dependencies = [...]` predates `[dependency-groups]`; its contents merge with `dependency-groups.dev`. It will eventually be deprecated and removed.
- If it exists, `uv add --dev` writes there instead of creating `dependency-groups.dev`.

## Build dependencies

- Packaged projects declare build-only deps in `build-system.requires` (PEP 518):

```toml
[build-system]
requires = ["setuptools>=42"]
build-backend = "setuptools.build_meta"

[tool.uv.sources]
setuptools = { path = "./packages/setuptools" }   # sources apply to build deps too
```

- uv respects `tool.uv.sources` for build deps by default. Before publishing, run `uv build --no-sources` to confirm the package builds without sources, as with other tools such as `pypa/build`.

## Editable dependencies

- A regular install builds a wheel and copies files, so edits go stale. Editable installs add a `.pth` link so the interpreter uses the source directly.
- Limits: the build backend must support editables, and native modules aren't recompiled before import.
- Workspace packages are editable by default.

```bash
uv add --editable ./path/foo
uv add --no-editable ./path/foo    # opt out within a workspace
```

## Virtual dependencies

- Virtual = the dependency itself is not installed, only its dependencies. Never virtual by default.
- A `path` dependency is virtual only if it sets `tool.uv.package = false`. Otherwise uv builds it even without a build system.
- Per-source override:

```toml
[tool.uv.sources]
bar = { path = "../projects/bar", package = false }   # virtual
# bar = { path = "../projects/bar", package = true }  # force install despite tool.uv.package = false
```

- A `workspace` dependency is virtual only if the member sets `tool.uv.package = false`; otherwise it is built even without a build system.
- A workspace member that is **not** a dependency of anything, and has no build system, is virtual by default: it isn't installed, but its deps (e.g. `anyio`) are. Once the root depends on it (`child = { workspace = true }`), it is built and installed.

## Dependency specifiers (PEP 508)

- Order: name, optional extras, version specifier, optional environment marker.
- Comma-separated specifiers combine: `foo >=1.2.3,<2,!=1.4.0`.
- Zero padding: `foo ==2` matches 2.0.0.
- Wildcard: `foo ==2.1.*` accepts any 2.1 release.
- Compatible release: `foo ~=1.2` equals `foo >=1.2,<2`; `foo ~=1.2.3` equals `foo >=1.2.3,<1.3`.
- Extras: `pandas[excel,plot] ==2.2` (whitespace between extras ignored).
- Markers: `colorama >=0.4.6,<5; platform_system == "Windows"`. Combine with `and`, `or`, parentheses: `aiohttp >=3.7.4,<4; (sys_platform != 'win32' or implementation_name != 'pypy') and python_version >= '3.10'`.
- Versions inside markers must be quoted; versions outside markers must not be.
