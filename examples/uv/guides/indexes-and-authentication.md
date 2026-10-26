# Package indexes and authentication

Source pages: https://docs.astral.sh/uv/concepts/indexes/, https://docs.astral.sh/uv/concepts/authentication/, https://docs.astral.sh/uv/concepts/preview/, https://docs.astral.sh/uv/concepts/cache/

uv uses PyPI by default. Add other indexes, including private ones, with `[[tool.uv.index]]` in config or `--index` on the CLI.

## Defining indexes

```toml
[[tool.uv.index]]
name = "pytorch"                               # optional
url = "https://download.pytorch.org/whl/cpu"   # required
```

- **Priority = definition order.** The first listed index is consulted first. CLI-provided indexes come before config-file ones.
- PyPI is the implicit **default** index, used when a package isn't on any other index. Replace it with `default = true` on another entry, or `--default-index`.
- **The default index is always lowest priority**, wherever it sits in the list.
- Names may contain only ASCII alphanumerics, `-`, `_` and `.`.
- `--index`/`--default-index` and `UV_INDEX`/`UV_DEFAULT_INDEX` accept a URL, a configured name, or `<name>=<url>`:

```console
$ uv lock --index pytorch=https://download.pytorch.org/whl/cpu
$ UV_INDEX=pytorch=https://download.pytorch.org/whl/cpu uv lock
```

