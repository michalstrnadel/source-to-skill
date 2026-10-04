# Chapter 8 — Customizing Git

*Load this when you need to tune Git's behaviour: config levels and useful keys, line endings and whitespace, external diff/merge tools, per-path `.gitattributes` (binary handling, textconv diffs, clean/smudge filters, archive export, merge drivers), client- and server-side hooks, or building a push policy with an `update` hook.*

Git has three ways to customize it: **configuration** (`git config`, global behaviour), **attributes** (`.gitattributes`, per-path behaviour), and **hooks** (scripts fired on events). Pick the lightest one that does the job.

## Configuration levels

| Level | File | Flag | Scope |
|---|---|---|---|
| system | `[path]/etc/gitconfig` | `--system` | every user, every repo on the machine |
| global | `~/.gitconfig` or `~/.config/git/config` | `--global` | one user, all their repos |
| local | `.git/config` in the repo | `--local` (the default) | that one repository |

- Later levels override earlier ones: local beats global beats system.
- The files are plain text; you may edit them by hand, but `git config` is usually easier.
- Full list of recognized keys: `man git-config` or https://git-scm.com/docs/git-config. For advanced setups, look up "Conditional includes" there.
- Options split into client-side (the vast majority — personal preferences) and server-side (a handful, mostly `receive.*`).

## Useful client-side keys

| Key | What it does | Example |
|---|---|---|
| `core.editor` | Editor for commit/tag messages. Without it Git uses `$VISUAL` or `$EDITOR`, falling back to `vi`. | `git config --global core.editor emacs` |
| `commit.template` | File used as the starting text of every commit message. | `git config --global commit.template ~/.gitmessage.txt` |
| `core.pager` | Pager for `log`, `diff`, etc. Default is `less`; empty string disables paging (full output printed). | `git config --global core.pager ''` |
| `user.signingkey` | GPG key ID so `git tag -s <tag-name>` needs no key argument. | `git config --global user.signingkey <gpg-key-id>` |
| `core.excludesfile` | A global ignore file applied to all your repos. | `git config --global core.excludesfile ~/.gitignore_global` |
| `help.autocorrect` | Auto-run the single most similar command for a typo. Value is in **tenths of a second** of delay. | `1` = 0.1 s; `50` = 5 s to cancel |

**Commit template pattern.** A template file such as:

```
Subject line (try to keep under 50 characters)

Multi-line description of commit,
feel free to be detailed.

[Ticket: X]
```

reminds committers to keep the subject short (it is what `git log --oneline` shows), add detail below, and cite a ticket. Installing a team template on each machine raises the odds a commit-message policy is actually followed.

**Global ignore example** (`~/.gitignore_global`) for OS/editor droppings:

```
*~
.*.swp
.DS_Store
```

Without autocorrect, a typo like `git chekcout master` only prints a suggestion ("The most similar command is checkout") and does nothing.

### Colors

- `color.ui` is the master switch. Default `auto`: color when writing to a terminal, plain when piped/redirected. `false` turns all color off. `always` colors even in pipes — rarely wanted; prefer passing `--color` to the one command instead.
- Per-command switches (`true` / `false` / `always`): `color.branch`, `color.diff`, `color.interactive`, `color.status`.
- Each has subsettings for individual output parts, e.g. diff meta in blue on black, bold:

```
git config --global color.diff.meta "blue black bold"
```

- Colors: `normal, black, red, green, yellow, blue, magenta, cyan, white`. Attributes: `bold, dim, ul` (underline), `blink, reverse` (swap fg/bg).

## External diff and merge tools

Pattern: wrap the GUI tool in tiny scripts, then point Git's config at the wrappers. Swapping tools later means editing only the wrapper.

Git calls an external diff program with seven arguments:

```
path old-file old-hex old-mode new-file new-hex new-mode
```

Wrappers (P4Merge on macOS; adjust paths elsewhere — on Windows replace `/usr/local/bin` with a directory on your path):

