# Python versions

Source pages: https://docs.astral.sh/uv/concepts/python-versions/, https://docs.astral.sh/uv/reference/storage/

A Python version is the interpreter (`python` executable), the standard library and its supporting files.

## Managed vs system Python

- **Managed**: installed by uv. **System**: everything else. uv doesn't distinguish between OS-installed Pythons and ones managed by other tools, so a `pyenv` Python counts as *system*.
- Managed Pythons live in the `python/` subdirectory of the persistent data dir (e.g. `~/.local/share/uv/python`). Show with `uv python dir`, override with `UV_PYTHON_INSTALL_DIR`. Moving the install dir doesn't update existing venvs; recreate them. (https://docs.astral.sh/uv/reference/storage/)
- Python executables go to the executable directory (e.g. `~/.local/bin`). Show with `uv python dir --bin`, override with `UV_PYTHON_BIN_DIR`.

## Requesting a version

Most commands accept `--python`. uv ensures that version is available, downloading it if needed:

```console
$ uv venv --python 3.11.6
```

Request formats:

- `<version>`: `3`, `3.12`, `3.12.3`
- `<version-specifier>`: `>=3.12,<3.13`
- `<version><short-variant>`: `3.13t`, `3.12.0d`
- `<version>+<variant>`: `3.13+freethreaded`, `3.12.0+debug`, `3.14+gil`
- `<implementation>`: `cpython` or `cp`
- `<implementation>@<version>`: `cpython@3.12`
- `<implementation><version>`: `cpython3.12`, `cp312`
- `<implementation><version-specifier>`: `cpython>=3.12,<3.13`
- `<implementation>-<version>-<os>-<arch>-<libc>`: `cpython-3.12.3-macos-aarch64-none`
- Specific system interpreter: `<executable-path>` (`/opt/homebrew/bin/python3`), `<executable-name>` (`mypython3`), `<install-dir>` (`/some/environment/`)

Architecture: `UV_PYTHON_ARCH=x86_64` makes e.g. `uv sync` use an x86_64 interpreter while honoring the project's version request. A request that names an architecture or an interpreter executable takes precedence.

Implementations (names are case-insensitive): CPython `cpython`/`cp`, PyPy `pypy`/`pp`, GraalPy `graalpy`/`gp`, Pyodide `pyodide`. An unsupported implementation can't be discovered.

## `.python-version` files

- Set the default version request. uv searches the working directory and each parent, then the user-level config directory.
- Any request format works, but a plain version number is recommended for interoperability with other tools.
- `uv python pin` creates one in the current directory. `uv python pin --global` creates one in the user config directory.
- `--no-config` disables discovery.
- The search stops at project/workspace boundaries (the user config dir is the exception).
- A `.python-versions` file (plural) lists several versions; `uv python install` installs all of them.

## Project Python versions

Project commands respect `requires-python` from `pyproject.toml`: uses the first compatible Python unless a version is requested otherwise (`.python-version` or `--python`).

## Installing

uv bundles a list of downloadable CPython and PyPy distributions for macOS, Linux and Windows. **You usually don't need `uv python install`: versions download automatically when needed.**

```console
$ uv python install 3.12.3          # exact
$ uv python install 3.12            # latest patch
$ uv python install '>=3.8,<3.10'   # constraint
$ uv python install 3.9 3.10 3.11   # several
$ uv python install pypy            # implementation
```

- All request formats work except local-interpreter ones (file paths).
- With no arguments: ensures a managed Python is installed (latest), or installs what `.python-version` lists.
- **The available versions are frozen per uv release. New Python releases may require upgrading uv.**

### Python executables on PATH

- Installs versioned executables into `PATH` by default, e.g. `uv python install 3.12` puts `python3.12` in `~/.local/bin` on Unix. If that isn't on `PATH`, run `uv python update-shell`.
- `--default` (experimental) also installs `python` and `python3`: `uv python install 3.12 --default`.
- Only overwrites executables uv manages. An existing non-uv `~/.local/bin/python3.12` needs `--force`.
- Prefers the latest patch per minor version:

```console
$ uv python install 3.12.7  # Adds `python3.12` to `~/.local/bin`
$ uv python install 3.12.6  # Does not update `python3.12`
$ uv python install 3.12.8  # Updates `python3.12` to point to 3.12.8
```

## Upgrading

- Only for uv-managed versions. **Not supported for PyPy, GraalPy, Pyodide.**
- Patch upgrades only (3.13.4 to 3.13.5). Never across minors (3.12 to 3.13), because that can change dependency resolution.

