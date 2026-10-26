# The pip interface (`uv pip`, `uv venv`)

Source pages: https://docs.astral.sh/uv/pip/compatibility/ · https://docs.astral.sh/uv/pip/compile/ · https://docs.astral.sh/uv/pip/dependencies/ · https://docs.astral.sh/uv/pip/environments/ · https://docs.astral.sh/uv/pip/inspection/ · https://docs.astral.sh/uv/pip/packages/

`uv pip` is a drop-in replacement for common `pip` / `pip-tools` workflows: swapping `pip install` for `uv pip install` should usually "just work". It is *not* an exact clone; the further from common workflows, the more differences. Use it when you manage environments by hand (requirements files, existing venvs, CI images); use the project interface (`uv add` / `uv lock` / `uv sync`) for `uv.lock`-based projects.

## Environments: where `uv pip` installs

- uv requires a virtual environment by default (unlike `pip`, which installs into the global environment when no venv is active). https://docs.astral.sh/uv/pip/environments/
- Discovery order for mutating commands (`uv pip install`, `uv pip sync`):
  1. Activated venv from `VIRTUAL_ENV`.
  2. Activated Conda env from `CONDA_PREFIX`.
  3. `.venv` in the current directory or the nearest parent directory (does not need to be activated).
  4. Nothing found: uv prompts to create one with `uv venv`.
- Non-mutating commands (e.g. `uv pip compile`) do not *require* a venv, but still need a Python interpreter.
- `VIRTUAL_ENV=/path/to/venv` makes uv install there; ignored if the directory is not a PEP 405 compliant venv.
- `--python /path/to/python` installs into the environment of that interpreter, venv or not; also accepts a venv root directory.
- `--system` installs into the first Python on `PATH` (roughly `--python $(which python)`, but venv-linked executables are skipped). Appropriate in CI and containers.
- `--system` is also the opt-in to mutate a system interpreter found by a version request: with `--python 3.12`, if uv finds `/usr/lib/python3.12`, `--system` is required. Without `--system`, uv ignores non-venv interpreters; with `--system`, it ignores venv interpreters.
- System Python installs are best-effort; e.g. Debian Python < 3.10 is unsupported (distro patches `distutils` but not `sysconfig`). In such non-standard environments, venvs are required.
- `python -m uv` (uv installed into a Python env via pip) defaults to the parent interpreter's environment; adds startup overhead, not recommended for general use.
- uv itself does not depend on Python, but needs a Python environment to install into and to build source distributions.
- `--user` is not supported, and uv never falls back to the `user` scheme when the target is not writable (pip does). Use venvs. https://docs.astral.sh/uv/pip/compatibility/
- `EXTERNALLY-MANAGED` installs need `--break-system-packages` (`UV_BREAK_SYSTEM_PACKAGES`), intended for CI against apt-managed Pythons.
- `--target <dir>` installs packages flat into a directory; `--prefix <dir>` installs into `lib`/`bin`/... as if a venv were there. Prefer `--python` over `--prefix`: scripts installed via `--prefix` reference the installing interpreter and are non-portable. Both only need an interpreter for resolution (uv downloads one if missing; disable with `--no-python-downloads`).

### Creating and activating venvs

```bash
uv venv                    # creates .venv
uv venv my-name            # custom path
uv venv --python 3.11      # specific Python; downloaded if unavailable
uv pip install ruff        # finds .venv automatically, no activation needed

source .venv/bin/activate          # POSIX sh/bash/zsh
source .venv/bin/activate.fish     # fish
source .venv/bin/activate.csh      # csh
use .venv\Scripts\activate.nu      # nushell
.venv\Scripts\activate             # PowerShell
deactivate
```

Useful `uv venv` flags (see cli-reference.md): `--seed` (pip/setuptools/wheel; setuptools and wheel not included for Python 3.12+), `--clear`, `--allow-existing`, `--relocatable`, `--prompt`, `--system-site-packages` (runtime access only; uv commands like `uv pip list` ignore system site packages, unlike pip).

## Managing packages