```sh
# /usr/local/bin/extMerge
#!/bin/sh
/Applications/p4merge.app/Contents/MacOS/p4merge $*

# /usr/local/bin/extDiff — forward only old-file ($2) and new-file ($5)
#!/bin/sh
[ $# -eq 7 ] && /usr/local/bin/extMerge "$2" "$5"
```

```
$ sudo chmod +x /usr/local/bin/extMerge
$ sudo chmod +x /usr/local/bin/extDiff
```

Four settings wire it up:

- `merge.tool` — which tool/strategy `git mergetool` uses.
- `mergetool.<tool>.cmd` — how to invoke it.
- `mergetool.<tool>.trustExitCode` — whether the tool's exit code means "resolved successfully".
- `diff.external` — command used for diffs.

```ini
[merge]
  tool = extMerge
[mergetool "extMerge"]
  cmd = extMerge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"
  trustExitCode = false
[diff]
  external = extDiff
```

(Equivalent: `git config --global merge.tool extMerge`, `git config --global mergetool.extMerge.cmd 'extMerge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"'`, `git config --global mergetool.extMerge.trustExitCode false`, `git config --global diff.external extDiff`.)

- After this, `git diff 32d1776b1^ 32d1776b1` opens the GUI instead of printing; after a conflicted merge, `git mergetool` opens it to resolve.
- Switching to KDiff3 = change the binary path inside `extMerge` only.
- **Built-in tools need no `cmd`.** `git mergetool --tool-help` lists them (e.g. emerge, gvimdiff, opendiff, p4merge, vimdiff; plus valid-but-not-installed ones like araxis, bc3, kdiff3, meld, tkdiff, tortoisemerge, xxdiff). Some only work in a windowed environment and fail in a terminal-only session.
- Merge-only GUI, keep normal text diffs: `git config --global merge.tool kdiff3` (with `kdiff3` on your path) and skip the wrapper scripts.

## Line endings and whitespace

### `core.autocrlf`

Windows uses CRLF; macOS/Linux use LF. Windows editors often silently convert. Git can normalize: CRLF→LF when adding to the index, LF→CRLF on checkout.

| You are… | Setting | Effect |
|---|---|---|
| On Windows, collaborating cross-platform | `git config --global core.autocrlf true` | CRLF in your checkout, LF in the repo |
| On macOS/Linux | `git config --global core.autocrlf input` | Convert CRLF→LF on commit only; never convert on checkout |
| Windows-only project | `git config --global core.autocrlf false` | No conversion; carriage returns stored in the repo |

The `true`/`input` combination keeps CRLF in Windows working trees and LF everywhere else, including the repository.

### `core.whitespace`

Six detectable problems:

- **On by default** (disable with `-name`): `blank-at-eol` (trailing spaces on a line), `blank-at-eof` (blank lines at end of file), `space-before-tab` (spaces before tabs in leading indentation).
- **Off by default** (enable by listing): `indent-with-non-tab` (line starts with spaces instead of tabs; governed by `tabwidth`), `tab-in-indent` (tabs in indentation), `cr-at-eol` (declares CR at end of line acceptable).
- Value is a comma-separated list; `-` prefix disables; omitted names keep their default. `trailing-space` is shorthand for both `blank-at-eol` and `blank-at-eof`.

```
# everything except space-before-tab
git config --global core.whitespace \
    trailing-space,-space-before-tab,indent-with-non-tab,tab-in-indent,cr-at-eol
# same intent, listing only the changes from default
git config --global core.whitespace \
    -space-before-tab,indent-with-non-tab,tab-in-indent,cr-at-eol
```

Where it bites:

- `git diff` highlights offending whitespace in color so you can fix it before committing.
- `git apply --whitespace=warn <patch>` warns; `git apply --whitespace=fix <patch>` repairs before applying.
- `git rebase --whitespace=fix` cleans whitespace in commits you have made but not yet pushed, as it rewrites them.

## Server-side configuration

All set with `--system` on the server:

