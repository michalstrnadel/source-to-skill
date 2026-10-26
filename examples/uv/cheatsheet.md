# uv cheatsheet

Commands, config keys and snippets from across the uv docs. Each line ends
with its live docs page (base https://docs.astral.sh/uv/).

## Install and update

```
curl -LsSf https://astral.sh/uv/install.sh | sh        # standalone; put a version in the URL to pin, e.g. /uv/0.13.5/install.sh
UV_NO_MODIFY_PATH=1                                     # installer: don't edit shell profiles
UV_UNMANAGED_INSTALL=/path                              # installer for CI: no profile edits, no self-update
uv self update                                          # standalone-installer installs only
uv generate-shell-completion zsh                        # uvx: uvx --generate-shell-completion <shell>
```
getting-started/installation/, reference/installer/

## Projects

```
uv init example-app                 # app (default): src/ layout, uv_build backend, [project.scripts]
uv init --lib example-lib           # library: always packaged, adds py.typed
uv init --no-package app            # flat main.py, no build system (project not installed)
uv init --bare                      # only pyproject.toml
uv init --build-backend maturin x   # hatchling | uv_build | flit-core | pdm-backend | setuptools | maturin | scikit-build-core
uv add requests       # --dev | --group lint | --optional net | --bounds major
uv add git+https://github.com/encode/httpx --tag 0.27.0   # --branch / --rev / --lfs
uv add torch --index pytorch=https://download.pytorch.org/whl/cpu
uv add -r requirements.txt -c constraints.txt              # migrate from requirements files
uv remove requests
uv run --with httpx==0.26.0 python   # extra dep for one run, overrides the project's version
uv run --locked ...                  # error if uv.lock is stale (CI)
uv run --frozen ...                  # use uv.lock without checking it
uv run --no-sync ...                 # don't check the environment (implies --frozen)
uv lock --check                      # same as --locked
uv lock --upgrade                    # upgrade everything within constraints
uv lock --upgrade-package <pkg>[==<ver>]
uv sync --inexact                    # keep extraneous packages (sync is exact by default)
uv sync --extra foo --all-extras --no-dev --only-dev --group g --only-group g --no-group g --all-groups
uv sync --no-install-project | --no-install-workspace | --no-install-package <pkg>   # partial installs (Docker layers)
uv sync --no-editable
uv tree
uv export --format requirements.txt | pylock.toml | cyclonedx1.5 --output-file F
uv version --bump patch --bump beta  # 1.3.0 => 1.3.1b1; --dry-run
uv build [--sdist|--wheel] --no-sources
uv publish --index testpypi          # index needs publish-url; --check-url <url> for safe retries
uv audit --ignore-until-fixed <ID>
```
concepts/projects/init/, concepts/projects/dependencies/, concepts/projects/sync/, concepts/projects/export/, guides/package/, reference/cli/

## pyproject.toml keys

```toml
[tool.uv]
package = false                      # never build/install the project (virtual project)
default-groups = ["dev", "foo"]      # or "all"
constraint-dependencies = ["grpcio<1.65"]       # narrow only (workspace root only)
override-dependencies = ["werkzeug==2.3.0"]     # replace declared requirements
exclude-dependencies = ["werkzeug"]
environments = ["sys_platform == 'darwin'"]     # limit platforms resolved
required-environments = ["sys_platform == 'darwin' and platform_machine == 'x86_64'"]
conflicts = [[{ extra = "cpu" }, { extra = "cu130" }]]
exclude-newer = "1 week"             # or an RFC 3339 timestamp
cache-keys = [{ file = "pyproject.toml" }, { git = { commit = true } }]   # replaces the defaults
required-version = ">=0.5.0"
compile-bytecode = true
no-build-isolation-package = ["cchardet"]

[tool.uv.extra-build-dependencies]
flash-attn = [{ requirement = "torch", match-runtime = true }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true                      # only for packages that name it in sources

[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]
mylib = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/seeds"]

[tool.uv.build-backend]
module-root = ""                     # flat layout (default "src")
```
reference/settings/, concepts/projects/config/, concepts/indexes/, concepts/projects/workspaces/

## Scripts and tools

```
uv run --with rich example.py
uv run --no-project example.py                  # flag goes before the script
uv add --script example.py 'requests<3'         # PEP 723 inline metadata
uv lock --script example.py                     # creates example.py.lock
#!/usr/bin/env -S uv run --script
# /// script  [tool.uv] exclude-newer = "2023-10-16T00:00:00Z"
uvx ruff                                         # = uv tool run ruff
uvx ruff@latest | uvx ruff@0.3.0 | uvx --isolated ruff
uvx --from httpie http
uv tool install ruff | uv tool install --with-executables-from ansible-core,ansible-lint ansible
uv tool upgrade --all                            # keeps install-time constraints
uv tool update-shell                             # put the tool bin dir on PATH
```
guides/scripts/, concepts/tools/

## Python

```
uv python install 3.12 [--default]   # --default also adds python/python3
uv python upgrade
uv python pin 3.12 [--global]        # writes .python-version
uv python find [--system]
uv python list --only-installed
python-preference = "managed" | "only-managed" | "system" | "only-system"
python-downloads = "manual"          # or --no-python-downloads
```
concepts/python-versions/, guides/install-python/

## Resolution

```
uv pip compile --universal requirements.in -o requirements.txt
uv pip compile --python-platform linux --python-version 3.10 ...   # exact version, not a lower bound
--resolution lowest | lowest-direct          # test library lower bounds in CI
--prerelease if-necessary | allow | disallow | explicit   # default if-necessary
--fork-strategy requires-python | fewest
--exclude-newer "1 week"
--index-strategy first-index | unsafe-first-match | unsafe-best-match
```
concepts/resolution/, concepts/indexes/

## pip interface

```
uv venv --python 3.11 --seed
uv pip install --system pkg          # first Python on PATH (CI/containers); or UV_SYSTEM_PYTHON=1
uv pip compile requirements.in -o requirements.txt --upgrade-package ruff
uv pip sync requirements.txt         # exact: removes extraneous packages (also pylock.toml)
uv pip install --no-build-isolation pkg
uv pip install torch --torch-backend=auto     # UV_TORCH_BACKEND; uv pip only
--override overrides.txt | --build-constraint file | --compile-bytecode
```
pip/compile/, pip/environments/, pip/compatibility/

## Cache and config

```
uv cache clean [pkg] | uv cache prune | uv cache prune --ci | uv cache dir
--refresh | --refresh-package <pkg> | --reinstall    # prefer --refresh over --no-cache
--no-config | --config-file uv.toml
uv run --env-file .env | UV_ENV_FILE | --no-env-file
--preview | --preview-features a,b | UV_PREVIEW=1
```
concepts/cache/, concepts/configuration-files/, concepts/preview/

## Docker

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```
Also: `.venv` in `.dockerignore`; `--no-editable` for multi-stage builds;
`UV_NO_DEV=1`, `UV_PYTHON_DOWNLOADS=0`. guides/integration/docker/

## CI and registries

```
astral-sh/setup-uv  (version: "0.13.5", enable-cache: true, python-version: ${{ matrix.python-version }})
uv sync --locked --all-extras --dev && uv run pytest tests
uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
uv cache prune --ci
astral-sh/uv-pre-commit hooks: uv-lock, uv-export, pip-compile
UV_INDEX_<NAME>_USERNAME / UV_INDEX_<NAME>_PASSWORD     # usernames: aws (CodeArtifact), oauth2accesstoken (Google)
uv tool install keyring --with keyrings.codeartifact ; UV_KEYRING_PROVIDER=subprocess
uv publish --index <name> -u "" -p "$JFROG_TOKEN"        # JFrog: --token gives a 401
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=project
uvx marimo edit --sandbox my_notebook.py
```
guides/integration/github/, guides/integration/aws/, guides/integration/jfrog/, guides/integration/jupyter/, guides/integration/marimo/

## Environment variables worth knowing

```
UV_DEFAULT_INDEX / UV_INDEX          # replace deprecated UV_INDEX_URL / UV_EXTRA_INDEX_URL
UV_LOCKED=1 / UV_FROZEN=1
UV_PROJECT_ENVIRONMENT               # project venv path (default .venv)
UV_HTTP_TIMEOUT (30 s), UV_HTTP_CONNECT_TIMEOUT (10 s), UV_HTTP_RETRIES (3), UV_UPLOAD_HTTP_TIMEOUT (900 s)
UV_LOCK_TIMEOUT                      # cache lock wait, default 300 s (5 min)
UV_SYSTEM_CERTS=true / SSL_CERT_FILE # OS trust store / custom PEM (replaces the bundled roots)
UV_PYTHON_INSTALL_MIRROR
RUST_LOG=uv=debug                    # same as --verbose
```
reference/environment/
