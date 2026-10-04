# Chapter 7 — Git Tools

*Load this for power-user work: naming commits and ranges, partial staging, stash/clean, GPG signing, searching code and history, rewriting history, understanding reset vs checkout, hard merges, rerere, bisect/blame, submodules, bundles, replace, and credential helpers.*

## Quick decision guide

| You want to... | Reach for |
|---|---|
| Name a commit relative to another | `HEAD^`, `HEAD~3`, `d921970^2`, `master@{yesterday}` |
| See what a branch has that another lacks | `git log master..experiment` |
| See what you are about to push | `git log origin/master..HEAD` (or `origin/master..`) |
| Commit only some hunks of a file | `git add -p` |
| Park dirty work to switch branches | `git stash` / `git stash push`, later `git stash pop` |
| Delete untracked cruft | `git clean -n -d` first, then `git clean -f -d` |
| Find when a string appeared/disappeared | `git log -S <string>` (pickaxe) |
| See the history of one function | `git log -L :funcname:file.c` |
| Fix the last commit | `git commit --amend` (`--no-edit` to keep the message) |
| Reword / reorder / squash / split / drop older commits | `git rebase -i <parent-of-oldest>` |
| Scrub a file from all history | `git filter-branch --tree-filter 'rm -f file' HEAD` (prefer `git-filter-repo`) |
| Undo commits but keep changes staged / unstaged / nowhere | `reset --soft` / `reset` (mixed) / `reset --hard` |
| Merge drowning in whitespace conflicts | `git merge -Xignore-space-change <branch>` |
| See base version inside conflict markers | `git checkout --conflict=diff3 <file>` |
| Undo a merge already shared | `git revert -m 1 HEAD` |
| Stop re-resolving the same conflicts | `git config --global rerere.enabled true` |
| Find which commit introduced a bug | `git bisect start/bad/good`, or `git bisect run <script>` |
| Find who last touched lines | `git blame -L 69,82 <file>` |
| Embed another repo at a pinned commit | `git submodule add <url>` |
| Move repo data without a network | `git bundle create` / `git clone x.bundle` |
| Stop typing HTTPS passwords | `git config --global credential.helper cache` |

---

## Revision Selection

### Single commits
- **Short SHA-1**: any unambiguous prefix of at least 4 characters works (`git show 1c002d`). `git log --abbrev-commit` prints 7 chars by default, lengthening when needed. 8–10 chars is normally plenty; the book notes the Linux kernel (875k+ commits, ~7M objects, Feb 2019) had no collisions in the first 12 characters.
- **SHA-1 collisions**: if a new object hashed to an existing SHA-1, Git would silently reuse the old object (you would always get the first object's data). Accidental collision is astronomically unlikely; deliberate collisions were demonstrated (shattered.io, Feb 2017). Git is moving toward SHA-256 and has mitigations.
- **Branch name** = its tip commit. `git rev-parse topic1` shows the SHA-1 any ref resolves to (plumbing, but handy for debugging).

### Reflog shortnames
- Git logs every move of HEAD and branch tips for "the last few months". `git reflog` lists them.
- `HEAD@{5}` = where HEAD was five moves ago; `master@{yesterday}`, `HEAD@{2.months.ago}` = where it was at a time.
- `git log -g master` shows the reflog in `git log` format.
- **Reflog is strictly local** — like shell history. A fresh clone has an empty reflog; `@{2.months.ago}` only works if your clone is that old.
- PowerShell: escape braces — `git show "HEAD@{0}"` or ``git show HEAD@`{0`}``.

### Ancestry: `^` vs `~`
- `HEAD^` = first parent. `HEAD^2` = **second parent** (only meaningful for merges; parent 1 is the branch you were on, parent 2 the branch merged in).
- `HEAD~` = first parent too. `HEAD~3` = first parent of first parent of first parent (= `HEAD~~~`).
- Combine: `HEAD~3^2` = second parent of the great-grandparent.
- Windows cmd.exe: `^` is special — use `HEAD^^` or `"HEAD^"`.

