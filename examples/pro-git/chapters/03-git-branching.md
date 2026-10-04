# Chapter 3 — Git Branching

*Load this when a question involves creating, switching, merging, deleting or renaming branches; resolving merge conflicts; remote-tracking/upstream branches, push/fetch/pull of branches; or choosing between merge and rebase.*

## Core mental model: a branch is just a pointer

- Git stores **snapshots**, not diffs. A commit object holds: a pointer to the root **tree** (snapshot), author name/email, message, and pointers to its **parent(s)** — zero for the initial commit, one for a normal commit, two or more for a merge commit.
- One commit of three files creates **five objects**: three **blobs** (file contents), one **tree** (maps file names to blobs), one **commit** (metadata + pointer to the tree).
- A **branch** is a lightweight, movable pointer to a commit. Physically it is a file holding the 40-character SHA-1 of the commit — creating one costs writing 41 bytes (40 chars + newline). That is why branching is near-instant and Git encourages branching and merging many times a day, unlike older VCSs that copy the whole project directory.
- The checked-out branch's pointer **advances automatically** with each commit.
- **`HEAD`** is a special pointer to the local branch you are currently on. (Unlike HEAD in Subversion/CVS.)
- `master` is not special: it exists only because `git init` creates it by default. Likewise `origin` is just the default remote name `git clone` gives (`git clone -o booyah` yields `booyah/master`).
- Because commits record parents, Git finds the **merge base** automatically, making merges easy.
- All branching and merging is **local** — no server communication until you push/fetch.

## Creating and switching branches

```sh
git branch testing               # create pointer at current commit; does NOT switch
git checkout testing             # move HEAD to testing + rewrite working dir
git checkout -b iss53            # create and switch (= git branch iss53 && git checkout iss53)

# Git 2.23+
git switch testing-branch        # switch to existing branch
git switch -c new-branch         # create and switch (--create)
git switch -                     # return to previously checked-out branch
```

Seeing where pointers are:

```sh
git log --oneline --decorate                 # shows (HEAD -> master, testing) next to commits
git log --oneline --decorate --graph --all   # all branches + divergence as ASCII graph
git log testing                              # history of a specific branch
```

Gotchas:
- **`git log` shows only the history reachable from the checked-out branch** by default. A branch "missing" from the log has not vanished — pass its name or `--all`.
- **Switching branches rewrites your working directory**: Git adds, removes and modifies files so it matches the last commit on the target branch.
- If uncommitted changes in the working directory or staging area **conflict** with the target branch, Git refuses to switch. Aim for a clean working state before switching (workarounds: stashing and commit amending — see `chapters/07-git-tools.md`, "Stashing and Cleaning").
- After switching back to an older branch and committing, history **diverges**; both lines are isolated and can be merged later.

## Basic branching and merging workflow

Canonical scenario: you are on topic branch `iss53`, an urgent production bug arrives.

```sh
git checkout -b iss53                    # start story work
git commit -a -m 'Create new footer [issue 53]'
git checkout master                      # working dir now exactly as before iss53
git checkout -b hotfix
git commit -a -m 'Fix broken email address'
git checkout master
git merge hotfix                         # "Fast-forward"
git branch -d hotfix                     # master points at same commit; safe to delete
git checkout iss53                       # resume work
```

- The hotfix work is **not** in `iss53`. Either `git merge master` into `iss53` now, or wait until `iss53` is merged back into `master`.

### Two kinds of merge

| Situation | What Git does | Output |
|---|---|---|
| Target commit is reachable by following your current commit's history forward (no divergent work) | **Fast-forward**: simply moves the branch pointer ahead | `Fast-forward` |
| Histories diverged (current commit is not an ancestor of the merged branch) | **Three-way merge** of the two branch tips + their common ancestor; creates a new snapshot and a **merge commit** with more than one parent | `Merge made by the 'recursive' strategy.` |

Rule: check out the branch you want to merge **into**, then `git merge <other>`.

```sh
git checkout master
git merge iss53
git branch -d iss53     # close issue, delete branch
```

## Resolving merge conflicts

A conflict happens when the same part of the same file was changed differently on both branches. Git **pauses** — no merge commit is created.

```
$ git merge iss53
Auto-merging index.html
CONFLICT (content): Merge conflict in index.html
Automatic merge failed; fix conflicts and then commit the result.
```

Procedure:
1. `git status` — conflicted files appear under "Unmerged paths" as `both modified`.
2. Edit each file. Markers look like:
   ```
   <<<<<<< HEAD:index.html
   ...version from the branch you had checked out (HEAD)...
   =======
   ...version from the branch being merged (iss53)...
   >>>>>>> iss53:index.html
   ```
   Pick one side, the other, or combine — and **delete all `<<<<<<<`, `=======`, `>>>>>>>` lines**.
3. `git add <file>` on each resolved file — staging is what marks it resolved.
4. `git status` should report "All conflicts fixed but you are still merging."
5. `git commit` to finalize. The default message is `Merge branch 'iss53'` plus a `Conflicts:` list; consider adding how and why you resolved non-obvious conflicts.