| Key | Purpose |
|---|---|
| `receive.fsckObjects true` | Verify every pushed object (SHA-1 matches, points to valid objects). Off by default because it is expensive on large repos/pushes; protects against faulty or malicious clients. |
| `receive.denyNonFastForwards true` | Reject force-pushes (non-fast-forward updates, e.g. after rebasing pushed commits). |
| `receive.denyDeletes true` | Reject deletion of any branch or tag by anyone — closes the "delete then re-push" loophole around `denyNonFastForwards`. To remove a remote branch you then delete ref files on the server by hand. |

For per-user nuance (e.g. only some users may force-push), use a server-side receive hook instead — see the policy example below.

## Git attributes (`.gitattributes`)

Path-specific settings. Put them in `.gitattributes` (usually at the project root, committed) or in `.git/info/attributes` (not committed). Line format: `<pattern> <attribute>[=<value>]`.

### Treating text as binary

```
*.pbxproj binary
```

For machine-written "text" that is really a database (e.g. Xcode `.pbxproj` JSON-like files): Git will no longer fix CRLF in it, nor compute or print diffs for it in `git show`/`git diff`.

### Diffing binaries via `textconv`

Two steps: map a pattern to a named diff driver in `.gitattributes`, then define the driver's `textconv` program in config. Git runs both versions through the converter and diffs the text.

Word documents:

```
# .gitattributes
*.docx diff=word
```

```sh
# wrapper script named docx2txt on your PATH (chmod a+x it); requires docx2txt.pl installed
#!/bin/bash
docx2txt.pl "$1" -
```

```
git config diff.word.textconv docx2txt
```

Result: `git diff` shows added paragraphs (e.g. `+Testing: 1, 2, 3.`) instead of "Binary files differ". Limitation: pure formatting changes don't appear.

Images (diff the EXIF metadata):

```
# .gitattributes
*.png diff=exif
```
```
git config diff.exif.textconv exiftool
```

Now a replaced image shows changed File Size, Image Width/Height, etc.

### Keyword expansion

Problem: you can't write commit info into a file after committing, because Git checksums the content first. Solution: inject on checkout, strip before staging.

**`ident`** — replaces `$Id$` with the SHA-1 of the **blob** (not the commit) on checkout:

```
# .gitattributes
*.txt ident
```
```
$ echo '$Id$' > test.txt
$ rm test.txt
$ git checkout -- test.txt
$ cat test.txt
$Id: 42812b7653c7b88933f8a9d6cad0ca16714b9bb3 $
```

Limited value: a blob SHA-1 tells you nothing about age or order.

**Clean/smudge filters** — the general mechanism:

- **smudge** runs on checkout (repo → working tree).
- **clean** runs when files are staged (working tree → index).

Run all C files through `indent` before committing:

```
# .gitattributes
*.c filter=indent
```
```
git config --global filter.indent.clean indent
git config --global filter.indent.smudge cat     # cat = pass-through
```

RCS-style `$Date$` expansion — smudge script `expand_date` (Ruby, on your PATH):

```ruby
#! /usr/bin/env ruby
data = STDIN.read
last_date = `git log --pretty=format:"%ad" -1`
puts data.gsub('$Date$', '$Date: ' + last_date.to_s + '$')
```

```
git config filter.dater.smudge expand_date
git config filter.dater.clean 'perl -pe "s/\\\$Date[^\\\$]*\\\$/\\\$Date\\\$/"'
```
```
# .gitattributes
date*.txt filter=dater
```

After commit + re-checkout, `# $Date$` becomes `# $Date: Tue Apr 21 07:26:52 2009 -0700$`. The clean step strips it back to `$Date$` so the stored content is stable.

**Gotcha:** `.gitattributes` travels with the repo, but the filter driver (the `filter.dater.*` config and scripts) does not. Design filters to fail gracefully so the project still works where the driver is missing.

### Exporting with `git archive`

- `export-ignore` — keep a path in the repo but out of archives:

  ```
  test/ export-ignore
  ```

