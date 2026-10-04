# Appendix C — Git Commands

*Load to find the right Git command for a task, see what each common command actually does, and know which chapter covers it in depth. It doubles as the editor table for `core.editor`.*

## General rules

- **Long options can be abbreviated** as long as the prefix is unique: `git commit --a` behaves like `git commit --amend`. **Always spell options out in full in scripts.**
- `git help <command>` gives the complete options for any command.
- Almost every command works on the local database. Only a handful touch the network: `fetch`, `pull`, `push`, plus remote management with `remote`.

## Command map by purpose

Chapter references point to the files in `chapters/`.

### Setup and config
| Command | What it does | Notable uses / where |
|---|---|---|
| `git config` | Reads and writes settings at system, global, or repo level | Name, email, editor (ch01); aliases (ch02); `pull --rebase` as default (ch03); credential store (ch07); smudge/clean filters and everything in Git Configuration (ch08) |
| `git help` | Shows the bundled docs for any command | ch01; the `git-shell` help when setting up a server (ch04) |

### Getting and creating projects
| Command | What it does | Notable uses / where |
|---|---|---|
| `git init` | Turns a directory into a new repository | Basics (ch02); changing the default branch name from "master" (ch03); empty bare repo for a server (ch04); what it creates (ch10) |
| `git clone` | Wrapper: new dir → `git init` → `git remote add origin <url>` → `git fetch` → `git checkout` the latest commit | Basics (ch02); `--bare` (ch04); clone from a bundle (ch07); `--recurse-submodules` (ch07) |

### Basic snapshotting
| Command | What it does | Notable uses / where |
|---|---|---|
| `git add` | Copies working-dir content into the index; `commit` only looks at the index | Tracking files (ch02); marking conflicts resolved (ch03); interactive staging (ch07); emulated with plumbing (ch10) |
| `git status` | Shows file states across working dir and index, with hints for moving between them | Full and short forms (ch02) |
| `git diff` | Difference between any two trees | `git diff` = working dir vs index; `--staged` = index vs last commit; `git diff master branchB` = two commits (ch02); `--check` for whitespace (ch05); `A...B` (ch05); `-b`, `--ours/--theirs/--base` (ch07); `--submodule` (ch07) |
| `git difftool` | Opens an external diff tool | ch02 |
| `git commit` | Records the staged snapshot and advances the current branch pointer | `-a` (skip `add`), `-m` (ch02); `--amend` (ch02); how it works with branches (ch03); `-S` signing (ch07); implementation (ch10) |
| `git reset` | Moves HEAD; optionally updates the index; with `--hard` also the working dir | Unstaging (ch02); Reset Demystified (ch07); aborting a merge with `--hard` / `git merge --abort` (ch07) |
| `git rm` | Stages a file's removal (and deletes it from disk) | Basics and `--cached` (keep on disk) (ch02); `--ignore-unmatch` in filter-branch (ch10) |
| `git mv` | Convenience wrapper: move, `git add` the new path, `git rm` the old | ch02 |
| `git clean` | Deletes untracked clutter (build artifacts, merge leftovers) | ch07 |

**Warning:** `git reset --hard` can destroy work. Understand it before using it.

### Branching and merging
| Command | What it does | Notable uses / where |
|---|---|---|
| `git branch` | Lists, creates, deletes, renames branches | ch03; `-u` to set upstream (ch03); internals (ch10) |
| `git checkout` | Switches branches and checks content out into the working dir | ch03; `--track` (ch03); `--conflict=diff3` (ch07); relation to reset (ch07); HEAD internals (ch10) |
| `git merge` | Merges branch(es) into the current one and advances it | `git merge <branch>` (ch03); squash merge (ch05); `-Xignore-space-change`, `--abort` (ch07); verifying signatures (ch07); subtree merging (ch07) |
| `git mergetool` | Opens an external merge helper | ch03; custom tools (ch08) |
| `git log` | Reachable history going backwards from a commit; can compare branches | `-p`, `--stat`, `--pretty`, `--oneline`, date/author filters (ch02); `--decorate`, `--graph` (ch03); `A..B` (ch05, ch07); `A...B`, `--left-right`, `--merge`, `--cc` (ch07); `-g` reflog view (ch07); `-S`, `-L` search (ch07); `--show-signature` (ch07) |
| `git stash` | Shelves uncommitted work temporarily to clean the working dir | ch07 |
| `git tag` | Permanent bookmark on a point in history, usually a release | ch02; release tagging (ch05); `-s` sign / `-v` verify (ch07) |

### Sharing and updating
| Command | What it does | Notable uses / where |
|---|---|---|
| `git fetch` | Downloads what the remote has and you don't, into your local database | ch02, ch03, ch05; single out-of-namespace ref (ch06 PR refs); from a bundle (ch07); custom refspecs (ch10) |
| `git pull` | `fetch` then immediately `merge` into the current branch | ch02; rebase recovery (ch03); one-off pull from a URL (ch05); `--verify-signatures` (ch07) |
| `git push` | Works out what the remote lacks and sends it; needs write access | ch02; specific branches and upstreams (ch03); `--delete` (ch03); multiple remotes (ch05); `--tags` (ch02); `--recurse-submodules` (ch07); `pre-push` hook (ch08); full refspecs (ch10) |
| `git remote` | Manages short names for remote URLs (add, rename, remove, list) | ch02; elsewhere always `git remote add <name> <url>` |
| `git archive` | Creates an archive of one snapshot | Release tarball (ch05) |
| `git submodule` | Manages repositories nested in a repository (`add`, `update`, `sync`, …) | ch07 |

