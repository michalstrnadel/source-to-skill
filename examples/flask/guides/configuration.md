# Configuration

From the docs page: Configuration Handling.

`app.config` is a dict subclass. Flask, extensions and your own code all
read from it. Configuration has to be available at startup, so load it
early, before extensions call `init_app`.

```python
app.config['TESTING'] = True
app.testing = True                 # some keys are forwarded to app attributes
app.config.update(TESTING=True, SECRET_KEY='...')
```

## Built-in keys (defaults)

| Key | Default | Notes |
|---|---|---|
| `DEBUG` | `False` | Set via `--debug` / `FLASK_DEBUG`. Unreliable if set in code. Never in production. |
| `TESTING` | `False` | Exceptions propagate instead of hitting error handlers. Enable in tests. |
| `PROPAGATE_EXCEPTIONS` | `None` | Implicitly true when `TESTING` or `DEBUG` is on. |
| `TRAP_HTTP_EXCEPTIONS` | `False` | Unhandled `HTTPException`s go to the debugger. |
| `TRAP_BAD_REQUEST_ERRORS` | `None` | A missing `args`/`form` key raises instead of returning 400. On in debug mode if unset. |
| `SECRET_KEY` | `None` | Signs the session cookie. Long random bytes or str. Never commit it. |
| `SECRET_KEY_FALLBACKS` | `None` | (3.1) Old keys still accepted for unsigning, for rotation. The last one is tried first, so order them oldest to newest. Remove them after a while because each adds overhead. |
| `SESSION_COOKIE_NAME` | `'session'` | |
| `SESSION_COOKIE_DOMAIN` | `None` | Unset is stricter and more secure. Changing it can create duplicate cookies. Since 2.3 it doesn't fall back to `SERVER_NAME`. |
| `SESSION_COOKIE_PATH` | `None` | Falls back to `APPLICATION_ROOT` or `/`. |
| `SESSION_COOKIE_HTTPONLY` | `True` | |
| `SESSION_COOKIE_SECURE` | `False` | Requires HTTPS. |
| `SESSION_COOKIE_PARTITIONED` | `False` | (3.1) For third-party/iframe contexts. Implies `SECURE`. |
| `SESSION_COOKIE_SAMESITE` | `None` | `'Lax'` is recommended, or `'Strict'`. |
| `PERMANENT_SESSION_LIFETIME` | `timedelta(days=31)` (2678400 s) | Used when `session.permanent` is set. The signature age is also validated against it. Accepts int or timedelta. |
| `SESSION_REFRESH_EACH_REQUEST` | `True` | Resend the permanent-session cookie on every response. |
| `USE_X_SENDFILE` | `False` | Only useful behind servers such as Apache. |
| `SEND_FILE_MAX_AGE_DEFAULT` | `None` | `None` means conditional requests instead of a timed cache, which is usually preferable. Override per file with `get_send_file_max_age`. |
| `TRUSTED_HOSTS` | `None` | (3.1) Valid hosts. A leading `.` matches subdomains. Invalid hosts get 400 during routing; before/after hooks still run. |
| `SERVER_NAME` | `None` | Required for `subdomain_matching` and for `url_for` external URLs outside a request. Since 3.1 it no longer restricts requests to that domain. |
| `APPLICATION_ROOT` | `'/'` | Mount path, used for URLs outside a request and as the session cookie path. |
| `PREFERRED_URL_SCHEME` | `'http'` | For external URLs outside a request. |
| `MAX_CONTENT_LENGTH` | `None` | Larger bodies get 413 `RequestEntityTooLarge`. Per view via `request.max_content_length`. With `None` and no `Content-Length` (and no stream termination from the server), nothing is read. |
| `MAX_FORM_MEMORY_SIZE` | `500_000` | (3.1) Maximum size of a non-file multipart field → 413. |
| `MAX_FORM_PARTS` | `1_000` | (3.1) Maximum number of multipart fields → 413. |
| `TEMPLATES_AUTO_RELOAD` | `None` | On in debug mode if unset. |
| `EXPLAIN_TEMPLATE_LOADING` | `False` | Logs how each template was found. |
| `MAX_COOKIE_SIZE` | `4093` | Warn above this many bytes. `0` disables the warning. |
| `PROVIDE_AUTOMATIC_OPTIONS` | not stated (enabled) | (3.1) `False` disables automatic `OPTIONS` responses. |