### Commit ranges
- **Double dot** `A..B`: commits reachable from B but not from A.
  - `git log master..experiment` — work on experiment not yet merged to master.
  - `git log origin/master..HEAD` — what `git push` would send. Omitted side defaults to HEAD: `git log origin/master..`.
- **Multiple points**: `^ref` or `--not ref` excludes. These are equivalent:
  ```
  git log refA..refB
  git log ^refA refB
  git log refB --not refA
  ```
  Only this form allows 3+ refs: `git log refA refB ^refC`.
- **Triple dot** `A...B`: commits reachable from either but not both (symmetric difference). Add `--left-right` to mark sides with `<` / `>`:
  ```
  git log --left-right master...experiment
  ```

---

## Interactive Staging

Goal: split a messy working tree into focused, reviewable commits.

- `git add -i` opens a menu: `status`, `update` (stage), `revert` (unstage), `add untracked`, `patch`, `diff` (staged diff, like `git diff --cached`), `quit`, `help`. Select files by number (`1,2`), Enter on an empty prompt to apply.
- **Patch mode** (`p` in the menu, or directly `git add -p` / `git add --patch`) walks hunks. Key answers:
  - `y`/`n` stage/skip hunk; `a`/`d` stage/skip this and all remaining hunks in the file
  - `s` split hunk smaller; `e` edit hunk manually; `/` search by regex; `g` jump to a hunk
  - `j`/`J`/`k`/`K` leave undecided and move next/previous
- A partially staged file shows counts in both the staged and unstaged columns.
- Patch mode exists elsewhere too: `git reset --patch` (partial unstage), `git checkout --patch` (partial revert of working files), `git stash --patch` (partial stash).

---

## Stashing and Cleaning

### Stash basics
- Stash saves modified tracked files plus staged changes onto a stack, leaving a clean tree; it can be reapplied on any branch.
- `git stash save` is being deprecated in favor of `git stash push` (which adds stashing specific pathspecs). `git stash` alone = push.

```
git stash                 # save
git stash list            # stash@{0}, stash@{1}, ...
git stash apply           # reapply newest; keeps it on the stack
git stash apply stash@{2} # a specific one
git stash apply --index   # also restore what was staged
git stash drop stash@{0}  # delete
git stash pop             # apply + drop
```

- **Gotcha**: plain `apply` does not re-stage previously staged files — use `--index`.
- Applying onto a dirty tree or different branch is allowed; conflicts are reported if it no longer applies cleanly.