### Inspection and comparison
| Command | What it does | Where |
|---|---|---|
| `git show` | Human-readable view of an object (commit, tag, …) | Annotated tags (ch02); revision selection (ch07); pulling individual merge stages out during a conflict (ch07) |
| `git shortlog` | `git log` summary grouped by author; takes log options | Changelog (ch05) |
| `git describe` | Stable, human-readable, unambiguous name for any commit-ish | Build numbers and release names (ch05) |

### Debugging
| Command | What it does | Where |
|---|---|---|
| `git bisect` | Automatic binary search for the first bad commit | ch07 |
| `git blame` | Annotates each line with the last commit to change it and its author | ch07 |
| `git grep` | Searches for a string or regex in files, including older versions | ch07 |

### Patching (commits as a series of patches)
| Command | What it does | Where |
|---|---|---|
| `git cherry-pick` | Re-applies one commit's change as a new commit on the current branch; take a commit or two without merging the whole branch | ch05 |
| `git rebase` | An automated cherry-pick: replays a series of commits, in order, somewhere else | ch03 (incl. the dangers of rebasing public branches); `--onto` with replace (ch07); conflicts with rerere (ch07); `-i` (ch07) |
| `git revert` | Reverse cherry-pick: a new commit that undoes a target commit | Undoing a merge commit (ch07) |

### Email workflow
| Command | What it does | Where |
|---|---|---|
| `git apply` | Applies a patch from `git diff` or GNU diff (like `patch`, with small differences) | ch05 |
| `git am` | Applies patches from an mbox inbox; `--resolved`, `-i`, `-3` | ch05; hooks (ch08); GitHub PR patches (ch06) |
| `git format-patch` | Generates mbox-formatted patches for mailing lists | ch05 |
| `git imap-send` | Uploads a format-patch mailbox to an IMAP drafts folder | ch05 |
| `git send-email` | Sends format-patch patches by email | ch05 |
| `git request-pull` | Generates a message body asking someone to pull from your public branch, instead of mailing patches | ch05 |

### External systems
| Command | What it does | Where |
|---|---|---|
| `git svn` | Git as a Subversion client: check out from and commit to an SVN server | ch09 |
| `git fast-import` | Fast import from other VCSs or almost any format | Custom importer (ch09) |

### Administration
| Command | What it does | Where |
|---|---|---|
| `git gc` | Garbage collection: removes unneeded files and packs the rest efficiently; usually runs automatically | ch10 |
| `git fsck` | Checks the database for problems; finds dangling objects | ch10 |
| `git reflog` | History of where your branch heads have been, for finding commits lost by rewriting | ch07; recovering a lost branch (ch10) |
| `git filter-branch` | Rewrites many commits by pattern: remove a file everywhere, extract a subdirectory | `--commit-filter`, `--subdirectory-filter`, `--tree-filter` (ch07); cleaning up imports (ch09); removing large files with `--index-filter` (ch10) |

### Plumbing seen outside the internals chapter
- `git ls-remote` — raw refs on the server (ch06, PR refs).
- `git ls-files` — a raw view of the index (ch07: manual re-merging, rerere, the index).
- `git rev-parse` — turns almost any revision string into an object SHA-1 (ch07).
- Most other plumbing (`hash-object`, `cat-file`, `update-index`, `write-tree`, `read-tree`, `commit-tree`, `update-ref`, `symbolic-ref`, `verify-pack`, `count-objects`, `prune`, …) is in `chapters/10-git-internals.md`.

## `core.editor` settings by editor

| Editor | Command |
|---|---|
| Atom | `git config --global core.editor "atom --wait"` |
| BBEdit (macOS, with command line tools) | `git config --global core.editor "bbedit -w"` |
| Emacs | `git config --global core.editor emacs` |
| Gedit (Linux) | `git config --global core.editor "gedit --wait --new-window"` |
| Gvim (Windows 64-bit) | `git config --global core.editor "'C:\Program Files\Vim\vim72\gvim.exe' --nofork '%*'"` |
| Helix | `git config --global core.editor "hx"` |
| Kate (Linux) | `git config --global core.editor "kate --block"` |
| nano | `git config --global core.editor "nano -w"` |
| Notepad (Windows 64-bit) | `git config core.editor notepad` |
| Notepad++ (Windows 64-bit) | `git config --global core.editor "'C:\Program Files\Notepad++\notepad++.exe' -multiInst -notabbar -nosession -noPlugin"` |
| Scratch (Linux) | `git config --global core.editor "scratch-text-editor"` |
| Sublime Text (macOS) | `git config --global core.editor "/Applications/Sublime\ Text.app/Contents/SharedSupport/bin/subl --new-window --wait"` |
| Sublime Text (Windows 64-bit) | `git config --global core.editor "'C:\Program Files\Sublime Text 3\sublime_text.exe' -w"` |
| TextEdit (macOS) | `git config --global core.editor "open --wait-apps --new -e"` |
| Textmate | `git config --global core.editor "mate -w"` |
| Textpad (Windows 64-bit) | `git config --global core.editor "'C:\Program Files\TextPad 5\TextPad.exe' -m"` |
| UltraEdit (Windows 64-bit) | `git config --global core.editor Uedit32` |
| Vim | `git config --global core.editor "vim --nofork"` |
| Visual Studio Code | `git config --global core.editor "code --wait"` |
| VSCodium | `git config --global core.editor "codium --wait"` |
| WordPad | `git config --global core.editor "'C:\Program Files\Windows NT\Accessories\wordpad.exe'"` |
| Xi | `git config --global core.editor "xi --wait"` |

- **Gotcha:** a 32-bit editor on 64-bit Windows lives under `C:\Program Files (x86)\`, not `C:\Program Files\`. Adjust the Windows paths above accordingly.
- Note the Notepad entry has no `--global`.
