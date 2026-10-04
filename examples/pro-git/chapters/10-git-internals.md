# Chapter 10 — Git Internals

*Load when you need to know how Git stores data (objects, refs, packfiles), write refspecs, debug transfer or performance, recover lost commits, purge a large file from history, or use Git's environment variables and plumbing commands in scripts.*

## Core mental model

- **Git is a content-addressable filesystem with a VCS interface layered over it.** At the bottom is a key-value store: you put content in, Git hands back a SHA-1 key, and that key retrieves the content later.
- **Everything is one of four object types**, linked by SHA-1 pointers:
  - **blob** — file contents only (no filename).
  - **tree** — a directory listing: entries of `mode type SHA-1 name`, pointing to blobs or subtrees.
  - **commit** — one top-level tree + zero or more parents + author/committer + message.
  - **tag** (annotated) — tagger, date, message, and a pointer to (usually) a commit; can point to any object.
- **Refs are just files holding a SHA-1** (or, for symbolic refs, the name of another ref). A branch is a movable pointer to the head of a line of work; a lightweight tag is a pointer that never moves; `HEAD` is a symbolic ref to the current branch.
- **What `git add` + `git commit` really do:** write blobs for changed files, update the index, write tree objects from the index, write a commit pointing at the top-level tree and the previous commit, then move the branch ref.
- **Storage starts "loose" (one zlib file per object) and is later packed** into packfiles that store similar objects as deltas.
- **Anything not reachable from a ref (or the reflog) is a candidate for garbage collection** — and anything that *is* reachable stays in every clone forever, which is why removing a big file requires rewriting history.

## Plumbing vs porcelain

- **Porcelain:** the ~30 user-friendly commands (`checkout`, `branch`, `remote`, …) used in the rest of the book.
- **Plumbing:** low-level commands designed to be chained UNIX-style or called from scripts/tools. Use them to build tools and to understand why Git behaves as it does.

### The `.git` directory

Copying `.git` gives you nearly everything needed to back up or clone a repo. A fresh `git init` contains:

| Entry | Role |
|---|---|
| `HEAD` | Points to the currently checked-out branch |
| `index` | Staging-area information (created once you stage something) |
| `objects/` | The object database — all content |
| `refs/` | Pointers into commits: branches (`heads`), `tags`, remotes |
| `config` | Project-specific configuration |
| `info/` | Global exclude file for ignore patterns you don't want in `.gitignore` |
| `hooks/` | Client/server hook scripts (see `chapters/08-customizing-git.md`) |
| `description` | Used only by GitWeb — ignore |

The four that matter: `HEAD`, `index`, `objects/`, `refs/`.

## Objects in practice

### Blobs: store and retrieve raw content

```console
$ echo 'test content' | git hash-object -w --stdin
d670460b4b4aece5915caf5c68d12f560a9fe3e4
$ find .git/objects -type f
.git/objects/d6/70460b4b4aece5915caf5c68d12f560a9fe3e4
$ git cat-file -p d670460b4b4aece5915caf5c68d12f560a9fe3e4
test content
```

- `git hash-object` — computes the key; `-w` actually writes the object; `--stdin` reads content from stdin (otherwise give a filename).
- Path layout: subdirectory = first 2 hex chars of the SHA-1, filename = remaining 38.
- `git cat-file -p <sha>` — pretty-print any object based on its type. `-t` prints the type (`blob`, `tree`, `commit`, `tag`); `-s` prints the size in bytes.
- You can version a file purely with plumbing: `git hash-object -w test.txt` after each edit, then `git cat-file -p <sha> > test.txt` to restore any version. The limitation: you must remember SHA-1s, and no filename is stored — hence trees.

### Trees: filenames and directories

```console
$ git cat-file -p master^{tree}
100644 blob a906cb2a4a904a152e80877d4088654daad0c859      README
100644 blob 8f94139338f9404f26296befa88755fc2598c289      Rakefile
040000 tree 99f1a6d12cb4b6f19c8655fca46c3ecf317074e0      lib
```

- `master^{tree}` = the tree pointed to by the last commit on `master`.
- **Shell gotchas for `^{tree}`:**
  - Windows CMD: `^` is an escape char → `git cat-file -p master^^{tree}`
  - PowerShell: quote braces → `git cat-file -p 'master^{tree}'`
  - Zsh: `^` globs → `git cat-file -p "master^{tree}"`
