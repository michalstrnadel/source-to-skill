# Errors, logging and debugging

From the docs pages: Handling Application Errors, Logging, Debugging Application Errors.

## Why errors happen even with correct code

Clients disconnect mid-read, databases overload, disks fill up, backends
fail, libraries have bugs, and networks drop. In production, Flask shows a
simple error page and logs to `app.logger`.

## Error tracking

The docs recommend Sentry over error emails. Sentry aggregates duplicate
errors, captures stack traces and local variables, and alerts on new
errors or frequency thresholds.

```python
# pip install sentry-sdk[flask]
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
sentry_sdk.init('YOUR_DSN_HERE', integrations=[FlaskIntegration()])
```

## Registering handlers

```python
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400          # set the status yourself

app.register_error_handler(400, handle_bad_request)   # same, without decorator
```

- **The handler's code is not applied to the response automatically.**
  Always return the status.
- An exception class and its HTTP code are interchangeable
  (`BadRequest.code == 400`).
- Werkzeug doesn't know non-standard codes. Subclass `HTTPException` with
  a `code` and `description`, then register and raise that class.
- Handlers can target any exception class. They also catch subclasses.

## How Flask picks a handler

1. Look up by status code.
2. Otherwise, walk the class hierarchy. The most specific handler wins.
   For example, a `ConnectionRefusedError` handler beats a
   `ConnectionError` handler.
3. Otherwise: an `HTTPException` returns its generic page, and anything
   else becomes a 500.

- Blueprint handlers take precedence over app handlers for requests the
  blueprint handles. A blueprint **can't** handle routing 404s, and 404/405
  handlers on a blueprint fire only on an explicit `abort` or `raise`.
  Branch on `request.path` in an app-level handler instead.
- **Generic handlers:**
  - A handler for `HTTPException` also catches routing 404s and 405s.
  - A handler for `Exception` is like a bare `except Exception:` and
    catches all HTTP errors too.
  - Prefer specific handlers, or pass HTTP errors through:
    `if isinstance(e, HTTPException): return e`.
  - With both registered, the `HTTPException` handler still wins for HTTP
    errors.
- **Unhandled exceptions:** a registered `InternalServerError` (500)
  handler always receives an `InternalServerError` (since 1.1.0). The
  original exception is in `e.original_exception`. The 500 handler also
  receives uncaught exceptions. **In debug mode the 500 handler is
  skipped** and the debugger is shown instead.

## Common recipes

- **`abort(400)` / `abort(404)`** raise HTTP errors from a view.
- **Custom 404/500 pages:** `return render_template('404.html'), 404`. With
  a factory, use `app.register_error_handler(404, page_not_found)`. On a
  blueprint, use `@blog.errorhandler(500)`.
- **HTTP errors as JSON:**

```python
@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()            # keeps status and headers
    response.data = json.dumps({"code": e.code, "name": e.name, "description": e.description})
    response.content_type = "application/json"
    return response
```

- **API errors:**
  - `abort(404, description="Resource not found")` plus a 404 handler
    returning `jsonify(error=str(e)), 404`.
  - Or a custom `InvalidAPIUsage(Exception)` with `status_code` (default
    400), `message`, an optional `payload`, and a `to_dict()` method. Its
    handler returns `jsonify(e.to_dict()), e.status_code`.

Doc bug: the error-handling examples call `request.arg.get(...)`. The real
attribute is `request.args`.

## Logging

- `app.logger` is a standard `logging.Logger` named after `app.name`. Use
  it for your own messages too. Python's default level is usually WARNING,
  so lower levels are hidden until you configure logging.
- **Configure logging before creating the app.** If `app.logger` is
  accessed first, Flask adds a default handler.

```python
from logging.config import dictConfig
dictConfig({
    'version': 1,
    'formatters': {'default': {'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'}},
    'handlers': {'wsgi': {'class': 'logging.StreamHandler',
                          'stream': 'ext://flask.logging.wsgi_errors_stream',
                          'formatter': 'default'}},
    'root': {'level': 'INFO', 'handlers': ['wsgi']},
})
app = Flask(__name__)
```

- **Default handler:** a `StreamHandler` that writes to
  `environ['wsgi.errors']` during requests (usually stderr) and to stderr
  otherwise. Remove it with
  `app.logger.removeHandler(flask.logging.default_handler)`.
- **Email errors:** add a `logging.handlers.SMTPHandler` at the `ERROR`
  level, only when `not app.debug`. It needs an SMTP server.
- **Request info in logs:** subclass `logging.Formatter`. When
  `has_request_context()`, set `record.url = request.url` and
  `record.remote_addr = request.remote_addr`, otherwise `None`.
- **Other libraries:** attach handlers to the root logger, or to each
  logger you care about (`app.name`, `'sqlalchemy'`, ...).
- Werkzeug logs requests to the `'werkzeug'` logger and adds its own
  handler if the root logger has none.

## Debugging

- **Production:** never run the dev server or the built-in debugger there.
  Its PIN shouldn't be relied on. Use Sentry or logging.
  - With server access, you can start an external debugger only when
    `request.remote_addr` matches your IP. Enable it only temporarily.
- **Built-in debugger:** on in debug mode (`flask --app hello run --debug`
  or `app.run(debug=True)`).
- **External or IDE debuggers:** keep debug mode on, otherwise errors
  become generic 500 pages. Disable the built-in debugger and reloader:
  `flask --app hello run --debug --no-debugger --no-reload`, or
  `app.run(debug=True, use_debugger=False, use_reloader=False)`.
  - If you leave them on, the built-in debugger catches exceptions first,
    and the reloader can restart mid-breakpoint.
  - `passthrough_errors=True` stops the dev server from catching
    exceptions. You usually don't want that.
