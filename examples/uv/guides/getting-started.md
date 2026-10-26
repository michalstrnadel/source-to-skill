# Getting started with uv

Source pages: https://docs.astral.sh/uv/llms.txt, https://docs.astral.sh/uv/getting-started/features/, https://docs.astral.sh/uv/getting-started/first-steps/, https://docs.astral.sh/uv/getting-started/installation/

## What uv is and what it replaces

- uv is an extremely fast Python package and project manager, written in Rust. It installs Python dependencies, runs scripts, manages virtual environments, builds and publishes packages, and installs Python itself.
- It can replace `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv`, and more.
- Two interfaces:
  - **pip-compatible CLI**: prepend `uv` to a pip command, e.g. `uv pip install ruff`.
  - **Project interface** (first-class): e.g. `uv add ruff`, with lockfiles and workspace support.
- Fetching docs: use explicit `index.md` paths for directories (e.g. `https://docs.astral.sh/uv/concepts/projects/dependencies/index.md`) to get clean markdown instead of rendered HTML.

## Feature / command map by area

The areas can be used independently or together (https://docs.astral.sh/uv/getting-started/features/).

### Python versions (installing and managing Python itself)

- `uv python install`: install Python versions.
- `uv python list`: view available Python versions.
- `uv python find`: find an installed Python version.
- `uv python pin`: pin the current project to a specific Python version.
- `uv python uninstall`: uninstall a Python version.

### Scripts (standalone files, e.g. `example.py`)

- `uv run`: run a script.
- `uv add --script`: add a dependency to a script.
- `uv remove --script`: remove a dependency from a script.

### Projects (anything with a `pyproject.toml`)

- `uv init`: create a new Python project.
- `uv add` / `uv remove`: add / remove a dependency.
- `uv sync`: sync the project's dependencies with the environment.
- `uv lock`: create a lockfile for the project's dependencies.
- `uv run`: run a command in the project environment.
- `uv tree`: view the dependency tree.
- `uv build`: build the project into distribution archives.
- `uv publish`: publish the project to a package index.

### Tools (CLI packages from indexes, e.g. `ruff`, `black`)

- `uvx` / `uv tool run`: run a tool in a temporary environment.
- `uv tool install`: install a tool user-wide.
- `uv tool uninstall`: uninstall a tool.
- `uv tool list`: list installed tools.
- `uv tool update-shell`: update the shell to include tool executables.

### The pip interface (legacy workflows, or when high-level commands lack control)

- Virtual environments (replaces `venv` and `virtualenv`): `uv venv`.
- Package management (replaces `pip` and `pipdeptree`): `uv pip install`, `uv pip show`, `uv pip freeze`, `uv pip check`, `uv pip list`, `uv pip uninstall`, `uv pip tree`.
- Locking (replaces `pip-tools`): `uv pip compile` (requirements to lockfile), `uv pip sync` (sync an environment with a lockfile).
- **Important:** these commands do not exactly implement the interfaces and behavior of the tools they are based on. The further you stray from common workflows, the more likely you hit differences; see the pip-compatibility guide (https://docs.astral.sh/uv/pip/compatibility/).

### Utility (uv's own state)

- `uv cache clean`: remove cache entries.
- `uv cache prune`: remove outdated cache entries and all centralized project environments.
- `uv cache dir`: show the cache directory path.
- `uv tool dir`: show the tool directory path.
- `uv python dir`: show the path of uv-installed Python versions.
- `uv self update`: update uv to the latest version.

## First steps

- Verify the install by running bare `uv`; it prints a help menu (`Usage: uv [OPTIONS] <COMMAND>`) listing available commands.

## Installation methods

Source: https://docs.astral.sh/uv/getting-started/installation/

### Standalone installer (macOS / Linux)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# without curl:
wget -qO- https://astral.sh/uv/install.sh | sh
# pin a specific version by putting it in the URL:
curl -LsSf https://astral.sh/uv/0.13.5/install.sh | sh
```

### Standalone installer (Windows PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# specific version:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.13.5/install.ps1 | iex"
```

- Changing the execution policy (`-ExecutionPolicy ByPass`) is what allows running a script from the internet.
- Inspect the script before running it: `curl -LsSf https://astral.sh/uv/install.sh | less` or `powershell -c "irm https://astral.sh/uv/install.ps1 | more"`.
- Installer customization options are in the installer reference (https://docs.astral.sh/uv/reference/installer/).

### PyPI

```bash
pipx install uv   # recommended: isolated environment
pip install uv    # also works
```

- uv ships prebuilt wheels for many platforms; if no wheel exists for a platform, uv is built from source, which requires a Rust toolchain.

### Package managers and other channels

```bash
brew install uv                    # Homebrew (core packages)
sudo port install uv               # MacPorts
winget install --id=astral-sh.uv -e   # WinGet
scoop install main/uv              # Scoop
cargo install --locked uv          # crates.io; builds from source, needs a compatible Rust toolchain
```

- **Docker**: image at `ghcr.io/astral-sh/uv` (see the Docker integration guide).
- **GitHub Releases**: https://github.com/astral-sh/uv/releases has binaries for all supported platforms, plus instructions for using the standalone installer via `github.com` instead of `astral.sh`.

## Upgrading uv

- Standalone installer installs can self-update:

  ```bash
  uv self update
  ```

- `uv self update` re-runs the installer and can modify shell profiles; set `UV_NO_MODIFY_PATH=1` to prevent that.
- Any other install method: self-updates are disabled; use that package manager's upgrade, e.g. `pip install --upgrade uv`.

## Shell autocompletion

Determine your shell with `echo $SHELL`. Then restart the shell or source the config file.

uv:

```bash
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
echo 'uv generate-shell-completion fish | source' > ~/.config/fish/completions/uv.fish
echo 'eval (uv generate-shell-completion elvish | slurp)' >> ~/.elvish/rc.elv
```

uvx (note the flag form `--generate-shell-completion`):

```bash
echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc
echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
echo 'uvx --generate-shell-completion fish | source' > ~/.config/fish/completions/uvx.fish
echo 'eval (uvx --generate-shell-completion elvish | slurp)' >> ~/.elvish/rc.elv
```

PowerShell:

```powershell
if (!(Test-Path -Path $PROFILE)) {
  New-Item -ItemType File -Path $PROFILE -Force
}
Add-Content -Path $PROFILE -Value '(& uv generate-shell-completion powershell) | Out-String | Invoke-Expression'
# for uvx: '(& uvx --generate-shell-completion powershell) | Out-String | Invoke-Expression'
```

## Uninstalling uv

1. Optional: remove stored data first (see the storage reference, https://docs.astral.sh/uv/reference/storage/, for locations):

   ```bash
   uv cache clean
   rm -r "$(uv python dir)"
   rm -r "$(uv tool dir)"
   ```

2. Remove the `uv`, `uvx`, and `uvw` binaries (the Unix example removes `uv` and `uvx`; the Windows example also removes `uvw.exe`):

   ```bash
   rm ~/.local/bin/uv ~/.local/bin/uvx
   ```

   ```powershell
   rm $HOME\.local\bin\uv.exe
   rm $HOME\.local\bin\uvx.exe
   rm $HOME\.local\bin\uvw.exe
   ```

- Before 0.5.0, uv was installed into `~/.cargo/bin`. Remove binaries from there; upgrading from an older version does not automatically remove them.
