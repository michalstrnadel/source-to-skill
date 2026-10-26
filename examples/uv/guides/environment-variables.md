# Environment variables

Source pages: https://docs.astral.sh/uv/reference/environment/

Every variable on the reference page. Grouping is by area; the page itself lists them alphabetically. Most `UV_*` variables are documented as "Equivalent to the `--flag` command-line argument". **Deprecated** marks variables the page labels deprecated.

General notes:

- "Uses space-separated list of files": `UV_CONSTRAINT`, `UV_OVERRIDE`, `UV_EXCLUDE`, `UV_BUILD_CONSTRAINT`.
- `UV_INDEX` and `UV_EXTRA_INDEX_URL` are space-separated lists. `UV_FIND_LINKS` is comma-separated.
- Per-package lists (`UV_NO_BINARY_PACKAGE`, `UV_NO_BUILD_PACKAGE`, `UV_NO_SOURCES_PACKAGE`, `UV_NO_GROUP`) are space-delimited.
- Boolean ones are documented as "set to `true`" (`UV_SYSTEM_PYTHON`, `UV_BREAK_SYSTEM_PACKAGES`, `UV_REQUIRE_HASHES`, `UV_SYSTEM_CERTS`) or a true value like `1` (`UV_LEGACY_TAR_BACKEND`, `UV_MALWARE_CHECK`).

```bash
# Typical CI setup
export UV_SYSTEM_PYTHON=true        # use first python on PATH (CI/containers only)
export UV_LOCKED=1                  # assert uv.lock is unchanged
export UV_COMPILE_BYTECODE=1
export UV_NO_PROGRESS=1
export UV_HTTP_TIMEOUT=60           # default 30 s
export UV_INDEX_FOO_USERNAME=user UV_INDEX_FOO_PASSWORD=secret   # creds for index named "foo"
```

## Configuration files and discovery

- `UV_CONFIG_FILE`: `--config-file`, the path to a local `uv.toml` to use.
- `UV_NO_CONFIG`: `--no-config`, reads no config files from the current directory, parents or user config dirs.
- `UV_NO_SYSTEM_CONFIG`: skips system-level config files.
- `UV_ISOLATED`: `--isolated`, avoids discovering a `pyproject.toml` or `uv.toml`.
- `UV_PROJECT`: `--project`. `UV_NO_PROJECT`: `--no-project`.
- `UV_WORKING_DIR`: `--directory`. `UV_WORKING_DIRECTORY` (added v0.9.1) is still supported for backwards compatibility.
- `UV_PROJECT_ENVIRONMENT`: path to the project's virtual environment directory (see https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path).

## Lockfile, sync and dependency selection

- `UV_LOCKED`: `--locked`, asserts that `uv.lock` stays unchanged.
- `UV_FROZEN`: `--frozen`, runs without updating `uv.lock`.
- `UV_NO_SYNC`: `--no-sync`, skips updating the environment.
- `UV_DEV` / `UV_NO_DEV`: `--dev` / `--no-dev`, includes or excludes dev dependencies.
- `UV_NO_DEFAULT_GROUPS`: `--no-default-groups`, ignores `tool.uv.default-groups`.
- `UV_NO_GROUP`: `--no-group`, disables the listed groups.
- `UV_NO_EDITABLE`: `--no-editable`, installs or exports editables (project and workspace members included) as non-editable.
- `UV_NO_INSTALL_PROJECT`: `--no-install-project`, installs the deps but not the project.
- `UV_NO_INSTALL_WORKSPACE`: `--no-install-workspace`, installs no workspace members, including the current project.
- `UV_NO_INSTALL_LOCAL`: `--no-install-local`, skips the project, members and any local path/editable packages, installing only remote deps.
- `UV_NO_SOURCES`: `--no-sources`, ignores `[tool.uv.sources]`. `UV_NO_SOURCES_PACKAGE`: `--no-sources-package`, the same for listed packages.
- `UV_ENV_FILE`: `.env` files to load for `uv run`. `UV_NO_ENV_FILE`: ignores `.env` files in `uv run`.
- `UV_RUN_RLIMIT_NOFILE`: soft open-file limit for commands run by `uv run`.
  - Applied right before the command is spawned; the hard limit is unchanged.
  - If it can't be applied, uv exits with an error. Unix only.
