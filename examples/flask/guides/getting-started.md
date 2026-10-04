# Getting started

From the docs pages: Installation, Quickstart, Development Server, Welcome to Flask.

## Installation

- Python 3.10+ is supported. The docs recommend the latest Python.
- **Installed automatically:** Werkzeug (WSGI), Jinja (templates), MarkupSafe
  (escaping untrusted input), ItsDangerous (signing data, protects the
  session cookie), Click (the `flask` command and custom commands), Blinker
  (signals).
- **Optional, detected if present:** `python-dotenv` (loads `.env` and
  `.flaskenv` for `flask` commands) and `watchdog` (a faster reloader).
- **gevent** needs greenlet >= 1.0. On PyPy, PyPy >= 7.3.7 is needed. These
  mark the first versions with the needed features, not supported minimums.
  Use the latest versions.
- **Always use a virtual environment.** Each project gets its own isolated
  set of libraries.

```
mkdir myproject && cd myproject
python3 -m venv .venv          # Windows: py -3 -m venv .venv
. .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install Flask
```

## The minimal app, explained

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
```

1. An instance of `Flask` is the WSGI application.
2. The first argument is the module or package name. `__name__` fits most
   cases. Flask uses it to locate templates and static files.
3. `route()` binds a URL to the function.
4. The return value is the response body. The default content type is HTML.

Don't call the file `flask.py`, because it conflicts with Flask itself.
Run it with `flask --app hello run` or `python -m flask --app hello run`.
A file named `app.py` or `wsgi.py` doesn't need `--app`.

## Development server

- `flask run` is the recommended way to run the dev server. Add `--debug`
  to enable the interactive debugger and the reloader.
- **Never use it in production.** It isn't designed to be efficient,
  stable or secure. The debugger executes arbitrary Python from the
  browser. It is PIN-protected, but that is still a major risk.
- By default only your own machine can reach the server. Add
  `--host=0.0.0.0` to listen on all public IPs, but only with the debugger
  disabled or on a trusted network.
- **Port in use:** you get `OSError: [Errno 98] Address already in use` (or
  `[WinError 10013]` on Windows). Find the process with
  `netstat -nlp | grep 5000` or `lsof -P -i :5000` (Windows:
  `netstat -ano | findstr 5000`), or pick another port with
  `flask run --port 5001`. On macOS Monterey and later, the AirPlay
  Receiver service takes port 5000. Disable it in System Settings.
- **Deferred errors on reload:** with the reloader on, a syntax error added
  while the server runs shows up in the debugger on the next page load
  instead of crashing the server. A syntax error that is already present at
  startup fails immediately with a traceback.
- **From code:** `app.run(debug=True)` inside `if __name__ == "__main__":`.
  Without that guard it interferes with production servers that import the
  app. Unlike the CLI, this version crashes on errors during reload.

## Where the docs go next

- The tutorial builds a complete small app (Flaskr). See
  guides/tutorial-flaskr.md.
- The Patterns section collects common recipes. See guides/patterns.md.
- Flask's behavior also depends on Werkzeug, Jinja and Click. Check their
  docs too.
