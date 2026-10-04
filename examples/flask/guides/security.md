# Security considerations

From the docs pages: Security Considerations, Uploading Files, Quickstart (Sessions, HTML Escaping), Configuration Handling.

Flask handles some security issues by default. Others depend on your
application and threat model, and many hosting platforms handle some of
them for you.

## Resource use (DoS)

| Limit | Default | Effect |
|---|---|---|
| `MAX_CONTENT_LENGTH` / `request.max_content_length` | unset | Bytes read per request. Truly unbounded streams are still blocked unless the WSGI server signals support. |
| `MAX_FORM_MEMORY_SIZE` / `request.max_form_memory_size` | 500 kB | Maximum size of a non-file multipart field |
| `MAX_FORM_PARTS` / `request.max_form_parts` | 1000 | Maximum number of multipart fields. With the default field size, a form tops out at about 500 MB of memory. |

Exceeding a limit returns 413. Also set limits in the OS, container, WSGI
server, HTTP server and hosting platform. For uploads,
`app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000` caps the body at
16 MB. On the dev server you may see a connection reset instead of the 413.

## XSS

- Jinja autoescapes values. You still need care when:
  - generating HTML without Jinja
  - calling `Markup` on user data
  - serving uploaded HTML (send `Content-Disposition: attachment`)
  - serving uploaded text files, which some browsers content-sniff into HTML
- **Always quote attributes** that contain Jinja expressions:
  `<input value="{{ value }}">`. Without quotes, an attacker can inject
  `onmouseover=...` handlers.
- Escaping **doesn't stop `javascript:` URIs** in `href`. Use a
  Content-Security-Policy header.
- Restrict upload extensions so users can't upload HTML (XSS) or `.php`
  files that the server would execute.

## CSRF

- Cookie-based auth means other sites can trigger state-changing requests.
- The fix: a one-time token stored in the cookie **and** sent with the
  form, compared on the server.
- Flask doesn't do this itself because it has no form validation
  framework. Use a form library or extension (the WTForms pattern points to
  Flask-WTF).

## JSON

Since Flask 0.10, `jsonify` serializes top-level arrays. The old
ECMAScript 4 vulnerability only affects extremely old browsers.

## Security headers

Flask-Talisman can manage HTTPS and these headers:

```python
response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
response.headers['Content-Security-Policy'] = "default-src 'self'"   # very strict
response.headers['X-Content-Type-Options'] = 'nosniff'
response.headers['X-Frame-Options'] = 'SAMEORIGIN'                   # anti-clickjacking
```

## Cookies

- `Secure` (HTTPS only), `HttpOnly` (no JavaScript access), and
  `SameSite`. `'Lax'` is recommended: it blocks cookies on CSRF-prone
  cross-site requests such as form posts. `'Strict'` blocks them on all
  external requests, including normal links.

```python
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax')
response.set_cookie('username', 'flask', secure=True, httponly=True, samesite='Lax')
response.set_cookie('snakes', '3', max_age=600)   # expires in 10 minutes
```

- Without `Expires` or `Max-Age`, the cookie is deleted when the browser
  closes.
- **Permanent sessions** use `PERMANENT_SESSION_LIFETIME`, and the
  signature age is validated against it. Lowering it, for example to
  `600`, helps against replay attacks. On login: `session.clear()`, set
  the user id, then `session.permanent = True`.
- To sign other values, use `itsdangerous.TimedSerializer`.

## Sessions and secrets

- The session cookie is **signed, not encrypted**. Users can read it but
  can't change it without `SECRET_KEY`.
- Generate the key with
  `python -c 'import secrets; print(secrets.token_hex())'`. Never reveal or
  commit it.
- Rotate keys with `SECRET_KEY_FALLBACKS`.
- The tutorial's `'dev'` key must be replaced in production, because
  anyone could forge sessions with the public value.
- Values that don't persist across requests may mean the cookie is over
  the browser's size limit. `MAX_COOKIE_SIZE` (4093) warns about this.

## Host header

By default any `Host` is accepted, and attackers can set it outside
browsers. Set `TRUSTED_HOSTS` in production, because it affects
`url_for(..., _external=True)`. Use ProxyFix to say which proxy values to
trust.

## Other rules from across the docs

- **Uploaded filenames:** always use `secure_filename()`.
  `'../../../../home/username/.bashrc'` becomes `'home_username_.bashrc'`.
- **SQL:** use `?` placeholders with an argument tuple, never string
  formatting.
- **Passwords:** store `werkzeug.security.generate_password_hash(...)` and
  check with `check_password_hash`.
- **Copy/paste to terminal:** hidden `\b` characters render differently in
  HTML than in a terminal (`import y\bose\bm\bi\bt\be\b` shows as
  `import yosemite` but runs `import os`). Strip them with
  `body.replace("\b", "")` if users copy code from your site.
- **The debugger** allows arbitrary code execution. Never expose it.
- **ProxyFix** with the wrong proxy count trusts forged headers.