- `UV_INIT_BARE`: `uv init --bare`, creates only a `pyproject.toml`.
- `UV_INIT_BUILD_BACKEND`: `uv init --build-backend`, the default backend for new projects.

## Resolution inputs and strategy

- `UV_CONSTRAINT` (`--constraints`), `UV_OVERRIDE` (`--overrides`), `UV_EXCLUDE` (`--excludes`), `UV_BUILD_CONSTRAINT` (`--build-constraints`, for sdist builds): files, space-separated.
- `UV_RESOLUTION`: `--resolution`, e.g. `lowest-direct`.
- `UV_PRERELEASE`: `--prerelease`, e.g. `allow`.
- `UV_FORK_STRATEGY`: `--fork-strategy`, version selection during universal resolution.
- `UV_EXCLUDE_NEWER`: `--exclude-newer`, excludes distributions published after a date. `false` disables it.
- `UV_TORCH_BACKEND`: `--torch-backend`, e.g. `cpu`, `cu126`, `auto`.
- `UV_CUSTOM_COMPILE_COMMAND`: `--custom-compile-command`, replaces `uv` in the header of `uv pip compile` output (for wrapper scripts).
- `UV_PYTHON_ARCH`: default architecture for Python requests that don't specify one (`x86_64`, `aarch64`). Requests naming an executable take precedence.
- `UV_LIBC`: overrides the detected libc on Linux for the current platform in Python requests: `gnu`, `gnueabi`, `gnueabihf`, `musl`, `musleabi`, `musleabihf`, `none`.

## Indexes, sources and authentication

- `UV_DEFAULT_INDEX`: `--default-index`.
- `UV_INDEX`: `--index`, additional indexes (space-separated).
- `UV_INDEX_URL`: `--index-url`. **Deprecated**: use `UV_DEFAULT_INDEX`.
- `UV_EXTRA_INDEX_URL`: `--extra-index-url`. **Deprecated**: use `UV_INDEX`.
- `UV_INDEX_STRATEGY`: `--index-strategy`. `unsafe-best-match` considers versions across all indexes instead of stopping at the first index that has the package.
- `UV_FIND_LINKS`: `--find-links` (comma-separated).
- `UV_INDEX_{name}_USERNAME` / `UV_INDEX_{name}_PASSWORD`: HTTP Basic credentials for a named index. For index `foo` they are `UV_INDEX_FOO_USERNAME` and `UV_INDEX_FOO_PASSWORD`.
- `UV_KEYRING_PROVIDER`: `--keyring-provider`.
- `UV_CREDENTIALS_DIR`: credential storage directory for the plain-text backend.
- `UV_INSECURE_HOST`: `--allow-insecure-host`.
- `UV_NO_HF_TOKEN`: disables Hugging Face auth even when `HF_TOKEN` is set.
- `UV_GIT_LFS`: fetches Git LFS files when installing from Git.
- `UV_NO_GITHUB_FAST_PATH`: disables the GitHub-specific requests that let uv skip `git fetch`.
- Cloud storage endpoints (requests are signed):
  - `UV_S3_ENDPOINT_URL`: S3-compatible, AWS SigV4, using `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE`, `AWS_CONFIG_FILE`.
  - `UV_GCS_ENDPOINT_URL`: GCS-compatible, using `GOOGLE_APPLICATION_CREDENTIALS` or Application Default Credentials.
  - `UV_AZURE_ENDPOINT_URL`: Azure Blob, using the default credential chain (Azure CLI, workload identity).

## Network, TLS, timeouts and retries

- `UV_OFFLINE`: `--offline`, disables network access.
- `UV_HTTP_TIMEOUT`: HTTP read timeout in seconds, **default 30 s**. `UV_REQUEST_TIMEOUT` and the external `HTTP_TIMEOUT` are equivalent.
- `UV_HTTP_CONNECT_TIMEOUT`: connect timeout, **default 10 s**. If `UV_HTTP_TIMEOUT` is lower, that value is used.
- `UV_UPLOAD_HTTP_TIMEOUT`: upload-only timeout, **default 900 s**.
- `UV_HTTP_RETRIES`: retry count, **default 3**.
- `UV_SYSTEM_CERTS`: `--system-certs`. `true` loads the platform's native cert store instead of the bundled Mozilla roots.
- `UV_NATIVE_TLS`: `--native-tls`. **Deprecated**: use `UV_SYSTEM_CERTS`.
- `UV_INSECURE_NO_ZIP_VALIDATION`: disables ZIP validation for streamed wheels and ZIP sdists. Security risk: a rejected ZIP is likely malformed, so report it to the maintainer instead.
- `UV_SKIP_WHEEL_FILENAME_CHECK`: skips checking that a wheel's filename matches its contents. Not recommended; a workaround for rare invalid artifacts.

