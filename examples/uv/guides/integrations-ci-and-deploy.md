# uv in CI, containers and deployment

Source pages:
- https://docs.astral.sh/uv/guides/integration/docker/
- https://docs.astral.sh/uv/guides/integration/github/
- https://docs.astral.sh/uv/guides/integration/gitlab/
- https://docs.astral.sh/uv/guides/integration/pre-commit/
- https://docs.astral.sh/uv/guides/integration/dependabot/
- https://docs.astral.sh/uv/guides/integration/renovate/
- https://docs.astral.sh/uv/guides/integration/bazel/
- https://docs.astral.sh/uv/guides/integration/aws-lambda/
- https://docs.astral.sh/uv/guides/integration/coiled/
- https://docs.astral.sh/uv/guides/integration/fastapi/

Version numbers below (`0.13.5`, action SHAs) are the ones the docs use as examples; substitute your own pin.

## Docker

Reference project: `astral-sh/uv-docker-example`.

### Image choice

- **Distroless** images contain only the `uv`/`uvx` binaries; use them to `COPY --from` uv into your own image.
  - `ghcr.io/astral-sh/uv:latest`, `:{major}.{minor}.{patch}` (e.g. `:0.13.5`), `:{major}.{minor}` (e.g. `:0.13`, latest patch).
- **Derived** images = an OS (or Python) base with uv preinstalled. Tags:
  - Alpine: `alpine` / `alpine3.23`, `alpine3.22`
  - Debian: `debian-slim` / `trixie-slim` (on `debian:trixie-slim`), `debian` / `trixie` (on `buildpack-deps:trixie`)
  - Docker Hardened Images: `alpine-dhi` / `alpine3.23-dhi`, `debian-dhi` / `trixie-dhi`, `python3.14-dhi` ... `python3.10-dhi`
  - Python bases: `python3.15-alpine` ... `python3.11-alpine` (also `-alpine3.23` suffixed), `python3.15-trixie` ... `python3.11-trixie`, `python3.15-trixie-slim` ... `python3.11-trixie-slim`
  - Versioned forms: `ghcr.io/astral-sh/uv:{major}.{minor}.{patch}-{base}` and `{major}.{minor}-{base}`, e.g. `ghcr.io/astral-sh/uv:0.13.5-alpine`.
- Since `0.8`, every derived image sets `UV_TOOL_BIN_DIR=/usr/local/bin` so `uv tool install` works for the default user.
- Quick try: `docker run --rm -it ghcr.io/astral-sh/uv:debian uv --help`

### Installing uv into an image

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
```

- Alternative: the installer (`ADD https://astral.sh/uv/install.sh` then `RUN sh /uv-installer.sh && rm /uv-installer.sh`, plus `ENV PATH="/root/.local/bin/:$PATH"`). Requires `curl` and `ca-certificates`. Pin via `https://astral.sh/uv/0.13.5/install.sh`.
- Pin a version, not `latest`. For reproducible builds pin the SHA256 (tags can move): `COPY --from=ghcr.io/astral-sh/uv@sha256:<digest> /uv /uvx /bin/`.
- uv not needed in the final image? Mount it per `RUN` instead of copying:

```dockerfile
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync
```

### Installing a project (simple form)

```dockerfile
COPY . /app
# Disable development dependencies
ENV UV_NO_DEV=1
WORKDIR /app
# Assert the lockfile is up to date
RUN uv sync --locked
CMD ["uv", "run", "my_app"]
```

- **Important:** add `.venv` to `.dockerignore`. The venv is platform-specific and must be created from scratch in the image.
- Using the env afterwards: either `ENV PATH="/app/.venv/bin:$PATH"` (activate) or prefix commands with `uv run`. Or set `UV_PROJECT_ENVIRONMENT` before syncing to install into the system Python and skip activation.
- Installed tools: put the tool bin dir on `PATH` (`ENV PATH=/root/.local/bin:$PATH`), find it with `uv tool dir --bin`, or fix it with `ENV UV_TOOL_BIN_DIR=/opt/uv-bin/`.

### Intermediate layers (best practice for build time)

Install dependencies in their own layer, the project afterwards, because dependencies change rarely and the project often:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```

- Only `uv.lock` is mounted for the first sync; `pyproject.toml` and sources come in before the final sync.
- Exclude more packages from the first sync with `--no-install-package <name>`.
- **Workspaces:** use `--no-install-workspace` (excludes the project *and* all members) in the first sync.
- Decision rule `--frozen` vs `--locked`: uv cannot verify `uv.lock` is current without the member `pyproject.toml` files, so the first (lock-only) sync uses `--frozen`; the final sync, after everything is copied, uses `--locked` to validate the lockfile.

### Non-editable installs / multi-stage

- Projects and workspace members install **editable by default**. `uv sync --no-editable` / `uv run --no-editable` removes the dependency on source code.
- Multi-stage pattern: sync with `--no-editable` in a builder, then copy only `.venv` into the final image.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Use the system Python across both stages
ENV UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-editable
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
CMD ["/app/.venv/bin/hello"]
```

