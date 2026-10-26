# Resolution

Source pages: https://docs.astral.sh/uv/concepts/resolution/

Resolution turns a list of requirements into a concrete set of package versions that satisfy them, recursively, including transitive dependencies. Direct dependencies are the ones your project declares; indirect (transitive) ones come from your dependencies.

## Platform-specific vs universal resolution

Markers (e.g. `bar ; python_version < "3.9"`) make dependencies depend on OS, CPU architecture, Python version and implementation. Resolving only for the *current* machine yields a lockfile that only works on that platform, which is why uv also does universal resolution.

- **Platform-specific** (like `pip-tools`): the default for `uv pip compile`. The project interface has no way to do platform-specific resolution.
  - Target another platform/Python: `uv pip compile --python-platform linux --python-version 3.10 requirements.in`.
  - Here `--python-version` is the *exact* version, not a lower bound.
  - `--python-platform` is best-effort; markers like macOS `platform_version` (which includes kernel build time) can't be fully expressed, so complex combos may lose fidelity.
- **Universal**: always used for `uv.lock` (created/modified by `uv lock`, `uv sync`, `uv add`); portable across OS, architecture and Python version. Available in the pip interface with `uv pip compile --universal` (output carries markers).
  - A package may appear multiple times with different versions/URLs for different platforms; markers pick one.
  - Usually more constrained than platform-specific, since all markers must be satisfied.
  - **Every dependency must support the whole `requires-python` range.** With `requires-python = ">=3.8"`, resolution fails if all versions of a dependency need 3.9+. The project's `requires-python` must be a subset of every dependency's.
  - By default uv picks the latest compatible version *per supported Python version* (see forking below).
  - **Upper bounds on dependencies' `requires-python` are ignored**: `>=3.8, <4` is treated as `>=3.8`. Respecting them leads to "formally correct but practically incorrect" resolutions (backtracking to old releases that lacked the bound).

## Limiting environments: `environments`

By default the universal resolver solves for all platforms and Python versions. To *reduce* that set, use PEP 508 markers:

```toml
[tool.uv]
environments = [
    "sys_platform == 'darwin'",
    "sys_platform == 'linux'",
]
```

```toml
[tool.uv]
environments = ["implementation_name == 'cpython'"]  # skip alternative implementations
```

- Entries must be **disjoint**. `sys_platform == 'darwin'` and `sys_platform == 'linux'` are fine; `sys_platform == 'darwin'` and `python_version >= '3.9'` are not (both can be true).

## Requiring environments: `required-environments`

Installation needs a wheel; without a compatible wheel uv builds from the sdist. Packages that ship wheels but **no sdist** (e.g. PyTorch) are only installable where a wheel exists, which breaks universal resolution on some platform.

- Default: each such package must have at least one wheel compatible with the target Python version.
- `required-environments` *expands* the set uv must support: any package without an sdist must have a wheel for each listed environment, or resolution fails (uv backtracks past latest releases if needed).
- Contrast: `environments = ["sys_platform == 'darwin'"]` means "only solve for macOS"; `required-environments = ["sys_platform == 'darwin'"]` means "wheel-only packages must have a macOS wheel".

```toml
[tool.uv]
required-environments = [
    "sys_platform == 'darwin' and platform_machine == 'x86_64'"   # guarantee Intel macOS
]
```

- Require a macOS release via its Darwin kernel version in `platform_release` (macOS 15 = Darwin 24):

```toml
[tool.uv]
required-environments = [
    "sys_platform == 'darwin' and platform_machine == 'arm64' and platform_release == '24.0.0'"
]
```

- Use `==` to require baseline coverage. A range like `>= '24.0.0'` can be satisfied by a wheel supporting only a newer release. Newer-release wheels are still kept in the lockfile.

### `minimum-libc-version` (preview)

Markers carry no libc info. In preview: enable with `--preview-features minimum-libc-version` or `preview-features = ["minimum-libc-version"]` to drop the warning.