## Concurrency and locking

- `UV_CONCURRENT_DOWNLOADS`: maximum in-flight downloads.
- `UV_CONCURRENT_BUILDS`: maximum concurrent sdist builds.
- `UV_CONCURRENT_INSTALLS`: install/unzip threads.
- `UV_CONCURRENT_CACHE_READS`: threads that read cached HTTP responses.
- `UV_LOCK_TIMEOUT`: seconds to wait for a file lock, **default 300 s (5 min)**.

## Cache

- `UV_CACHE_DIR`: `--cache-dir`.
- `UV_NO_CACHE`: `--no-cache`, uses no cache for any operation.

## Build and install behavior

- `UV_NO_BUILD`: `--no-build`, never builds sdists; first-party/workspace packages are still built. `UV_NO_BUILD_PACKAGE`: `--no-build-package`, the same per package.
- `UV_NO_BINARY`: `--no-binary`, installs everything from source; wheels are still used for metadata. `UV_NO_BINARY_PACKAGE`: `--no-binary-package`, the same per package.
- `UV_NO_BUILD_ISOLATION`: `--no-build-isolation`.
- `UV_HIDE_BUILD_OUTPUT`: suppresses build-backend output, even when a build fails.
- `UV_COMPILE_BYTECODE`: `--compile-bytecode`. `UV_COMPILE_BYTECODE_TIMEOUT`: compile timeout in seconds.
- `UV_LINK_MODE`: `--link-mode`.
- `UV_REQUIRE_HASHES`: `--require-hashes`. `true` requires a hash for every requirement.
- `UV_NO_VERIFY_HASHES`: `--no-verify-hashes`, disables hash verification for `requirements.txt`.
- `UV_REQUIRE_BUILD_HASHES`: requires hashes for build deps across project, build, tool and pip commands.
- `UV_NO_INSTALLER_METADATA`: doesn't write `INSTALLER`, `REQUESTED` or `direct_url.json` into `.dist-info`.
- `UV_LEGACY_TAR_BACKEND`: uses the legacy tar reader/writer (set to e.g. `1`).
- `UV_BREAK_SYSTEM_PACKAGES`: `--break-system-packages`. `true` allows conflicts with system packages. CI/containers only.
- `UV_SYSTEM_PYTHON`: `--system`. `true` uses the first Python on `PATH`. CI/containers only.
- `UV_MALWARE_CHECK`: `1` enables a post-`uv sync` OSV malware check after every lockfile sync. `0` opts out.
- `UV_MALWARE_CHECK_URL`: service URL, default `https://api.osv.dev/`.

## Virtual environments (`uv venv`)

- `UV_VENV_CLEAR`: `--clear`, removes existing files at the target.
- `UV_VENV_RELOCATABLE`: `--relocatable`.
- `UV_VENV_SEED`: installs seed packages (`pip`, `setuptools`, `wheel`). `setuptools` and `wheel` are not included in Python 3.12+ environments.

## Python discovery and managed installs

- `UV_PYTHON`: `--python`. A path makes uv use that interpreter for all operations.
- `UV_MANAGED_PYTHON`: requires uv-managed Pythons. `UV_NO_MANAGED_PYTHON`: disables them.
- `UV_PYTHON_PREFERENCE`: prefer system or managed Pythons.
- `UV_PYTHON_DOWNLOADS`: the `python-downloads` setting; when disabled, the same as `--no-python-downloads`.
- `UV_PYTHON_SEARCH_PATH`: directories searched for interpreters instead of `PATH`.
- `UV_PYTHON_INSTALL_DIR`: where managed Pythons are stored.
- `UV_PYTHON_BIN_DIR`: where links to managed Python executables go. `UV_PYTHON_INSTALL_BIN`: whether to install the executable there.
- `UV_PYTHON_CACHE_DIR`: cache for downloaded Python archives.
- Windows registry:
  - `UV_PYTHON_INSTALL_REGISTRY`: registers the Python in the Windows registry.
  - `UV_PYTHON_NO_REGISTRY`: no discovery from the registry or Microsoft Store, and no registration.
