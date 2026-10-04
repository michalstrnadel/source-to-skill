# Chapter 2 — Git Basics

*Load this for everyday local Git: init/clone, the file lifecycle, status/add/diff/commit, .gitignore, rm/mv, reading history with `git log`, undoing (amend, unstage, discard), remotes (fetch/pull/push), tags, and aliases.*

## Core mental models

- **Two axes of file state.** A file is *untracked* (not in the last snapshot and not staged) or *tracked* (Git knows it). Tracked files cycle through *unmodified -> modified -> staged -> (commit) -> unmodified*. Right after a clone, everything is tracked and unmodified.
- **`git add` means "put exactly this content into the next commit"**, not "add this file to the project". It tracks new files, stages modifications, and marks merge conflicts resolved.
- **Staging is a snapshot of the moment you ran `git add`.** Edit the file again afterwards and it shows up as *both* staged and unstaged; the commit gets the version from the last `git add`. Re-run `git add` to stage the latest edits.
- **A commit records the staging area**, not the working tree. Anything unstaged stays modified on disk for a later commit.
- **Committed = recoverable; uncommitted = likely gone.** Even commits on deleted branches or replaced by `--amend` can usually be recovered (Data Recovery, `chapters/10-git-internals.md`). Discarded working-tree changes cannot.
- **`git status` tells you how to undo.** Its hint lines show the unstage/discard commands for your Git version.

## Getting a repository

```console
$ cd /home/user/my_project      # Linux  (macOS: /Users/user/my_project, Windows: C:/Users/user/my_project)
$ git init                      # creates .git/ skeleton; nothing tracked yet
$ git add *.c
$ git add LICENSE
$ git commit -m 'Initial project version'
```

```console
$ git clone https://github.com/libgit2/libgit2            # creates ./libgit2
$ git clone https://github.com/libgit2/libgit2 mylibgit   # custom directory name
```

- `clone` (not "checkout") pulls down nearly all data the server has: every version of every file. A clone can often restore a corrupted server (you may lose server-side hooks, but not versioned data). See `chapters/04-git-on-the-server.md`.
- Clone creates the directory, initializes `.git`, downloads all data, and checks out the latest version.
- Transfer protocols: `https://`, `git://`, and SSH (`user@server:path/to/repo.git`).

## Recording changes

### `git status` and short status

```console
$ git status
On branch master
Your branch is up-to-date with 'origin/master'.
nothing to commit, working tree clean
```

