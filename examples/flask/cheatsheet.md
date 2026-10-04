# Flask cheatsheet

Commands and snippets collected from across the Flask docs.

## Setup and run

```
python3 -m venv .venv && . .venv/bin/activate
pip install Flask                         # extras: flask[async]; optional: python-dotenv, watchdog
flask --app hello run --debug             # dev server + debugger + reloader
flask --app 'hello:create_app("dev")' run # factory with args
flask run --host=0.0.0.0 --port 5001
flask --app hello run --debug --no-debugger --no-reload   # for IDE debuggers
flask shell
python -c 'import secrets; print(secrets.token_hex())'    # SECRET_KEY
```

## App skeleton (factory)

```python
import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev",
                            DATABASE=os.path.join(app.instance_path, "app.sqlite"))
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    from . import db, auth
    db.init_app(app)
    app.register_blueprint(auth.bp)
    return app
```

## Routing and responses

```python
@app.route("/post/<int:post_id>")          # string|int|float|path|uuid|any
@app.get("/login") / @app.post("/login")
@app.route("/users/", defaults={"page": 1})
@app.route("/users/page/<int:page>")

url_for("profile", username="John Doe")    # /user/John%20Doe
url_for(".index")                          # same blueprint
url_for("static", filename="style.css")
url_for("index", _external=True)           # needs SERVER_NAME outside a request

return "text"                              # 200 text/html
return {"k": "v"}                          # JSON
return render_template("404.html"), 404
return body, 201, {"X-Header": "v"}
resp = make_response(...); resp.set_cookie("k", "v", secure=True, httponly=True, samesite="Lax")
return redirect(url_for("login"))
abort(404, description="Resource not found")
```

## Request data

```python
request.method
request.form["username"]                   # missing -> 400
request.args.get("q", "")
request.files["file"].save(path)           # + secure_filename()
request.json                               # bad JSON 400, wrong content type 415
request.cookies.get("username")
request.form.get("a", type=int)
```

## Session, flash, g

```python
session["user_id"] = user["id"]; session.clear(); session.pop("k", None)
session["numbers"].append(42); session.modified = True   # mutations aren't tracked
session.permanent = True                    # uses PERMANENT_SESSION_LIFETIME
flash("Saved", "error"); get_flashed_messages(with_categories=True)
g.user = ...                                # lives for one app context
```

## Hooks

```python
@app.before_request          # return a value to short-circuit
@app.after_request           # def f(response): ...; return response
@app.teardown_request        # always runs, receives exc
@app.teardown_appcontext     # close DB connections here
@after_this_request          # inside a request; one-off response modifier
@app.context_processor       # return dict merged into template context
@app.template_filter("name")
@app.errorhandler(404) / app.register_error_handler(500, fn)
@bp.before_app_request       # blueprint hook that runs for every request
@app.url_value_preprocessor / @app.url_defaults
```

## Blueprints

```python
bp = Blueprint("auth", __name__, url_prefix="/auth",
               template_folder="templates", static_folder="static", cli_group=None)
parent.register_blueprint(child)            # nested: parent.child.*
app.register_blueprint(bp, url_prefix="/pages")
```

## Class-based views

```python
class ItemAPI(MethodView):
    init_every_request = False
    decorators = [login_required]
    def __init__(self, model): self.model = model
    def get(self, id): ...
    def patch(self, id): ...
    def delete(self, id): return "", 204

app.add_url_rule("/users/<int:id>", view_func=ItemAPI.as_view("users-item", User))
```

## Config loading

```python
app.config.from_object("pkg.default_settings")   # class: from_object(Cls()) for @property
app.config.from_envvar("YOURAPPLICATION_SETTINGS")
app.config.from_pyfile("application.cfg", silent=True)
app.config.from_file("config.toml", load=tomllib.load, text=False)
app.config.from_prefixed_env()                   # FLASK_SECRET_KEY -> SECRET_KEY; FLASK_A__b -> ["A"]["b"]
```

`.flaskenv` holds public values (`FLASK_APP`). `.env` holds private values
and is not committed. CLI > `.env` > `.flaskenv`. `FLASK_RUN_PORT=8000`.
`FLASK_SKIP_DOTENV=1`.

## CLI commands

```python
@app.cli.command("create-user")
@click.argument("name")
def create_user(name): ...

user_cli = AppGroup("user"); app.cli.add_command(user_cli)   # flask user create x
```

```toml
[project.entry-points."flask.commands"]
my-command = "my_extension.commands:cli"
```

## Testing

```python
client = app.test_client()
client.get("/posts", query_string={"k": "v"}, headers={})
client.post("/edit", data={"name": "x", "pic": open(p, "rb")})
client.post("/api", json={...}).json
client.get("/logout", follow_redirects=True).history
with client: client.post(...); assert session["user_id"] == 1
with client.session_transaction() as s: s["user_id"] = 1
runner = app.test_cli_runner(); runner.invoke(args=["hello", "--name", "Flask"]).output
with app.test_request_context("/x", method="POST", data={}): app.preprocess_request()
```

```
coverage run -m pytest && coverage report    # or: coverage html
```

## Production

```
pip install build && python -m build --wheel
gunicorn -w 4 'hello:create_app()'           # -k gevent, -b 0.0.0.0, --access-logfile=-
waitress-serve --host 127.0.0.1 --call hello:create_app
mod_wsgi-express start-server wsgi.py --processes 4
uwsgi --http 127.0.0.1:8000 --master -p 4 -w wsgi:app
hypercorn module:asgi_app                    # asgi_app = WsgiToAsgi(app)
```

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```

## Security baseline

```python
app.config.update(
    SECRET_KEY=..., SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax", TRUSTED_HOSTS=["example.com", ".example.com"],
    MAX_CONTENT_LENGTH=16 * 1000 * 1000,
)
response.headers["Content-Security-Policy"] = "default-src 'self'"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "SAMEORIGIN"
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

## Anti-patterns called out in the docs

- Running `flask run`, or the debugger, in production.
- Setting `DEBUG` in code instead of using `--debug`.
- Naming your module `flask.py`.
- Changing routes, config or blueprints after the first request, or from
  inside views.
- Storing `self.app` on an extension. Use `init_app` and `current_app`.
- Passing `current_app` (a proxy) as a signal sender.
- A catch-all `Exception` error handler that swallows HTTP errors.
- Forgetting the status code when returning from an error handler.
- Modifying the session or headers inside a streaming generator.
- Spawning `asyncio.create_task` background work from async views.
- Passing ORM objects to Celery tasks.
- String-formatting SQL, or trusting upload filenames.
- Unquoted Jinja expressions in HTML attributes.
- ProxyFix without a proxy, or with the wrong hop counts.
- Binding `0.0.0.0` behind a reverse proxy.
- Running WSGI servers as root.
