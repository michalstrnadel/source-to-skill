# Security Policy

## Supported versions

Only the latest minor release line receives security fixes. Upgrade to the
newest release (or the current `main` of the plugin) before reporting.

| Version          | Supported |
| ---------------- | --------- |
| latest minor     | yes       |
| anything older   | no        |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately through GitHub's security advisories:
<https://github.com/michalstrnadel/source-to-skill/security/advisories/new>

Include the affected version, the source (URL or file) or a minimal
reproducer, and the impact you observed. You should get an acknowledgement
within a few days; fixes are released as a patch version and credited in the
advisory unless you prefer otherwise.

## Threat surface

source-to-skill processes content you point it at, which is untrusted by
definition. Areas we treat as security-relevant:

- **Untrusted archives** — GitHub repo tarballs are extracted with
  path-traversal-safe handling (no absolute paths, no `..` escapes, no
  links pointing outside the destination). Any bypass is a vulnerability.
- **Untrusted HTML** — web articles are parsed, never executed or rendered;
  only text is kept. Parser crashes or resource exhaustion on hostile pages
  are in scope.
- **Downloaded media and documents** — audio/video (yt-dlp, local Whisper),
  PDFs and EPUBs (PyMuPDF / stdlib zip+XML) come from third parties.
  Vulnerabilities in those libraries should go upstream, but unsafe use of
  them here (e.g. writing outside the work dir, unbounded downloads) is in
  scope.
- **Local paths** — extraction writes only into its work directory and the
  install destination you choose.

## Prompt injection: review generated skills

A generated skill is derived from untrusted content. A transcript, paper,
article, or README can contain text written to manipulate an agent
("ignore previous instructions…", hidden instructions to run commands or
exfiltrate data), and your agent may carry that into the generated
`SKILL.md` or its support files.

**Review a generated skill before installing it**, especially its
`SKILL.md` description and any instructions, scripts, or tool permissions
it contains. Treat a skill made from a source you don't trust the same way
you would treat code from that source. Reports of extraction or template
behavior that makes such injection easier are welcome via the private
channel above.
