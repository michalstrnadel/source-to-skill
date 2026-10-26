# Python, project, and publishing workflows

Source pages: https://docs.astral.sh/uv/guides/install-python/, https://docs.astral.sh/uv/guides/projects/, https://docs.astral.sh/uv/guides/package/

This is the guide-level workflow. Deeper project concepts (dependencies, sync, lockfile, layout, build backends) live in the concept pages.

## Installing Python

Source: https://docs.astral.sh/uv/guides/install-python/

- If Python is already on the system, uv detects and uses it with no configuration. uv can also install and manage Python, and **automatically installs missing versions** when needed, so you don't need Python preinstalled.
- uv uses distributions from Astral's `python-build-standalone` project, because Python does not publish official distributable binaries.

```bash
uv python install              # latest Python
uv python install 3.12         # specific version
uv python install 3.11 3.12    # several versions
uv python install pypy@3.10    # alternative implementation
uv python install --default    # also install `python` and `python3` executables (experimental)
uv python install --reinstall  # reinstall all previously installed uv-managed versions
uv python list                 # available and installed versions
uv python upgrade 3.12         # upgrade to latest supported patch release
uv python upgrade              # upgrade all uv-managed versions
```

- Installed Python is used by `uv` commands automatically and added to `PATH` as a **versioned** executable only (e.g. `python3.15`). Use `--default` to get `python` / `python3`.
- `--reinstall` can fix bugs even when the version number does not change, because the distributions keep improving.

### Automatic downloads

