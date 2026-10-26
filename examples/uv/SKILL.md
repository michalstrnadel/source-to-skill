---
name: uv
description: Working reference for uv (Astral), the Rust-based Python package and project manager that replaces pip, pip-tools, pipx, poetry, pyenv, twine and virtualenv, distilled from the official docs (docs.astral.sh/uv, 56 pages via llms.txt). Covers installing uv, projects (uv init/add/lock/sync/run, uv.lock, workspaces, dependency groups, sources), scripts with inline metadata, tools (uvx, uv tool install), managed Python versions, resolution (universal lockfile, overrides, constraints, exclude-newer), package indexes and authentication, caching, configuration files, the uv_build backend, building and publishing, the uv pip interface, Docker/GitHub Actions/GitLab/PyTorch/Jupyter integrations, and the full CLI, settings and environment-variable references. Load it when setting up or debugging a uv project, migrating from pip/poetry, writing a Dockerfile or CI job with uv, configuring private indexes, or looking up a uv flag, setting or UV_* variable.
---

# uv

Source: the uv documentation, https://docs.astral.sh/uv/ (extracted from
https://docs.astral.sh/uv/llms.txt: 56 pages in 7 sections). uv is "an
extremely fast Python package and project manager, written in Rust". It
installs dependencies, runs scripts, manages virtual environments, builds and
publishes packages, and installs Python itself. Docs snapshot: October 2026
(the docs pin `uv_build>=0.13.5,<0.14` in examples).

## Two interfaces

- **Project interface** (first-class): `uv init`, `uv add`, `uv remove`,
  `uv lock`, `uv sync`, `uv run`, `uv tree`, `uv build`, `uv publish`.
  It uses `pyproject.toml`, a universal `uv.lock` and `.venv`.
- **pip interface** (`uv pip install|compile|sync|...`, `uv venv`) is meant
  for legacy workflows or when you need low-level control. It does **not**
  exactly reproduce pip/pip-tools behavior. → [guides/pip-interface.md](guides/pip-interface.md)
- Also: scripts (`uv run script.py`, `uv add --script`), tools (`uvx`,
  `uv tool install`), Python (`uv python install|list|find|pin|upgrade`),
  utilities (`uv cache clean|prune|dir`, `uv self update`).

## Install and start

```
curl -LsSf https://astral.sh/uv/install.sh | sh     # standalone installer (macOS/Linux)
uv self update                                      # only for standalone-installer installs
uv init hello-world && cd hello-world
uv add requests                                     # writes pyproject.toml, locks, syncs
uv run main.py                                      # locks + syncs, then runs
```

pip/pipx, Homebrew, Docker images and more are in
[guides/getting-started.md](guides/getting-started.md).

## Core mental model

- **Lock and sync are automatic.** `uv run` checks that `uv.lock` matches
  `pyproject.toml` and that `.venv` matches the lock before every run.
  `uv sync` is *exact* (removes extraneous packages; `--inexact` keeps
  them). `uv run` is *inexact* (`--exact` to opt in). → [projects](guides/projects.md)
- **New releases never make `uv.lock` stale.** Upgrades are explicit:
  `uv lock --upgrade` or `uv lock --upgrade-package <pkg>[==<ver>]`. Locked
  versions are preferred until constraints exclude them.
- **`uv.lock` is universal.** It covers every platform and Python version in
  `requires-python`. Commit it, never edit it by hand. Its format is uv-only;
  export with `uv export --format requirements.txt|pylock.toml|cyclonedx1.5`.
- **`[build-system]` decides whether the project itself is installed.** Without
  one only its dependencies are installed. `uv init` (an app by default) now
  defines a `uv_build` build system and a `src/` layout. `--no-package` or
  `--bare` skip it, and `tool.uv.package = true|false` overrides it.
- **Dependency groups:** the `dev` group is synced by default and extras are
  not. Use `--extra foo` or `--all-extras`, and `--no-dev`, `--only-dev` or
  `--group/--only-group/--no-group`. Exclusions beat inclusions.
  Change the defaults with `default-groups`. → [dependencies](guides/dependencies.md)
- **`tool.uv.sources` (git, path, url, index, workspace) is uv-only.** Run
  `uv build --no-sources` before publishing to check the package builds
  without them.
- **Never `uv pip install` into a project's `.venv`.** Use `uv add`, or
  `uv run --with pkg` / `uvx` for one-off needs.

## Decision rules

- **`--locked` vs `--frozen`:** `--locked` errors if `uv.lock` is out of date
  (use it in CI; same as `uv lock --check`). `--frozen` uses the lock as-is
  without checking it. `--no-sync` skips checking the environment.
- **`uvx` vs `uv tool install`:** prefer `uvx` (a temporary environment,
  cached). Install a tool when other programs need it, when it goes into a
  Docker image, or when you use it constantly. Tools that need your project
  installed (pytest, mypy) belong in `uv run`. → [scripts-and-tools](guides/scripts-and-tools.md)
- **Scripts:** inline metadata (PEP 723) makes `uv run` ignore the project's
  dependencies. Scripts are locked only with `uv lock --script`. Add
  `exclude-newer` in the script's `[tool.uv]` for reproducibility.
- **Multiple indexes:** the default `first-index` strategy uses only the
  first index that has the package. This prevents dependency confusion
  (the torchtriton attack). `unsafe-best-match` is the most pip-like and the
  riskiest. Pin a package to an index with `explicit = true` plus
  `tool.uv.sources`. → [indexes-and-authentication](guides/indexes-and-authentication.md)
