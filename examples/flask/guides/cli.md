# The `flask` command line

From the docs pages: Command Line Interface, Working with the Shell, Development Server.

Installing Flask installs the `flask` script, a Click CLI. `--help` works
on every command.

## Application discovery (`--app`)

| Value | Meaning |
|---|---|
| (unset) | Import `app` or `wsgi` (`.py` file or package), then detect an instance named `app` or `application`, or a factory named `create_app` or `make_app` |
| `--app hello` | Import `hello`, with the same detection |
| `--app src/hello` | Change the working directory to `src`, then import `hello` |
| `--app hello.web` | Dotted import path |
| `--app hello:app2` | Use the instance named `app2` |
| `--app 'hello:create_app("dev")'` | Call the factory. Arguments are parsed as Python literals, so strings need quotes |

Detection order inside the import: an instance named `app` or
`application`, then any instance, then a factory named `create_app` or
`make_app`.

## Running

- `flask --app hello run`. `--debug` enables the debugger and reloader. It
  can go before or after `run`. `--debug` on the top-level `flask` command
  applies to every command.
- `--extra-files a:dir/b` makes the reloader watch more files.
  `--exclude-patterns` ignores files (fnmatch patterns). Separate entries
  with `:`, or `;` on Windows.
- `--port`, `--host`. External debuggers need
  `--debug --no-debugger --no-reload`.

## Environment variables and dotenv

- Every option can come from the environment:
  - `FLASK_OPTION`, for example `FLASK_APP`
  - `FLASK_COMMAND_OPTION`, for example `FLASK_RUN_PORT=8000`
- With `python-dotenv` installed, `flask` loads `.env` and `.flaskenv`.
  Precedence: command line > `.env` > `.flaskenv`.
  - `.flaskenv` holds public values such as `FLASK_APP` and is committed.
  - `.env` holds private values and is **not** committed.
  - `flask` searches for the files upward from the current directory.
  - `--env-file` loads an extra file.
- The files are only loaded by `flask` or `app.run()`. In production, call
  `flask.cli.load_dotenv()` yourself.
- Without python-dotenv, Flask prints a tip if dotenv files exist.
  `FLASK_SKIP_DOTENV=1` disables loading. The variables must be set before
  the app loads.
- The alternative is to export variables at the end of the virtualenv's
  `activate` script. The docs prefer dotenv because `.flaskenv` travels
  with the repo.

## Custom commands

```python
import click

@app.cli.command("create-user")
@click.argument("name")
def create_user(name): ...
# flask create-user admin
```

- **Groups:** `user_cli = AppGroup('user')`, `@user_cli.command('create')`,
  then `app.cli.add_command(user_cli)`. Run it as `flask user create demo`.
- **Blueprint commands:** `@bp.cli.command('create')` is nested under the
  blueprint name. Change the group with `cli_group='other'` (on the
  `Blueprint` or in `register_blueprint`), or flatten it with
  `cli_group=None`.
- **App context:** commands registered via `app.cli` or a `FlaskGroup`
  run with an app context pushed. For plain Click commands, use
  `@with_appcontext`.
- **Plugins:** an extension can add commands through the
  `flask.commands` entry point in `pyproject.toml`:
  ```toml
  [project.entry-points."flask.commands"]
  my-command = "my_extension.commands:cli"
  ```
- **Custom scripts:** `@click.group(cls=FlaskGroup, create_app=create_app)`
  plus `[project.scripts] wiki = "wiki:cli"`, then `pip install -e .`. Now
  `wiki run` works without `--app`. Drawback: an error in module-level
  code breaks the reloader, because the entry point can no longer load.
  The docs recommend the plain `flask` command in most cases.
- Test commands with `app.test_cli_runner()` (see guides/testing.md).

## Shell

- `flask shell` opens Python with an app context active and the app
  imported. `@app.shell_context_processor` adds more automatic imports.
- The shell has no request. Create one with
  `ctx = app.test_request_context(); ctx.push()` ... `ctx.pop()`.
- That doesn't run hooks. Call `app.preprocess_request()` (if it returns a
  response, ignore it). For after-request functions, call
  `app.process_response(app.response_class())` before `ctx.pop()`.
  Teardown runs on pop.
- Put helpers in a module (for example `shelltools`) and star-import them.

## PyCharm

The Community Edition needs a custom Python run configuration:

- Module name: `flask`
- Parameters: `--app hello run --debug`

Copy the configuration for other commands. If the project is installed as
a package, uncheck the PYTHONPATH options to match deployment.