### Stash variants
- `git stash --keep-index` — stash everything (including staged), but leave the staged content in the index (useful to test exactly what you'll commit).
- `git stash -u` / `--include-untracked` — also stash untracked files (not ignored ones).
- `git stash -a` / `--all` — also stash ignored files.
- `git stash --patch` — choose hunks to stash interactively.
- `git stash branch <name>` — create a branch at the commit where the stash was made, apply the stash there, and drop it if it applied cleanly. Use when the stash no longer applies on the moved-on branch.

### git clean
- Removes **untracked** files; often unrecoverable. Safer alternative: `git stash --all` (removes but keeps a copy).
- `-f` is required unless `clean.requireForce` is set to false. `-d` also removes untracked directories.
- **Always dry-run first**: `git clean -d -n` (`--dry-run`).
- Ignored files are kept unless you add `-x` (e.g. to wipe build outputs for a truly clean build).
- `git clean -x -i` — interactive mode (filter by pattern, select by number, ask each).
- Nested Git repos (e.g. submodule dirs) survive `git clean -fd`; add a second `-f` (`-ffd`) to remove them.

---

## Signing Your Work (GPG)

```
gpg --list-keys
gpg --gen-key
git config --global user.signingkey 0A46826A!
```

- **Tags**: `git tag -s v1.5 -m 'my signed 1.5 tag'` (`-s` instead of `-a`). `git show v1.5` displays the PGP signature.
- **Verify tags**: `git tag -v <tag>` — needs the signer's public key in your keyring, otherwise "public key not found".
- **Commits** (Git ≥ 1.7.9): `git commit -a -S -m 'Signed commit'`.
- **Inspect**: `git log --show-signature -1`; or `git log --pretty="format:%h %G? %aN  %s"` — `%G?` shows `G` (good signature) or `N` (none).
- **Enforce on merge** (Git ≥ 1.8.3): `git merge --verify-signatures <branch>` refuses if any commit lacks a valid signature; works for `git pull` too. Add `-S` to also sign the merge commit.
- **Team rule**: if you adopt signing, everyone must do it — have each person run `git config --local commit.gpgsign true`, or you'll spend time helping people rewrite commits. Understand GPG before mandating it.

---

## Searching

### git grep
Searches the working tree by default, or any committed tree or the index. Fast, and can search old versions without checking them out.

```
git grep -n gmtime_r                # line numbers
git grep --count gmtime_r           # matches per file
git grep -p gmtime_r *.c            # show enclosing function
git grep --break --heading \
  -n -e '#define' --and \( -e LINK -e BUF_MAX \) v1.8.0   # boolean, in a tag
```
- `--and` requires all patterns on the same line; `--break`/`--heading` make output readable.

### Log searching
- **Pickaxe** `git log -S ZLIB_BUF_MAX --oneline` — commits that changed the *number of occurrences* of a string (i.e. introduced/removed it).
- `git log -G <regex>` — regex variant.
- **Line-log** `git log -L :git_deflate_bound:zlib.c` — every change to a function, as patches back to its creation. If Git can't detect the function boundaries in your language, give a regex range: `git log -L '/unsigned long git_deflate_bound/',/^}/:zlib.c`; line numbers/ranges also work.

---

## Rewriting History

**Cardinal rule**: rewrite freely while work is local; treat pushed work as final unless you have a good reason. Don't push until you're happy with it. Every rewrite changes SHA-1s of the rewritten commits and all descendants.

### Amend the last commit
- `git commit --amend` — edit message; stage extra changes first to also change content.
- `git commit --amend --no-edit` — trivial fix, keep message.
- Amending is "a very small rebase": never amend a pushed commit. If content changes substantially, update the message too.

### Interactive rebase
`git rebase -i HEAD~3` — the argument is the **parent** of the oldest commit you want to edit (to edit the last three, pass `HEAD~3`, i.e. `HEAD~2^`). Everything in `HEAD~3..HEAD` may be rewritten.

The todo list is in **reverse log order** (oldest first) because it's a replay script run top to bottom. Commands:

| Command | Effect |
|---|---|
| `pick` (p) | use commit |
| `reword` (r) | use, edit message |
| `edit` (e) | use, stop for amending |
| `squash` (s) | meld into previous commit, combine messages |
| `fixup` (f) | like squash, discard this message |
| `exec` (x) | run shell command |
| `break` (b) | stop here; resume with `--continue` |
| `drop` (d) | remove commit |
| `label` / `reset` / `merge` | label HEAD, reset to label, create merge commit |

Deleting a line loses that commit; deleting everything aborts.

Recipes:
- **Change an old message**: mark `edit` → `git commit --amend` → `git rebase --continue`.
- **Reorder / remove**: reorder lines; delete or `drop` a line.
- **Squash three into one**: `pick` the first, `squash` the rest; Git then opens an editor to merge messages.
- **Split a commit**: mark `edit`, then:
  ```
  git reset HEAD^
  git add README
  git commit -m 'Update README formatting'
  git add lib/simplegit.rb
  git commit -m 'Add blame'
  git rebase --continue
  ```
  Commits before the first changed one (left as `pick`) keep their SHA-1.
- Dropping/editing an early commit can cause many conflicts in later dependent commits.
- Bail out mid-way: `git rebase --abort`. Regret after finishing: recover the old branch tip via `git reflog` (see `chapters/10-git-internals.md`, Data Recovery).

### filter-branch (the nuclear option)
For scripted rewrites across many commits. Only on history others haven't built on. The book flags it as having many pitfalls and **no longer recommended** — prefer `git-filter-repo` (https://github.com/newren/git-filter-repo).

```
git filter-branch --tree-filter 'rm -f passwords.txt' HEAD   # remove file from every commit
git filter-branch --tree-filter 'rm -f *~' HEAD              # editor backups
git filter-branch --subdirectory-filter trunk HEAD           # make trunk/ the new root
```
- `--tree-filter` runs the command on each checked-out snapshot and recommits. `--all` = all branches.
- `--subdirectory-filter` also drops commits that didn't touch that subdirectory.
- Changing your email everywhere — use `--commit-filter` and only touch your own address:
  ```
  git filter-branch --commit-filter '
          if [ "$GIT_AUTHOR_EMAIL" = "schacon@localhost" ];
          then
                  GIT_AUTHOR_NAME="Scott Chacon";
                  GIT_AUTHOR_EMAIL="schacon@example.com";
                  git commit-tree "$@";
          else
                  git commit-tree "$@";
          fi' HEAD
  ```
  This changes every commit SHA-1 (parents are hashed in), not just matching ones.
- Practice: run in a test branch, then hard-reset master once satisfied.

---

## Reset Demystified

### The three trees
| Tree | Role | Inspect with |
|---|---|---|
| HEAD | last commit snapshot; parent of next commit | `git cat-file -p HEAD`, `git ls-tree -r HEAD` |
| Index | proposed next commit (staging area; really a flat manifest) | `git ls-files -s` |
| Working Directory | sandbox of real files | your editor |

`git add` copies working dir → index; `git commit` turns the index into a commit and moves the branch; `git status` reports differences between the trees. Checkout of a branch moves HEAD, fills the index from that commit, then copies the index into the working dir.

### What `git reset <commit>` does, in order
1. **Move the branch HEAD points to** to `<commit>` — stop here with `--soft` (undoes `git commit`; changes stay staged).
2. **Make the index match HEAD** — stop here by default / `--mixed` (undoes commit and `git add`).
3. **Make the working directory match the index** — only with `--hard` (undoes your edits too).

> `--hard` is the one form of reset that can destroy data; uncommitted work it overwrites is gone. Committed versions can still be found via the reflog.

### Reset with a path
- Skips step 1 (HEAD can't point at part of a commit); applies steps 2(+3) to the given files.
- `git reset file.txt` = `git reset --mixed HEAD file.txt` → copies file from HEAD into the index = **unstage** (exact opposite of `git add`).
- `git reset eb43bf file.txt` → stages the old version of the file without touching the working dir; committing records a revert of that file.
- `git reset --patch` unstages hunk by hunk.

### Squash with reset
For "oops"/"WIP" commits: `git reset --soft HEAD~2` then `git commit` — the branch now has one commit containing the combined result.

### checkout vs reset
- `git checkout <branch>` vs `git reset --hard <branch>`: both make all three trees match, but checkout is **working-directory safe** (refuses to clobber changed files; does a trivial merge), and checkout **moves HEAD itself** while reset **moves the branch HEAD points to**. On `develop`, `git reset master` makes develop point at master's commit; `git checkout master` leaves develop alone.
- `git checkout [commit] <paths>` — updates index *and* working file from the commit; like a path-level `reset --hard`; **not WD-safe**; HEAD doesn't move. Supports `--patch`.

### Cheat sheet
| Command | HEAD | Index | Workdir | WD safe? |
|---|---|---|---|---|
| **Commit level** | | | | |
| `reset --soft [commit]` | REF | NO | NO | YES |
| `reset [commit]` | REF | YES | NO | YES |
| `reset --hard [commit]` | REF | YES | YES | **NO** |
| `checkout <commit>` | HEAD | YES | YES | YES |
| **File level** | | | | |
| `reset [commit] <paths>` | NO | YES | NO | YES |
| `checkout [commit] <paths>` | NO | YES | YES | **NO** |

REF = moves the branch HEAD points to; HEAD = moves HEAD itself. Pause before any NO in "WD safe?".

---

## Advanced Merging

Git philosophy: be smart about recognizing unambiguous merges, but don't try clever automatic resolution of real conflicts. Merge long-lived branches often to keep conflicts small.

**Before a risky merge, have a clean working directory** (commit to a temp branch or stash) so everything is undoable.

### Getting out
- `git merge --abort` — restore pre-merge state (may be imperfect only if you had uncommitted changes).
- `git reset --hard HEAD` — start over; loses uncommitted work.

### Whitespace conflicts
Sign: every line removed on one side and re-added on the other. Abort and redo with:
- `-Xignore-all-space` — ignore whitespace entirely when comparing lines.
- `-Xignore-space-change` — treat runs of whitespace as equivalent.
```
git merge -Xignore-space-change whitespace
```

### Manual re-merge of a single file
Conflicted index holds three **stages**: 1 = common ancestor, 2 = ours, 3 = theirs (MERGE_HEAD).
```
git show :1:hello.rb > hello.common.rb
git show :2:hello.rb > hello.ours.rb
git show :3:hello.rb > hello.theirs.rb
git ls-files -u                      # blob SHA-1s per stage
dos2unix hello.theirs.rb             # preprocess one side
git merge-file -p hello.ours.rb hello.common.rb hello.theirs.rb > hello.rb
git clean -f                         # remove the helper copies
```
This fixes the content rather than ignoring differences (ignore-space-change can leave mixed line endings).

Review the result against each side before committing: `git diff --ours`, `git diff --theirs -b`, `git diff --base -b`.

### More context on conflicts
- `git checkout --conflict=diff3 hello.rb` — rewrite markers with an extra `||||||| base` section; `--conflict=merge` restores default markers. Make diff3 default: `git config --global merge.conflictstyle diff3`.
- `git checkout --ours <file>` / `--theirs <file>` — take one side wholesale (great for binary files).
- `git log --oneline --left-right HEAD...MERGE_HEAD` — all unique commits on each side.
- `git log --oneline --left-right --merge` — only commits touching currently conflicted files; add `-p` for diffs.

### Combined diff
- During a conflict, `git diff` shows only unresolved content, in "combined diff" format with **two columns**: col 1 = vs ours, col 2 = vs theirs. Lines `++` exist in neither parent (e.g. markers, or your new resolution).
- After the fact: `git show <merge>` or `git log --cc -p -1` displays the resolution.

### Undoing merges
1. **Fix the references** (unpushed only): `git reset --hard HEAD~`. Rewrites history; also loses any commits made after the merge.
2. **Reverse the commit** (shared history):
   ```
   git revert -m 1 HEAD
   ```
   `-m 1` keeps parent 1 (mainline) and undoes what parent 2 brought in.
   - **Gotcha**: the reverted branch's commits remain in history, so re-merging says "Already up-to-date" and later merges bring only *new* commits. Fix: revert the revert, then merge again:
     ```
     git revert <revert-commit>
     git merge topic
     ```

### Other merge types
- `-Xours` / `-Xtheirs` (recursive strategy option): merge normally, but on conflicting hunks pick that side wholesale (including binaries); no markers. Also `git merge-file --ours`.
- `-s ours` (strategy — different!): a fake merge that records both parents but keeps your tree exactly (`git diff HEAD HEAD~` is empty). Use to mark a branch as merged, e.g. merge a bugfix into release normally and `-s ours` into master so a later release→master merge doesn't conflict on it.
- **Subtree merge** — keep another project as a branch and merge it into a subdirectory:
  ```
  git remote add rack_remote https://github.com/rack/rack
  git fetch rack_remote --no-tags
  git checkout -b rack_branch rack_remote/master
  git checkout master
  git read-tree --prefix=rack/ -u rack_branch       # import into rack/
  # later, after pulling upstream into rack_branch:
  git merge --squash -s recursive -Xsubtree=rack rack_branch
  git diff-tree -p rack_branch                      # compare subdir vs branch
  ```
  Pros: all code in one place, no submodules. Cons: more complex, easy to reintegrate wrongly or push a branch to an unrelated repo; normal `git diff` doesn't work for the comparison.

---

## Rerere (reuse recorded resolution)

Records how you resolved a conflicting hunk and replays it when the same conflict reappears.

```
git config --global rerere.enabled true   # or create .git/rr-cache in one repo
```
Use cases: test-merge a long-lived topic branch repeatedly and back out (no clutter merge commits), keep rebasing a branch without re-resolving, switch a resolved merge to a rebase, or rebuild an integration branch without a failing topic.

Workflow signals:
- On conflict: "Recorded preimage for 'hello.rb'".
- `git rerere status` — files with recorded preimages; `git rerere diff` — what the resolution will be.
- After `git add` + `git commit`: "Recorded resolution for 'hello.rb'".
- Next time (e.g. `git rebase master`): "Resolved 'hello.rb' using previous resolution." — file already clean; just `git add` and continue.
- `git checkout --conflict=merge hello.rb` restores markers; `git rerere` reapplies the cached resolution.
- Note: rerere resolves the file but you still `git add` it yourself.

---

## Debugging with Git

### git blame
```
git blame -L 69,82 Makefile
```
- Fields: short SHA-1, author, authored date, line number, content.
- A `^` prefix on the SHA-1 means the line is unchanged since the repository's initial commit (yet another meaning of `^`).
- `git blame -C -L 141,153 GITPackUpload.m` — detects code copied/moved from other files and shows the original file and commit, not the commit that moved it. Works because Git infers renames/moves after the fact rather than tracking them.

### git bisect (binary search)
```
git bisect start
git bisect bad            # current commit is broken
git bisect good v1.0      # last known good
# test each checkout Git gives you, then:
git bisect good | git bisect bad
git bisect reset          # ALWAYS finish here, back to where you started
```
- Git reports "<sha> is first bad commit" with its details.
- **Automate**: script exits 0 for good, non-zero for bad:
  ```
  git bisect start HEAD v1.0     # bad first, then good
  git bisect run test-error.sh   # or make / make tests
  ```

---

## Submodules

A submodule = a Git repo kept as a subdirectory of another, with separate commits. Solves "use a library but still customize it and merge upstream changes".

### Core model
- `git submodule add https://github.com/chaconinc/DbConnector [path]` creates:
  - `.gitmodules` (versioned): `[submodule "DbConnector"] path = ... url = ...`. Others clone from this URL, so use one everyone can reach; override locally with `git config submodule.DbConnector.url PRIVATE_URL`. Relative URLs can help.
  - A gitlink entry with mode **160000**: the superproject records a *specific commit* of the submodule, not its files.
- `git diff --cached --submodule` for readable output; make default with `git config --global diff.submodule log`.
- `git config status.submodulesummary 1` adds a submodule summary to `git status`.
- Modern Git keeps submodule Git data in the top project's `.git`, so deleting a submodule directory doesn't lose commits/branches.

### Cloning
```
git clone --recurse-submodules <url>      # all-in-one, includes nested
# or, after a plain clone (submodule dirs are empty):
git submodule init && git submodule update
git submodule update --init               # combined
git submodule update --init --recursive   # foolproof, nested too
```

### Consuming upstream submodule changes
- Manually: `cd` into it, `git fetch`, `git merge origin/master`; then commit in the superproject to lock in the new commit.
- `git submodule update --remote [name]` — fetch and update to the remote default branch (all submodules if no name).
- Track another branch: `git config -f .gitmodules submodule.DbConnector.branch stable` (omit `-f .gitmodules` to set only locally; keeping it in `.gitmodules` shares it).

### Pulling superproject changes
- `git pull` fetches submodule changes but **does not update** them; `git status` shows "modified (new commits)" with `<` arrows (recorded in superproject, absent locally). Finish with:
  ```
  git submodule update --init --recursive
  ```
- `git pull --recurse-submodules` (Git ≥ 2.14) does the update automatically; `git config submodule.recurse true` makes it default for every command supporting `--recurse-submodules` except clone (for pull since 2.15).
- If upstream changed a submodule URL in `.gitmodules` and update fails:
  ```
  git submodule sync --recursive
  git submodule update --init --recursive
  ```

### Working inside a submodule
- `submodule update` leaves the submodule in **detached HEAD**; commits made there can be lost on the next update. Fix: `cd` in and `git checkout stable` (a branch), then update with a strategy:
  - `git submodule update --remote --merge`
  - `git submodule update --remote --rebase`
- Forgetting `--merge`/`--rebase` resets to detached HEAD at upstream; your work is still on your branch — check it out and merge/rebase manually.
- Uncommitted local changes block the update (Git won't overwrite them); conflicts are resolved inside the submodule as usual.

### Publishing
- Pushing the superproject without pushing submodule commits breaks everyone else.
- `git push --recurse-submodules=check` — fail if submodule commits aren't pushed. Default: `git config push.recurseSubmodules check`.
- `git push --recurse-submodules=on-demand` — push submodules first; if that fails, the main push fails. Default: `git config push.recurseSubmodules on-demand`.

### Merging diverged submodule pointers
- Fast-forward cases resolve automatically; Git won't even attempt a trivial merge of diverged ones ("merge following commits not found" = it found no existing submodule merge commit containing both).
- Get both SHA-1s from `git diff` (`index eb41d76,c771610..`): first = ours, second = theirs. Then:
  ```
  cd DbConnector
  git branch try-merge c771610
  git merge try-merge          # resolve, commit
  cd ..
  git add DbConnector
  git commit -m "Merge Tom's Changes"
  ```
- If Git suggests an existing merge commit with a `git update-index --cacheinfo 160000 ...` command, prefer instead to `cd` in, `git merge <sha>` (fast-forward), test, then `git add` + commit in the superproject.

### Tips and aliases
```
git submodule foreach 'git stash'
git submodule foreach 'git checkout -b featureA'
git diff; git submodule foreach 'git diff'
git config alias.sdiff '!'"git diff && git submodule foreach 'git diff'"
git config alias.spush 'push --recurse-submodules=on-demand'
git config alias.supdate 'submodule update --remote --merge'
```

### Known pain points
- **Switching branches (Git < 2.13)**: leaving a branch that added a submodule leaves an untracked dir; remove with `git clean -ffdx` and repopulate later with `git submodule update --init`. With Git ≥ 2.13 use `git checkout --recurse-submodules <branch>` — recommended always when a project has submodules (otherwise submodules appear "modified (new commits)" after switching between branches that pin different commits). Older Git: follow checkout with `git submodule update --init --recursive`.
- **Converting a subdirectory into a submodule**: `rm -Rf dir` then `submodule add` fails ("already exists in the index"). Do `git rm -r CryptoLibrary` first. Switching back to a branch where it was a plain directory errors on untracked files; `git checkout -f` works (beware unsaved changes), and you may need `git checkout .` inside the submodule afterwards to restore files.

---

## Bundling

Packages what `git push` would send into one binary file — for no network, offline sites, or emailing many commits instead of format-patch.

```
git bundle create repo.bundle HEAD master   # whole branch; include HEAD if it will be cloned
git clone repo.bundle repo                  # without HEAD in bundle: add -b master
```
Incremental bundle — you must compute the range yourself (no network negotiation):
```
git log --oneline master ^origin/master     # check what's new
git bundle create commits.bundle master ^9a466c5
```
Receiver:
```
git bundle verify ../commits.bundle         # valid? prerequisites present?
git bundle list-heads ../commits.bundle
git fetch ../commits.bundle master:other-master
```
- If the bundle omits a commit the receiver lacks, `verify` reports "Repository lacks these prerequisite commits".

---

## Replace

Objects are immutable, but `git replace <old> <new>` makes Git pretend one object is another everywhere — e.g. graft histories without rewriting SHA-1s.

Example: split a repo into a short "recent" repo and a long "historical" repo, then rejoin on demand.
```
git branch history c6e1e95
git push project-history history:master          # publish history
echo 'Get history from blah blah blah' | git commit-tree 9c68fdc^{tree}   # parentless base commit
git rebase --onto 622e88 9c68fdc                  # replay recent commits on it
# a collaborator who wants full history:
git remote add project-history https://github.com/schacon/project-history
git fetch project-history
git replace 81a708d c6e1e95
```
- `git log` then shows the full history; bisect/blame work normally. The replaced commit still displays its own SHA-1 (`81a708d`), but `cat-file` shows the replacement's data (including its parent).
- Replacements are stored as refs (`refs/replace/<sha>`), so they can be pushed and shared.
- `commit-tree` is plumbing (see `chapters/10-git-internals.md`).

---

## Credential Storage

HTTP(S) needs credentials on every connection (SSH can use a passphrase-less key); 2FA tokens make typing worse. Built-in helpers:

| Mode | Behavior |
|---|---|
| (default) | no caching; prompt every time |
| `cache` | in memory only; purged after 15 min (`--timeout <seconds>`, default 900) |
| `store` | plaintext file, never expires (`--file <path>`, default `~/.git-credentials`) — **cleartext risk** |
| `osxkeychain` | macOS keychain; on disk, encrypted, never expires |
| Git Credential Manager | Windows Credential Store; can also serve WSL1/WSL2 |

```
git config --global credential.helper cache
git config --global credential.helper 'store --file ~/.my-credentials'
```
Multiple helpers are queried in order until one answers; on save, all receive the credentials:
```
[credential]
    helper = store --file /mnt/thumbdrive/.git-credentials
    helper = cache --timeout 30000
```

### Under the hood
- `git credential fill` reads `key=value` lines (`protocol=`, `host=`, ...) on stdin until a blank line, then prints what it knows (adding `username=`, `password=`), prompting the user if no helper knows.
- `credential.helper` value forms: `foo` → runs `git-credential-foo`; `foo -a --opt=bcd` → with args; `/absolute/path/foo -xyz` → that program; `!f() { echo "password=s3cre7"; }; f` → shell code after `!`.
- Helpers implement actions `get` (return creds), `store` (save), `erase` (purge). Only `get` output matters; output lines act as assignments overriding what Git knows. A helper that knows nothing exits silently.
- The `store` file is one credential-decorated URL per line: `https://bob:s3cre7@mygithost`.
- **Custom helper**: any executable named `git-credential-<name>` on PATH works. The book's example `git-credential-read-only` (Ruby) answers only `get`, reads a shared store-format file (`--file`), matches protocol/host/username, and ignores `store`/`erase` — useful for team-shared, frequently changing deploy credentials:
  ```
  git config --global credential.helper 'read-only --file /mnt/shared/creds'
  ```

---

## Anti-patterns and gotchas (summary)
- Amending, rebasing, resetting, or filter-branching commits that others already have.
- `git clean -f` without a `-n` dry run; `reset --hard` or `checkout <commit> -- <path>` over uncommitted work.
- Expecting `git stash apply` to restore staging (needs `--index`).
- Expecting reflog entries in a fresh clone or on another machine.
- Re-merging a branch after `revert -m 1` without first reverting the revert.
- Confusing `-Xours` (option: prefer our side on conflicts) with `-s ours` (strategy: ignore their tree entirely).
- Forgetting `git bisect reset`.
- Committing inside a submodule on detached HEAD; pushing a superproject before its submodules.
- Using `credential.helper store` without accepting cleartext passwords on disk.
