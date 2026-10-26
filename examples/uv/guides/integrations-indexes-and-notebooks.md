# Private indexes, PyTorch and notebooks

Source pages:
- https://docs.astral.sh/uv/guides/integration/aws/
- https://docs.astral.sh/uv/guides/integration/azure/
- https://docs.astral.sh/uv/guides/integration/google/
- https://docs.astral.sh/uv/guides/integration/jfrog/
- https://docs.astral.sh/uv/guides/integration/pytorch/
- https://docs.astral.sh/uv/guides/integration/jupyter/
- https://docs.astral.sh/uv/guides/integration/marimo/

## Private registries: the common pattern

All four registry guides declare the index the same way. Credentials go in per-index env vars derived from the index **name**:

```toml
[[tool.uv.index]]
name = "private-registry"
url = "<registry simple URL>"
publish-url = "<registry upload URL>"   # only if you publish there
```

- `UV_INDEX_<NAME>_USERNAME` / `UV_INDEX_<NAME>_PASSWORD`. `<NAME>` must match the index name in `pyproject.toml`. In the docs' examples, index `private-registry` uses `UV_INDEX_PRIVATE_REGISTRY_*`.
- Tokens use HTTP "Basic" auth: token in the password field, plus a **registry-specific username** (see table below).
- **keyring** (CodeArtifact, Azure, Google): uv supports `keyring` only in **subprocess mode**.
  - The `keyring` executable must be on `PATH` (installed globally or in the active env).
  - The `keyring` CLI needs the username in the URL, or set via `UV_INDEX_<NAME>_USERNAME`.
  - keyring and its plugin must be installed from a source *other than* the private registry (e.g. public PyPI): `uv tool install keyring --with <plugin>`.
  - Enable with `export UV_KEYRING_PROVIDER=subprocess`, or the `tool.uv.keyring-provider` setting in `uv.toml`/`pyproject.toml`.
- **Publishing:** add `publish-url`, set `UV_PUBLISH_USERNAME` / `UV_PUBLISH_PASSWORD` (if not using keyring), then `uv publish --index private-registry`.
  - The publish variables do **not** include the index name.
  - `UV_PUBLISH_URL=<upload URL> uv publish` works without `publish-url`, but it is not preferable: uv then cannot check whether the package is already published before uploading.

Required usernames per registry:

- AWS CodeArtifact: `aws` (token and keyring). Otherwise auth fails.
- Azure Artifacts: any string with a PAT (docs use `dummy`); `VssSessionToken` with keyring.
- Google Artifact Registry: `oauth2accesstoken` (token and keyring). Otherwise auth fails.
- JFrog Artifactory: your username with a password; **empty string** `""` with a JWT.

## AWS CodeArtifact

https://docs.astral.sh/uv/guides/integration/aws/ (assumes `awscli` is installed and authenticated)

- Index URL: `https://<DOMAIN>-<ACCOUNT_ID>.d.codeartifact.<REGION>.amazonaws.com/pypi/<REPOSITORY>/simple/`
- Publish URL: the same URL without `simple/`, i.e. `.../pypi/<REPOSITORY>/`

```bash
export AWS_CODEARTIFACT_TOKEN="$(
    aws codeartifact get-authorization-token \
    --domain <DOMAIN> \
    --domain-owner <ACCOUNT_ID> \
    --query authorizationToken \
    --output text
)"   # may need extra params such as --region
export UV_INDEX_PRIVATE_REGISTRY_USERNAME=aws
export UV_INDEX_PRIVATE_REGISTRY_PASSWORD="$AWS_CODEARTIFACT_TOKEN"
```

- keyring: `uv tool install keyring --with keyrings.codeartifact`, `UV_KEYRING_PROVIDER=subprocess`, `UV_INDEX_PRIVATE_REGISTRY_USERNAME=aws`. The plugin wraps boto3 to generate short-lived tokens, store them in the system keyring and refresh them on expiry.
- Publish: `UV_PUBLISH_USERNAME=aws`, `UV_PUBLISH_PASSWORD="$AWS_CODEARTIFACT_TOKEN"`, `uv publish --index private-registry`.

