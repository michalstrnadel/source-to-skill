# Running scripts and tools with uv

Source pages: https://docs.astral.sh/uv/guides/scripts/, https://docs.astral.sh/uv/guides/tools/, https://docs.astral.sh/uv/concepts/tools/

## Scripts: core model

- A script is a file meant for standalone execution (`python <script>.py`). `uv run` manages its dependencies without you managing environments by hand.
- uv prefers creating environments **on demand** over a long-lived, manually managed virtualenv, which requires dependencies to be declared explicitly.
- Recommended ways to declare dependencies: a project, or inline script metadata. Per-invocation `--with` is also supported (https://docs.astral.sh/uv/guides/scripts/).

## Running a script

```bash
uv run example.py                 # no deps or stdlib-only: nothing else needed
uv run example.py hello world!    # arguments go after the script
echo 'print("hello world!")' | uv run -   # script from stdin
uv run - <<EOF
print("hello world!")
EOF
```

- Inside a **project** (directory with `pyproject.toml`), `uv run` installs the current project before running the script. If the script does not depend on the project, skip that with `--no-project`, which must come **before** the script name:

  ```bash
  uv run --no-project example.py
  ```

## Per-invocation dependencies: `--with`

```bash
uv run --with rich example.py
uv run --with 'rich>12,<13' example.py   # version constraints allowed
```

- Repeat `--with` for multiple dependencies.
- In a project, `--with` dependencies are added **in addition to** the project's dependencies; opt out with `--no-project`.
- Without a declared dependency, an import fails with `ModuleNotFoundError`.

## Inline script metadata (PEP 723)

- Python has a standard format for inline script metadata that selects Python versions and declares dependencies inside the script.
- Create a script with metadata:

  ```bash
  uv init --script example.py --python 3.12
  ```

- Add / update dependencies (writes the TOML block at the top of the file):

  ```bash
  uv add --script example.py 'requests<3' 'rich'
  ```

  ```python
  # /// script
  # dependencies = [
  #   "requests<3",
  #   "rich",
  # ]
  # ///

  import requests
  from rich.pretty import pprint
  ```

- `uv run example.py` then auto-creates an environment with those dependencies.
- **Important:** with inline metadata, the project's dependencies are ignored even when `uv run` is used inside a project; `--no-project` is not required.
- Python requirement is respected; uv searches for the required version and downloads it if not installed:

  ```python
  # /// script
  # requires-python = ">=3.12"
  # dependencies = []
  # ///
  ```

- The `dependencies` field must be present **even if empty**.

## Shebang: executable scripts

Run a script without typing `uv run`, e.g. when it is on `PATH` or in the current folder:

```python
#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

import httpx

print(httpx.get("https://example.com"))
```

```bash
chmod +x greet && ./greet
```

## Alternative package indexes for scripts

```bash
uv add --index "https://example.com/simple" --script example.py 'requests<3' 'rich'
```

Adds to the inline metadata:

```python
# [[tool.uv.index]]
# url = "https://example.com/simple"
```

For index authentication see https://docs.astral.sh/uv/concepts/indexes/.

## Locking scripts

- Scripts can be locked with the `uv.lock` format, but **unlike projects, they must be locked explicitly**:

  ```bash
  uv lock --script example.py   # creates example.py.lock next to the script
  ```

- Once locked, `uv run --script`, `uv add --script`, `uv export --script`, and `uv tree --script` reuse the locked dependencies and update the lockfile if necessary.
- Without a lockfile, commands like `uv export --script` still work but do not create one.

## Reproducibility: `exclude-newer`

- `exclude-newer` in the `[tool.uv]` section of inline metadata limits resolution to distributions released before a date; use it so a script resolves the same way later.
- Value is an RFC 3339 timestamp (e.g. `2006-12-02T02:07:43Z`).

```python
# /// script
# dependencies = [
#   "requests",
# ]
# [tool.uv]
# exclude-newer = "2023-10-16T00:00:00Z"
# ///
```

## Python version per invocation

```bash
uv run example.py               # default Python (may differ per machine)
uv run --python 3.10 example.py # specific version
```

## GUI scripts (Windows)

- On Windows, scripts ending in `.pyw` are run with `pythonw`: `uv run example.pyw`.
- Works with dependencies too: `uv run --with PyQt5 example_pyqt.pyw`.

## Tools: `uvx` vs `uv tool install`

Tools are Python packages that provide command-line interfaces (https://docs.astral.sh/uv/concepts/tools/).

- `uvx` is an alias for `uv tool run`; the two are **exactly equivalent**. All other tool commands need the full `uv tool` prefix.
- `uvx <tool>`: runs without installing, in a temporary, isolated environment (isolated from the current project).
- `uv tool install <pkg>`: executables go on `PATH`; still an isolated virtualenv, but it is kept after the command completes.
- **Decision rule:** in most cases, running with `uvx` is more appropriate than installing. Install when the tool must be available to other programs, e.g. a script you don't control requires it, or in a Docker image where users need it. Also install if a tool is used often, instead of invoking `uvx` repeatedly.
- **`uvx` vs `uv run` in a project:** if the tool needs your project installed (e.g. `pytest`, `mypy`), use `uv run`, not `uvx`; otherwise the tool runs isolated from your project. With a flat layout (no `src` directory), the project need not be installed and `uvx` is fine; `uv run` then only helps if you want to pin the tool's version in the project's dependencies (https://docs.astral.sh/uv/guides/tools/).

## Running tools with `uvx`

```bash
uvx ruff
uvx pycowsay hello from uv          # args after the tool name
uvx --from httpie http              # command name differs from package name
uvx ruff@0.3.0 check                # exact version
uvx ruff@latest check               # latest version
uvx --from 'ruff==0.3.0' ruff check
uvx --from 'ruff>0.2.0,<0.3.0' ruff check   # ranges need --from
uvx --from 'mypy[faster-cache,reports]' mypy --xml-report mypy_report        # extras
uvx --from 'mypy[faster-cache,reports]==1.13.0' mypy --xml-report mypy_report
uvx --with mkdocs-material mkdocs --help    # plugins / extra deps
uvx --python 3.10 ruff
```

- The `@` syntax only supports an **exact** version; use `--from` with a specifier for anything else.
- Git sources via `--from`:

  ```bash
  uvx --from git+https://github.com/httpie/cli httpie           # from git
  uvx --from git+https://github.com/httpie/cli@master httpie    # latest commit on branch
  uvx --from git+https://github.com/httpie/cli@3.2.4 httpie     # tag
  uvx --from git+https://github.com/httpie/cli@2843b87 httpie   # commit
  uvx --lfs --from git+https://github.com/astral-sh/lfs-cowsay lfs-cowsay   # Git LFS
  ```

- `--with` may be repeated, accepts specifiers (`--with <pkg>==<version>`), and has the shorthand `-w`. If the requested version conflicts with the tool's requirements, resolution fails and the command errors.

## Installing tools

```bash
uv tool install ruff
uv tool install httpie                     # installs all its executables: http, https, httpie
uv tool install 'httpie>0.1.0'             # versions without --from
uv tool install git+https://github.com/httpie/cli
uv tool install --lfs git+https://github.com/astral-sh/lfs-cowsay
uv tool install mkdocs --with mkdocs-material
uv tool install --with-executables-from ansible-core,ansible-lint ansible
uv tool install --python 3.10 ruff
uv tool install ruff@latest
uv tool install ruff@0.6.0
```

- Unlike `uvx`, `uv tool install` operates on a **package** and installs all executables it provides.
- Unlike `uv pip install`, installing a tool does **not** make its modules importable in the current environment (`python -c "import ruff"` fails). This isolation reduces conflicts between tools, scripts, and projects.
- `--with` vs `--with-executables-from`:
  - `--with`: adds packages as dependencies, does **not** install their executables.
  - `--with-executables-from`: adds packages as dependencies **and** installs their executables, all in the same tool environment. Combinable with `--with`.

## Tool versions and caching

- `uv tool install` without a version installs the latest available.
- `uvx` uses the latest version **on the first invocation**, then the cached version unless a different version is requested, the cache is pruned, or the cache is refreshed. A newly released version is not picked up until the cache is refreshed.
- `uvx <tool>@latest` requests the latest version and refreshes the cache.
- Once a tool is installed with `uv tool install`, `uvx` uses the **installed** version by default. Bypass it with:
  - `uvx ruff@latest` (explicit latest), or
  - `uvx --isolated ruff` (ignores the installed version without refreshing the cache).

## Upgrading tools

```bash
uv tool upgrade ruff
uv tool upgrade --all
uv tool upgrade black --upgrade-package click      # one package in the tool env
uv tool upgrade black --reinstall                  # reinstall all packages
uv tool upgrade black --reinstall-package click    # reinstall one package
uv tool upgrade --python 3.10 ruff
```

- Upgrades respect the constraints given at install time: after `uv tool install black >=23,<24`, `uv tool upgrade black` stays within `>=23,<24`. To change constraints, reinstall: `uv tool install black>=24`.
- Upgrades also retain install-time settings, e.g. `--prerelease allow`.
- Upgrades reinstall the tool executables even if unchanged.

## Tool environments and where tools live

- `uvx` environments live in the **uv cache** and are disposable: `uv cache clean` deletes them, and they are recreated automatically. They are cached only to cut overhead on repeat runs.
- `uv tool install` environments live in the **uv tools directory** (`uv tool dir`; see https://docs.astral.sh/uv/reference/storage/#tools). They stay until the tool is uninstalled; if deleted manually, the tool fails to run.
- **Important:** never mutate a tool environment manually, e.g. with a `pip` operation.
- Each tool environment is linked to one Python version, found with the usual discovery logic but **ignoring** non-global requests like `.python-version` files and `requires-python` from `pyproject.toml`. Default is the first interpreter found; override with `--python`.
- If the Python version a tool uses is uninstalled, the tool environment breaks and the tool may be unusable.

## Tool executables and PATH

- Executables = all console entry points, script entry points, and binary scripts of the package. **Executables of the tool's dependencies are not installed.**
- Symlinked into the executable directory on Unix, copied on Windows.
- The executable directory must be on `PATH`; otherwise a warning is shown. Fix with `uv tool update-shell`, which adds it to common shell config files.
- uv will not overwrite executables it did not install (e.g. one installed by `pipx`), so `uv tool install` fails. Override with `--force`.
- Legacy Windows setuptools scripts (`.ps1`, `.cmd`, `.bat` only) are available via `$(uv tool dir)\<tool-name>\Scripts`. The extension can be omitted; `uvx` tries `.ps1`, `.cmd`, `.bat` in that order:

  ```bash
  uv tool run --from nuitka==2.6.7 nuitka --version
  ```

## `uv tool run` vs `uv run`

`uvx <name>` is nearly equivalent to:

```bash
uv run --no-project --with <name> -- <name>
```

Differences with the tool interface:

- No `--with` needed: the package is inferred from the command name.
- The temporary environment is cached in a dedicated location.
- No `--no-project` needed: tools always run isolated from the project.
- If the tool is already installed, `uv tool run` uses the installed version; `uv run` does not.

If the tool should **not** be isolated from the project (e.g. `pytest`, `mypy`), use `uv run`.
