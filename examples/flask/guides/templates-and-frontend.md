# Templates, flashing, JavaScript and streaming

From the docs pages: Templates, Template Inheritance, Message Flashing, JavaScript, fetch, and JSON, Streaming Contents, Quickstart (Rendering Templates, HTML Escaping), API (JSON Support).

## Rendering

- `render_template('hello.html', person=name)` looks in `templates/`, next
  to a module or inside a package.
- `render_template_string(...)` renders a template from a string.
- Templates can produce any text format: HTML, markdown, plain-text email.
- You can use another engine, but Jinja must be installed because Flask
  and extensions depend on it.

## Jinja as configured by Flask

- **Autoescaping is on** for templates ending in `.html`, `.htm`, `.xml`,
  `.xhtml`, and `.svg` when using `render_template`, and for all strings
  rendered with `render_template_string`.
- Templates can opt in or out with `{% autoescape %}`.
- **Docs inconsistency:** an old 0.5 note in the Quickstart says templates
  loaded from a string have autoescaping *disabled*. The current Templates
  page says `render_template_string` autoescapes everything. Trust the
  Templates page.
- **Standard context:** `config`, `request`, `session` and `g` (the last
  three only when a request context is active), plus the functions
  `url_for()` and `get_flashed_messages()`.
- These are added to the render context, not as Jinja globals. **Imported
  macros don't see them.** Either pass the value to the macro explicitly,
  or import it with context:
  `{% from '_helpers.html' import my_macro with context %}`.

## Marking HTML as safe

Three ways, in order of preference:

1. Wrap the string in `markupsafe.Markup` in Python. This is the
   recommended way.
2. Use the `|safe` filter in the template.
3. Use `{% autoescape false %}...{% endautoescape %}`, carefully.

```python
Markup('<strong>Hello %s!</strong>') % '<blink>hacker</blink>'   # argument gets escaped
Markup.escape('<blink>hacker</blink>')
Markup('<em>Marked up</em> &raquo; HTML').striptags()            # 'Marked up » HTML'
```

## Filters, tests, globals, context processors

- `@app.template_filter` uses the function name. `@app.template_filter("reverse")`
  sets a name. `app.add_template_filter(fn, "reverse")` registers without a
  decorator.
- Tests and globals work the same way: `template_test` / `add_template_test`
  and `template_global` / `add_template_global`.
- Blueprint versions with the `app_` prefix register for all templates.
- `app.jinja_env` can be modified directly.
- **Context processors** return a dict that is merged into every template's
  context. They can also inject functions:

```python
@app.context_processor
def utility_processor():
    def format_price(amount, currency="€"):
        return f"{amount:.2f}{currency}"
    return dict(format_price=format_price)
```

## Template inheritance

- The base `layout.html` defines `{% block head %}`, `title`, `content`
  and `footer`.
- A child starts with `{% extends "layout.html" %}`, which **must be the
  first tag**, and overrides blocks. `{{ super() }}` renders the parent
  block's content.
- Trick from the tutorial: put `{% block title %}` inside
  `{% block header %}` so the window title and the page heading share one
  value.

## Message flashing

- `flash(msg, category='message')` records a message for the **next
  request only**. Read it with `get_flashed_messages()`, usually in the
  base layout:

```jinja
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}<ul class=flashes>
    {% for category, message in messages %}<li class="{{ category }}">{{ message }}</li>{% endfor %}
  </ul>{% endif %}
{% endwith %}
```

- Filter by category with `get_flashed_messages(category_filter=["error"])`.
- Flashes live in the session cookie. **Messages too large for the cookie
  fail silently.**

## JavaScript, fetch and JSON

- Templates render on the server and JavaScript runs in the browser, so JS
  can't affect rendering. Pass data into scripts with
  `const chart_data = {{ chart_data|tojson }}`. Without `tojson` you get a
  `SyntaxError`. In a `data-` attribute, use **single quotes**:
  `<div data-chart='{{ chart_data|tojson }}'>`.
- `tojson` uses the app's JSON provider and marks its output safe.
- **URLs:** render them with `{{ url_for(...)|tojson }}`. For URLs built in
  JS, expose `const SCRIPT_ROOT = {{ request.script_root|tojson }}`.
- **Sending:** prefer `FormData` (read with `request.form`). For JSON, send
  `Content-Type: application/json`, or Flask returns 415.
- **Redirects:** fetch follows them without changing the page. Check
  `response.redirected` and set `window.location = response.url`.
- **Returning JSON:**
  - Return a dict or list from the view.
  - `jsonify(...)` builds the response for other JSON types.
  - Don't put file data in JSON (base64 is slow, larger, and hard to cache).
    Return a URL to the file instead.
- **Receiving JSON:** `request.json`. Invalid JSON → 400, wrong content
  type → 415.
- **JSON provider:** Flask uses the stdlib `json` by default. Swap it with
  `app.json_provider_class` or `app.json`. The `flask.json` functions
  delegate to `app.json` when an app context is active.
- jQuery/AJAX patterns are documented as obsolete in favor of `fetch`.
- **SPA:** use `Flask(__name__, static_folder='app', static_url_path="/app")`
  plus a catch-all route (`'/'` with `defaults={'path': ''}` and
  `'/<path:path>'`) returning `app.send_static_file("index.html")`.

## Streaming

- Return a generator, for example `return generate(), {"Content-Type": "text/csv"}`.
  Each `yield` is sent to the client.
- Some WSGI middleware (profilers, debug tools) can break streaming.
- **All headers must be set before the body starts.** If the generator
  reads `session`, also read it in the view so the `Vary: Cookie` header is
  set. Never modify the session inside the generator, because
  `Set-Cookie` has already been sent.
- `request` is gone once the generator runs. Wrap the generator with
  `stream_with_context(generate())` (also usable as a decorator) to keep
  the request context.
- `stream_template("timeline.html")` and `stream_template_string` render
  Jinja templates piece by piece. They apply `stream_with_context`
  automatically when a request is active.

## Favicon

- Put a 16×16 ICO in `static/favicon.ico` and link it with
  `<link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">`.
- For old browsers that request `/favicon.ico`, either redirect with
  `app.add_url_rule("/favicon.ico", endpoint="favicon", redirect_to=url_for("static", filename="favicon.ico"))`,
  or serve it with `send_from_directory(..., mimetype='image/vnd.microsoft.icon')`.
- Better still, let the web server serve it.