- **Valid file modes** (only these three for blobs): `100644` normal file, `100755` executable, `120000` symlink. Directories use `040000`; other modes exist for submodules.

Build trees by hand via the index:

```console
$ git update-index --add --cacheinfo 100644 \
  83baae61804e65cc73a7201a7252750c76066a30 test.txt   # stage an object already in the DB
$ git write-tree                                        # index -> tree object (no -w needed)
d8329fc1cc938780ffdd9f94e0d364e0ea74f579
$ git update-index --add new.txt                        # stage a file from disk
$ git read-tree --prefix=bak d8329fc1cc938780ffdd9f94e0d364e0ea74f579  # graft a tree as subdir
```

- `--add` is required when the path isn't in the index yet; `--cacheinfo` means the content is in the database, not the working directory.
- `git write-tree` creates the tree only if it doesn't already exist.
- `git read-tree --prefix=<dir>` reads an existing tree into the index as a subtree.

### Commits: who, when, why, and history

```console
$ echo 'First commit' | git commit-tree d8329f
fdf4fc3344e67ab068f836878b6c4951e3b15f3d
$ echo 'Second commit' | git commit-tree 0155eb -p fdf4fc3
$ echo 'Third commit'  | git commit-tree 3c4e9c -p cac0cab
$ git log --stat 1a410e        # a real history, built with no porcelain
```

Commit object format (as shown by `git cat-file -p`):

```
tree d8329fc1cc938780ffdd9f94e0d364e0ea74f579
author Scott Chacon <schacon@gmail.com> 1243040974 -0700
committer Scott Chacon <schacon@gmail.com> 1243040974 -0700

First commit
```

- Fields: top-level tree; `parent` line(s) if any; author and committer (from `user.name`/`user.email` plus timestamp); blank line; message.
- Your hashes will differ from the book's — commit SHA-1s depend on author data and creation time.

### How an object is stored on disk

1. Header = type + space + content length in bytes + NUL byte, e.g. `"blob 16\0"`.
2. SHA-1 is computed over **header + content** (so `hash-object` is not just a SHA-1 of the file).
3. Header + content is zlib-deflated.
4. Written to `.git/objects/<first 2>/<remaining 38>`.

```console
$ echo -n "what is up, doc?" | git hash-object --stdin
bd9dbf5aae1a3862dd1526723246b20206e5fc37
```

(The book reproduces this exact SHA-1 in Ruby with `Digest::SHA1.hexdigest("blob 16\0what is up, doc?")` and writes a valid object with `Zlib::Deflate.deflate`.) Commits and trees use the same scheme with a `commit`/`tree` header, but their content has a strict format; blob content can be anything.

## References

| Ref kind | Location | Notes |
|---|---|---|
| Branch | `refs/heads/<name>` | Moves as you commit |
| Tag | `refs/tags/<name>` | Lightweight: points at a commit; annotated: points at a tag object |
| Remote-tracking | `refs/remotes/<remote>/<branch>` | Last known state on the server; read-only |
| `HEAD` | `.git/HEAD` | Usually `ref: refs/heads/<branch>` |
| Packed | `.git/packed-refs` | Fallback after `git gc` |

### Creating and moving refs

```console
$ git update-ref refs/heads/master 1a410efbd13591db07496601ebc7a059dd55cfe9
$ git update-ref refs/heads/test cac0ca        # a branch at an older commit
$ git log --pretty=oneline test
```

- **Rule:** use `git update-ref` instead of `echo <sha> > .git/refs/heads/...`. It's safer, and it updates the reflog (hand-written refs don't — which matters for recovery).
- `git branch <name>` is essentially `update-ref` with the SHA-1 of whatever `HEAD` resolves to.

### HEAD

