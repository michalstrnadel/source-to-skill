# Deploying to production, async and concurrency

From the docs pages: Deploying to Production, Gunicorn, Waitress, mod_wsgi, uWSGI, gevent, eventlet, ASGI, nginx, Apache httpd, Tell Flask it is Behind a Proxy, Using async and await, Async with Gevent, Deploy to Production (tutorial).

"Production" means "not development", even for a single private user.
**Never use the dev server, debugger or reloader there.** Flask is a WSGI
*application*. A WSGI *server* converts HTTP to `environ` and back. A
dedicated HTTP server in front of it (a "reverse proxy") handles TLS and
security and performance concerns.

## Choosing a WSGI server

| Server | Strengths | Limits |
|---|---|---|
| Gunicorn | Pure Python, easy install, integrates with hosting platforms, gevent workers built in | No Windows (works under WSL) |
| Waitress | Pure Python, easy config, **supports Windows** | No request streaming (bodies fully buffered); one process with threads |
| mod_wsgi | Tight Apache integration, supports Windows, no reverse proxy needed, can bind 80/443 as root and drop privileges | Needs a compiler and Apache dev headers |
| uWSGI | Compiled, very fast, extensive features | Complex to configure; no Windows (works under WSL); may need a compiler |
| gevent | Many concurrent connections | The docs prefer Gunicorn or uWSGI with gevent workers |
| eventlet | - | **No longer maintained**; use gevent |

Install pattern for all of them:

```
python -m venv .venv
. .venv/bin/activate
pip install .            # your app
pip install <server>
```

## Commands

```
gunicorn -w 4 'hello:app'                 # from hello import app
gunicorn -w 4 'hello:create_app()'        # factory call
gunicorn -k gevent 'hello:create_app()'   # async worker
waitress-serve --host 127.0.0.1 hello:app
waitress-serve --host 127.0.0.1 --call hello:create_app
mod_wsgi-express start-server wsgi.py --processes 4   # wsgi.py defines `application`
uwsgi --http 127.0.0.1:8000 --master -p 4 -w hello:app
uwsgi --http 127.0.0.1:8000 --master --gevent 100 -w wsgi:app
```

- **Worker count:** a starting value is `CPU * 2`. Gunicorn's default is 1
  worker, which is probably not what you want with the sync worker type.
- **Default ports:** Gunicorn and uWSGI in these examples use 8000.
  Waitress serves on 8080.
- Gunicorn shows no access logs by default. Add `--access-logfile=-`.
  Waitress shows only errors and is configured through Python. mod_wsgi
  writes errors to the log file it names at startup.
- **mod_wsgi needs a variable named `application`:** `application = app`
  or `application = create_app()`. uWSGI with a factory needs a small
  `wsgi.py` that calls it.
- **Binding:** don't run Gunicorn, Waitress, uWSGI or gevent as root. It
  would run your app as root. Use a reverse proxy for ports 80 and 443.
  Binding `0.0.0.0` exposes the app on all IPs, but don't do that behind a
  proxy, because clients could bypass it. mod_wsgi can start as root with
  `--user hello --group hello --port 80`.
- **gevent server directly:**
  `WSGIServer(("127.0.0.1", 8000), app).serve_forever()` in `wsgi.py`. It
  prints nothing on start.
- **ASGI servers:** wrap the app with `asgi_app = WsgiToAsgi(app)` (from
  asgiref) and serve it with, for example, `hypercorn module:asgi_app`.

## Reverse proxy

nginx (`/etc/nginx/nginx.conf`), assuming the WSGI server is on
127.0.0.1:8000:

```nginx
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Prefix /;
    }
}
```

Apache httpd: load `mod_proxy` and `mod_proxy_http`, add
`ProxyPass / http://127.0.0.1:8000/` and
`RequestHeader set X-Forwarded-Proto http` and `X-Forwarded-Prefix /`.
`ProxyPass` sets `X-Forwarded-For` and `X-Forwarded-Host` itself. For
local testing, add `127.0.0.1 hello.localhost` to `/etc/hosts`.

**Then tell Flask it is behind a proxy:**

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```

Use it only when there really is a proxy, and set the number of proxies
that set each header. Clients can fake these headers, so a wrong count is a
security problem. Most hosting platforms need ProxyFix too.

## Hosting platforms named in the docs

PythonAnywhere, Google App Engine, Google Cloud Run, AWS Elastic
Beanstalk, Microsoft Azure. The list isn't exhaustive. Compare
capabilities, configuration, pricing and support.

## Deploying a packaged app (tutorial flow)

1. `pip install build`, then `python -m build --wheel`. This produces
   `dist/flaskr-1.0.0-py3-none-any.whl`.
2. On the server: create a virtualenv, then
   `pip install flaskr-1.0.0-py3-none-any.whl`.
3. Re-run `flask --app flaskr init-db`. An installed app uses
   `.venv/var/flaskr-instance` as its instance folder.
4. Put a real `SECRET_KEY` in `<instance>/config.py`, generated with
   `python -c 'import secrets; print(secrets.token_hex())'`.
5. `pip install waitress`, then `waitress-serve --call 'flaskr:create_app'`.

## async/await (Flask 2.0+)

- `pip install flask[async]`. Routes, error handlers, before/after-request
  and teardown functions, `View.dispatch_request` and `MethodView`
  handlers can all be `async def`.
- **How it runs:** each request starts an event loop in a thread and still
  occupies one worker. Throughput stays the same. The gain is concurrent
  I/O *inside* a view. **Async isn't inherently faster.** It helps
  IO-bound concurrent work, not CPU-bound work.
- **Background tasks don't survive.** The loop stops when the view
  finishes, so `asyncio.create_task` work gets cancelled. Use a task queue,
  or an ASGI server with `WsgiToAsgi`, whose loop runs continuously.
- **Use Quart** (an ASGI reimplementation of Flask) for mainly-async
  codebases, many concurrent or long requests, or websockets.
- **Extensions** written before async support may not await views. They
  can support async with `current_app.ensure_sync(func)(*args, **kwargs)`.
- Only `asyncio` is supported. Override `Flask.ensure_sync` to use another
  library.

## gevent

- Gevent patches the stdlib to run in greenlets. It's a reliable way to
  hold many long-lived connections without `async def`.
- Call `gevent.monkey.patch_all()` **as early as possible**, at the top of
  the main module or package `__init__.py`.
- For libuv, set `gevent.config.loop = "libuv"` *before* patching. Use
  gevent's libuv support, not uvloop.
- Use `gevent.spawn(fn, ...)` for concurrent work inside views. Pass the
  data the function needs. If it needs `request`, wrap it with
  `stream_with_context` or `copy_current_request_context`.
- **Mixing with asyncio:** subclass `Flask` and override `async_to_sync`.
  Run an `asyncio.EventLoop()` via `gevent.spawn(loop.run_forever)` and
  submit coroutines with `asyncio.run_coroutine_threadsafe(coro, loop).result()`.