- Mirrors (each replaces a base URL; `file://` reads a local dir):
  - `UV_PYTHON_INSTALL_MIRROR`: replaces `https://github.com/astral-sh/python-build-standalone/releases/download`. Beats `UV_ASTRAL_MIRROR_URL` for CPython.
  - `UV_PYPY_INSTALL_MIRROR`: replaces `https://downloads.python.org/pypy`.
  - `UV_GRAALPY_INSTALL_MIRROR`: replaces `https://github.com/oracle/graalpython/releases/download`.
  - `UV_PYODIDE_INSTALL_MIRROR`: replaces `https://github.com/pyodide/pyodide/releases/download`.
- `UV_PYTHON_DOWNLOADS_JSON_URL`: a local path or URL to a JSON list that overrides the list of Python installations hardcoded in the binary (custom URLs, older or newer versions).
- Build pins:
  - `UV_PYTHON_CPYTHON_BUILD`: build date, e.g. `20250814`.
  - `UV_PYTHON_PYPY_BUILD`: e.g. `7.3.20`.
  - `UV_PYTHON_GRAALPY_BUILD`: e.g. `24.2.2`.
  - `UV_PYTHON_PYODIDE_BUILD`: e.g. `0.28.1`.

## Tools

- `UV_TOOL_DIR`: where managed tools are stored.
- `UV_TOOL_BIN_DIR`: the "bin" directory for tool executables.

## Publishing (`uv publish`)

- `UV_PUBLISH_URL`: `--publish-url`, the upload endpoint.
- `UV_PUBLISH_INDEX`: `--index`, the name of a configured index to publish to.
- `UV_PUBLISH_TOKEN`: `--token`, sent with username `__token__`.
- `UV_PUBLISH_USERNAME` / `UV_PUBLISH_PASSWORD`: `--username` / `--password`.
- `UV_PUBLISH_CHECK_URL`: `--check-url`, the index URL; files that already exist there are skipped.
- `UV_PUBLISH_NO_ATTESTATIONS`: `--no-attestations`, doesn't upload attestations.

## Installing and updating uv itself

- `UV_INSTALL_DIR`: install dir for the standalone installer and `self update`, default `~/.local/bin`.
- `UV_NO_MODIFY_PATH`: doesn't modify `PATH`. The alias `INSTALLER_NO_MODIFY_PATH` is kept for backwards compatibility.
- `UV_UNMANAGED_INSTALL`: for ephemeral environments like CI; installs to a specific path without touching shell profiles or env vars.
- `UV_DOWNLOAD_URL`: download URL for the standalone installer, default GitHub Releases. The alias `INSTALLER_DOWNLOAD_URL` is kept.
- `UV_INSTALLER_GITHUB_BASE_URL` / `UV_INSTALLER_GHE_BASE_URL`: GitHub or GitHub Enterprise base URL for the installer and `self update`. Both beat `UV_ASTRAL_MIRROR_URL` for `self update`.
- `UV_GITHUB_TOKEN`: `--token` for `self update`.
- `UV_ASTRAL_MIRROR_URL`: replaces `https://releases.astral.sh` for all Astral-mirrored metadata and artifacts, e.g. an Artifactory or Nexus proxy.
  - There is no fallback to GitHub once set.
  - Path components are kept; only trailing slashes are trimmed.
  - More specific settings win: `UV_PYTHON_INSTALL_MIRROR` / `python-install-mirror` for CPython, and the installer URLs for `self update`.

## Output, logging, preview, misc

- `UV_NO_PROGRESS`: `--no-progress`, no spinners or progress bars.
- `UV_NO_WRAP`: disables line wrapping of diagnostics.
- `UV_LOG_CONTEXT`: adds context and structure to log messages. No effect unless logging is enabled (`RUST_LOG` or `-v`).
- `UV_PREVIEW`: `--preview`. `UV_PREVIEW_FEATURES`: `--preview-features`, enables specific features.
- `UV_STACK_SIZE`: stack size in bytes. With it and `RUST_MIN_STACK` unset, uv uses 4 MB (4194304). It takes precedence over `RUST_MIN_STACK`, and uv's main2 thread gets `max(UV_STACK_SIZE, 1MB)`.