```toml
[tool.uv]
preview-features = ["minimum-libc-version"]
required-environments = [
    "sys_platform == 'linux' and platform_machine == 'x86_64'",
    "sys_platform == 'linux' and platform_machine == 'aarch64'",
]
minimum-libc-version = { glibc = "2.31" }
# both: minimum-libc-version = { glibc = "2.31", musl = "1.2" }
```

- With glibc 2.31: `manylinux_2_17` satisfies, `manylinux_2_34` does not. Both stay in the lockfile and exported hashes, so newer machines can still use the newer wheel.
- Musl wheels are kept but don't satisfy a glibc requirement. Omitting an implementation means "not required", not "excluded".
- Each configured libc needs coverage in `required-environments`. If a required environment lacks a compatible wheel or usable sdist, uv tries another package version.
- Generic Linux wheels (`linux_x86_64`) don't constrain libc and satisfy either implementation.

## Common marker values

| Marker | Linux | macOS | Windows |
| --- | --- | --- | --- |
| `sys_platform` | `'linux'` | `'darwin'` | `'win32'` |
| `platform_system` | `'Linux'` | `'Darwin'` | `'Windows'` |
| `platform_machine` (x86-64) | `'x86_64'` | `'x86_64'` | `'AMD64'` |
| `platform_machine` (ARM64) | `'aarch64'` | `'arm64'` | `'ARM64'` |
| `os_name` | `'posix'` | `'posix'` | `'nt'` |

- On Windows, `sys_platform` is always `'win32'`, even on 64-bit.
- Check your platform: `uvx python -c "import sysconfig; print(sysconfig.get_config_vars())"`.

## Dependency preferences

If an output already exists (`uv.lock` or the `requirements.txt` output file), uv *prefers* the versions listed there; when installing into a venv it prefers already-installed versions. Locked/installed versions only change when an incompatible version is requested or you pass `--upgrade`.

## Resolution strategy: `--resolution`

- Default: latest version of each package. `flask>=2.0.0` resolves to e.g. 3.0.0, so tests never check the declared lower bound.
- `--resolution lowest`: lowest version for all dependencies, direct and transitive.
- `--resolution lowest-direct`: lowest for direct deps, latest for everything else.
- Build dependencies always use the latest versions.

```console
$ uv pip compile --resolution lowest requirements.in -o requirements.txt
# flask>=2.0.0 -> flask==2.0.0, click==7.1.2, werkzeug==2.0.0, ...
```

- **Libraries: run tests in CI separately with `--resolution lowest` or `lowest-direct`** to validate declared lower bounds.

## Pre-releases: `--prerelease`

- `if-necessary` (default): prefer stable; fall back to pre-releases only if every stable candidate satisfying the constraints is rejected.
- `allow`: consider pre-releases for every package without preferring stable first.
- `disallow`: exclude pre-releases entirely.
- `explicit`: pre-releases only for first-party requirements that contain a pre-release identifier (still stable-first); disallowed for all other packages.
- Per-package override: `--prerelease-package foo=allow`, or:

```toml
[tool.uv]
prerelease = "disallow"
prerelease-package = { foo = "allow", bar = "if-necessary" }
```

## Multi-version (forking) resolution: `--fork-strategy`

In universal resolution a package can be locked at several versions/URLs for different platforms or Pythons. `--fork-strategy` trades off fewer versions (consistency) vs newest-per-platform.

- `requires-python` (default): latest version per supported Python version, while minimizing versions across platforms. For numpy with `requires-python >= 3.8`:

```
numpy==1.24.4 ; python_version == "3.8"
numpy==2.0.2 ; python_version == "3.9"
numpy==2.2.0 ; python_version >= "3.10"
```

- `fewest`: minimize the number of selected versions per package, preferring older versions that cover more Pythons/platforms (here: `numpy==1.24.4` everywhere).

## Constraints vs overrides vs exclusions

**Constraints** (`--constraint constraints.txt`, like pip): narrow allowed versions. Listing a package as a constraint never adds it; it only applies if the package is pulled in directly or transitively. Use to restrict a transitive dependency's range, or to keep a resolution in sync with another resolved set.