- `export-subst` — expand `$Format:...$` placeholders (using `git log`'s pretty-format codes) in that file when archiving:

  ```
  # .gitattributes
  LAST_COMMIT export-subst
  ```
  ```
  $ echo 'Last commit date: $Format:%cd by %aN$' > LAST_COMMIT
  $ git add LAST_COMMIT .gitattributes
  $ git commit -am 'adding LAST_COMMIT file for archives'
  $ git archive HEAD | tar xCf ../deployment-testing -
  $ cat ../deployment-testing/LAST_COMMIT
  Last commit date: Tue Apr 21 08:38:48 2009 -0700 by Scott Chacon
  ```

  Placeholders can include the full message (`%B`), notes, and wrapping (`%+w(76,6,9)`), e.g. `$Format:Last commit: %h by %aN at %cd%n%+w(76,6,9)%B$`. `git archive` strips the `$Format:` / `$` markers.
- An exported archive suits deployment, not further development.

### Per-file merge strategy

Keep your version of a file whenever it conflicts on merge (e.g. branch-specific `database.xml`):

```
# .gitattributes
database.xml merge=ours
```
```
git config --global merge.ours.driver true
```

`git merge topic` then reports `Auto-merging database.xml` with no conflict, and the file stays as your side had it.

## Hooks

Scripts in the repo's hooks directory (normally `.git/hooks`) that fire on events.

**Installing:**

- `git init` populates `.git/hooks` with example scripts ending in `.sample` — they also document each hook's inputs.
- To enable a hook: file named exactly after the hook, **no extension**, and **executable**. Any language works (shell, Perl, Ruby, Python…).
- **Client-side hooks are not copied by `git clone`.** Anything meant as policy must be enforced on the server; client hooks must be distributed separately (in the project or another repo) and installed by each user.
- For hook scripts others will read, prefer long-form flags.

### Client-side: commit workflow

| Hook | When | Input | Can abort? | Typical use |
|---|---|---|---|---|
| `pre-commit` | Before the message is even typed | none | Yes (non-zero); bypass with `git commit --no-verify` | lint, tests, trailing-whitespace check (the sample does this), docs on new methods |
| `prepare-commit-msg` | After default message is built, before the editor opens | message file path, commit type, SHA-1 (for amends) | Yes | edit auto-generated messages: templates, merges, squashes, amends |
| `commit-msg` | After the message is written | path to temp message file | Yes | validate message format / project state |
| `post-commit` | After the commit completes | none (use `git log -1 HEAD`) | No | notifications |

### Client-side: email workflow (`git am` only)

| Hook | When | Can abort? | Use |
|---|---|---|---|
| `applypatch-msg` | First; gets temp file with proposed message | Yes | check/normalize message in place |
| `pre-applypatch` | After patch applied, **before** commit (despite the name) | Yes | run tests on the snapshot |
| `post-applypatch` | After commit | No | notify group / patch author |

### Client-side: other

- `pre-rebase` — before any rebase; non-zero halts. Use it to forbid rebasing already-pushed commits (the sample does this, with workflow assumptions).
- `post-rewrite` — after commands that replace commits (`git commit --amend`, `git rebase`; **not** `git filter-branch`). Arg: which command; stdin: list of rewrites.
- `post-checkout` — after successful `git checkout`; set up the working dir (move in untracked large binaries, generate docs).
- `post-merge` — after successful merge; restore untracked data like permissions, verify external files.
- `pre-push` — during `git push`, after remote refs are updated but before objects are sent. Args: remote name and location; stdin: refs to update. Non-zero aborts the push.
- `pre-auto-gc` — just before `git gc --auto`; notify, or abort if now is a bad time.

### Server-side

| Hook | Runs | Input | Rejection scope |
|---|---|---|---|
| `pre-receive` | Once per push, first | refs being pushed, on stdin | Non-zero rejects **all** refs |
| `update` | Once **per ref** being updated | args: ref name, old SHA-1, new SHA-1 | Non-zero rejects **only that ref** |
| `post-receive` | After everything completes | same stdin as `pre-receive` | Cannot stop the push |

- "Pre" hooks can print an error message back to the client.
- `post-receive` uses: email a list, notify CI, update a ticket tracker (even parse messages to open/close tickets). The client stays connected until it finishes — keep it fast.
- Anything a server hook writes to stdout is shown to the pushing client.

## Worked example: enforcing a policy

Goal: (1) every commit message must contain `[ref: 1234]`-style ticket refs; (2) users may only push changes to paths an ACL allows. Server enforces; client hooks give early warning.

### Server: `update` hook (Ruby)

Setup — args and pushing user (assumes `$USER` identifies the pusher; with a shared SSH account like `git` you'd need a shell wrapper that sets it from the public key):

```ruby
#!/usr/bin/env ruby
$refname = ARGV[0]
$oldrev  = ARGV[1]
$newrev  = ARGV[2]
$user    = ENV['USER']
puts "Enforcing Policies..."
puts "(#{$refname}) (#{$oldrev[0,6]}) (#{$newrev[0,6]})"
```

Building blocks (plumbing):

- `git rev-list <old>..<new>` — SHA-1s of the commits being pushed (like `git log` but SHA-1s only).
- `git cat-file commit <sha> | sed '1,/^$/d'` — raw commit, minus headers up to the first blank line = the message.
- `git log -1 --name-only --pretty=format:'' <sha>` — files changed by one commit.

Message check:

```ruby
$regex = /\[ref: (\d+)\]/
def check_message_format
  missed_revs = `git rev-list #{$oldrev}..#{$newrev}`.split("\n")
  missed_revs.each do |rev|
    message = `git cat-file commit #{rev} | sed '1,/^$/d'`
    if !$regex.match(message)
      puts "[POLICY] Your message is not formatted correctly"
      exit 1
    end
  end
end
check_message_format
```

ACL file `acl` in the bare repo, CVS-like, `|`-delimited: `avail|unavail`, comma-separated users, path (blank = everything):

```
avail|nickh,pjhyett,defunkt,tpw
avail|usinclair,cdickens,ebronte|doc
avail|schacon|lib
avail|schacon|tests
```

Parse into `{user => [paths]}` (only `avail` lines; `nil` path = full access), then for each new commit's changed files require that some allowed path is a prefix (or the user has `nil`), else print `[POLICY] You do not have access to push to <path>` and `exit 1`.

Make it executable: `chmod u+x .git/hooks/update`. A bad push then shows your stdout lines, then `error: hook declined to update refs/heads/master` and `! [remote rejected] master -> master (hook declined)` — one rejected line per declined ref.

### Client: early-warning hooks

Rejected pushes are frustrating because fixing them means rewriting history. Ship client hooks so problems surface at commit time:

- **`commit-msg`** — read `ARGV[0]` (the message file), apply the same regex, `exit 1` on mismatch. `git commit -am 'Test'` is refused; `git commit -am 'Test [ref: 132]'` succeeds.
- **`pre-commit`** ACL check — same logic as the server with two changes:
  - ACL path is `.git/acl` (hook runs from the working directory).
  - Changed files come from the staging area, since no commit exists yet: `git diff-index --cached --name-only HEAD`.
  - Assumes your local user name equals the one you push as; otherwise set `$user` manually.
- **`pre-rebase`** — refuse to rebase commits already on a remote. For each commit in `git rev-list <base>..<topic>`, check every `git branch -r` ref with `git rev-list ^<sha>^@ refs/remotes/<ref>`; if the commit appears, abort. `<sha>^@` means "all parents of that commit". Drawback: can be slow and is often unnecessary — without `-f`, the server already refuses non-fast-forward pushes (assuming `receive.denyNonFastForwards`/`receive.denyDeletes` are set).

## Decision rules

- Machine-wide or personal preference → `git config` at the right level. Per-path behaviour → `.gitattributes`. Reacting to an event → hook.
- Policy that must hold → server-side (`receive.*` config or `pre-receive`/`update`). Client hooks are convenience only — they're not cloned and can be bypassed (`--no-verify`).
- Reject whole push → `pre-receive`; reject per branch → `update`; side effects after push → `post-receive`.
- Committed `.gitattributes` filters need drivers configured on every machine — make them degrade gracefully.

See also: `chapters/01-getting-started.md` (first-time config), `chapters/07-git-tools.md` (signing, revision selection), `chapters/10-git-internals.md` (plumbing used in hooks).
