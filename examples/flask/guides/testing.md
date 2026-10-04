# Testing Flask applications

From the docs pages: Testing Flask Applications, Test Coverage (tutorial), The App and Request Context, Signals.

The docs use pytest (`pip install pytest`). Tests live in `tests/`, in
`test_*.py` modules, as `test_*` functions, optionally grouped in `Test*`
classes. Test your own code, not the libraries'. Extract complex logic into
functions you can test on their own.

## Fixtures (`tests/conftest.py`)

```python
import pytest
from my_project import create_app

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    # set up resources (e.g. create database)
    yield app
    # tear down resources

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
```

- `TESTING=True` propagates exceptions instead of running error handlers,
  and lets extensions adapt.
- The tutorial version creates a temporary database file with
  `tempfile.mkstemp()`, passes `{'TESTING': True, 'DATABASE': db_path}` to
  the factory, runs `init_db()` and seed SQL inside `app.app_context()`,
  and closes and unlinks the file after `yield`.

## Test client

- `client.get()`, `client.post()` and so on take `path`, `query_string={}`,
  `headers={}`, `data` or `json`. The full argument list is Werkzeug's
  `EnvironBuilder`.
- It returns a `TestResponse`:
  - `response.data` is bytes, so compare against bytes.
  - `response.text` or `get_data(as_text=True)` gives text.
  - Also: `response.json`, `status_code`, `headers["Location"]`.
- **Form data:** pass a dict to `data`. The content type is set
  automatically.
  - A file opened in `"rb"` becomes an upload. Pass
    `(file, filename, content_type)` to override those.
  - Files are closed for you.
  - Keep fixtures in `tests/resources`, located via
    `Path(__file__).parent / "resources"`.
- **JSON:** `json={...}` sets `application/json`.
- **Redirects:** use `follow_redirects=True`. `response.history` holds the
  intermediate responses, and `response.request.path` shows where you
  ended up.

## Sessions and context in tests

- Use `with client:` to keep the context active **after** the request, so
  you can assert on `session[...]` or `g`.
- `with client.session_transaction() as session:` sets session values
  *before* a request. The session is saved when the block exits.
- To test a function that needs a context without making a request:
  - `with app.app_context():` for database work.
  - `with app.test_request_context("/user/2/edit", method="POST", data={...}):`
    for code that reads `request`. It takes the same arguments as the
    client.
  - It **doesn't run** `before_request`. Call `app.preprocess_request()`
    yourself if needed.

## CLI runner

```python
@app.cli.command("hello")
@click.option("--name", default="World")
def hello_command(name):
    click.echo(f"Hello, {name}!")

def test_hello_command(runner):
    assert "World" in runner.invoke(args="hello").output
    assert "Flask" in runner.invoke(args=["hello", "--name", "Flask"]).output
```

To check that a command calls a function, use
`monkeypatch.setattr('flaskr.db.init_db', fake)` with a recorder.

## Patterns from the tutorial

- **AuthActions fixture:** a class wrapping `client.post('/auth/login', data=...)`
  and `client.get('/auth/logout')`, exposed as an `auth` fixture.
- **`pytest.mark.parametrize`** runs one test over many invalid inputs and
  expected messages, or over several protected paths (`/create`,
  `/1/update`, `/1/delete` must redirect to `/auth/login`).
- **Authorization tests:** change the post's author in the database, then
  assert that update and delete return 403 and that the edit link
  disappears. Missing ids return 404.
- **Factory test:** `assert not create_app().testing` and
  `assert create_app({'TESTING': True}).testing`.
- **DB lifecycle test:** `get_db()` returns the same connection inside one
  context, and using it after the context raises
  `sqlite3.ProgrammingError` containing "closed".

## Capturing rendered templates with signals

```python
@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
```

## Coverage

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["flaskr"]
```

- `pip install pytest coverage`
- `coverage run -m pytest`, then `coverage report` or `coverage html`
  (writes `htmlcov/index.html`). `pytest -v` lists each test.
- 100% coverage doesn't mean no bugs, and it doesn't test how users
  interact with the app in the browser.
