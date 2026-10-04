---
name: flask
description: Working reference for Flask (pallets/flask), the Python WSGI micro web framework built on Werkzeug, Jinja and Click, distilled from the official docs in the repository. Covers routing and views, the app/request context and request lifecycle, application factories and blueprints, configuration (every built-in config key with its default), the flask CLI and dotenv, Jinja templating, error handling, logging and debugging, testing with pytest, production deployment (Gunicorn, Waitress, mod_wsgi, uWSGI, gevent, ASGI, nginx/Apache with ProxyFix), security, extensions, common patterns (SQLite, SQLAlchemy, Celery, uploads) and the Flaskr tutorial. Load it when building, debugging, testing, configuring or deploying a Flask app, or when writing a Flask extension.
---

# Flask

Source: https://github.com/pallets/flask - README plus the `docs/` tree
(77 pages). Flask is a lightweight WSGI web application framework: quick to
start, able to scale to complex apps. It depends on Werkzeug (WSGI), Jinja
(templates), MarkupSafe (escaping), ItsDangerous (signing the session
cookie), Click (the `flask` command) and Blinker (signals). Supports
Python 3.10 and newer.

## Core mental model

- **"Micro" means a small, extensible core**, not a toy. Flask picks the
  template engine (Jinja) and the WSGI layer (Werkzeug) and nothing else.
  It will never ship a database layer or a form library. Extensions cover those.
- **One explicit application object.** `app = Flask(__name__)`. Flask uses
  `__name__` to find templates, static files and resources relative to your
  package. An explicit object means you can run several apps at once (useful
  for tests), subclass `Flask`, and wrap the WSGI app in middleware.
- **Setup phase vs. serving phase.** Register routes, blueprints, config,
  Jinja settings and extensions *before* the first request. WSGI servers run
  many workers, so changes made later never reach all of them. Flask raises
  an error if you call a setup method such as `route` after the app has handled a request.
- **Context-local proxies.** `current_app`, `g`, `request` and `session`
  point at the active context of the current worker (thread, greenlet,
  coroutine). An app context (CLI, `with app.app_context()`) gives
  `current_app` and `g`. A request adds `request` and `session`. Accessing them
  outside a context raises `RuntimeError: Working outside of application/request context`.
- **Return values become responses:** str, bytes or iterator → body. dict or
  list → JSON. `(body, status)`, `(body, headers)` or
  `(body, status, headers)` → body plus overrides. A `Response` passes through
  unchanged. Anything else is treated as a WSGI app.
- **Production is never `flask run`.** The development server and its
  debugger allow arbitrary code execution. Use a WSGI server, usually
  behind a reverse proxy.

## Install and first app

```
python3 -m venv .venv && . .venv/bin/activate
pip install Flask
```

```python
# hello.py  (never name it flask.py: it shadows Flask itself)
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
```

```
flask --app hello run --debug     # reloader + interactive debugger
```

- If the file is `app.py` or `wsgi.py`, you can omit `--app`.
- The server listens on `127.0.0.1:5000` and is visible only from your
  machine. `--host=0.0.0.0` exposes it, but only do that with the debugger
  off or on a trusted network.
- On macOS Monterey and later, AirPlay Receiver occupies port 5000. Turn it
  off, or run `flask run --port 5001`.

## Core usage patterns

- **Routing:** `@app.route("/post/<int:id>")`. The converters are `string` (the
  default, no slashes), `int`, `float`, `path` (accepts slashes), `uuid`, and
  `any` (listed in the API docs). Use the method shortcuts `@app.get` and
  `@app.post`. Routes answer `GET` only by default. `HEAD` and `OPTIONS` are
  automatic.
- **Trailing slash rule:** `/projects/` redirects `/projects` to the
  canonical URL. `/about` returns 404 for `/about/`.
- **URL building:** `url_for("endpoint", **values)`. Values that don't match
  the rule become query args. Blueprint endpoints are `bp.view`, and `.view`
  refers to the same blueprint. Static files: `url_for('static', filename=...)`.
