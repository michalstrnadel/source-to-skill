# Patterns for Flask

From the docs section "Patterns for Flask": SQLite 3, SQLAlchemy, MongoEngine, Uploading Files, Background Tasks with Celery, Caching, Form Validation with WTForms, Request Content Checksums, Single-Page Applications. Patterns covered in other guides: packages, factories, dispatching (app-structure.md); URL processors, view decorators, lazy views, method overrides, deferred callbacks (routing-and-views.md); template inheritance, flashing, JavaScript, streaming, favicon (templates-and-frontend.md).

## SQLite 3

```python
import sqlite3
from flask import g

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:      # teardown runs even if setup never happened
        db.close()
```

- It connects on first use. Outside a request, use
  `with app.app_context():`.
- **Rows as dicts:** use a custom `row_factory`, or
  `db.row_factory = sqlite3.Row`, which allows access by index and by name.
- **Helper:** `query_db(query, args=(), one=False)` runs `execute`,
  `fetchall` and `close`, and returns the first row or `None` when
  `one=True`.
- **Always use `?` placeholders.** String formatting allows SQL injection.
- **Schema:** `init_db()` runs inside an app context and executes
  `app.open_resource('schema.sql', mode='r')` with `executescript`, then
  commits.
- SQLite writes are serialized. That's fine for small apps. Switch
  databases as you grow (tutorial note).

## SQLAlchemy

There are four approaches. A package layout with models in their own module
is recommended.

1. **Flask-SQLAlchemy:** the recommended quick start.
2. **Declarative:**
   - `database.py` sets up the engine,
     `scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))`,
     `Base = declarative_base()`, `Base.query = db_session.query_property()`,
     and an `init_db()` that imports the models modules, then calls
     `Base.metadata.create_all(bind=engine)`.
   - Remove the session per app context:

     ```python
     @app.teardown_appcontext
     def shutdown_session(exception=None):
         db_session.remove()
     ```

   - `scoped_session` takes care of threads, so `g` isn't needed.
3. **Manual ORM mapping:** separate `Table` and class definitions, joined
   with `mapper(User, users)`. More flexible, more typing. Teardown is the
   same.
4. **SQL abstraction layer only:** `engine` plus `MetaData`. Use
   `Table('users', metadata, autoload=True)`, then `users.insert()` and
   `users.select(...)`.

## MongoDB with MongoEngine

- `pip install flask-mongoengine`, set
  `app.config['MONGODB_SETTINGS'] = {"db": "myapp"}`, then
  `db = MongoEngine(app)`.
- Models subclass `me.Document`. Nested fields use `EmbeddedDocument`
  together with `EmbeddedDocumentField`.
- Save with `doc.save()`. Query with
  `Movie.objects(title=...).get_or_404()`. Operators go after a double
  underscore: `actors__in`, `year__gte`.

## File uploads

1. The form needs `enctype=multipart/form-data` and an
   `<input type=file>`.
2. Read the file from `request.files['file']`.
3. Check that the part exists and that `file.filename != ''`, because the
   browser sends an empty part when nothing is selected.
4. Check an `ALLOWED_EXTENSIONS` set.
5. Save with
   `file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))`.

- **Serve uploads:** `send_from_directory(app.config["UPLOAD_FOLDER"], name)`.
  If the web server serves them instead, register the endpoint with
  `build_only=True` so `url_for` still works.
- **Storage:** small uploads stay in memory, larger ones go to
  `tempfile.gettempdir()`. Flask accepts unlimited sizes unless
  `MAX_CONTENT_LENGTH` is set (then 413).
- **Progress bars:** use client-side JavaScript form plugins, not
  server-side polling of chunked reads. Upload extensions also exist.

## Background tasks with Celery

```python
from celery import Celery, Task

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
```

- **Config:**
  `CELERY=dict(broker_url="redis://localhost", result_backend="redis://localhost", task_ignore_result=True)`.
  This ignores results by default, so opt in per task with
  `@shared_task(ignore_result=False)`.
- **With a factory:** call `celery_init_app(app)` in `create_app`. Add a
  `make_celery.py` containing
  `celery_app = create_app().extensions["celery"]`, then run
  `celery -A make_celery worker --loglevel INFO` (and `beat` for
  schedules).
- **Use `@shared_task`, not `@celery_app.task`.** The latter ties tasks to
  one app instance and needs the object at import time.
- **Call** `task.delay(a, b)` and return `{"result_id": result.id}`. Poll a
  `/result/<id>` route that uses `AsyncResult(id)` with `.ready()`,
  `.successful()` and `.result`.
- **Pass minimal, serializable data**, such as ids, never ORM objects:
  `generate_user_archive.delay(current_user.id)`.
- The repository's `examples/celery` shows JavaScript submitting tasks and
  polling for results.

## Caching

Flask has no cache. Use Flask-Caching, which supports several backends or
a custom one. See the `cached` view decorator in routing-and-views.md.

## WTForms

- Define forms as classes, for example a `RegistrationForm` with
  `StringField`, `PasswordField`, `BooleanField` and validators like
  `Length`, `DataRequired` and `EqualTo('confirm')`.
- In the view, build the form from `request.form` (POST) or `request.args`
  (GET), then check `request.method == 'POST' and form.validate()` and
  read `form.<name>.data`.
- In templates, a `render_field(field)` macro renders the label, the field
  (`field(**kwargs)|safe`, where kwargs become HTML attributes) and its
  errors.
- Flask-WTF adds helpers on top.

## Request content checksums

Wrap `environ['wsgi.input']` in a stream whose `read` and `readline` feed
`hashlib.sha1()`. Install the wrapper before anything reads the body,
including `request.form` and `before_request` handlers. Read
`hash.hexdigest()` after accessing `request.files` or `request.form`.

## Single-page applications

```python
app = Flask(__name__, static_folder='app', static_url_path="/app")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return app.send_static_file("index.html")
```

API routes such as `/heartbeat` sit next to the catch-all route.