**Overrides**: a last resort when you *know* a dependency works despite its metadata. They replace every declared requirement on that package.

- Example: a transitive dep declares `pydantic>=1.0,<2.0` but works with 2.x; override `pydantic>=1.0,<3`, and the original requirement is ignored completely.
- Constraints only *reduce* the acceptable set; overrides can *expand* it (escape hatch for bad upper bounds). Like constraints, global overrides don't add a dependency.
- Project: `tool.uv.override-dependencies`. Pip interface: `--override <file>` (constraints-file format).
- Scoped overrides apply only to one package's (or package version's) dependencies:

```toml
[tool.uv]
override-dependencies = [
    "foo>1",                                                          # global
    { package = { name = "bar", version = "0.0.5" }, dependencies = ["foo>2"] },  # only bar==0.0.5's foo req
]
```

- Scoped: if `bar` doesn't depend on `foo`, the scoped override *adds* it; other `bar` deps unchanged. Omit `version` to cover all versions of `bar`.
- Precedence: version-specific beats all-versions; scoped beats global for the same dependency.
- Scoped overrides support registry version specifiers only. No direct URL/path/Git sources, no explicit indexes.
- Under `explicit` pre-release mode, a pre-release specifier in *any* scoped override enables stable-first pre-release fallback for that package across the whole resolution. Likewise, an exact yanked-version pin in any scoped override enables yanked candidates for that package everywhere, even if the scope isn't selected.
- Multiple overrides for the same package must be differentiated with markers. A dependency with a marker is replaced unconditionally, whether or not the marker evaluates true.

**Exclusions** remove packages from the graph:

```toml
[tool.uv]
exclude-dependencies = ["foo"]   # every requirement on foo, including direct ones
# scoped: only foo as required by bar==0.0.5
exclude-dependencies = [
    { package = { name = "bar", version = "0.0.5" }, dependencies = ["foo"] },
]
```

- Combine a scoped override and a scoped exclusion to swap one dependency for another (e.g. replace `lightning` with `pytorch-lightning` for `bar==0.0.5`).
- When the same dependency is both overridden and excluded in a matching scope, the exclusion wins.

## Static dependency metadata: `[[tool.uv.dependency-metadata]]`

Sdist-only packages may have no static metadata, so uv must build them (e.g. run `setup.py`) just to read their dependencies. That is slow and requires the package to build on all platforms. A Linux-only package that fails to build on macOS/Windows can still be locked if you provide its metadata upfront.

```toml
[[tool.uv.dependency-metadata]]
name = "chumpy"
version = "0.70"
requires-dist = ["numpy>=1.8.1", "scipy>=0.13.0", "six>=1.11.0"]
```

- Also handy for packages that need build isolation disabled. E.g. `flash-attn` from Git (`tag = "v2.6.3"`) with `requires-dist = ["torch", "einops"]` resolves without building (which itself needs `torch`).
- Also for incorrect/incomplete metadata or packages missing from the index. Overrides change allowed versions globally; metadata overrides change one specific package's declared metadata.
- `version` is optional for registry deps (omitted = all versions) but **required for direct URL deps** (e.g. Git).
- Follows Metadata 2.3, but uv only reads `name`, `version`, `requires-dist`, `requires-python`, `provides-extra`.

## Conflicting dependencies: `conflicts`

uv resolves project deps, extras and dependency groups **together**. Incompatible extras (e.g. `extra1 = ["numpy==2.1.2"]`, `extra2 = ["numpy==2.0.0"]`) make `uv lock` fail with "No solution found". Declare the conflict and uv resolves them separately:

```toml
[tool.uv]
conflicts = [
    [
      { extra = "extra1" },
      { extra = "extra2" },
    ],
]
```

- After that, `uv sync --extra extra1 --extra extra2` errors: "extra `extra1`, extra `extra2` are incompatible with the declared conflicts". You can't install both in one environment.
- Dependency groups work the same way with the `group` key instead of `extra`.
- Workspaces: all members must be mutually compatible; declare cross-member conflicts with `package`:
  - extras across members: `{ package = "member1", extra = "extra1" }, { package = "member2", extra = "extra2" }`
  - one member's `project.dependencies` vs another's extra: `{ package = "member1" }, { package = "member2", extra = "extra2" }`
  - two members' project dependencies: `{ package = "member1" }, { package = "member2" }`. Then nothing (e.g. the workspace root with `dependencies = ["member1", "member2"]`) can depend on both.