### Bytecode compilation

- Usually desirable for production images: better startup time, at the cost of install time and image size.
- `RUN uv python install --compile-bytecode` / `RUN uv sync --compile-bytecode`, or for every command: `ENV UV_COMPILE_BYTECODE=1`.
- Note: uv compiles the standard library only for *managed* Pythons during `uv python install`. For unmanaged Pythons the distributor decides; the official `python` image does **not** ship a compiled stdlib.

### Caching

```dockerfile
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
```

- `UV_LINK_MODE=copy` silences link warnings: cache mount and sync target are on different filesystems.
- Not mounting a cache? Shrink the image with `--no-cache` or `UV_NO_CACHE`.
- Managed Python downloads are not cached by default; combine `ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python` with the cache mount for `uv python install`.
- Find the cache with `uv cache dir`; pin it with `ENV UV_CACHE_DIR=/opt/uv-cache/`.

### Developing in a container

- Mount the project but **not** `.venv` (keep the image's platform-specific venv): `docker run --rm --volume .:/app --volume /app/.venv [...]` (anonymous volume for `.venv`; `--rm` cleans it up).
- Compose `watch` (needs Compose 2.22.0 / Docker Desktop 4.24): `action: sync` of `.` to `/app` with `ignore: [.venv/]`, plus `action: rebuild` on `./pyproject.toml`; run `docker compose watch`.

### pip interface in Docker

- The container is already isolated, so the system env is safe: `uv pip install --system ruff`, or `ENV UV_SYSTEM_PYTHON=1`.
- Or create a venv: `RUN uv venv /opt/venv`, `ENV VIRTUAL_ENV=/opt/venv`, `ENV PATH="/opt/venv/bin:$PATH"`, then omit `--system`.
- Requirements: `COPY requirements.txt .` then `RUN uv pip install -r requirements.txt`.
- Project + requirements: copy and install deps first for layer caching:

```dockerfile
COPY pyproject.toml .
RUN uv pip install -r pyproject.toml
COPY . .
RUN uv pip install -e .
```

### Verifying image provenance

- Images are signed at build time (attestations; SLSA provenance v1, built by `.github/workflows/build-docker.yml`).
- `gh attestation verify --owner astral-sh oci://ghcr.io/astral-sh/uv:latest`
- Also verifiable with `cosign verify-blob-attestation` against the multi-platform manifest (sigstore-based).
- Verify a specific version tag, or better, a specific digest, rather than `latest`.

## GitHub Actions

### Install uv

- Use the official `astral-sh/setup-uv` action: installs uv, adds it to PATH, optionally persists the cache; all uv platforms.
- Best practice: pin the uv version.

```yaml
steps:
  - uses: actions/checkout@<sha> # v7.0.1
  - name: Install uv
    uses: astral-sh/setup-uv@<sha> # v9.0.0
    with:
      version: "0.13.5"
```

### Python

- `run: uv python install` respects the project's pinned Python.
- Alternative: `actions/setup-python`, which can be faster because GitHub caches Python versions on the runner. Use `python-version-file: ".python-version"` (pinned version) or `python-version-file: "pyproject.toml"` (ignores the pin; latest version matching `requires-python`).
- Matrix: set `python-version: ${{ matrix.python-version }}` on `setup-uv`; it overrides `pyproject.toml`/`.python-version`. Without `setup-uv`, set `env: UV_PYTHON: ${{ matrix.python-version }}`.

### Sync and run

```yaml
- name: Install the project
  run: uv sync --locked --all-extras --dev
- name: Run tests
  run: uv run pytest tests
```

- `UV_PROJECT_ENVIRONMENT` installs into the system Python instead of a venv.

### Caching

- Built in: `setup-uv` with `enable-cache: true`.
- Manual with `actions/cache`: set `UV_CACHE_DIR: /tmp/.uv-cache`, key `uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}` with restore-keys `uv-${{ runner.os }}`, and finish with `run: uv cache prune --ci` (reduces cache size, CI-optimized).
- With `uv pip`, key on `requirements.txt` instead of `uv.lock`.
- Non-ephemeral self-hosted runners: the default cache dir can grow unbounded, so don't share it between jobs. Use `UV_CACHE_DIR: ${{ github.workspace }}/.cache/uv` and remove it with a post-job hook script (`uv cache clean`), registered on the runner via `ACTIONS_RUNNER_HOOK_JOB_STARTED`.

### uv pip

- `uv pip` requires a virtual environment by default. For the system env use `--system` on every invocation, or `UV_SYSTEM_PYTHON: 1` at workflow, job or step `env` scope. Opt out per command with `--no-system`.

### Private GitHub dependencies

Create a PAT with read access, store it as a repo secret, and let `gh` configure a Git credential helper:

```yaml
- run: echo "${{ secrets.MY_PAT }}" | gh auth login --with-token
- run: gh auth setup-git
```

### Publishing to PyPI (Trusted Publishing)

- Example repo: `astral-sh/trusted-publishing-examples`. No credentials needed.
- **Important:** split into `build` and `publish` jobs so only `publish` holds `id-token: write`. This reduces supply-chain attack surface.
- `build` job (`permissions: contents: read`, checkout with `persist-credentials: false`, `setup-uv` with `enable-cache: false`): `uv build`, then optional (recommended) smoke tests:
  - `uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py`
  - `uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py`
  - upload `dist/` as an artifact.
- `publish` job (`needs: build`, `environment: name: pypi`, `permissions: id-token: write`): download `dist/`, generate PEP 740 attestations with `astral-sh/attest-action`, then `run: uv publish`.
- Trigger on tags such as `"v[0-9]+.[0-9]+.[0-9]+"` (plus `rc` and `a`/`b` variants). Create the GitHub environment ("Settings" -> "Environments") and add a Trusted Publisher in the PyPI project settings with matching fields. Release with `git tag -a v0.1.0 -m v0.1.0 && git push --tags`.

## GitLab CI/CD

```yaml
variables:
  UV_VERSION: "0.13.5"
  PYTHON_VERSION: "3.12"
  BASE_LAYER: trixie-slim
  # GitLab CI creates a separate mountpoint for the build directory,
  # so we need to copy instead of using hard links.
  UV_LINK_MODE: copy

uv:
  image: ghcr.io/astral-sh/uv:$UV_VERSION-python$PYTHON_VERSION-$BASE_LAYER
  script:
    # your `uv` commands
```

- Distroless image: set `image: { name: ghcr.io/astral-sh/uv:$UV_VERSION, entrypoint: [""] }`.
- Cache: `UV_CACHE_DIR: .uv-cache`, `cache: key: files: [uv.lock]`, `paths: [$UV_CACHE_DIR]`, and `after_script: uv cache prune --ci` (recommended to reduce cache size).
- `uv pip`: same as GitHub. Use `--system` or `UV_SYSTEM_PYTHON: 1` (top-level `variables`), opt out with `--no-system`. With `uv pip`, consider `requirements.txt` or `pyproject.toml` as cache key files instead of `uv.lock`.

## pre-commit

Official hooks repo: `astral-sh/uv-pre-commit` (`rev` = uv version).

```yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.13.5
    hooks:
      - id: uv-lock      # keep uv.lock up to date when pyproject.toml changes
      - id: uv-export    # keep requirements.txt in sync with uv.lock
      - id: pip-compile  # compile requirements files
        args: [requirements.in, -o, requirements.txt]
```

- Other files: change `args` and add `files`, e.g. `args: [requirements-dev.in, -o, requirements-dev.txt]`, `files: ^requirements-dev\.(in|txt)$`.
- Multiple files: repeat the `pip-compile` hook entry with distinct `name`s.

## Dependabot

- Supports updating `uv.lock`. Some use cases still don't work; track astral-sh/uv#2512.

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    cooldown:
      default-days: 7   # match exclude-newer = "1 week"
```

- Rule: if you use uv's `exclude-newer`, set the equivalent Dependabot `cooldown`. Otherwise you get PRs that uv cannot lock.

## Renovate

- Detects uv from the presence of `uv.lock`. It upgrades project, optional and development dependencies, updating both `pyproject.toml` and `uv.lock`.
- Refresh transitive deps regularly with `lockFileMaintenance: { enabled: true }`.
- PEP 723 scripts are not auto-detected. List them under `pep723: { managerFilePatterns: ["docs/build.py", "scripts/**/*.py"] }`. Renovate does **not** update script lockfiles yet (renovatebot/renovate#33591), so update those by hand.
- Cooldown: with `exclude-newer`, set `minimumReleaseAge` to match, e.g. `"1 week"`, either globally or in a `packageRules` entry with `matchDatasources: ["pypi"]`.

## Bazel

- For full workflows see the `rules_py` and `rules_python` uv guides. The uv page only covers authentication.
- Bazel 7+ supports `--credential_helper`. Reuse uv-stored credentials:

```
$ uv auth login https://packages.example.com
```

```
# .bazelrc
common --credential_helper=packages.example.com=%workspace%/bazel/uv-auth-helper
common --credential_helper=files.example.com=%workspace%/bazel/uv-auth-helper
```

```bash
#!/usr/bin/env bash
# bazel/uv-auth-helper  (chmod +x)
exec uv --preview-features auth-helper auth helper --protocol=bazel "$@"
```

- List every host that serves the index *and* the files. `auth helper` is a preview feature (`--preview-features auth-helper`).

## AWS Lambda

Reference project: `astral-sh/uv-aws-lambda-example`. The example app is FastAPI + `mangum` (ASGI adapter), handler `app.main.handler`, with `fastapi[standard]` in the `dev` group; run locally with `uv run fastapi dev`.

### Container image (multi-stage)

```dockerfile
FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM public.ecr.aws/lambda/python:3.13 AS builder
# Bytecode: better cold-start performance
ENV UV_COMPILE_BYTECODE=1
# No installer metadata: deterministic layer
ENV UV_NO_INSTALLER_METADATA=1
# Copy mode: supports bind-mount caching
ENV UV_LINK_MODE=copy
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

FROM public.ecr.aws/lambda/python:3.13
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ./app ${LAMBDA_TASK_ROOT}/app
CMD ["app.main.handler"]
```

- Pattern: `uv export` the lock to requirements, then `uv pip install --target` the task root. `--no-emit-workspace` and `--no-dev` keep the deps layer cached across app-code and `pyproject.toml` changes while `uv.lock` is unchanged.
- Benefits: the uv binary is not in the final image (minimal size), and source edits reuse cached layers (millisecond rebuilds).
- ARM: use `public.ecr.aws/lambda/python:3.13-arm64`.
- Build with `uv lock && docker build -t fastapi-app .`, push to ECR, then `aws lambda create-function --package-type Image --code ImageUri=...` or `aws lambda update-function-code --image-uri ... --publish`.
- **Workspaces / local libraries:** add a second `RUN` with the same mounts plus `--mount=type=bind,source=library,target=library`, running `uv export --frozen --no-dev --no-editable` (without `--no-emit-workspace`), so third-party deps stay cached separately from workspace changes.

### Zip archive

- Simpler for small apps, but limited to **250 MB**.

```
$ uv export --frozen --no-dev --no-editable -o requirements.txt
$ uv pip install \
   --no-installer-metadata \
   --no-compile-bytecode \
   --python-platform x86_64-manylinux2014 \
   --python 3.13 \
   --target packages \
   -r requirements.txt
$ cd packages && zip -r ../package.zip . && cd ..
$ zip -r package.zip app
```

- ARM: `--python-platform aarch64-manylinux2014`.
- Deploy with `aws lambda create-function --runtime python3.13 --zip-file fileb://package.zip --handler app.main.handler ...`. The console defaults the handler to `lambda_function.lambda_handler`, so change it for a different entrypoint.

### Lambda layer (deps separate from code)

- Reusing the deps layer across deploys can improve cold-start performance for application updates.
- Use `--prefix packages` instead of `--target` (layer layout differs), then `mkdir python && cp -r packages/lib python/ && zip -r layer_content.zip python`.
- `zip -X` gives deterministic archives (excludes extended attributes/metadata).
- `aws lambda publish-layer-version --layer-name dependencies-layer --zip-file fileb://layer_content.zip --compatible-runtimes python3.13 --compatible-architectures "x86_64"`, zip only `app` for the function, then attach with `aws lambda update-function-configuration --layers <layer ARN>`. On dependency changes, republish the layer and update the configuration with the new ARN version.

## Coiled

- Runs PEP 723 scripts on cloud VMs (AWS, GCP, Azure). Inline metadata makes the script self-contained, so it runs anywhere.
- `uvx coiled login`, then add Coiled directives above the script block:

```python
# COILED container ghcr.io/astral-sh/uv:debian-slim
# COILED region us-east-2

# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "pyarrow", "s3fs"]
# ///
```

- Submit with `uvx coiled batch run uv run process.py`. Monitor at cloud.coiled.io or with `coiled batch status` / `wait` / `logs`.
- The container directive ensures uv exists on the VM. Pick the region where the data lives to avoid egress; drop or change `region` if not on AWS. The default instance is a 4-core VM with 16 GiB memory (instance type, disk, spot are configurable).

## FastAPI

Reference: `astral-sh/uv-fastapi-example`.

- Migrate an existing app: `uv init --no-package` (flat, unpackaged project), then `uv add fastapi --extra standard`, then `uv run fastapi dev`. `uv run` locks, creates the venv and runs.
- Docker deploy:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app
WORKDIR /app
RUN uv sync --frozen --no-cache
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]
```

- `docker build -t fastapi-app .` then `docker run -p 8000:80 fastapi-app`. For layering and caching, apply the Docker section above.