- **Request data:** `request.form` for POST/PUT form data, `request.args`
  for the query string, `request.files` for uploads, `request.json` for JSON
  bodies (415 if `Content-Type` isn't `application/json`), and
  `request.cookies`. A missing key raises a 400 unless you catch it. Use
  `.get(key, default)` instead.
- **Sessions:** a signed cookie. The user can read it but can't modify it.
  It requires `SECRET_KEY`. Generate one with
  `python -c 'import secrets; print(secrets.token_hex())'`. In-place
  mutation isn't detected, so set `session.modified = True`.
- **Escaping:** Jinja autoescapes `.html/.htm/.xml/.xhtml/.svg` templates.
  For HTML you build by hand, use `markupsafe.escape()`.
- **App factory and blueprints** are the default structure for anything
  non-trivial. Create the extension objects unbound, then call
  `ext.init_app(app)` inside `create_app()`. See guides/app-structure.md.
- **Hooks**, in request order: `url_value_preprocessor` → `before_request`
  (returning a value short-circuits the request) → view → `errorhandler` →
  `after_this_request` → `after_request` → session save → `teardown_request`
  → `teardown_appcontext`. Teardown hooks always run, even after an error,
  so don't depend on earlier hooks having run.

## Decision rules

- **Async views** (`pip install flask[async]`): use them for concurrent I/O
  inside one view. Each request still occupies one worker, async is not faster
  than sync, and background tasks get cancelled. For a mainly-async codebase
  use Quart. For many long-lived connections use gevent. For background work
  use a task queue (Celery).
- **Blueprints vs. multiple apps:** blueprints share one config and are
  separated at the Flask level. Use `DispatcherMiddleware` when apps must be
  fully isolated at the WSGI level.
- **Debug mode:** set it with `--debug`. Setting `DEBUG` in code or config is
  strongly discouraged, because `flask run` can't read it early enough.
- **ProxyFix:** apply it only when the app really runs behind a proxy, and
  set exactly as many hops as there are proxies. Getting this wrong is a
  security issue.
- **Error handlers:** register them for specific exceptions. A handler for
  `Exception` also swallows every HTTP error. Pass `HTTPException` through.
- **Form data vs. JSON from JavaScript:** prefer form data. Use JSON only
  when you need complex structures.

## Doc index

| Guide | Covers |
|---|---|
| [guides/getting-started.md](guides/getting-started.md) | Install, quickstart walkthrough, dev server, debug mode, port conflicts |
| [guides/routing-and-views.md](guides/routing-and-views.md) | Rules, converters, `url_for`, methods, request data, responses, cookies, class-based views, view decorators, URL processors |
| [guides/app-structure.md](guides/app-structure.md) | Request lifecycle, contexts, factories, packages, blueprints, dispatching, signals, design rationale |
| [guides/configuration.md](guides/configuration.md) | All built-in config keys and defaults, loading from files, objects and env vars, instance folders |
| [guides/cli.md](guides/cli.md) | `flask` command, `--app` discovery, dotenv, custom commands, plugins, shell |
| [guides/templates-and-frontend.md](guides/templates-and-frontend.md) | Jinja setup, context, autoescaping, filters, inheritance, flashing, `fetch`/JSON, streaming |
| [guides/errors-logging-debugging.md](guides/errors-logging-debugging.md) | Error handlers, JSON API errors, Sentry, logging config, debuggers |
| [guides/testing.md](guides/testing.md) | pytest fixtures, test client, sessions, CLI runner, context in tests |
| [guides/deployment.md](guides/deployment.md) | Gunicorn, Waitress, mod_wsgi, uWSGI, gevent, ASGI, nginx/Apache, ProxyFix, async and gevent |
| [guides/security.md](guides/security.md) | Resource limits, XSS, CSRF, security headers, cookie options, host validation |
| [guides/extensions.md](guides/extensions.md) | Using extensions and writing them: `init_app`, config, `g` namespacing, guidelines |
| [guides/patterns.md](guides/patterns.md) | SQLite, SQLAlchemy, MongoEngine, uploads, Celery, caching, WTForms and other recipes |
| [guides/tutorial-flaskr.md](guides/tutorial-flaskr.md) | The Flaskr blog tutorial in reading order: factory, DB, auth, blog, packaging, tests, deploy |
| [cheatsheet.md](cheatsheet.md) | Commands and code snippets from across the docs |

## Not covered by this skill

- `docs/api.rst` is mostly Sphinx `autoclass`/`autofunction` directives, so
  the full method signatures and docstrings (which live in the source) were
  not extracted. Only the hand-written parts are here: converters,
  `add_url_rule` parameters, the signal list, and view-function attributes.
- The changelog (`CHANGES.rst`) and the license text are pulled in by
  `include` directives and were not extracted.