Status sections: **Untracked files** (Git won't include these until you `git add` them, which keeps generated binaries out by accident), **Changes to be committed** (staged), **Changes not staged for commit** (tracked + modified).

`git status -s` / `--short` uses two columns: **left = staging area, right = working tree**.

| Code | Meaning |
|---|---|
| `??` | Untracked |
| `A ` | New file, staged |
| `M ` (left) | Modified and staged |
| ` M` (right) | Modified, not staged |
| `MM` | Staged, then modified again (has staged and unstaged changes) |

### Default branch name note

GitHub switched its default branch from `master` to `main` in mid-2020 and other hosts followed; the default can also be configured (`init.defaultBranch`, see `chapters/01-getting-started.md`). Git itself still defaults to `master`, which the book uses.

### Ignoring files: `.gitignore`

Set up `.gitignore` before you start so you never commit build output, logs, editor temp files, etc.

```gitignore
*.[oa]
*~
```

Pattern rules:

- Blank lines and lines starting with `#` are ignored.
- Standard glob patterns apply recursively throughout the working tree.
- Leading `/` prevents recursion (anchors to that directory).
- Trailing `/` marks a directory.
- Leading `!` negates a pattern.
- Globs: `*` = zero or more chars; `[abc]` = one of those chars; `?` = one char; `[0-9]` = a range; `**` matches nested directories (`a/**/z` matches `a/z`, `a/b/z`, `a/b/c/z`).

```gitignore
# ignore all .a files
*.a
# but do track lib.a, even though you're ignoring .a files above
!lib.a
# only ignore the TODO file in the current directory, not subdir/TODO
/TODO
# ignore all files in any directory named build
build/
# ignore doc/notes.txt, but not doc/server/arch.txt
doc/*.txt
# ignore all .pdf files in the doc/ directory and any of its subdirectories
doc/**/*.pdf
```

- Nested `.gitignore` files in subdirectories apply only to files under that directory (the Linux kernel has 206 of them). Details: `man gitignore`.
- Templates for many languages: https://github.com/github/gitignore

### Seeing exact changes: `git diff`

| Command | Compares | Answers |
|---|---|---|
| `git diff` | working tree vs staging area | What have I changed but not staged? |
| `git diff --staged` (synonym `--cached`) | staging area vs last commit | What will go into the next commit? |

- Gotcha: plain `git diff` does **not** show everything since the last commit — only unstaged changes. If everything is staged it prints nothing.
- External viewers: `git difftool` (emerge, vimdiff, commercial tools); list options with `git difftool --tool-help`.

### Committing

```console
$ git commit                 # opens editor (core.editor, else $EDITOR)
$ git commit -v              # also shows the diff in the editor
$ git commit -m "Story 182: fix benchmarks for speed"
[master 463dc4f] Story 182: fix benchmarks for speed
 2 files changed, 2 insertions(+)
 create mode 100644 README
```

- The editor template contains the commented-out `git status` output; comments (and the `-v` diff) are stripped from the message. An empty message aborts the commit.
- Output reports branch, abbreviated SHA-1, files changed, and line stats.

**Skipping the staging area:** `git commit -a` auto-stages every *already tracked* modified file before committing.

```console
$ git commit -a -m 'Add new benchmarks'
```

- Anti-pattern risk: `-a` can sweep in unwanted changes. It also does not pick up untracked files.

### Removing files

| Goal | Command |
|---|---|
| Stop tracking and delete from disk | `git rm PROJECTS.md` |
| File modified or already staged | `git rm -f <file>` (safety check against losing unrecorded data) |
| Stop tracking but keep the file on disk (e.g. forgot `.gitignore`, staged a big log) | `git rm --cached README` |
| Glob removal | `git rm log/\*.log`, `git rm \*~` |

- Deleting with plain `rm` only shows up as "Changes not staged for commit"; `git rm` stages the removal.
- Escape `*` with `\` so Git does its own glob expansion (in addition to the shell's).

### Moving / renaming

Git stores no rename metadata; it infers renames after the fact. `git mv` is a one-command convenience:

```console
$ git mv README.md README
# equivalent to:
$ mv README.md README
$ git rm README.md
$ git add README
```

Status shows `renamed: README.md -> README` either way. You can rename with any tool and sort out add/rm before committing.

## Viewing history: `git log`

Default: commits in reverse chronological order with SHA-1, author name/email, date, message. Example repo: `git clone https://github.com/schacon/simplegit-progit`.

### Output formatting

| Option | Effect |
|---|---|
| `-p`, `--patch` | Patch introduced by each commit (great for review) |
| `--stat` | Per-commit list of changed files with line counts, plus summary |
| `--shortstat` | Only the changed/insertions/deletions line |
| `--name-only` | Files changed |
| `--name-status` | Files changed with added/modified/deleted marker |
| `--abbrev-commit` | Abbreviated SHA-1 instead of all 40 chars |
| `--relative-date` | Dates like "2 weeks ago" |
| `--graph` | ASCII branch/merge graph |
| `--pretty=oneline\|short\|full\|fuller\|format:"..."` | Alternate formats |
| `--oneline` | Shorthand for `--pretty=oneline --abbrev-commit` |

```console
$ git log -p -2
$ git log --pretty=format:"%h - %an, %ar : %s"
$ git log --pretty=format:"%h %s" --graph
```

- Rule: use `--pretty=format` for machine parsing; the explicit format won't change across Git updates.

`--pretty=format` specifiers:

| Spec | Output | Spec | Output |
|---|---|---|---|
| `%H` / `%h` | Commit hash / abbreviated | `%an` / `%ae` | Author name / email |
| `%T` / `%t` | Tree hash / abbreviated | `%ad` / `%ar` | Author date (respects `--date=`) / relative |
| `%P` / `%p` | Parent hashes / abbreviated | `%cn` / `%ce` | Committer name / email |
| `%s` | Subject | `%cd` / `%cr` | Committer date / relative |

**Author vs committer:** the author originally wrote the work; the committer last applied it. If a maintainer applies your patch, you are author and they are committer (more in `chapters/05-distributed-git.md`).

### Limiting output

| Option | Effect |
|---|---|
| `-<n>` | Last n commits (rarely needed — output is paged by default) |
| `--since`, `--after` | Commits after a date |
| `--until`, `--before` | Commits before a date |
| `--author` | Author matches string |
| `--committer` | Committer matches string |
| `--grep` | Commit message contains string |
| `-S <string>` | "Pickaxe": commits that changed the number of occurrences of the string |
| `--no-merges` | Hide merge commits (often uninformative noise) |
| `-- <path>` | Only commits touching that path; always last, preceded by `--` |

- Dates accept specific (`"2008-01-15"`) or relative (`"2 years 1 day 3 minutes ago"`, `2.weeks`) forms.
- Multiple `--author` / `--grep` match **any**; add `--all-match` to require all `--grep` patterns.

```console
$ git log --since=2.weeks
$ git log -S function_name                # last commit adding/removing a reference to a function
$ git log -- path/to/file
$ git log --pretty="%h - %s" --author='Junio C Hamano' --since="2008-10-01" \
   --before="2008-11-01" --no-merges -- t/
```

The last example narrows nearly 40,000 commits in Git's history to 6.

## Undoing things

Caution: this is one of the few areas where a mistake can lose work, and some undos can't be undone.

### Amend the last commit

```console
$ git commit -m 'Initial commit'
$ git add forgotten_file
$ git commit --amend
```

- Takes the current staging area as the new commit; with nothing new staged, only the message changes (editor opens prefilled with the old message).
- It **replaces** the old commit entirely — the old one no longer appears in history. Good for avoiding "Oops, forgot a file" commits.
- **Rule: only amend commits that are still local.** Amending pushed commits and force-pushing causes problems for collaborators (see The Perils of Rebasing in `chapters/03-git-branching.md`).

### Unstage / discard — classic vs `git restore` (Git 2.23+)

| Goal | Classic | Git 2.23+ | Safety |
|---|---|---|---|
| Unstage a file (keep edits) | `git reset HEAD <file>` | `git restore --staged <file>` | Safe: working tree untouched |
| Discard working-tree changes | `git checkout -- <file>` | `git restore <file>` | **Dangerous**: local changes are gone |

- `git reset` can be dangerous with `--hard`; the file-path form above is relatively safe. Full treatment: Reset Demystified in `chapters/07-git-tools.md`.
- Discarding replaces the file with the last staged or committed version. Never run it unless you're certain you don't want those changes; to set work aside instead, prefer stashing or branching (the book points to `chapters/03-git-branching.md`).
- Since 2.23, Git uses `restore` instead of `reset` for many undo operations, and `git status` hints change accordingly.

## Working with remotes

A remote is another copy of the project "elsewhere" — on the network, the Internet, or even the same machine. Each is typically read-only or read/write for you.

```console
$ git remote                       # shortnames; 'origin' = the server you cloned from
$ git remote -v                    # with fetch/push URLs
$ git remote add pb https://github.com/paulboone/ticgit
$ git fetch pb                     # Paul's master now at pb/master
$ git remote show origin           # URLs, tracked branches, pull/push config
$ git remote rename pb paul        # also renames remote-tracking branches (pb/master -> paul/master)
$ git remote remove paul           # or: git remote rm paul; deletes its remote-tracking branches and config
```

### fetch vs pull vs push

- `git fetch <remote>` downloads everything you don't have and creates remote-tracking references. It **does not merge** or touch your current work; merge manually when ready.
- `git pull` = fetch + merge of the remote branch your current branch tracks. `clone` automatically sets your local default branch (`master` or whatever it is called) to track the remote one.
- Since Git 2.27, `git pull` warns until `pull.rebase` is set:

```console
$ git config --global pull.rebase "false"   # default: fast-forward if possible, else merge commit
$ git config --global pull.rebase "true"    # rebase when pulling
```

- `git push <remote> <branch>`, e.g. `git push origin master`. Works only with write access and if nobody pushed in the meantime; otherwise the push is rejected and you must fetch and incorporate their work first.

### Reading `git remote show`

It reports: fetch/push URLs, the remote HEAD branch, each remote branch as `tracked`, `new (next fetch will store in remotes/origin)`, or `stale (use 'git remote prune' to remove)`, which local branches merge with which remote branch on `git pull`, and which local refs push where (with up-to-date status).

## Tagging

Used to mark important points, typically releases (`v1.0`, `v2.0`).

### Listing

```console
$ git tag                    # alphabetical; -l/--list optional here
$ git tag -l "v1.8.5*"       # wildcard: -l/--list is MANDATORY
```

### Lightweight vs annotated

| | Lightweight | Annotated |
|---|---|---|
| What it is | Pointer to a commit (commit checksum in a file), like a branch that never moves | Full object in the Git database |
| Metadata | None | Checksummed; tagger name, email, date; message; can be GPG-signed and verified |
| Create | `git tag v1.4-lw` (no `-a`, `-s`, `-m`) | `git tag -a v1.4 -m "my version 1.4"` (no `-m` opens editor) |
| `git show` | Just the commit | Tagger info, date, message, then the commit |
| Use for | Temporary/private tags | **Recommended default** |

Tag an older commit by giving its (partial) checksum:

```console
$ git tag -a v1.2 9fceb02
```

### Sharing and deleting

- **Gotcha: `git push` does not push tags by default.**

```console
$ git push origin v1.5               # one tag
$ git push origin --tags             # all tags not on remote (lightweight AND annotated)
$ git push <remote> --follow-tags    # annotated tags only
$ git tag -d v1.4-lw                 # delete locally only
$ git push origin :refs/tags/v1.4-lw # delete on remote: push "nothing" onto the tag
$ git push origin --delete <tagname> # delete on remote (more intuitive)
```

- There is no option to push only lightweight tags.

### Checking out a tag = detached HEAD

```console
$ git checkout v2.0.0           # detached HEAD
$ git checkout -b version2 v2.0.0   # branch from the tag to make changes
```

- In detached HEAD, new commits belong to no branch and are reachable only by exact hash; the tag doesn't move.
- To fix bugs on an old release, create a branch from the tag. That branch then advances past the tag — be careful.
- Git's advice in this state: `git switch -c <new-branch-name>` to keep commits, `git switch -` to go back; silence it with `advice.detachedHead=false`.

## Git aliases

Git doesn't autocomplete partially typed commands; aliases fill that gap and let you invent missing commands.

```console
$ git config --global alias.co checkout
$ git config --global alias.br branch
$ git config --global alias.ci commit
$ git config --global alias.st status
$ git config --global alias.unstage 'reset HEAD --'   # git unstage fileA == git reset HEAD -- fileA
$ git config --global alias.last 'log -1 HEAD'        # git last
$ git config --global alias.visual '!gitk'            # leading ! runs an external command
```

Git substitutes the alias text literally; prefix with `!` to run a non-Git command (useful for your own tooling).

## Gotchas and anti-patterns

- Editing after `git add` without re-adding: the commit gets the older staged version.
- Trusting `git diff` to show all pending changes — use `git diff --staged` too.
- `git commit -a` sweeping in unrelated edits.
- `git checkout -- <file>` / `git restore <file>` on work you might want: unrecoverable.
- Amending or force-pushing commits that others already have.
- Forgetting to push tags explicitly.
- Committing in detached HEAD without creating a branch.
- Glob in `git rm` without escaping `*`.
- Forgetting `.gitignore` and staging build artefacts — fix with `git rm --cached`.