- Note: the Preview features page lists package-level conflicts (`package-conflicts`) as a preview feature, while the resolution page documents them without a preview caveat (https://docs.astral.sh/uv/concepts/preview/).

## Lower bounds

- `uv add` adds lower bounds by default. In projects, uv warns if direct dependencies lack lower bounds.
- Why it matters: on conflicts, without lower bounds the resolver can backtrack to the oldest versions. That's slow, old versions often fail to build, or it picks a version so old it doesn't depend on the conflicting package but doesn't work with your code either.
- Critical for libraries: declare the lowest working version of each dependency and verify with `--resolution lowest`/`lowest-direct`.

## Reproducible resolutions: `exclude-newer`

`--exclude-newer` limits resolution to distributions **uploaded** before a date. Each artifact's upload time is compared, not the version's release date. Formats: RFC 3339 timestamp (`2006-12-02T02:07:43Z`) or local date (`2006-12-02`, in the system time zone).

```toml
[tool.uv]
exclude-newer = "2006-12-02T02:07:43Z"
exclude-newer-package = { setuptools = "2006-12-02T02:07:43Z" }   # or { setuptools = false } to opt out
```

- **Important:** the index must provide PEP 700 `upload-time`. Distributions without it are treated as unavailable unless the package is opted out (`--exclude-newer-package <package>=false`), the index has its own `exclude-newer`, or the index sets `exclude-newer = false`. PyPI provides `upload-time` for all packages.
- Unsatisfiable-resolution errors won't mention exclusion; newer distributions behave as if they don't exist.
- Applies only to registry packages (not Git, etc.). With `uv pip`, previously installed packages aren't downgraded unless `--reinstall` is passed.
- Disable a lower-priority global cutoff: `--exclude-newer false`, `UV_EXCLUDE_NEWER=false`, or `exclude-newer = false` in a higher-priority config file.
- Local date times are not allowed in persistent configuration.
- Per-package: `--exclude-newer-package setuptools=2006-12-02`. `=false` opts the package out (to temporarily use a newer version, or for an index without upload times).
- Precedence: package-specific beats index-specific, which beats global. Per index:

```toml
[[tool.uv.index]]
name = "internal"
url = "https://internal.example.com/simple"
exclude-newer = "7 days"     # or false to disable for this index
```

## Dependency cooldowns

Same option, but given a duration, so resolution ignores packages newer than that. This improves security posture by letting the community vet releases first.

- Friendly durations (`24 hours`, `1 week`, `30 days`) or ISO 8601 (`PT24H`, `P7D`, `P30D`).
- Days are always 24 h (DST ignored). Months and years are not allowed.
- The timestamp is computed relative to now and stored in `uv.lock`. uv doesn't relock as time passes; it updates the timestamp on a new resolution (e.g. `--upgrade`, `--refresh`).

```toml
[tool.uv]
exclude-newer = "1 week"
exclude-newer-package = { setuptools = "30 days" }
```

CLI: `--exclude-newer-package "setuptools=30 days"`.

## Source distribution formats

PEP 625 requires sdists to be `.tar.gz`. **As of 0.12, uv rejects non-conforming sdist extensions, except `.zip`**, which is still accepted for backward compatibility.

## Lockfile versioning

- `uv.lock` has a schema `version`. A uv release reads and writes its own schema version and rejects lockfiles with a *greater* one (a uv supporting v1 errors on v2).
- Newer uv *may* read older schemas if the change was backwards-compatible, but that's not guaranteed.
- The schema version is public API, bumped only in minor releases. All patch versions within a minor release have full lockfile compatibility, so rejections happen only across minor releases.
- The `revision` field tracks backwards-compatible changes (e.g. new distribution fields); revision changes don't break older uv.
