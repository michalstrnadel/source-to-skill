# The Flaskr tutorial (in reading order)

From the docs Tutorial section. The tutorial's toctree order is: layout, factory, database, views, templates, static, blog, install, tests, deploy, next. The extractor emitted these pages in filename order, so they are re-ordered here.

Flaskr is a small blog. Users register, log in, and create, edit and delete
their own posts. The finished project is in the repository under
`examples/tutorial`. The tutorial uses only Flask and Python, no
extensions.

## 1. Project layout

- `flask-tutorial/` contains the `flaskr/` package, `tests/`, `.venv/` and
  `pyproject.toml`.
- Ignore these in git: `.venv/`, `*.pyc`, `__pycache__/`, `instance/`,
  `.pytest_cache/`, `.coverage`, `htmlcov/`.
- The final package contains `__init__.py`, `db.py`, `schema.sql`,
  `auth.py`, `blog.py`, `templates/` (`base.html`, `auth/`, `blog/`) and
  `static/style.css`.

## 2. Application factory (`flaskr/__init__.py`)

```python
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    return app
```

Run it with `flask --app flaskr run --debug` from `flask-tutorial/`, not
from inside the package.

## 3. Database (`flaskr/db.py`)

- `get_db()` caches a `sqlite3.connect(current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)`
  connection on `g.db`, with `row_factory = sqlite3.Row`. `close_db()`
  pops it from `g` and closes it.
- `schema.sql` drops and recreates two tables:
  - `user`: id, unique username, password
  - `post`: id, author_id foreign key, created timestamp defaulting to
    `CURRENT_TIMESTAMP`, title, body
- `init_db()` runs the schema through `current_app.open_resource`. The
  Click command `init-db` wraps it.
- `sqlite3.register_converter("timestamp", ...)` parses timestamps into
  `datetime`.
- `init_app(app)` calls `app.teardown_appcontext(close_db)` and
  `app.cli.add_command(init_db_command)`. Call it from the factory.
- `flask --app flaskr init-db` creates `instance/flaskr.sqlite`.

## 4. Blueprints and views (`flaskr/auth.py`)

- `bp = Blueprint('auth', __name__, url_prefix='/auth')`, registered in the
  factory.
- **register:**
  - validate that the username and password aren't empty
  - `INSERT` with `?` placeholders and `generate_password_hash(password)`
  - catch `db.IntegrityError` and report "User {username} is already
    registered."
  - redirect to `url_for("auth.login")`
  - otherwise call `flash(error)`
- **login:**
  - look up the user and compare with `check_password_hash`
  - on success: `session.clear()`, `session['user_id'] = user['id']`,
    redirect to `index`
- **`@bp.before_app_request` `load_logged_in_user`** sets `g.user` from
  `session['user_id']` on *every* request, or `None`.
- **logout:** `session.clear()`.
- **`login_required` decorator:** redirects to `auth.login` when
  `g.user is None`. Uses `functools.wraps`.
- **Endpoints:** a blueprint view's endpoint is `blueprint.function`,
  for example `auth.login`.

## 5. Templates

- `base.html`:
  - a nav that shows the username and Log Out when `g.user` is set,
    otherwise Register and Log In
  - a loop over `get_flashed_messages()`
  - blocks `title`, `header` and `content`
- Blueprint templates live in folders named after the blueprint
  (`auth/register.html`, `auth/login.html`).
- The `required` attribute is only a client-side convenience. **Always
  validate on the server too.**

## 6. Static files

Flask serves `flaskr/static/` automatically. Link files with
`url_for('static', filename='style.css')`. If a change doesn't show, clear
the browser cache.

## 7. Blog blueprint (`flaskr/blog.py`)

- `bp = Blueprint('blog', __name__)` has **no url_prefix**, so the index is
  `/`.
- `app.add_url_rule('/', endpoint='index')` makes `url_for('index')` and
  `url_for('blog.index')` produce the same URL.
- **index:** posts `JOIN` users, ordered by `created DESC`. It shows an
  Edit link only to the author. `loop.last` skips the final `<hr>`.
- **create**, `@login_required`: a required title, then `INSERT`, then
  redirect to `blog.index`.
- **`get_post(id, check_author=True)`:**
  `abort(404, f"Post id {id} doesn't exist.")` for missing posts, and
  `abort(403)` for someone else's.
- **update**, on `/<int:id>/update`: the form uses
  `{{ request.form['title'] or post['title'] }}` so invalid submissions
  keep the user's input.
- **delete**, POST-only on `/<int:id>/delete`: triggered by a second form
  in `update.html` with a JavaScript `confirm()`.

## 8. Make it installable

- `pyproject.toml` (`[project] name="flaskr"`, `version="1.0.0"`,
  `dependencies=["flask"]`, `flit_core<4` backend), then `pip install -e .`
  (editable mode).
- The tutorial notes this comes late in the tutorial, but new projects
  should always start with it.

## 9. Tests

See guides/testing.md: the temporary-database `app` fixture, the
`AuthActions` fixture, parametrized validation tests, and
`coverage run -m pytest`.

## 10. Deploy

See guides/deployment.md: build a wheel, install it, run `init-db` again
(instance folder at `.venv/var/flaskr-instance`), set a real `SECRET_KEY`
in the instance `config.py`, then
`waitress-serve --call 'flaskr:create_app'`.

## 11. Ideas to extend it

- a detail view per post
- like/unlike
- comments
- tags
- search
- pagination (5 per page)
- an image upload per post
- Markdown formatting
- an RSS feed