- By default uv downloads Python when a command needs it, e.g. `uvx python@3.12 -c "print('hello world')"` downloads 3.12 if missing.
- Even with no version requested, uv downloads the latest on demand: `uv venv` on a machine with no Python installs Python first.
- Automatic downloads can be disabled (see https://docs.astral.sh/uv/concepts/python-versions/#disabling-automatic-python-downloads).

### Existing Python

- uv uses the system Python if it satisfies the command's requirements, with no configuration needed.
- Force system Python with `--no-managed-python`.

## Working on projects

Source: https://docs.astral.sh/uv/guides/projects/

### Create a project

```bash
uv init hello-world && cd hello-world   # new directory
# or, in the current directory:
mkdir hello-world && cd hello-world && uv init
```

Created files: `.git/`, `.gitignore`, `.python-version`, `pyproject.toml`, `README.md`, `src/hello_world/__init__.py`. The `pyproject.toml` defines a `hello-world` entrypoint:

```bash
uv run hello-world
# Hello from hello-world!
```

### Project structure

- The first project command (`uv run`, `uv sync`, or `uv lock`) also creates `.venv/` and `uv.lock` in the project root.
- `pyproject.toml`: project metadata and dependencies. Edit by hand or with `uv add` / `uv remove`. uv settings go in a `[tool.uv]` section. Generated example:

  ```toml
  [project]
  name = "hello-world"
  version = "0.1.0"
  description = "Add your description here"
  readme = "README.md"
  authors = [
    { name = "ferris", email = "ferris@example.org" }
  ]
  requires-python = ">=3.14"
  dependencies = []

  [project.scripts]
  hello-world = "hello_world:main"

  [build-system]
  requires = ["uv_build>=0.13.5,<0.14"]
  build-backend = "uv_build"
  ```

- `.python-version`: the project's default Python version; tells uv which version to use when creating the project's virtualenv.
- `.venv`: the project's isolated virtual environment, where dependencies are installed.
- `uv.lock`: cross-platform lockfile with the exact resolved versions (whereas `pyproject.toml` holds broad requirements). **Commit it** for reproducible installs across machines. It is human-readable TOML but managed by uv; **do not edit it manually**.

### Manage dependencies

```bash
uv add requests                            # updates pyproject.toml, lockfile, and environment
uv add 'requests==2.31.0'                  # version constraint
uv add git+https://github.com/psf/requests # git dependency
uv add -r requirements.txt -c constraints.txt   # migrate from requirements.txt
uv remove requests
uv lock --upgrade-package requests         # upgrade one package, keep the rest of the lockfile
```

- `--upgrade-package` tries to move only that package to the latest compatible version and keeps the rest of the lockfile intact.

### Read the project version

```bash
uv version                       # hello-world 0.7.0
uv version --short               # 0.7.0
uv version --output-format json  # {"package_name": ..., "version": ..., "commit_info": null}
```

### Run commands

- Before every `uv run`, uv checks that the lockfile matches `pyproject.toml` and that the environment matches the lockfile, so the command always runs with all required dependencies at their locked versions, with no manual sync.
- Note: `uv run` does **not** remove extraneous packages (not in the lockfile) by default (https://docs.astral.sh/uv/concepts/projects/sync/#handling-of-extraneous-packages).

```bash
uv add flask
uv run -- flask run -p 3000
uv run example.py                 # script that imports a project dependency
```

Alternative: sync manually and activate the environment (activation is required to run without `uv run`, and differs per shell / platform):

```bash
uv sync
source .venv/bin/activate         # Windows: .venv\Scripts\activate
flask run -p 3000
python example.py
```

## Building and publishing packages

Source: https://docs.astral.sh/uv/guides/package/

### Prepare: build system

- Without a `[build-system]` table in `pyproject.toml`, uv does **not** build the project during `uv sync`, and `uv build` falls back to the legacy setuptools build system.
- `uv init` projects include `[build-system]` by default. The docs strongly recommend configuring a build system.

### Build

```bash
uv build                       # current directory -> dist/
uv build <SRC>                 # a specific directory
uv build --package <PACKAGE>   # a specific package in the current workspace
uv build --no-sources          # recommended check before publishing
```

- Output is a source distribution and a wheel, e.g. `dist/hello_world-0.1.0-py3-none-any.whl` and `dist/hello_world-0.1.0.tar.gz`.
- By default `uv build` respects `tool.uv.sources` when resolving `build-system.requires`. Before publishing, run `uv build --no-sources` to make sure the package builds without `tool.uv.sources`, as with other build tools like `pypa/build`.

### Bump the version: `uv version`

```bash
uv version 1.0.0                         # set exact: hello-world 0.7.0 => 1.0.0
uv version 2.0.0 --dry-run               # preview, pyproject.toml unchanged
uv version --bump minor                  # 1.2.3 => 1.3.0
uv version --bump patch --bump dev=66463664   # 0.0.1 => 0.0.2.dev66463664
uv version --bump patch --bump beta      # 1.3.0 => 1.3.1b1  (stable -> pre-release)
uv version --bump major --bump alpha     # 1.3.0 => 2.0.0a1
uv version --bump beta                   # 1.3.0b1 => 1.3.0b2 (pre-release -> next pre-release)
uv version --bump stable                 # 1.3.1b2 => 1.3.1  (clear pre-release)
```

- `--bump` components: `major`, `minor`, `patch`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev`. When given several times they apply from largest (`major`) to smallest (`dev`).
- `--bump <component>=<value>` sets the resulting component explicitly.
- Stable to pre-release: bump `major`/`minor`/`patch` **plus** the pre-release component.
- By default, modifying the version triggers a lock and sync. `--frozen` prevents both; `--no-sync` prevents only the sync.

### Publish

```bash
uv publish
```

Credentials:

- Token: `--token` or `UV_PUBLISH_TOKEN`.
- Username / password: `--username` / `UV_PUBLISH_USERNAME`, `--password` / `UV_PUBLISH_PASSWORD`.
- PyPI no longer supports username and password; generate a token. A token is equivalent to `--username __token__` with the token as the password.
- **Trusted publishing** (GitHub Actions or another Trusted Publisher to PyPI): no credentials needed; add a trusted publisher to the PyPI project instead. A full GitHub Actions to PyPI guide is at https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi.
- With trusted publishing, uv tries to invalidate the short-lived PyPI token after publishing, even if publishing fails. If invalidation fails, uv only warns; the publish result is unchanged. Tokens passed via `--token` / `UV_PUBLISH_TOKEN` are not revoked.

Custom index (e.g. TestPyPI): add `publish-url` to the index and publish with `--index <name>`:

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

```bash
uv publish --index testpypi
```

- `uv publish --index <name>` requires `pyproject.toml` to be present, so a CI publish job needs a checkout step.

Partial failures and retries:

- `uv publish` retries failed uploads, but a publish can still stop halfway with some files uploaded.
- PyPI: rerun the exact same command; existing identical files are ignored.
- Other registries: pass `--check-url <index url>` (the index URL, **not** the publish URL). With `--index`, the index URL is used as the check URL automatically. uv then skips files identical to ones in the registry and handles raced parallel uploads.
- Existing files must match exactly, which prevents publishing an sdist and wheels with different contents for the same version.

### Attestations

- `uv publish` uploads PEP 740 attestations to registries that support them, like PyPI. It discovers and matches them automatically, e.g. `hello_world-1.0.0-py3-none-any.whl.publish.attestation` next to the wheel.
- `uv publish` does **not** generate attestations; create them separately before publishing.
- Some third-party indexes reject uploads with attestations instead of ignoring them. Disable with `--no-attestations` or `UV_PUBLISH_NO_ATTESTATIONS`.

### Verify the published package

```bash
uv run --with <PACKAGE> --no-project -- python -c "import <PACKAGE>"
```

- `--no-project` avoids installing the package from your local project directory.
- If you recently installed the package, add `--refresh-package <PACKAGE>` to avoid a cached version.