Graphical alternative:

```sh
git mergetool            # launches a visual tool; lists candidates if merge.tool isn't configured
git mergetool --tool-help
```
- Without `merge.tool` configured Git picks a default (e.g. `opendiff` on macOS); type another listed name (kdiff3, meld, p4merge, vimdiff, …) to use it. After exiting, answer that the merge succeeded and Git stages the file for you.
- Harder conflicts: see "Advanced Merging" in `chapters/07-git-tools.md`.
- The merge commit template notes that `.git/MERGE_HEAD` marks an in-progress merge; remove it only if the commit should not be a merge.

## Branch management

```sh
git branch                    # list; * marks the branch HEAD points to
git branch -v                 # + last commit on each branch
git branch --merged           # branches already merged into current branch
git branch --no-merged        # branches with unmerged work
git branch --no-merged master # same question relative to master, without checking it out
git branch -d <name>          # safe delete; fails if not fully merged
git branch -D <name>          # force delete, discarding unmerged work
```

- Branches in `--merged` without a `*` are generally safe to delete with `-d` — their work is already incorporated elsewhere.
- `-d` on an unmerged branch errors with `The branch 'testing' is not fully merged.` — use `-D` only if you truly want to lose that work.
- `--merged`/`--no-merged` default to the current branch when no argument is given.

### Renaming a branch (local + remote)

Rules first: **don't rename branches collaborators are still using**; don't rename `master`/`main`/`mainline` casually.

```sh
git branch --move bad-branch-name corrected-branch-name   # local only
git push --set-upstream origin corrected-branch-name      # publish new name
git branch --all                                          # old name still on remote
git push origin --delete bad-branch-name                  # remove old remote branch
```

### Renaming the default branch (`master` → `main`)

Renaming the default branch breaks integrations, services, helper utilities and build/release scripts. Consult collaborators and search the repo for references first.

```sh
git branch --move master main
git push --set-upstream origin main
# remote still has master; remotes/origin/HEAD -> origin/master
```

Transition checklist before deleting the old branch:
- Update dependent projects' code/config.
- Update test-runner configuration.
- Adjust build and release scripts.
- Change repo-host settings: default branch, merge rules, anything matching branch names.
- Update docs referencing the old name.
- Close or merge PRs targeting the old branch.

Then, once `main` performs like `master` did:

```sh
git push origin --delete master
```

Until then, collaborators keep basing work on the remote `master`.

## Branching workflows

### Long-running branches (progressive stability)
- Since repeated three-way merges between the same branches stay easy, you can keep several always-open branches representing stability levels.
- Common pattern: `master` holds only fully stable (released / to-be-released) code; a parallel `develop` or `next` branch is where work is integrated and tested and is merged into `master` when stable. Topic branches merge into `develop`/`next` first.
- Larger projects add a `proposed` / `pu` (proposed updates) branch for integrated work not yet ready for `next` or `master`.
- Two views of the same thing: pointers at different heights on one commit line (stable ones lag behind), or **silos** that commits graduate through once tested.
- Optional — most helpful for very large or complex projects.

### Topic branches
- Short-lived branch for one feature or related piece of work; useful at any project size. Creating, merging and deleting several a day is normal.
- Benefits: fast, complete context switching; each branch contains only changes for one topic, which simplifies code review; merge in any order, after minutes or months.
- Example: branch `iss91`, then `iss91v2` off it to try an alternative, then `dumbidea` off `master`. Keep `iss91v2` and `dumbidea`, merge them, discard `iss91` (losing its commits).
- More workflow detail: `chapters/05-distributed-git.md`.

## Remote branches

### Remote references and remote-tracking branches
- **Remote references**: pointers (branches, tags, …) in remote repos. List explicitly with `git ls-remote <remote>` or `git remote show <remote>`.
- **Remote-tracking branches** (`<remote>/<branch>`, e.g. `origin/master`, `origin/iss53`): local refs you cannot move yourself; Git updates them during network communication. Treat them as **bookmarks of where remote branches were when you last connected**.
- After `git clone`, you get `origin/master` plus a local `master` starting at the same commit.
- If others push while you work locally, histories diverge; `origin/master` stays put until you contact the server.

```sh
git fetch origin          # download missing data, move origin/* pointers; working dir untouched
git remote add teamone <url>
git fetch teamone         # creates teamone/master (may transfer no data if objects already present)
```

### Pushing
- Local branches are **never synced automatically**; push explicitly. This lets you keep private branches private.

```sh
git push origin serverfix                 # expands to refs/heads/serverfix:refs/heads/serverfix
git push origin serverfix:serverfix       # same, explicit
git push origin serverfix:awesomebranch   # push local branch under a different remote name
```

- HTTPS pushes prompt for username/password; avoid retyping with an in-memory cache: `git config --global credential.helper cache` (more in "Credential Storage", `chapters/07-git-tools.md`).
- When collaborators fetch, they get `origin/serverfix` — a **non-editable** pointer, *not* a local `serverfix` branch. To use it:

```sh
git merge origin/serverfix                    # merge it into current branch, or
git checkout -b serverfix origin/serverfix    # own editable branch starting there
```

### Tracking (upstream) branches
- A **tracking branch** is a local branch with a direct relationship to a remote branch (its **upstream branch**). Checking out a local branch from a remote-tracking branch creates one. On a tracking branch, `git pull` knows which server and branch to fetch and merge.
- Clone normally makes `master` track `origin/master`.

```sh
git checkout -b <branch> <remote>/<branch>   # explicit
git checkout --track origin/serverfix        # shorthand, same local name
git checkout serverfix                       # shortcut: if branch doesn't exist and matches
                                             # a name on exactly one remote
git checkout -b sf origin/serverfix          # different local name
git branch -u origin/serverfix               # set/change upstream of existing branch
                                             # (--set-upstream-to)
```

- `@{upstream}` / `@{u}` refers to the upstream branch: `git merge @{u}` instead of `git merge origin/master`.
- `git branch -vv` lists each branch's upstream and ahead/behind counts, e.g. `[teamone/server-fix-good: ahead 3, behind 1]` = 3 local commits not pushed, 1 server commit not merged. No bracket = not tracking.
- **Gotcha**: those counts reflect only the last fetch; the command doesn't contact servers. For fresh numbers: `git fetch --all; git branch -vv`.

### Pulling
- `git fetch` never modifies your working directory.
- `git pull` is, in most cases, `git fetch` immediately followed by `git merge` of the current branch's upstream.

### Deleting remote branches

```sh
git push origin --delete serverfix
```
Only removes the pointer on the server; data generally lingers until garbage collection, so accidental deletions are often recoverable.

## Rebasing

### What rebase does
Two ways to integrate one branch into another: **merge** and **rebase**.

```sh
git checkout experiment
git rebase master          # replay experiment's commits on top of master
git checkout master
git merge experiment       # now a fast-forward
```

Mechanics: find the common ancestor of the current branch and the target; take the diff of each commit on the current branch; save them to temporary files; reset the current branch to the target commit; apply each change in order.

- The final snapshot is **identical** to what a merge would produce — only the **history differs**. Rebase yields a linear history that looks serial even when work was parallel.
- Merging joins the endpoints; rebasing replays changes in the order they were introduced.
- Typical use: before submitting patches to a project you don't maintain, rebase your work onto `origin/master` so the maintainer needs only a fast-forward or clean apply.

### Advanced forms

```sh
git rebase --onto master server client   # take commits on client since it diverged from server,
                                         # replay them as if client branched from master
git checkout master && git merge client  # fast-forward

git rebase master server                 # rebase <basebranch> <topicbranch>: checks out server
                                         # for you, replays it onto master
git checkout master && git merge server
git branch -d client
git branch -d server
```

Use `--onto` when a topic branch was cut from another topic branch and you want to ship only the second one.

### The perils of rebasing — the golden rule

> Do not rebase commits that exist outside your repository and that people may have based work on.

- Rebase **abandons existing commits and creates new, similar-but-different ones**. If others built on the originals and you force-push the rewrite, they must re-merge, and pulling their work back gets messy.
- Failure scenario: a collaborator pushes a merge, you merge it into your work, they rebase and `git push --force`. A plain `git pull` then creates a merge commit containing both lines; `git log` shows duplicate commits (same author, date, message), and pushing reintroduces the commits they intended to remove.

Safety ladder:
- Rebasing commits that never left your machine: fine.
- Rebasing pushed commits nobody has built on: fine.
- Rebasing publicly pushed commits others may have built on: trouble.

### Recovering: rebase when they rebase
- Besides the commit SHA-1, Git computes a **patch-id** — a checksum of only the patch a commit introduces.
- Rebasing onto the force-pushed branch (e.g. `git rebase teamone/master`) makes Git: find commits unique to your branch; drop merge commits; drop commits whose patch already exists in the target (same patch-id); apply the remaining ones on top of the target.
- Works only if the rewritten commits are nearly the same patch; otherwise Git adds a duplicate that likely fails to apply cleanly.

```sh
git pull --rebase                         # fetch + rebase instead of fetch + merge
git fetch && git rebase teamone/master    # manual equivalent
git config --global pull.rebase true      # make --rebase the default for git pull
```

If anyone must force-push rewritten history, make sure everyone knows to use `git pull --rebase`.

## Rebase vs. merge — decision framework

Two views of what history is:
- **Record of what actually happened** — a historical document; rewriting it misrepresents events. Messy merge commits are kept as-is.
- **Story of how the project was made** — like editing a draft before publishing; clean it up with tools like `rebase` and `filter-branch` before it reaches the mainline.

There is no universal winner; choose per team and project. The pragmatic "best of both" rule:

- **Rebase local, unpushed work to tidy it before pushing; never rebase anything you've already pushed somewhere.**

See also: the `refs/heads/` refspec layout in `chapters/10-git-internals.md`; team workflows in `chapters/05-distributed-git.md`.
