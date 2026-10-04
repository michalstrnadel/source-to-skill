# Extensions: using and writing them

From the docs pages: Extensions, Flask Extension Development.

## Using extensions

- Names are usually `Flask-Foo` or `Foo-Flask`. Search PyPI for the
  `Framework :: Flask` classifier.
- The typical shape: the extension reads its config from `app.config` and
  receives the app at init:

```python
from flask_foo import Foo
foo = Foo()
app = Flask(__name__)
app.config.update(FOO_BAR='baz', FOO_SPAM='eggs')
foo.init_app(app)
```

- Extensions the docs mention:
  - Flask-SQLAlchemy
  - Flask-Caching (Flask has no cache of its own)
  - Flask-WTF
  - Flask-MongoEngine
  - Flask-Talisman (security headers)
  - extensions for server-side sessions
- Extensions written before async support may not work with `async`
  views. Check their changelog.

## Writing an extension

**Naming:**

- Install names: `Flask-Name`, `flask-name-lower`, `Flask-ComboName` or
  `Name-Flask`.
- Import names: lowercase with underscores (`flask_name`,
  `flask_comboname`, `name_flask`).
- If you wrap a library, include its name and use the same case.

**The `init_app` pattern:**

```python
class HelloExtension:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(...)

hello = HelloExtension()          # importable before any app exists

def create_app():
    app = Flask(__name__)
    hello.init_app(app)
    return app
```

- **Never store the app** (`self.app = app`). Only touch the app inside
  `init_app`, and use `current_app` everywhere else. This keeps factories
  working, avoids circular imports, and makes per-config testing easy.
- Store per-app state in `app.extensions["<unique name>"]`. It's one shared
  namespace, so use the extension name without the `flask` prefix.

**Adding behavior:**

- Anything you can do on `Flask` works inside `init_app`.
- A common pairing: `before_request` sets something up and
  `teardown_request` cleans it up.
- A lazier alternative is an `ext.get_db()` method that connects on first
  use, so views that don't need it never connect.
- To add views, define a `Blueprint` and register it in `init_app`.

**Where configuration should live:**

| Level | Mechanism | For |
|---|---|---|
| Per app instance | `app.config`, keys prefixed with the extension name | Values that change per deployment, such as a database URL |
| Per extension instance | `__init__` arguments | How the extension is used; not per deployment |
| Per extension instance | Attributes or decorators (`ext.value = ...`, `@ext.register`) | Ergonomic setup after creation |
| Global | Class attributes (`Ext.connection_class`) | Defaults without subclassing |
| Advanced | Subclassing and overriding | Deep customization |

`Flask` itself uses all of these. Never change config after setup.

**Request data in `g`:** it's a single namespace, so prefix your keys
(`g._hello_user_id`) or use a namespace (`g._hello = SimpleNamespace()`).
`g` lives for one app context. Close resources in `teardown_appcontext`,
or in `teardown_request` if they only exist during requests.

**Views that need models defined later**, such as a Flask-SQLAlchemy
`db.Model`:

- Create the model in `__init__(self, db)` and pass it to
  `PostAPI.as_view(model=...)` in `init_app`.
- Or keep it on the extension and read
  `current_app.extensions["simple_blog"].post_model`.
- Or provide a base class (`blog.BasePost`) that users subclass and
  assign.

No option is perfect. Each is a trade-off.

## Recommended guidelines (formerly "approved extensions")

1. **A maintainer.** If the author leaves, transfer the repo, docs and PyPI
   access. Pallets-Eco offers community maintenance.
2. **Naming:** `Flask-ExtensionName` or `ExtensionName-Flask`, with
   exactly one package or module named `flask_extension_name`.
3. **An open source license.** BSD or MIT are preferred.
4. **The API must support:**
   - multiple apps in one process (`current_app`, state stored per app)
   - the factory pattern (`ext.init_app()`)
5. **Installable** in editable mode from a clone with `pip install -e .`.
6. **Tests** runnable with `tox -e py`, `nox -s test` or `pytest`, and
   included in the sdist. Without tox, list test deps in a requirements
   file.
7. **A docs link** in the PyPI metadata or README. The Flask theme from
   Pallets-Sphinx-Themes is preferred.
8. **Dependencies:** lower bounds only (for example `sqlalchemy>=1.4`), no
   upper bounds.
9. **`python_requires=">=version"`.** Pallets supports every Python
   version that is not within 6 months of end of life.

Discuss designs early on the Pallets Discord or GitHub Discussions, so
extensions share common patterns.