## Azure Artifacts

https://docs.astral.sh/uv/guides/integration/azure/

- Index URL: `https://pkgs.dev.azure.com/<ORGANIZATION>/<PROJECT>/_packaging/<FEED>/pypi/simple/`
- Publish URL: `.../_packaging/<FEED>/pypi/upload/`
- PAT (e.g. `$(System.AccessToken)` in an Azure pipeline):

```bash
export UV_INDEX_PRIVATE_REGISTRY_USERNAME=dummy
export UV_INDEX_PRIVATE_REGISTRY_PASSWORD="$AZURE_ARTIFACTS_TOKEN"
```

- keyring: `uv tool install keyring --with artifacts-keyring`, `UV_KEYRING_PROVIDER=subprocess`, `UV_INDEX_PRIVATE_REGISTRY_USERNAME=VssSessionToken`. The plugin wraps the Azure Artifacts Credential Provider, which supports several auth modes including interactive login.
- Publish: `UV_PUBLISH_USERNAME=dummy`, `UV_PUBLISH_PASSWORD="$AZURE_ARTIFACTS_TOKEN"`.

## Google Artifact Registry

https://docs.astral.sh/uv/guides/integration/google/ (assumes `gcloud` is installed and authenticated)

- Index URL: `https://<REGION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/`
- Publish URL: `https://<REGION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/`

```bash
export ARTIFACT_REGISTRY_TOKEN=$(
    gcloud auth application-default print-access-token
)   # may need extra params such as --project
export UV_INDEX_PRIVATE_REGISTRY_USERNAME=oauth2accesstoken
export UV_INDEX_PRIVATE_REGISTRY_PASSWORD="$ARTIFACT_REGISTRY_TOKEN"
```

- keyring: `uv tool install keyring --with keyrings.google-artifactregistry-auth`, `UV_KEYRING_PROVIDER=subprocess`, username `oauth2accesstoken`. The plugin wraps the gcloud CLI to produce, store and refresh short-lived tokens.
- Publish: `UV_PUBLISH_USERNAME=oauth2accesstoken`, `UV_PUBLISH_PASSWORD="$ARTIFACT_REGISTRY_TOKEN"`.

## JFrog Artifactory

https://docs.astral.sh/uv/guides/integration/jfrog/ (username/password or JWT; no keyring section)

- Index URL: `https://<organization>.jfrog.io/artifactory/api/pypi/<repository>/simple`
- Publish URL: `https://<organization>.jfrog.io/artifactory/api/pypi/<repository>`
- Username/password: `UV_INDEX_PRIVATE_REGISTRY_USERNAME="<username>"`, `UV_INDEX_PRIVATE_REGISTRY_PASSWORD="<password>"`.
- JWT: `UV_INDEX_PRIVATE_REGISTRY_USERNAME=""`, `UV_INDEX_PRIVATE_REGISTRY_PASSWORD="$JFROG_JWT_TOKEN"`.
- **Important (publishing):** do **not** use `--token` / `UV_PUBLISH_TOKEN` with JFrog. uv sends `__token__` as the username with `--token`, but JFrog requires an empty username, so you get **401 Unauthorized**. Instead:

```
$ uv publish --index <index_name> -u "" -p "$JFROG_TOKEN"
# or
$ export UV_PUBLISH_USERNAME=""
$ export UV_PUBLISH_PASSWORD="$JFROG_TOKEN"
$ uv publish --index private-registry
```

## PyTorch

https://docs.astral.sh/uv/guides/integration/pytorch/ (some features need uv >= 0.5.3)

### Why PyTorch is special