- Normally a **symbolic reference** (contains another ref's name, not a SHA-1): `ref: refs/heads/master`.
- **Detached HEAD**: checking out a tag, commit, or remote branch makes `HEAD` hold a raw SHA-1 instead.
- `git commit` uses whatever `HEAD` resolves to as the new commit's parent.

```console
$ git symbolic-ref HEAD                    # read
refs/heads/master
$ git symbolic-ref HEAD refs/heads/test    # write
$ git symbolic-ref HEAD test
fatal: Refusing to point HEAD outside of refs/
```

### Tags

- **Lightweight tag** = a ref that never moves: `git update-ref refs/tags/v1.0 <commit-sha>`.
- **Annotated tag** = a tag object + a ref pointing to that object:

```console
$ git tag -a v1.1 1a410efbd13591db07496601ebc7a059dd55cfe9 -m 'Test tag'
$ cat .git/refs/tags/v1.1
9585191f37f7b0fb9444f35a9bf50de191beadc2       # the tag object, not the commit
$ git cat-file -p 9585191f
object 1a410efbd13591db07496601ebc7a059dd55cfe9
type commit
tag v1.1
tagger Scott Chacon <schacon@gmail.com> Sat May 23 16:48:58 2009 -0700

Test tag
```

- Tags can point to **any** object: Git's maintainer tagged a blob holding their GPG public key (`git cat-file blob junio-gpg-pub` in a Git clone); the Linux kernel's first tag points to a tree.

### Remote references

- After a push or fetch, `refs/remotes/origin/master` holds the SHA-1 the server branch had at last contact.
- They are **read-only bookmarks**: you can check one out, but Git never makes `HEAD` symbolically point at it, so commits never advance it.

## Packfiles

- **Loose format**: one zlib file per object. Changing one line of a 22K file yields a whole new ~22K blob.
- **Packfile**: many objects in one binary file, with similar objects stored as deltas. Git packs when there are too many loose objects, when you run `git gc`, and when you push to a server.
- After `git gc`, `objects/pack/` holds a `pack-<sha>.pack` plus a `.idx` index of offsets for fast seeking. In the book's example ~15K of loose objects became a 7K pack.
- **Dangling objects** (not reachable from any commit) are left loose, not packed.
- Git looks for files named and sized similarly and stores deltas between versions. **The newest version is kept whole; older ones become deltas** — the most recent version is the one you most likely need fast.
- Repacking can happen any time; Git does it automatically and `git gc` forces it.

Inspect a pack:

```console
$ git verify-pack -v .git/objects/pack/pack-<sha>.idx
```

Columns: SHA-1, type, size, size-in-pack, offset; deltified entries add depth and base SHA-1. The book's example shows the old `repo.rb` blob taking 9 bytes in the pack, as a delta against the newer 22K blob.

## The refspec

Written by `git remote add origin <url>` into `.git/config`:

```ini
[remote "origin"]
	url = https://github.com/schacon/simplegit-progit
	fetch = +refs/heads/*:refs/remotes/origin/*
```

Format: `[+]<src>:<dst>`
- `<src>` — ref pattern on the remote side; `<dst>` — where it's tracked locally.
- Leading `+` — update the ref even when it isn't a fast-forward.
- `origin/master`, `remotes/origin/master`, `refs/remotes/origin/master` all expand to the same ref.

### Fetch recipes

```ini
# only master
fetch = +refs/heads/master:refs/remotes/origin/master

# several specific branches: one fetch line each
fetch = +refs/heads/master:refs/remotes/origin/master
fetch = +refs/heads/experiment:refs/remotes/origin/experiment

# partial glob (Git 2.6.0+)
fetch = +refs/heads/qa*:refs/remotes/origin/qa*

# namespace: master plus everything under the QA team's qa/ directory
fetch = +refs/heads/master:refs/remotes/origin/master
fetch = +refs/heads/qa/*:refs/remotes/origin/qa/*
```

One-off fetches on the command line:

```console
$ git fetch origin master:refs/remotes/origin/mymaster
$ git fetch origin master:refs/remotes/origin/mymaster \
    topic:refs/remotes/origin/topic
 ! [rejected]        master     -> origin/mymaster  (non fast forward)
 * [new branch]      topic      -> origin/topic
```

- **Gotcha:** without `+`, a non-fast-forward update is rejected. Prefix the refspec with `+` to force it.
- Namespaces (directories in ref names) scale well when QA, developers, and integrators all push branches to the same remote.

### Push refspecs

```console
$ git push origin master:refs/heads/qa/master     # push local master to remote qa/master
```

```ini
[remote "origin"]
	url = https://github.com/schacon/simplegit-progit
	fetch = +refs/heads/*:refs/remotes/origin/*
	push = refs/heads/master:refs/heads/qa/master   # default for `git push origin`
```

- **Limitation:** a single refspec can't fetch from one repo and push to another.

### Deleting remote refs

```console
$ git push origin :topic            # empty <src> = make remote topic "nothing"
$ git push origin --delete topic    # same thing, Git 1.7.0+
```

## Transfer protocols

### Dumb protocol (read-only HTTP)

- Needs no Git-specific code on the server: the client issues plain HTTP GETs and assumes the repo layout.
- **Rarely used now; hard to secure or make private; most hosts refuse it. Prefer the smart protocol.**
- Requires `update-server-info` (typically as a `post-receive` hook) to generate `info/refs` and `objects/info/packs`.
- Clone walk: `GET info/refs` → `GET HEAD` → GET each loose object from `objects/xx/...` and walk parents/trees → on 404, check `objects/info/http-alternates` (lets forks share objects), then `objects/info/packs`, the pack's `.idx`, and finally the `.pack` → check out the branch `HEAD` named.

### Smart protocol

A Git-aware process on the server works out what the client has and needs and builds a custom packfile. It can also accept writes, which the dumb protocol can't.

| Direction | Client process | Server process |
|---|---|---|
| Upload (push) | `send-pack` | `receive-pack` |
| Download (fetch/clone) | `fetch-pack` | `upload-pack` |

**pkt-line framing:** each chunk starts with 4 hex chars giving its length *including* those 4 bytes (`00a5` = 165 bytes); `0000` is a flush meaning "done with this section".

**Push over SSH:**
```console
$ ssh -x git@server "git-receive-pack 'simplegit-progit.git'"
```
1. Server lists each ref with its SHA-1; the first line also lists capabilities (`report-status`, `delete-refs`, `side-band-64k`, `ofs-delta`, agent, …).
2. Client sends one line per ref to update: `old-sha new-sha refname` (first line carries client capabilities). All zeros on the left = creating the ref; all zeros on the right = deleting it.
3. Client sends a packfile of objects the server lacks.
4. Server replies e.g. `000eunpack ok`.

**Push over HTTP(S):** `GET .../info/refs?service=git-receive-pack`, then `POST .../git-receive-pack` with the send-pack output + packfile; the HTTP response signals success. The data may also be wrapped in chunked transfer encoding.

**Fetch over SSH:** `ssh -x git@server "git-upload-pack 'simplegit-progit.git'"`. The server advertises refs and capabilities, including `symref=HEAD:refs/heads/master` so a clone knows what to check out. The client replies with `want <sha>` lines, `have <sha>` lines, then `done`; the server streams the packfile.

**Fetch over HTTP(S):** `GET $GIT_URL/info/refs?service=git-upload-pack`, then `POST $GIT_URL/git-upload-pack` with the want/have lines; the response carries the packfile.

## Maintenance

- **auto gc:** Git occasionally runs `git gc --auto`, which usually does nothing. A real gc fires at roughly **7,000 loose objects** or **more than 50 packfiles**; tune with `gc.auto` and `gc.autopacklimit`.
- **What `git gc` does:** packs loose objects, consolidates packfiles into one, removes unreachable objects that are a few months old, and packs refs into `.git/packed-refs`.

```
# pack-refs with: peeled fully-peeled
cac0cab538b970a37ea1e769cbbde608743bc96d refs/heads/experiment
ab1afef80fac8e34258ff41fc1b867c702daa24b refs/heads/master
cac0cab538b970a37ea1e769cbbde608743bc96d refs/tags/v1.0
9585191f37f7b0fb9444f35a9bf50de191beadc2 refs/tags/v1.1
^1a410efbd13591db07496601ebc7a059dd55cfe9
```

- Updating a ref writes a new file in `refs/` and leaves `packed-refs` alone. **Lookup order: `refs/` directory first, then `packed-refs`.** If a ref file seems missing, look in `packed-refs`.
- A `^<sha>` line means the tag above it is annotated, and gives the commit it ultimately points to.

## Data recovery

Typical causes of lost commits: force-deleting a branch you still needed, or `git reset --hard` past commits you wanted.

**1. Reflog (fastest).** Git records every change to `HEAD`, from commits, branch switches, and `update-ref`.

```console
$ git reflog
1a410ef HEAD@{0}: reset: moving to 1a410ef
ab1afef HEAD@{1}: commit: Modify repo.rb a bit
484a592 HEAD@{2}: commit: Create repo.rb
$ git log -g                          # same data, full log format
$ git branch recover-branch ab1afef   # make the lost commits reachable again
```

**2. `git fsck` (when the reflog doesn't have it).** The reflog lives in `.git/logs/`; if that's gone:

```console
$ git fsck --full
dangling blob d670460b4b4aece5915caf5c68d12f560a9fe3e4
dangling commit ab1afef80fac8e34258ff41fc1b867c702daa24b
dangling tree aea790b9a58f6cf6f2804eeac9f0abbe9631e4c9
```

Point a new branch at the `dangling commit` SHA-1.

## Removing a large file from history

**Why:** a clone downloads every version of every file. A huge file committed once, even if deleted in the next commit, stays reachable and gets downloaded by every future clone. This bites especially after importing from Subversion or Perforce, where clients never downloaded full history.

**Warning:** this rewrites every commit from the first one that touched the file. It's fine right after an import, before anyone has based work on it; otherwise every contributor must rebase onto the new commits.

```console
# 1. measure
$ git gc
$ git count-objects -v             # size-pack = packfile size in KB

# 2. find the biggest objects (3rd column = size)
$ git verify-pack -v .git/objects/pack/pack-29…69.idx \
  | sort -k 3 -n \
  | tail -3

# 3. map blob SHA-1 -> path
$ git rev-list --objects --all | grep 82c99a3
82c99a3e86bb1267b236a4b6eff7868d97489af1 git.tgz

# 4. which commits touched it
$ git log --oneline --branches -- git.tgz

# 5. rewrite from the first offending commit onward
$ git filter-branch --index-filter \
  'git rm --ignore-unmatch --cached git.tgz' -- 7b30847^..

# 6. drop everything still pointing at the old commits, then repack
$ rm -Rf .git/refs/original
$ rm -Rf .git/logs/
$ git gc
$ git count-objects -v             # size-pack drops (5MB -> 8K in the example)

# 7. optional: delete the now-loose object entirely
$ git prune --expire now
```

- `--index-filter` changes the index rather than a checked-out tree, so it's much faster than `--tree-filter` (no checkout per revision). That's why it needs `git rm --cached`, not `rm`.
- `--ignore-unmatch` stops `git rm` failing on commits where the file is absent.
- Limiting the range (`7b30847^..`) avoids rewriting from the very first commit.
- **Gotcha:** `.git/refs/original` (written by filter-branch) and the reflog still reference the old commits; until you remove them, gc keeps the blob.
- After gc the blob may still be loose (it shows in `size`), but it won't be sent on push or clone. `git prune --expire now` removes it for good.

## Environment variables

### Global behavior
| Variable | Effect |
|---|---|
| `GIT_EXEC_PATH` | Where Git finds sub-programs (`git --exec-path` shows it) |
| `HOME` | Where the global config is found; override it for a portable install |
| `PREFIX` | System config lives at `$PREFIX/etc/gitconfig` |
| `GIT_CONFIG_NOSYSTEM` | Ignore the system-wide config (useful when it interferes and you can't edit it) |
| `GIT_PAGER` | Pager for multi-page output; falls back to `PAGER` |
| `GIT_EDITOR` | Editor for commit messages etc.; falls back to `EDITOR` |

### Repository locations
| Variable | Effect |
|---|---|
| `GIT_DIR` | Location of `.git`; otherwise Git walks up toward `~` or `/` |
| `GIT_CEILING_DIRECTORIES` | Stop the `.git` search early (slow mounts, shell prompts) |
| `GIT_WORK_TREE` | Working-tree root. If `GIT_DIR`/`--git-dir` is set without `--work-tree`/`GIT_WORK_TREE`/`core.worktree`, the cwd is treated as the top level |
| `GIT_INDEX_FILE` | Path to the index (non-bare only) |
| `GIT_OBJECT_DIRECTORY` | Replaces `.git/objects` |
| `GIT_ALTERNATE_OBJECT_DIRECTORIES` | Colon-separated extra object dirs; avoids duplicating identical large files across projects |

### Pathspecs
- `GIT_GLOB_PATHSPECS=1` — wildcards act as wildcards (the default). `GIT_NOGLOB_PATHSPECS=1` — wildcards match only themselves (`*.c` matches a file literally named `*.c`).
- Per-pathspec overrides: `:(glob)*.c`, `:(literal)*.c`.
- `GIT_LITERAL_PATHSPECS` — disables wildcards *and* the override prefixes.
- `GIT_ICASE_PATHSPECS` — every pathspec becomes case-insensitive.

### Committing
`git-commit-tree` reads these first and falls back to config only when they're unset: `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_AUTHOR_DATE`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`, `GIT_COMMITTER_DATE`. `EMAIL` is the fallback when `user.email` is unset; after that Git uses the system user and host names.

### Networking
- `GIT_CURL_VERBOSE` — emit all libcurl messages (like `curl -v`).
- `GIT_SSL_NO_VERIFY` — skip SSL certificate verification (self-signed certs, half-configured servers).
- `GIT_HTTP_LOW_SPEED_LIMIT` / `GIT_HTTP_LOW_SPEED_TIME` — abort when throughput stays below N bytes/s for M seconds; override `http.lowSpeedLimit` / `http.lowSpeedTime`.
- `GIT_HTTP_USER_AGENT` — custom user-agent (default looks like `git/2.0.0`).

### Diffing and merging
- `GIT_DIFF_OPTS` — misleading name: only `-u<n>` / `--unified=<n>` (context-line count) are valid.
- `GIT_EXTERNAL_DIFF` — overrides `diff.external`; the program to run on `git diff`. Inside it, `GIT_DIFF_PATH_COUNTER` (1-based index) and `GIT_DIFF_PATH_TOTAL` describe the batch.
- `GIT_MERGE_VERBOSITY` (recursive strategy): 0 nothing except perhaps one error; 1 conflicts only; 2 file changes too (**default**); 3 skipped unchanged files; 4 every path processed; 5+ debug.

### Debugging (traces)
Value `true`, `1`, or `2` → trace goes to stderr; an absolute path starting with `/` → trace goes to that file.

| Variable | Shows |
|---|---|
| `GIT_TRACE` | General: alias expansion, delegation to sub-programs |
| `GIT_TRACE_PACK_ACCESS` | Each packfile access: pack file + offset |
| `GIT_TRACE_PACKET` | Packet-level network traffic |
| `GIT_TRACE_PERFORMANCE` | Time per git invocation (e.g. what `gc` runs internally) |
| `GIT_TRACE_SETUP` | Discovered git_dir, worktree, cwd, prefix |

```console
$ GIT_TRACE=true git lga
$ GIT_TRACE_PACKET=true git ls-remote origin
$ GIT_TRACE_PERFORMANCE=true git gc
```

The book's `GIT_TRACE_PERFORMANCE=true git gc` output shows gc running `pack-refs --all --prune`, `reflog expire --all`, `repack -d -l -A --unpack-unreachable=2.weeks.ago` (which calls `pack-objects`), `prune-packed`, `update-server-info`, `prune --expire 2.weeks.ago`, and `rerere gc`.

### Miscellaneous
- `GIT_SSH` — program run instead of `ssh`, invoked as `$GIT_SSH [username@]host [-p <port>] <command>`. **It can't take extra arguments**; for that use `GIT_SSH_COMMAND`, a wrapper script, or `~/.ssh/config`.
- `GIT_SSH_COMMAND` — interpreted by the shell, so arguments work: `GIT_SSH_COMMAND="ssh -i ~/.ssh/my_key" git clone git@example.com:my/repo`.
- `GIT_ASKPASS` — overrides `core.askpass`; the credential-prompt program gets the prompt as an argument and prints the answer on stdout.
- `GIT_NAMESPACE` — namespaced refs (same as `--namespace`); server-side use for storing several forks in one repo with separate refs.
- `GIT_FLUSH` — `1` flushes more often, `0` buffers everything; unset lets Git choose.
- `GIT_REFLOG_ACTION` — custom reflog text:

```console
$ GIT_REFLOG_ACTION="my action" git commit --allow-empty -m 'My message'
$ git reflog -1
9e3d55a HEAD@{0}: my action: My message
```

## Gotchas and anti-patterns

- **Hand-editing ref files** (`echo sha > .git/refs/...`) skips the reflog. Use `git update-ref` / `git symbolic-ref`.
- **Deleting a file in a later commit doesn't shrink the repo.** It's still in history; you need a history rewrite plus cleanup of `refs/original`, the reflog, and gc.
- **Rewriting shared history** forces every collaborator to rebase. Only do it right after an import or with coordination.
- **The dumb HTTP protocol** is insecure and inefficient — use smart.
- **A ref missing from `refs/`** is probably in `packed-refs`, not lost.
- **Deleting `.git/logs/`** removes your main recovery net. Fall back to `git fsck --full`.
- **Book SHA-1s won't match yours** for commits and tags; substitute your own.