```bash
uv pip install flask
uv pip install "flask[dotenv]"                 # extras
uv pip install flask ruff
uv pip install 'ruff>=0.2.0'
uv pip install 'ruff==0.3.0'
uv pip install "ruff @ ./projects/ruff"        # from disk
uv pip install "git+https://github.com/astral-sh/ruff"
uv pip install "git+https://github.com/astral-sh/ruff@v0.2.0"    # tag
uv pip install "git+https://github.com/astral-sh/ruff@1fadefa67b26508cc59cf38e6130bde2243c929d"  # commit
uv pip install "git+https://github.com/astral-sh/ruff@main"      # branch
uv pip install -e .                            # editable current project
uv pip install -e "ruff @ ./project/ruff"
uv pip uninstall flask ruff
```

From files (https://docs.astral.sh/uv/pip/packages/):

```bash
uv pip install -r requirements.txt
uv pip install -r pyproject.toml
uv pip install -r pyproject.toml --extra foo
uv pip install -r pyproject.toml --all-extras
uv pip install --group foo                               # group from ./pyproject.toml
uv pip install --project some/path/ --group foo --group bar
uv pip install --group some/path/pyproject.toml:foo --group other/pyproject.toml:bar
```

- As in pip, `--group` does not apply to sources given with `-r` / `-e`: `uv pip install -r some/path/pyproject.toml --group foo` takes `foo` from `./pyproject.toml`, not `some/path/pyproject.toml`.
- `uv pip install` keeps already-installed packages unless they conflict; use `uv pip sync` (or `uv pip install --exact`) for an exact match.
- Order matters more than in pip: `uv pip install foo bar` prioritizes newer versions of `foo` over `bar` and may resolve differently from `uv pip install bar foo`. Same for order inside input files. https://docs.astral.sh/uv/pip/compatibility/#package-priority

## Declaring dependencies

Best practice: declare dependencies in a static file, then lock. https://docs.astral.sh/uv/pip/dependencies/

```toml
[project]
dependencies = ["httpx", "ruff>=0.3.0"]

[project.optional-dependencies]
cli = ["rich", "click"]       # an "extra": --extra cli / --all-extras / pkg[cli]
```

`requirements.in` (one requirement per line, named `.in` to distinguish from the locked `requirements.txt`) does not support optional dependency groups / extras.

## Locking: `uv pip compile`

```bash
uv pip compile pyproject.toml -o requirements.txt
uv pip compile requirements.in -o requirements.txt
uv pip compile pyproject.toml requirements-dev.in -o requirements-dev.txt
uv pip compile setup.py -o requirements.txt     # setup.py / setup.cfg supported
echo "ruff" | uv pip compile -                  # stdin
uv pip compile pyproject.toml --extra foo
uv pip compile pyproject.toml --all-extras
uv pip compile --group foo                      # group from ./pyproject.toml
uv pip compile --project some/path/ --group foo --group bar
uv pip compile --group some/path/pyproject.toml:foo --group other/pyproject.toml:bar
```

- Without `-o/--output-file`, output is only displayed (pip-tools writes a file by default).
- `--group` does not apply to other sources: `uv pip compile some/path/pyproject.toml --group foo` sources `foo` from `./pyproject.toml`.
- Accepted inputs: `requirements.txt`, `.py` with inline metadata, `pylock.toml`, `pyproject.toml`, `setup.py`, `setup.cfg`. Output to `requirements.txt` or `pylock.toml` (`--format`, inferred from `-o` extension).
- Upgrading: pins already in the output file are kept on re-compile. `--upgrade-package ruff` (`-P`) upgrades one; `--upgrade` (`-U`) upgrades all.

```bash
echo "ruff==0.3.0" > requirements.txt
echo "ruff" | uv pip compile - -o requirements.txt                       # stays ruff==0.3.0
uv pip compile - -o requirements.txt --upgrade-package ruff
```

### Defaults that differ from pip-tools

https://docs.astral.sh/uv/pip/compatibility/#pip-compile-defaults
- Extras stripped by default (`--strip-extras`); keep with `--no-strip-extras`.
- No index URLs written; `--emit-index-url` includes *all* index URLs, including the default one.
- Environment markers stripped (resolution valid only for the target env); `--no-strip-markers` keeps them. `--universal` produces one platform-independent file (current/`--python-version` is a lower bound; implies `--no-strip-markers`).
- Other output flags: `--generate-hashes`, `--annotation-style line|split`, `--no-annotate`, `--no-header`, `--custom-compile-command` (`UV_CUSTOM_COMPILE_COMMAND`), `--emit-index-annotation`, `--emit-find-links`, `--emit-build-options`, `--no-emit-package` (= pip-compile `--unsafe-package`), `--no-deps`, `--python-version`, `--python-platform`.

### Constraints, build constraints, overrides, excludes

https://docs.astral.sh/uv/pip/compile/
- Constraints (`-c/--constraint`, `UV_CONSTRAINT`): only bound versions, never trigger installation. Additive. uv also appends `constraint-dependencies` from the workspace-root `pyproject.toml`.

  ```bash
  echo "pydantic<2.0" > constraints.txt
  uv pip compile requirements.in --constraint constraints.txt
  ```
- Build constraints (`--build-constraint`, `UV_BUILD_CONSTRAINT`): same idea for build-time deps (direct or transitive). uv also appends `build-constraint-dependencies` from the workspace root. `--constraint` is *not* applied to build dependencies in uv (pip applies `PIP_CONSTRAINT` to builds but not `--constraint`), so pin e.g. setuptools via `--build-constraint`.
- Build dependency hashes: put `setuptools==83.0.0 --hash=sha256:...` in the build constraints file and pass `--require-build-hashes`. This only covers build deps; for runtime deps use `--require-hashes` on `uv pip install` / `uv pip sync`.

  ```bash
  uv pip compile requirements.in --build-constraint build-constraints.txt --require-build-hashes
  ```
- Overrides (`--override`, `UV_OVERRIDE`): absolute; replace the requirements declared by packages, even if that makes the resolution formally invalid. Typical use: removing an upper bound on a transitive dep (`a` needs `c<2.0`, `b` needs `c>=2.0` -> override `c>=2.0`). Risk: runtime errors if `a` really doesn't support it.
- Excludes (`--exclude`, `UV_EXCLUDE`): packages listed are omitted entirely along with their own deps; specifiers and markers are ignored. (From the CLI reference.)
- Multiple entries per file and multiple files are allowed for constraints and overrides.

## Syncing: `uv pip sync`

```bash
uv pip sync requirements.txt
uv pip sync pylock.toml          # PEP 751
```

- Removes anything not listed (exact match); `uv pip install` would leave extraneous packages. Use sync for reproducibility.
- Input is assumed complete (output of `pip compile` / `uv export`): missing transitive deps are not installed. `--strict` warns about missing deps.
- Hashes: available hashes are verified by default but not required; `--require-hashes` (`UV_REQUIRE_HASHES`) enforces; `--no-verify-hashes` disables.
- `--allow-empty-requirements` lets an empty file clear the environment. `--check` / `--dry-run` inspect without changing.

## Inspecting environments

```bash
uv pip list                     # table; --format json|freeze, --outdated, -e (editables only)
uv pip freeze                   # requirements.txt format; --exclude, --exclude-editable
uv pip show numpy               # several packages allowed; --files lists installed files
uv pip tree                     # dependency tree; --show-version-specifiers
uv pip check                    # conflicts / missing deps
```

Installing in multiple steps can produce conflicting environments; `uv pip check` reports (https://docs.astral.sh/uv/pip/compatibility/#pip-check):
- missing or unparseable `METADATA`;
- `Requires-Python` lower bound excluding the running interpreter (upper bounds ignored);
- dependency on a package that isn't installed, or installed at an incompatible version;
- multiple versions of a package installed (pip check does not warn on this).

Names are shown PEP 503-normalized (`docstring-parser`, `jaraco-classes`, `pymupdfb`) whereas pip shows the published spelling.

## Behavioral differences from pip (decision rules)

All from https://docs.astral.sh/uv/pip/compatibility/

- **Config**: uv ignores `pip.conf` and `PIP_*` env vars (e.g. `PIP_INDEX_URL`). Use `UV_*` env vars (e.g. `UV_INDEX_URL`), `uv.toml`, or `[tool.uv.pip]` in `pyproject.toml`.
- **Pre-releases**: default `if-necessary` prefers stable and falls back to a pre-release only if every satisfying stable candidate is rejected. `--prerelease allow` considers pre-releases for all packages; `--prerelease disallow` excludes them; `explicit` allows them only for first-party requirements that contain a pre-release specifier.
- **Multiple indexes** (`--index-strategy` / `UV_INDEX_STRATEGY`): uv stops at the first index that has the package (extra indexes before the default) to prevent dependency confusion (cf. the Dec 2022 `torchtriton` attack). pip merges candidates from all indexes.
  - `first-index` (default): only versions from the first index containing the package.
  - `unsafe-first-match`: search all indexes, prefer the first index with a compatible version even if newer versions exist elsewhere.
  - `unsafe-best-match`: best version across all indexes; closest to pip, exposed to dependency confusion.
  - Alternatively pin a package to a dedicated index (see indexes concept docs).
- **Build isolation**: PEP 517 isolation always on (like `pip --use-pep517`). If a build fails for a missing build dep: try a newer package version, report upstream; escape hatch: preinstall build deps and disable isolation:

  ```bash
  uv pip install wheel && uv pip install --no-build-isolation biopython==1.77
  ```
- **Transitive URL dependencies**: uv assumes registry packages don't depend on URLs and rejects such URL deps; URL-based constraints/overrides may also reject transitive URL deps. Fix: declare the URL dependency directly in `pyproject.toml` / `requirements.in`.
- **Resolution strategy**: pip and uv may pick different but equally valid solutions (e.g. `starlette` + `fastapi` -> either `fastapi==0.1.17` + newest starlette, or `fastapi==0.110.0` + `starlette==0.36.3`). Undesirable results usually mean specifiers are too loose: tighten them (e.g. `fastapi>=0.110.0`).
- **`--only-binary`**: uv also enforces it for direct URL deps (pip doesn't), except it will build a URL sdist when the package name can't be inferred ahead of time. Editables are always allowed (`uv pip install -e . --only-binary :all:` works).
- **`--no-binary`**: refuses to install pre-built wheels but reuses wheels already in the cache, and the resolver still reads metadata from wheels (unlike pip).
- **`manylinux_compatible`** (PEP 600): respected, but only tested against the current glibc and applied globally; compatible with blanket implementations like `no-manylinux`.
- **Bytecode**: uv does not compile `.pyc` at install time by default. Enable with `--compile-bytecode` or `UV_COMPILE_BYTECODE=1`; recommended for Docker builds (faster startup, slower builds). Without it you may see `SyntaxWarning`/`DeprecationWarning` that pip installs hide.
- **Strictness**: uv rejects some spec violations pip tolerates (e.g. HTML indexes with invalid URL fragments, PEP 503); lenient exceptions exist for popular packages. First try a newer package version, then report upstream.
- **Missing options**: not all pip options/subcommands exist (e.g. `--trusted-host` tracked in #1339, `--user` in #2077); search/upvote issues.
- **Keyring**: only `--keyring-provider subprocess` (no `auto` / `import`), and keyring is not enabled by default. uv can send credentials supplied with a request or cached for its URL before a 401.
- **Eggs**: no `.egg` support. Existing `.egg-info` and legacy `.egg-link` distributions are respected in resolution, listed by `uv pip list` / `freeze`, and uninstallable, but uv won't install new ones.
- **`requires-python` upper bounds** ignored (`>=3.8, <4` treated as `>=3.8`) to avoid backtracking to ancient versions.
- **`requires-python` matching** truncates candidates to major.minor.patch: `>=3.13` accepts 3.13.0b1 (consistent with pip, not strictly PEP 440).
- **Wheel filename vs metadata**: wheels whose filename disagrees with internal metadata (e.g. `foo-1.0.0-...whl` containing version 1.0.1) are rejected; force with `UV_SKIP_WHEEL_FILENAME_CHECK=1`.
- **Name normalization**: output uses PEP 503-normalized names.