- Many wheels live on a dedicated PyTorch index, not PyPI.
- Each accelerator gets a distinct build, encoded in the **local version** (`2.11.0+cpu`, `2.11.0+cu130`).
- Each accelerator has its own index: `https://download.pytorch.org/whl/cpu`, `.../whl/cu130`, etc.

### Default (no config)

`uv add torch torchvision` installs from PyPI. That gives CPU-only wheels on Windows and macOS and CUDA wheels on Linux (CUDA 13.0 as of PyTorch 2.11.0). This is fine if that is what you want. Otherwise, configure indexes.

### Explicit PyTorch indexes

Available indexes (all with `explicit = true`):

- `pytorch-cpu` -> `https://download.pytorch.org/whl/cpu`
- `pytorch-cu118`, `pytorch-cu126`, `pytorch-cu128`, `pytorch-cu130` -> `https://download.pytorch.org/whl/cu1xx`
- `pytorch-rocm` -> `https://download.pytorch.org/whl/rocm7.2`
- `pytorch-xpu` -> `https://download.pytorch.org/whl/xpu`

Use `explicit = true` so the index serves **only** packages pinned to it (`torch`, `torchvision`, ...). Generic deps like `jinja2` keep coming from PyPI.

CPU-only on every platform:

```toml
[project]
dependencies = ["torch>=2.11.0", "torchvision>=0.26.0"]

[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]
torchvision = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Platform gating rules (sources with `marker`, falling back to PyPI elsewhere):

- CUDA (`cu118`/`cu126`/`cu128`/`cu130`): no macOS builds, so use `marker = "sys_platform == 'linux' or sys_platform == 'win32'"`.
- ROCm: Linux only (`sys_platform == 'linux'`). Also route `pytorch-triton-rocm` and `triton-rocm` to `pytorch-rocm` and list them in `project.dependencies`, e.g. `"pytorch-triton-rocm>=3.5.1 ; sys_platform == 'linux'"`, `"triton-rocm>=3.6.0 ; sys_platform == 'linux'"`.
- Intel XPU: no macOS builds (Linux + Windows). Also route `triton-xpu` to `pytorch-xpu` and add it to dependencies (`"triton-xpu>=3.7.0 ; sys_platform == 'win32' or sys_platform == 'linux'"`).

### Different accelerator per platform (markers)

CUDA on Linux, CPU elsewhere:

```toml
[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", marker = "sys_platform != 'linux'" },
  { index = "pytorch-cu130", marker = "sys_platform == 'linux'" },
]
torchvision = [
  { index = "pytorch-cpu", marker = "sys_platform != 'linux'" },
  { index = "pytorch-cu130", marker = "sys_platform == 'linux'" },
]
# plus [[tool.uv.index]] entries for pytorch-cpu and pytorch-cu130, explicit = true
```

### User-selected accelerator (extras + conflicts)

For `uv sync --extra cpu` vs `uv sync --extra cu130`:

```toml
[project.optional-dependencies]
cpu = ["torch>=2.11.0", "torchvision>=0.26.0"]
cu130 = ["torch>=2.11.0", "torchvision>=0.26.0"]

[tool.uv]
conflicts = [[{ extra = "cpu" }, { extra = "cu130" }]]

[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", extra = "cpu" },
  { index = "pytorch-cu130", extra = "cu130" },
]
torchvision = [
  { index = "pytorch-cpu", extra = "cpu" },
  { index = "pytorch-cu130", extra = "cu130" },
]
```

- The extras must be declared as conflicting.
- Note: with `cu130` enabled this fails to install on macOS (no GPU builds there).

### GPU-enabled extensions (Astral GPU indexes)

- `https://wheels.astral.sh/` provides prebuilt wheels for `flash-attn`, `deepspeed`, `deep-gemm`, `torch-scatter`, `vllm` across Python/CUDA/PyTorch versions. This avoids source builds that need the CUDA toolkit.
- `uv add flash-attn --index astral-cu128=https://wheels.astral.sh/simple/cu128/` adds the dep, configures the index and pins the package to it. Then set `explicit = true` on that index.
- Each index targets one CUDA version; local versions like `+cu.12.8.torch.2.11` encode CUDA 12.8 + PyTorch 2.11. Match Python, platform, CUDA and PyTorch versions.