- **Constraints vs overrides:** constraints only narrow, while overrides
  replace declared requirements and can widen bad upper bounds. Neither one
  adds a package. Both are read only from the workspace root. → [resolution](guides/resolution.md)
- **Workspaces** share one lockfile and the intersection of members'
  `requires-python`. If members have conflicting requirements or each needs
  its own venv, use path dependencies instead.
- **Python:** missing versions are downloaded automatically. A system Python
  that satisfies the request is used before downloading (`python-preference
  = managed` is the default). Use `--no-managed-python` or
  `python-downloads = "manual"` to control this. → [python-versions](guides/python-versions.md)
- **Cache:** prefer `--refresh` over `--no-cache`, and keep the cache on the
  same filesystem as your venvs. End CI jobs with `uv cache prune --ci`,
  which drops downloaded wheels and keeps wheels built from source.
  → [cache-config-and-build](guides/cache-config-and-build.md)
- **Config precedence:** CLI > env vars > project (`uv.toml` beats
  `pyproject.toml [tool.uv]` in the same directory) > user > system.
  `[tool.uv.pip]` applies only to `uv pip`.
- **Docker:** install dependencies in their own layer with
  `uv sync --frozen --no-install-project` (only `uv.lock` mounted), then
  copy the project and run `uv sync --locked`. Set `UV_COMPILE_BYTECODE=1`
  for production images, and `UV_LINK_MODE=copy` with a cache mount. Add
  `.venv` to `.dockerignore`. → [integrations-ci-and-deploy](guides/integrations-ci-and-deploy.md)

## Doc index

| Area | Covers | Guide | Live docs |
|---|---|---|---|
| Getting started | What uv replaces, command map, all install methods, upgrade, completion, uninstall | [getting-started.md](guides/getting-started.md) | https://docs.astral.sh/uv/getting-started/installation/ |
| Scripts and tools | Inline metadata, `--with`, shebangs, script locks, `uvx`, `uv tool install/upgrade`, tool envs | [scripts-and-tools.md](guides/scripts-and-tools.md) | https://docs.astral.sh/uv/guides/scripts/, https://docs.astral.sh/uv/concepts/tools/ |
| Python and publishing workflows | Installing Python, the projects walkthrough, `uv version --bump`, `uv build`, `uv publish`, trusted publishing | [python-and-publishing-workflows.md](guides/python-and-publishing-workflows.md) | https://docs.astral.sh/uv/guides/package/ |
| Projects | `uv init` templates and build backends, layout, config, `uv run`, lock/sync, export, build, workspaces | [projects.md](guides/projects.md) | https://docs.astral.sh/uv/concepts/projects/sync/ |
| Dependencies | `uv add`, sources (git/path/url/index/workspace), extras, groups, default groups, build deps, editables, markers | [dependencies.md](guides/dependencies.md) | https://docs.astral.sh/uv/concepts/projects/dependencies/ |
| Resolution | Universal vs platform resolution, strategies, pre-releases, forking, overrides, constraints, `exclude-newer`, conflicts | [resolution.md](guides/resolution.md) | https://docs.astral.sh/uv/concepts/resolution/ |
| Python versions | Managed vs system Python, discovery, `.python-version`, preferences, PyPy etc. | [python-versions.md](guides/python-versions.md) | https://docs.astral.sh/uv/concepts/python-versions/ |
| Indexes and auth | `[[tool.uv.index]]`, explicit/default/flat indexes, index strategies, credentials | [indexes-and-authentication.md](guides/indexes-and-authentication.md) | https://docs.astral.sh/uv/concepts/indexes/ |
| Cache, config, build backend | Cache semantics and CI, `cache-keys`, config discovery, `.env`, preview features, `uv_build`, storage dirs | [cache-config-and-build.md](guides/cache-config-and-build.md) | https://docs.astral.sh/uv/concepts/cache/ |
| CI and deploy integrations | Docker, GitHub Actions, GitLab, pre-commit, Dependabot, Renovate, Bazel, AWS Lambda, Coiled, FastAPI | [integrations-ci-and-deploy.md](guides/integrations-ci-and-deploy.md) | https://docs.astral.sh/uv/guides/integration/docker/ |
| Registries and notebooks | CodeArtifact, Azure, Google AR, JFrog, PyTorch accelerator indexes, Jupyter, marimo | [integrations-indexes-and-notebooks.md](guides/integrations-indexes-and-notebooks.md) | https://docs.astral.sh/uv/guides/integration/pytorch/ |
| pip interface | Differences from pip, `uv pip compile/sync`, `uv venv`, environment discovery | [pip-interface.md](guides/pip-interface.md) | https://docs.astral.sh/uv/pip/compatibility/ |
| CLI reference | Full command tree, global and per-command options, installer options | [cli-reference.md](guides/cli-reference.md) | https://docs.astral.sh/uv/reference/cli/ |
| Settings reference | Every `[tool.uv]` / `uv.toml` key with defaults | [settings-reference.md](guides/settings-reference.md) | https://docs.astral.sh/uv/reference/settings/ |
| Environment variables | Every `UV_*` variable and the external variables uv reads | [environment-variables.md](guides/environment-variables.md) | https://docs.astral.sh/uv/reference/environment/ |
| Cheatsheet | Commands, keys and snippets, each with its page | [cheatsheet.md](cheatsheet.md) | |

## Not covered

- The Authentication page is only an index of subpages (CLI, HTTP, Git,
  certificates, third-party), and those subpages are not in llms.txt.
- The per-command option lists in the CLI reference (about 800k characters)
  are condensed. Options shared by many commands are documented once.