```console
$ uv python upgrade 3.12   # one minor line
$ uv python upgrade        # all installed
```

- After an upgrade the new patch is preferred; the old one is kept since venvs may use it.
- Venvs using that minor version upgrade automatically, **unless created with an explicit patch** (`uv venv -p 3.10.8`).
- Mechanism: a minor-version directory such as `~/.local/share/uv/python/cpython-3.12-macos-aarch64-none` is a symlink (Unix) or junction (Windows) to the patch dir (e.g. `cpython-3.12.11-...`). If another tool canonicalizes that link when creating a venv, the venv won't auto-upgrade.

## Listing and finding

```console
$ uv python list                    # installed + available
$ uv python list 3.13               # filter by request
$ uv python list pypy
$ uv python list --all-versions     # include old patches
$ uv python list --all-platforms    # other platforms
$ uv python list --only-installed
$ uv python find                    # first available executable
$ uv python find '>=3.11'
$ uv python find --system           # ignore virtual environments
```

`uv python find` includes venvs by default. A `.venv` in the cwd or a parent, or `VIRTUAL_ENV`, wins over `PATH` executables.

## Discovery order

Locations checked:

1. Managed installations in `UV_PYTHON_INSTALL_DIR`.
2. `python`, `python3`, `python3.x` on `PATH` (macOS/Linux), or `python.exe` (Windows).
3. Windows only: registry and Microsoft Store interpreters (`py --list-paths`) that match the request.

- Some commands check a virtual environment's interpreter first (see pip-compatible environment discovery).
- Non-executable files are ignored. Each candidate is queried for metadata; failures are skipped; the first match is used without checking further.
- **Managed: newest version first. System: first compatible, not newest.**
- If nothing is found on the system, uv looks for a compatible managed download.

## Pre-release, free-threaded and debug builds

- **Pre-release Pythons**: not selected by default. Used only when nothing else matches, e.g. only a pre-release is available or its path is given explicitly. If a matching pre-release is available, uv won't download a stable one instead.
- **Free-threaded** (CPython 3.13+):
  - 3.13: only when explicitly requested (`3.13t`, `3.13+freethreaded`).
  - 3.14+: allowed without explicit selection, but GIL builds are still preferred (e.g. `uv python install 3.14`). A free-threaded interpreter that comes earlier on `PATH` will be used.
  - Use `+gil` to require the GIL-enabled build when both exist.
- **Debug builds**: slower and not for general use. Used only when nothing else matches or explicitly requested (`3.13d`, `3.13+debug`). Unlike regular uv CPython builds, their debug symbols aren't stripped, which helps with C-level debuggers.

## Controlling downloads and managed vs system

- `python-downloads` setting: `automatic` (default), or `manual` (download only during `uv python install`). Set it in a persistent config file, or pass `--no-python-downloads` to any command.
- `--managed-python`: managed only. `--no-managed-python`: system only.
- `python-preference` setting:
  - `managed` (default): prefer managed over system, but **system is still preferred over downloading** a managed version.
  - `only-managed`: never system (= `--managed-python`).
  - `system`: prefer system over managed.
  - `only-system`: never managed (= `--no-managed-python`).
- You can disable automatic downloads without changing the preference.

## Managed distributions

- **CPython**: from Astral's `python-build-standalone` (also used by Mise and `bazelbuild/rules_python`). Self-contained, portable, performant (no slow source build with PGO/LTO as in `pyenv`). Has portability-related quirks; see the python-build-standalone quirks docs.
- **PyPy**: from the PyPy project. Currently supports only up to Python 3.11.
- **Pyodide**: CPython port for WebAssembly/Emscripten, from the Pyodide project.
- GraalPy is also listed as downloadable; the page has no dedicated section for it.

## x86_64 emulation on aarch64

macOS (Rosetta 2) and Windows on ARM can run x86_64 binaries. Either uv binary can use either interpreter, but a given interpreter needs packages for its own architecture (all x86_64 or all aarch64). Force emulated x86_64 with `UV_PYTHON_ARCH=x86_64` or an explicit request like `cpython-3.14-windows-x86_64`.

## Windows registry

On Windows, managed installs are registered per PEP 514, so the `py` launcher can select them:

```console
$ uv python install 3.13.1
$ py -V:Astral/CPython3.13.1
```

Uninstall removes that registry entry plus any broken ones.