### uv pip interface

- Take PyTorch's own pip command and replace `pip3` with `uv pip`: `uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`.
- **Automatic backend:** `uv pip install torch --torch-backend=auto` (or `UV_TORCH_BACKEND=auto`).
  - uv detects the installed CUDA driver, AMD GPU versions and Intel GPU presence, then uses the most compatible PyTorch index for PyTorch-ecosystem packages.
  - It falls back to the CPU index if no GPU is found.
  - Index configuration for non-PyTorch packages is still respected.
- Specific backend: `--torch-backend=cu130` / `UV_TORCH_BACKEND=cu130`.
- `--torch-backend` is currently available **only in the `uv pip` interface** (not `uv lock`/`sync`/`run`).

## Jupyter

https://docs.astral.sh/uv/guides/integration/jupyter/

- **In a project (read-only use):** `uv run --with jupyter jupyter lab` (serves at `http://localhost:8888/lab`). Project modules and deps are importable.
- **Need to install packages from the notebook? Create a kernel (recommended):**

```
$ uv add --dev ipykernel
$ uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=project
$ uv run --with jupyter jupyter lab
```

  Select the `project` kernel. Then `!uv add pydantic` persists to `pyproject.toml`/`uv.lock`, while `!uv pip install pydantic` installs into the project venv without persisting.
- **Without a kernel (caveats):**
  - `!uv add` still modifies the *project* env and works immediately.
  - `!uv pip install` installs into *Jupyter's* isolated env (the "active" one). Those packages may disappear on later `jupyter` invocations.
  - For `%pip` magic, run `uv venv --seed` first so pip exists in the project venv. `%pip install` then targets the project venv but does not update `pyproject.toml`/`uv.lock`.
- **Standalone/ad hoc:** `uv tool run jupyter lab` (isolated env).
- **Non-project venv:** `uv venv --seed`, `uv pip install pydantic`, `uv pip install jupyterlab`, then `.venv/bin/jupyter lab` (Windows: `.venv\Scripts\jupyter lab`). There, `!uv pip install` and `!pip install` both work.
- **VS Code:**
  - `uv init project`, `cd project`, `uv add --dev ipykernel`, `code .`, then "Create: New Jupyter Notebook" -> "Python Environments" -> `.venv/bin/python` (`.venv\Scripts\python` on Windows).
  - VS Code requires `ipykernel` in the project env. To avoid a dev dep, use `uv pip install ipykernel`.
  - To run `!uv add` / `!uv pip install` from the notebook you may need `uv add --dev uv`.

## marimo

https://docs.astral.sh/uv/guides/integration/marimo/

marimo notebooks are plain Python scripts, so they integrate tightly with uv.

- **Standalone:** `uvx marimo edit` or `uvx marimo edit my_notebook.py`.
- **Inline script metadata (self-contained notebooks):**
  - `uv add --script my_notebook.py numpy`, then `uvx marimo edit --sandbox my_notebook.py`.
  - marimo uses uv to start an isolated env from the script's deps. Packages installed from the UI are written into the script metadata.
- **In a project:**
  - With marimo as a dependency: `uv run marimo edit my_notebook.py`. Packages added via `uv add` or marimo's UI (which calls `uv add`) persist.
  - Without it: `uv run --with marimo marimo edit my_notebook.py` can import project modules, but UI-installed packages are not added to the project and may disappear.
- **Non-project env:** `uv venv`, `uv pip install numpy marimo` (docs install them separately), then `uv run marimo edit`. The UI installer uses `uv pip install`.
- **Run as a script** (any setup): `uv run my_notebook.py`, with no browser session.