## Externally defined variables uv reads

- Proxies:
  - `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` (all requests).
  - `NO_PROXY`: comma-separated hostnames (`example.com`) and/or patterns (`192.168.1.0/24`) that bypass the proxy.
- TLS:
  - `SSL_CERT_FILE`: a PEM bundle (no DER). It **replaces** the default source (bundled Mozilla or system certs); only its certs are trusted.
  - `SSL_CERT_DIR`: a directory of PEM certs. Multiple entries use `:` on Unix and `;` on Windows. Any regular file is tried and unparseable files are ignored. It also replaces the default source.
  - `SSL_CLIENT_CERT`: a single PEM file with certificate and private key, for mTLS.
- Auth:
  - `NETRC`: location of the `.netrc` file.
  - `HF_TOKEN`: token for `huggingface.co` and its subdomains.
  - `PYX_API_KEY` (`sk-pyx-...`), `PYX_AUTH_TOKEN` (as output by `uv auth token`).
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`, `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE`, `AWS_REGION`, `AWS_DEFAULT_REGION` (used if `AWS_REGION` is unset): for signing S3 requests.
- CI detection:
  - `GITHUB_ACTIONS`, `GITLAB_CI`: when `true`, `uv publish` may attempt trusted publishing.
  - `DEPENDABOT`: detects Dependabot.
- Environments:
  - `VIRTUAL_ENV`: detects an active venv.
  - `VIRTUAL_ENV_DISABLE_PROMPT=1`: no venv name in the prompt.
  - `CONDA_PREFIX`, `CONDA_DEFAULT_ENV`, `_CONDA_ROOT`: Conda detection.
  - `JPY_SESSION_NAME`: Jupyter detection.
  - `PYTHONPATH`: adds to the module search path.
- Directories:
  - `XDG_CACHE_HOME`: the cache on Unix.
  - `XDG_CONFIG_HOME`: user config on Unix. `XDG_CONFIG_DIRS`: system config on Unix.
  - `XDG_DATA_HOME`: managed Pythons and tools.
  - `XDG_BIN_HOME`: executables.
  - `HOME`, `PATH`, `PWD`, `SHELL`, `PAGER` (pager choice).
  - Windows: `APPDATA` (user config), `SYSTEMDRIVE` (system config), `USERPROFILE`, `LOCALAPPDATA` (Microsoft Store Pythons).
- Shell detection: `BASH_VERSION`, `ZSH_VERSION`, `ZDOTDIR` (which `.zshenv`), `FISH_VERSION`, `KSH_VERSION`, `NU_VERSION`, `PSModulePath` (PowerShell), `PROMPT` (cmd.exe vs PowerShell).
- Color and terminal:
  - `NO_COLOR` disables color and takes precedence over `FORCE_COLOR`.
  - `FORCE_COLOR` forces color.
  - `CLICOLOR_FORCE` controls color via `anstyle`.
  - `COLUMNS`: terminal width; not read by uv directly.
- Cross-platform targets (with `--python-platform`):
  - `MACOSX_DEPLOYMENT_TARGET`: default `13.0`.
  - `IPHONEOS_DEPLOYMENT_TARGET`: default `13.0`.
  - `ANDROID_API_LEVEL`: default `24`.
- Debugging:
  - `RUST_LOG`: e.g. `uv=debug` is the same as `--verbose`, and `trace` gives trace-level logging.
  - `RUST_BACKTRACE`: `1` for a short backtrace, `full` for a full one.
  - `RUST_MIN_STACK`: prefer `UV_STACK_SIZE`, because this one also affects subprocesses such as Rust build backends.
  - `TRACING_DURATIONS_FILE`.
- Tool binaries:
  - `RUFF`: the Ruff binary for `uv format`.
  - `TY`: the ty binary for `uv check`.
- Other:
  - `UV`: path of the invoking uv binary, propagated to all subprocesses. It may be the symlink or its target, depending on the platform.
  - `PYC_INVALIDATION_MODE`: the mode used with `--compile`.
  - `HTTP_TIMEOUT`: same as `UV_HTTP_TIMEOUT`.
