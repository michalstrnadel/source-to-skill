# Routing, views, requests and responses

From the docs pages: Quickstart, API (URL Route Registrations, View Function Options), Class-based Views, View Decorators, Lazily Loading Views, Using URL Processors, Adding HTTP Method Overrides, Deferred Request Callbacks.

## Registering routes

There are three ways to register a route:

- the `@app.route()` decorator
- `app.add_url_rule(rule, endpoint=None, view_func=None, **options)`
- the underlying Werkzeug `app.url_map`

**Variable parts:** `<name>` or `<converter:name>`. They are passed to the
view as keyword arguments.

| Converter | Accepts |
|---|---|
| `string` | default; any text without a slash |
| `int` | integers |
| `float` | floating point values |
| `path` | like `string` but also slashes |
| `any` | one of the provided items |
| `uuid` | UUID strings |

The Quickstart table says `int` and `float` accept *positive* values, while
the API page says "integers" and floats without that qualifier. The two pages
disagree. The API reference is the more specific source. Custom converters
go on `app.url_map`.

**Trailing slashes:** a rule ending in `/` that is requested without the
slash redirects to the canonical URL. A rule without a trailing slash that
is requested with one returns 404. This keeps URLs unique.

**Defaults and multiple rules:**

```python
@app.route('/users/', defaults={'page': 1})
@app.route('/users/page/<int:page>')
def show_users(page): ...
```

A URL that matches a default value is redirected to its simpler form with a
308 (here `/users/page/1` → `/users/`). If the route also handles POST,
restrict the default route to GET, because redirects can't preserve form
data.

**`add_url_rule` / `route` parameters:**

- `rule`
- `endpoint`: defaults to the function name
- `view_func`
- `defaults`
- `subdomain`
- `**options`: forwarded to Werkzeug `Rule`, for example `methods`

Since Flask 0.6, `OPTIONS` is added automatically. `GET` implies `HEAD`.

**Attributes on view functions:**

- `methods`: used if not passed at registration
- `provide_automatic_options`: force the automatic `OPTIONS` response on or off
- `required_methods`: always added

`PROVIDE_AUTOMATIC_OPTIONS = False` disables automatic `OPTIONS` app-wide.

**Method shortcuts:** `@app.get`, `@app.post`, and so on, versus one view with
`methods=['GET', 'POST']` that branches on `request.method`. Both are valid.
Pick per view.

## URL building

`url_for(endpoint, **values)`. Reasons to use it instead of hard-coding:

- it's more descriptive
- you change URLs in one place
- it escapes special characters
- it always produces absolute paths
- it handles apps mounted under a sub-path

Unknown values become query args: `url_for('login', next='/')` →
`/login?next=/`. Outside a request, use `app.test_request_context()` to try
it out.

## Request data (`from flask import request`)

`request` is a proxy to the current worker's request.

- `request.method`
- `request.form`: POST/PUT form data. A missing key raises a special
  `KeyError`. If uncaught, it becomes **400 Bad Request**.
- `request.args`: the query string. Prefer `request.args.get('key', '')`.
- `request.files`: uploads. Each is a `FileStorage` with `.save()` and
  `.filename`. Never trust `filename`. Pass it through
  `werkzeug.utils.secure_filename`. The form needs
  `enctype="multipart/form-data"`.
- `request.json`: invalid JSON → 400. Wrong `Content-Type` → 415.
- `request.cookies`: a dict. Use `.get()`. For login state, use `session`,
  not raw cookies.

## Responses

The conversion rules, in order:

1. A `Response` is returned as is.
2. A str becomes the body with status 200 and type `text/html`.
3. An iterator or generator of str or bytes becomes a streaming response.
4. A dict or list goes through `jsonify`.
5. A tuple: `(body, status)`, `(body, headers)` or
   `(body, status, headers)`. Headers can be a list or a dict.
6. Anything else is treated as a WSGI app.

Use `make_response(...)` to get the object and modify it:

```python
resp = make_response(render_template('error.html'), 404)
resp.headers['X-Something'] = 'A value'
```

- Set cookies on the response: `resp.set_cookie('username', 'x')`.
- `redirect(url_for('login'))` redirects. `abort(401)` stops the request
  immediately, so code after it never runs.
- Every dict or list value returned as JSON must be serializable. Convert
  models first, for example with a serialization library.

**Setting a cookie before the response exists** (from a `before_request`):
register `@after_this_request` inside the hook. It runs only for the
current request and receives the response.

## Class-based views (`flask.views`)

- Subclass `View` and implement `dispatch_request()`. Register it with
  `app.add_url_rule("/users/", view_func=UserList.as_view("user_list"))`.
  You can't decorate the class with `@app.route`.
- Arguments after the name in `as_view(name, *args)` go to `__init__`. That
  makes one class reusable across models:
  `ListView.as_view("story_list", Story, "stories.html")`.
- URL variables arrive as keyword arguments to `dispatch_request`.
- By default a new instance is created per request, so writing to `self` is
  safe. `init_every_request = False` reuses one instance per `as_view`
  call. It's faster, but then never write to `self`. Use `g` instead.
- `decorators = [...]` applies decorators to the generated view function.
  The list order matters: the first item ends up innermost.
- `methods = ["GET", "POST"]` on the class is the same as passing methods,
  and subclasses inherit it.
- `MethodView` dispatches to the lowercase method name (`get`, `post`,
  `patch`, `delete`) and sets `methods` automatically. A common REST
  layout uses one `ItemAPI` (get, patch, delete on `/<name>/<int:id>`) and
  one `GroupAPI` (get list, post on `/<name>/`), registered by a
  `register_api(app, model, name)` helper.

## View decorators

- Wrap with `functools.wraps`. `@app.route` must be the **outermost**
  decorator.
- **login_required:** if `g.user is None`, redirect to
  `url_for('login', next=request.url)`. Carry `next` through the login
  form in a hidden input.
- **cached(timeout=5*60, key='view/{}'):** the key comes from
  `request.path`. Return the cached value or compute and store it. This
  needs a cache object, such as Flask-Caching.
- **templated(template=None):** the view returns a dict, which is rendered
  into the template. The default template name is the endpoint with dots
  replaced by slashes, plus `.html`. A non-dict return value is passed
  through unchanged.
- **Endpoint mapping:** `app.url_map.add(Rule('/', endpoint='index'))` plus
  `@app.endpoint('index')`.

## Lazy loading and a central URL map

When import time matters, use `add_url_rule` in one module plus a
`LazyView(import_name)` class that imports the real view on first call
(`werkzeug.utils.import_string` with `cached_property`). It must set
`__module__` and `__name__` correctly, because Flask uses them to name the
endpoint. Before- and after-request handlers still have to be imported
upfront.

## URL processors (for example a language code in every URL)

- `@app.url_defaults(endpoint, values)` injects values into `url_for`. Use
  `app.url_map.is_endpoint_expecting(endpoint, 'lang_code')`.
- `@app.url_value_preprocessor(endpoint, values)` runs right after
  matching. It pops the value into `g`, so views no longer receive it.
- On a blueprint with `url_prefix='/<lang_code>'`, the per-blueprint
  versions are simpler: `values.setdefault('lang_code', g.lang_code)` and
  `g.lang_code = values.pop('lang_code')`.

## HTTP method override

Proxies that don't support methods like PATCH can be worked around with WSGI
middleware. It reads `X-HTTP-Method-Override` from a POST and rewrites
`REQUEST_METHOD`, setting `CONTENT_LENGTH` to `'0'` for bodyless methods.
Install it with `app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)`.