- With `--preview-features index-by-name`, configured names take precedence over matching paths. The preview page describes `index-by-name` as what makes `--index internal` select the configured index named `internal`. (https://docs.astral.sh/uv/concepts/preview/)

## Pinning packages to an index (`tool.uv.sources`)

```toml
[tool.uv.sources]
torch = { index = "pytorch" }

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true      # only used for packages pinned to it
```

- `explicit = true`: nothing installs from that index unless it's pinned via `tool.uv.sources`. Everything else still comes from PyPI or other indexes.
- Pick an index per platform with markers:

```toml
[project]
dependencies = ["torch"]

[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", marker = "sys_platform == 'darwin'"},
  { index = "pytorch-cu130", marker = "sys_platform != 'darwin'"},
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
```

- **Named indexes used in `tool.uv.sources` must be defined in the project's `pyproject.toml`.** Indexes from the CLI, env vars or user-level config aren't recognized there.
- `default = true` + `explicit = true`: the index is explicit-only (usable only via sources), *and* PyPI is removed as the default.

## Index strategy: why `first-index` is the default

By default uv stops at the **first index that has the package** and only considers versions from that index. If an internal index has a package, it always comes from there and never from PyPI. This prevents **dependency confusion** attacks, where an attacker publishes a same-named malicious package on PyPI (e.g. the December 2022 `torchtriton` attack).

`--index-strategy` / `UV_INDEX_STRATEGY`:

- `first-index` (default): search all indexes, but limit candidates to the first index containing the package.
- `unsafe-first-match`: search all indexes; prefer the first index with a *compatible* version, even if other indexes have newer ones.
- `unsafe-best-match`: pick the best version from the combined candidates across all indexes. **Closest to pip, but exposed to dependency confusion.**

## pip-style `--index-url` / `--extra-index-url`

Supported for compatibility and usable alongside `[[tool.uv.index]]`, with the same priority rules:

- `--index-url` = an unnamed entry with `default = true` (maps to `--default-index`). Always lowest priority.
- `--extra-index-url` = an unnamed entry (maps to `--index`). Consulted in definition order along with `--index` and `[[tool.uv.index]]`.

## Flat indexes (`--find-links` style)

Entries are assumed to be PEP 503 Simple API registries. For a local directory or HTML page with a flat list of wheels/sdists:

```toml
[[tool.uv.index]]
name = "example"
url = "/path/to/directory"
format = "flat"
```

Same feature set as Simple API indexes (`explicit = true`, pinning via `tool.uv.sources`). Caching caveat: uv treats flat index contents as immutable and caches each file by name, so if you rebuild a wheel under the same filename it isn't picked up until you refresh. (https://docs.astral.sh/uv/concepts/cache/)

## Credentials

Provider-specific guides exist for Azure Artifacts, Google Artifact Registry, AWS CodeArtifact and JFrog Artifactory.

**Environment variables (keeps secrets out of `pyproject.toml`):** define the index without credentials, then set `UV_INDEX_<NAME>_USERNAME` / `UV_INDEX_<NAME>_PASSWORD`, where `<NAME>` is the index name uppercased with non-alphanumerics turned into `_`:

```toml
[[tool.uv.index]]
name = "internal-proxy"
url = "https://example.com/simple"
```

```console
export UV_INDEX_INTERNAL_PROXY_USERNAME=public
export UV_INDEX_INTERNAL_PROXY_PASSWORD=koala
```

**Embedded in the URL:** `url = "https://public:koala@pypi-proxy.corp.dev/simple"`.

- **Credentials are never written to `uv.lock`**, so uv needs the authenticated URL at install time too.

### Credential providers and the `authenticate` setting

- uv also finds credentials via netrc and keyring (details are on the HTTP authentication page).
- Default flow: try an unauthenticated request first; on failure, look up credentials and retry authenticated. If a username is set, uv looks up credentials *before* the first request.
- Some indexes (e.g. GitLab) forward unauthenticated requests to PyPI, so uv never looks for credentials. Fix it per index:

```toml
[[tool.uv.index]]
name = "example"
url = "https://example.com/simple"
authenticate = "always"   # search eagerly; error if none found
```

- `authenticate = "never"`: never search for credentials, and error if credentials are provided directly. Use it to prevent credential leaks.

### Error codes

- Under `first-index`, uv stops searching other indexes on **401 or 403**. The exception is the `pytorch` index, whose 403s are ignored because it returns 403 for missing packages.
- By default an HTTP error fetching metadata or an archive also stops resolution. Ignoring that error marks the package version unavailable so the resolver tries another.
- `ignore-error-codes = [403]` per index (e.g. together with `authenticate = "always"`).
- **404 always continues** to the next index. That can't be overridden.

## Cache-control per index

- uv respects index cache headers. PyPI serves metadata with `max-age=600` (10 minutes) and files with `max-age=365000000, immutable` (cached indefinitely).
- Override with `cache-control = { api = "...", files = "..." }`. `api` covers Simple API metadata; `files` covers wheel/sdist downloads. Values use HTTP Cache-Control syntax, e.g. `api = "no-cache"` to always revalidate.
- Typical use: private indexes that (often unintentionally) disable caching. Recommended values match PyPI: `api = "max-age=600"`, `files = "max-age=365000000, immutable"`.

## Hash algorithm per index (preview `index-hash-algorithm`)

```toml
[tool.uv]
preview-features = ["index-hash-algorithm"]

[[tool.uv.index]]
name = "private-index"
url = "https://private-index.com/simple"
hash-algorithm = "sha256"
```

If a locked distribution doesn't advertise that algorithm, uv fails instead of falling back to another.

## `exclude-newer` per index

```toml
[[tool.uv.index]]
name = "internal"
url = "https://internal.example.com/simple"
exclude-newer = "7 days"   # or false if the index has no upload-time metadata
```

Only affects packages served from that index. `exclude-newer-package` still takes precedence. The preview page lists this as the `index-exclude-newer` preview feature; the indexes page shows no preview gate. (https://docs.astral.sh/uv/concepts/preview/)

## Authentication section map (stub page)

https://docs.astral.sh/uv/concepts/authentication/ is a stub. It says authentication is needed for private repositories or indexes and links to subpages not covered here:

- Using the `uv auth` CLI (`cli/`)
- HTTP authentication (`http/`), which covers netrc, keyring and the uv credentials store
- Git authentication (`git/`)
- TLS certificates (`certificates/`)
- Third-party services (`third-party/`)

Related preview features (https://docs.astral.sh/uv/concepts/preview/):

- `native-auth`: `uv auth` stores credentials in Keychain (macOS), Credential Manager (Windows) or the Secret Service API (Linux), and only reads credentials it stored itself.
- `auth-helper`: `uv auth helper` serves credentials to external tools via the Bazel credential helper protocol (JSON on stdin/stdout).
- `s3-endpoint`, `gcs-endpoint`, `azure-endpoint`: authenticate to S3-compatible storage (AWS SigV4), GCS or Azure Blob endpoints. Set `UV_S3_ENDPOINT_URL`, `UV_GCS_ENDPOINT_URL` or `UV_AZURE_ENDPOINT_URL` respectively.