Removed keys (don't use):

- `LOGGER_NAME`, `LOGGER_HANDLER_POLICY` (1.0)
- `PRESERVE_CONTEXT_ON_EXCEPTION` (2.2)
- `JSON_AS_ASCII`, `JSON_SORT_KEYS`, `JSONIFY_MIMETYPE`,
  `JSONIFY_PRETTYPRINT_REGULAR`: use attributes on the `app.json` provider
  instead (2.3)
- `ENV` (2.3)

## Loading configuration

- **Python file via an env var**, a common pattern:
  ```python
  app.config.from_object('yourapplication.default_settings')
  app.config.from_envvar('YOURAPPLICATION_SETTINGS')   # path to a .cfg/.py file
  ```
  **Only UPPERCASE names** in config files are stored.
- **Data files:** `app.config.from_file("config.toml", load=tomllib.load, text=False)`
  or `from_file("config.json", load=json.load)`.
- **Mapping:** `app.config.from_mapping(SECRET_KEY="dev")`.
- **Prefixed environment variables:** `app.config.from_prefixed_env()`
  loads `FLASK_*` with the prefix stripped (`FLASK_SECRET_KEY` →
  `SECRET_KEY`).
  - Values are parsed with `json.loads`, so booleans must be lowercase
    `true`/`false`. Any other non-empty string is truthy.
  - Change behavior with the `prefix=` and `loads=` arguments.
  - `__` nests keys: `FLASK_MYAPI__credentials__username` →
    `app.config["MYAPI"]["credentials"]["username"]`. On Windows, env keys
    are uppercased.
  - For merging and case-insensitive Windows support, the docs point to
    Dynaconf.
- **Classes:** `app.config.from_object('configmodule.ProductionConfig')`.
  `from_object` **doesn't instantiate** the class. Pass an instance
  (`from_object(ProductionConfig())`) if you want `@property` keys.

## Best practices

1. Create the app in a factory so tests can pass their own config.
2. Don't read config at import time. Read it during requests so it can be
   reconfigured.
3. Load config before extensions initialize.
4. Keep a default config in version control. Switch configurations with an
   environment variable. Push code and config separately.
5. Debug mode: use `flask --app hello run --debug`. Setting `DEBUG` in code
   is strongly discouraged, because the CLI can't read it early and
   extensions may already be configured.

## Instance folders (since 0.8)

- `app.instance_path`: a deployment-specific folder, not under version
  control, for runtime files and secrets.
- Default locations:
  - `instance/` next to an uninstalled module or package
  - `$PREFIX/var/<name>-instance` when installed. `$PREFIX` is
    `sys.prefix`, for example the virtualenv.
- An explicit path must be absolute: `Flask(__name__, instance_path=...)`.
- `Flask(__name__, instance_relative_config=True)` makes relative config
  paths resolve against the instance folder:
  ```python
  app.config.from_object('yourapplication.default_settings')
  app.config.from_pyfile('application.cfg', silent=True)
  ```
- `app.open_instance_resource('application.cfg')` opens a file in the
  instance folder.
- Flask doesn't create the instance folder. The tutorial calls
  `os.makedirs(app.instance_path, exist_ok=True)`.

## Configuring extensions (from the extension guide)

- Per-app settings go in `app.config` with keys prefixed by the extension
  name.
- Settings that shouldn't change per deployment go in `__init__` arguments.
- **Never change config after setup**, because the change isn't guaranteed
  to reach other workers.
