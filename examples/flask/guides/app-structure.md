# Application structure, lifecycle and contexts

From the docs pages: Application Structure and Lifecycle, The App and Request Context, Application Factories, Large Applications as Packages, Modular Applications with Blueprints, Application Dispatching, Signals, Design Decisions in Flask, Subclassing Flask, API (Useful Internals).

## Setup phase

- Everything outside view functions is the setup phase. That includes
  routes, error handlers, `before_request` hooks, blueprints,
  `app.config`, `app.jinja_env`, the session interface, `app.json`
  providers, and extensions. All of it must be imported and run before
  serving.
- Never modify `Flask` or `Blueprint` objects from inside a request. Flask
  detects some of these cases ("The setup method 'route' can no longer be
  called on the application...") but not all of them.

## Serving: what happens around Flask

1. The client sends a request.
2. The WSGI server converts it to an `environ` dict and calls the app.
3. Flask routes the request and processes it.
4. Flask returns WSGI response data.
5. The server sends the HTTP response.

Middleware is a WSGI app that wraps another one. Wrap `app.wsgi_app`, not
`app`, so `app` still refers to Flask.

## Request lifecycle

1. The WSGI server calls `Flask.wsgi_app`. An `AppContext` is created and
   `environ` becomes a `Request`.
2. The context is pushed. `current_app`, `g`, `request` and `session`
   become available. The `appcontext_pushed` signal is sent.
3. The URL is matched. A failure (404, 405 or redirect) is stored for later.
   The `request_started` signal is sent.
4. `url_value_preprocessor` functions run, then `before_request` functions.
   If any of them returns a value, that value becomes the response.
5. A stored routing error is raised now. Otherwise the view runs.
6. On an exception, a matching `errorhandler` (by class or code) produces
   the response.
7. The return value is converted to a `Response`. `after_this_request`
   callbacks run, then `after_request`.
8. The session is saved through `app.session_interface`. The
   `request_finished` signal is sent.
9. Unhandled exceptions are dealt with now: HTTP exceptions become their
   status, anything else becomes a 500. The `got_request_exception` signal
   is sent.
10. The response goes to the server.
11. Cleanup: `teardown_request` → `request_tearing_down` →
    `teardown_appcontext` → `appcontext_tearing_down` → pop →
    `appcontext_popped`.

A CLI command or a plain app context follows the same order without the
request steps. Blueprint handlers run when the blueprint owns the matched
route.

**Teardown rules:** teardown callbacks run even after unhandled
exceptions. In some test scenarios they may run more than once. All of them
run even if one raises. Write them so they don't depend on other callbacks
having run.

## Contexts

- They solve two problems: circular imports (no need to import `app`) and
  passing request data through every function.
- **App context** gives `current_app` and `g`. **Request context** also
  gives `request` and `session`. As of 3.2, `RequestContext` is merged into
  `AppContext`. The old names are deprecated aliases that will be removed in
  Flask 4.0.
- **Outside an app context at setup**, for example when initializing an
  extension, use `with app.app_context(): init_db()`. Elsewhere, the error
  usually means the code belongs in a view or CLI command.
- **Outside a request context**: this is usually a test. Use
  `app.test_client()` for a full request, or
  `with app.test_request_context("/path", query_string={...})` to test a
  single function.
- Contexts are per worker. You can't hand proxies to another thread.
  `current_app._get_current_object()` returns the real object, for example
  to use as a signal sender.
- Implementation: Python `contextvars` plus Werkzeug `LocalProxy`, managed
  as a stack. Pushing a nested context is possible (an app used as WSGI
  middleware), but uncommon.
- `g` is a namespace for the lifetime of one app context. For example,
  `before_request` can load `g.user`. It has been bound to the app context
  since 0.10.

**Docs inconsistency:** the "Working with the Shell" page still describes
`test_request_context()` as returning a `RequestContext` with
`push()`/`pop()`. The API page marks that class as a deprecated alias
(3.2). Prefer the `with` form.

## Application factories

```python
def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)
    from yourapplication.model import db
    db.init_app(app)
    from yourapplication.views.admin import admin
    app.register_blueprint(admin)
    return app
```

- Why use a factory: tests with different settings, and several instances
  in one process.
- The trade-off: blueprints can't use `app` at import time. Use
  `current_app` inside requests instead.
- Extensions: create `db = SQLAlchemy()` unbound in a module, then call
  `db.init_app(app)` in the factory. Don't use `SQLAlchemy(app)`. This keeps
  app state off the extension object, so one extension object can serve
  several apps.
- Running: `flask --app hello run` auto-detects `create_app` or `make_app`.
  `flask --app 'hello:create_app(local_auth=True)' run` passes arguments.
- Improvements the docs suggest: accept config values for tests, call a
  setup function from blueprints, add middleware at creation.

## Packages (larger apps)

- Move the module into `yourapplication/__init__.py`. Add a
  `pyproject.toml` (flit_core backend), run `pip install -e .`, then
  `flask --app yourapplication run`.
- Create `app` in `__init__.py`, then import the views module **after**
  creating it (`import yourapplication.views`). This circular import is
  acceptable because nothing from views is used in `__init__`.

## Blueprints

- A blueprint records operations and applies them when registered. It is
  not an application. Uses:
  - splitting a large app
  - mounting at a `url_prefix` or `subdomain`
  - registering the same blueprint several times
  - shipping templates, static files and filters
  - registering things from an extension
- Blueprints share the app's config. **You can't unregister one** without
  destroying the app.
- Endpoints are prefixed with the blueprint name (`simple_page.show`). The
  name doesn't change URLs, only endpoints.
- `app.register_blueprint(bp, url_prefix='/pages')`.
- **Nesting:** `parent.register_blueprint(child)`. Names chain
  (`parent.child.create`), URL prefixes chain, and subdomains chain as
  `child.parent`. The parent's before-request hooks apply to the child, and
  the parent's error handlers are the fallback.
- **Resources:** the resource folder is inferred from the import name
  (`bp.root_path`). `bp.open_resource('static/style.css')` opens a file in
  it.
- **Static files:** `static_folder='static'` serves at the blueprint's
  `url_prefix` + `/static`, with endpoint `admin.static`. **Without a
  url_prefix, the blueprint's static folder is unreachable**, because the
  app's `/static` wins. Blueprint static folders are not a fallback for the
  app's.
- **Templates:** `template_folder` has lower priority than the app's
  templates folder. Among blueprints, the first registered wins. To avoid
  collisions, nest templates as `admin/templates/admin/index.html` and
  render `admin/index.html`. `EXPLAIN_TEMPLATE_LOADING` traces template
  lookup.
- **Error handlers:** `@bp.errorhandler(...)` works, but 404 and 405
  handlers only fire for an explicit `abort` or `raise` inside the
  blueprint. Routing errors happen before Flask knows which blueprint owns
  the URL. Branch on `request.path` in an app-level handler instead.
- **CLI:** `@bp.cli.command('create')` becomes `flask students create`.
  Change the group with `cli_group='other'`, or flatten it with
  `cli_group=None`.

## Application dispatching (multiple WSGI apps)

- Use `werkzeug.middleware.dispatcher.DispatcherMiddleware(frontend, {'/backend': backend})`
  to combine fully isolated apps (even non-Flask ones) by URL prefix.
- **By subdomain:** a WSGI callable creates and caches one app per
  subdomain under a `threading.Lock`. An unknown user returns a
  `NotFound()` exception, which is itself a valid WSGI app.
- **By path:** the same idea using `wsgiref.util.shift_path_info`, falling
  back to a default app when the factory returns `None`.

## Signals (Blinker)

- Signals notify subscribers about lifecycle events. Unlike hooks, they can
  be subscribed temporarily and can't change the app. Good for tests,
  metrics and auditing.
- `signal.connect(func, app)`: **always pass the sender** (the app) unless
  you really want every app's events. Accept `**extra` in subscribers
  because new arguments may be added. Unsubscribe with `disconnect`, scope
  a subscription with `connected_to(func, app)`, or use the decorator
  `@template_rendered.connect_via(app)`.
- Built-in signals: `template_rendered`, `before_render_template`,
  `request_started`, `request_finished`, `got_request_exception` (not for
  HTTP exceptions or handled errors), `request_tearing_down`,
  `appcontext_tearing_down` (both receive `exc`), `appcontext_pushed`,
  `appcontext_popped`, `message_flashed`.
- Custom signals: `Namespace().signal('model-saved')`, then
  `model_saved.send(self)`. Never pass `current_app` as the sender. Use
  `current_app._get_current_object()`.

## Design rationale (why Flask works this way)

- **Explicit app object:** allows several apps (tests), subclassing, and a
  reliable resource path from `__name__` instead of the cwd. The app is the
  WSGI app, which makes middleware wrapping easy.
- **Werkzeug routing** orders rules by complexity, so declaration order
  across modules doesn't matter. Ambiguous URLs redirect to the canonical
  form.
- **One template engine (Jinja):** extensions can rely on it being there.
  You can render with another engine, but Jinja is still configured.
- **Async:** coroutines run on a thread, not a main-thread event loop. That
  keeps backward compatibility with pre-async extensions, at a performance
  cost compared with ASGI frameworks.
- **Subclassing `Flask`** is the recommended way to change internals, for
  example `request_class = MyRequest` with
  `parameter_storage_class = ImmutableOrderedMultiDict`.
