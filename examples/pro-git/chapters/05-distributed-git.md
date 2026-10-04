# Chapter 5 — Distributed Git

*Load when choosing a team workflow, contributing to someone else's project (shared repo, fork, or email patches), or maintaining a project: applying patches, reviewing contributed branches, integrating, tagging and cutting releases.*

## Core mental model

- In a centralized VCS every developer is a node talking to one hub. In Git every developer can be **both a node and a hub**: contribute to other repositories and also publish a repository others build on. Workflows are therefore a team choice, not a tool constraint, and you can mix features of several.
- Two roles run through the chapter: **contributor** (make your work easy to accept) and **integrator/maintainer** (accept work in a way that is clear to contributors and sustainable for you).
- Git never merges on the server for you. If someone pushed first, your push is rejected as non-fast-forward until you fetch and merge (or rebase) locally — even when you touched different files. This is the key surprise for Subversion users.

## Choosing a workflow

| Workflow | Shape | Use when | Trade-off |
|---|---|---|---|
| Centralized | One shared repo, everyone has push access | Team already comfortable with a central model; scales to many devs using branches | Second pusher must merge first; Git refuses to let anyone overwrite others |
| Integration-manager | Canonical repo + each dev's public clone; maintainer pulls from contributors' repos | Hub-style hosting (GitHub, GitLab forks) | Everyone works at their own pace; maintainer can pull any time |
| Dictator and lieutenants | Devs → lieutenants (own subsystems) → benevolent dictator → reference repo | Huge, hierarchical projects (e.g. the Linux kernel) | Rare; lets the leader delegate and collect large subsets of code before integrating |

Dictator/lieutenants flow, step by step:
1. Developers work on topic branches and rebase onto `master` of the reference repository.
2. Lieutenants merge developers' topic branches into their own `master`.
3. The dictator merges lieutenants' `master` branches into the dictator's `master`.
4. The dictator pushes to the reference repo; everyone rebases on it.

Integration-manager flow: maintainer pushes public repo → contributor clones and changes → contributor pushes to own public copy → contributor asks maintainer to pull → maintainer adds contributor's repo as a remote, merges locally → maintainer pushes to main repo.

For a broader comparison of branching strategies (including high vs low integration frequency), the chapter points to Martin Fowler's "Patterns for Managing Source Code Branches": https://martinfowler.com/articles/branching-patterns.html

## Variables that decide how you contribute

Before contributing, answer:
- **Active contributor count / velocity** — two devs with a few commits a day vs thousands of devs and hundreds of commits daily. More activity means your change is more likely to go stale or break before it is applied.
- **Workflow in use** — equal write access? A maintainer who checks every patch? Peer review? Lieutenants you submit to first?
- **Your commit access** — with write access vs without changes everything. Without it: what does the project accept (fork + PR, email patches)? Is there a policy?
- **Size and frequency** of your contributions.

## Commit guidelines (apply to every workflow)

The Git project documents these in `Documentation/SubmittingPatches` in its source tree.

- **No whitespace errors.** Run before committing:
  ```
  $ git diff --check
  ```
  It lists possible whitespace problems.
- **One logical change per commit.** Don't bundle a weekend of work on five issues into one Monday commit. Use the staging area to split into at least one commit per issue; for changes in the same file, partially stage with `git add --patch` (see `chapters/07-git-tools.md`, Interactive Staging). The tip snapshot is identical whether you make one commit or five — so optimize for reviewers. Separate commits also make it easy to pull out or revert one change later.
- **Clean up before sharing** with history-rewriting tools (`chapters/07-git-tools.md`, Rewriting History).
- **Message format:**
  - Summary line of about 50 characters or less, capitalized.
  - Blank line (critical — tools like rebase get confused without it, unless there is no body at all).
  - Body wrapped at about 72 characters explaining the **motivation** and contrasting the new implementation with previous behavior (the Git project requires this).
  - **Imperative mood**: "Fix bug", not "Fixed bug" / "Fixes bug" — matches messages that `git merge` and `git revert` generate.
  - Further paragraphs separated by blank lines; hyphen/asterisk bullets with hanging indent are fine.
  - In email contexts the first line becomes the subject and the rest the body.

Template (adapted by the book from Tim Pope):
```
Capitalized, short (50 chars or less) summary

More detailed explanatory text, if necessary.  Wrap it to about 72
characters or so.  In some contexts, the first line is treated as the
subject of an email and the rest of the text as the body.  The blank
line separating the summary from the body is critical (unless you omit
the body entirely); tools like rebase will confuse you if you run the
two together.

Further paragraphs come after blank lines.

  - Bullet points are okay, too
  - Use a hanging indent
```
To see a well-formatted history, run `git log --no-merges` in the Git project. The book admits it mostly uses `git commit -m` for brevity: "do as we say, not as we do."

## Contributor scenario 1 — Private small team (shared push access)

Feels like Subversion, but merges happen client-side, not on the server at commit time.

```
# Jessica pushed first; John's push is rejected:
$ git push origin master
 ! [rejected]        master -> master (non-fast forward)

# John: fetch (does NOT merge), then merge, test, push
$ git fetch origin
$ git merge origin/master
$ git push origin master
```

Reading push output: `<oldref>..<newref>  fromref -> toref`, e.g. `1edee6b..fbff5bc  master -> master` = remote `master` moved from 1edee6b to fbff5bc using your local `master`.

Before integrating, see exactly what upstream has that your topic branch lacks:
```
$ git log --no-merges issue54..origin/master
```
`A..B` = commits reachable from B but not from A (detail: Commit Ranges, `chapters/07-git-tools.md`).

Integrating topic work plus upstream:
```
$ git checkout master        # "behind 'origin/master' by 2 commits, and can be fast-forwarded"
$ git merge issue54          # fast-forward
$ git merge origin/master    # real merge
$ git push origin master
```
Order of merging `issue54` vs `origin/master` doesn't matter for the final snapshot — only the history shape differs.

General loop: work in a topic branch → merge into `master` when ready → when sharing, fetch and merge `origin/master` if it moved → push `master`.

## Contributor scenario 2 — Private managed team (integrators own master)

Small groups share feature branches on the server; only integrators update `master`.

```
$ git checkout -b featureA
$ git commit -am 'Add limit to log function'
$ git push -u origin featureA                 # share with a teammate

$ git fetch origin
$ git checkout -b featureB origin/master      # start next feature from server's master

$ git fetch origin                            # teammate already pushed featureBee
$ git merge origin/featureBee
$ git push -u origin featureB:featureBee      # refspec: local featureB -> remote featureBee
```
- `local:remote` in push is a **refspec** (deep dive: The Refspec, `chapters/10-git-internals.md`).
- `-u` = `--set-upstream`: configures tracking so later `git push` / `git pull` need no arguments.
- Review a teammate's new commits before merging: `git log featureA..origin/featureA`, then `git checkout featureA && git merge origin/featureA`.
- Teams then tell integrators that branches are ready; integrators merge to mainline.
- Benefit: subgroups collaborate on remote branches without involving or blocking the whole team; lines of work merge late.

## Contributor scenario 3 — Forked public project

```
$ git clone <url>
$ cd project
$ git checkout -b featureA
# ... work, commit ...
$ git remote add myfork <url>          # after clicking "Fork" on the host
$ git push -u myfork featureA
$ git request-pull origin/master myfork
```
- Optionally squash/reorder with `rebase -i` first so the patch is easier to review.
- **Push the topic branch, not a merged `master`.** If your work is rejected or cherry-picked you then don't have to rewind `master`; accepted work comes back to you when you pull upstream anyway.
- `git request-pull <base> <repo-url>` prints a summary (base commit, commits by author, diffstat, where to pull from) you can email to the maintainer. GitHub has its own Pull Request mechanism (`chapters/06-github.md`).
- Keep `master` tracking `origin/master`; isolate each theme in a **topic branch** that you can discard if rejected. Start each new topic from upstream, not from your previous topic:
  ```
  $ git checkout -b featureB origin/master
  ```
  Topics then behave like independent patch queues you can rebase/rewrite without interference.

**Topic no longer merges cleanly** — rebase onto upstream, resolve conflicts yourself, force-push:
```
$ git checkout featureA
$ git rebase origin/master
$ git push -f myfork featureA
```
`-f` is required because the new tip isn't a descendant of the old one. Alternative: push to a new branch name (e.g. `featureAv2`).

**Maintainer asks for an implementation change** — rebuild on current upstream as a fresh branch:
```
$ git checkout -b featureBv2 origin/master
$ git merge --squash featureB
# ... change implementation ...
$ git commit
$ git push myfork featureBv2
```
- `--squash`: brings in all changes of the other branch as if merged, but makes no merge commit; your next commit has a single parent and you can add more changes first.
- `--no-commit`: delays the merge commit in a normal merge.

## Contributor scenario 4 — Public project over email

Same topic-branch discipline; submission is by mail to the developer list. Check each project's rules — they differ.

```
$ git format-patch -M origin/master
0001-add-limit-to-log-function.patch
0002-increase-log-output-to-30-from-25.patch
```
- `format-patch` makes one mbox-formatted email per commit: first message line → `Subject: [PATCH n/m] ...`, rest of message + diff → body. Applying such patches preserves all commit info.
- `-M` detects renames.
- Text added between the `---` line and the `diff --git` line is visible to reviewers but ignored when applying — use it for notes that shouldn't be in the commit message.
- **Don't paste patches into a "smart" mail client** — it may mangle newlines/whitespace.

Send via IMAP drafts (`~/.gitconfig`):
```
[imap]
  folder = "[Gmail]/Drafts"
  host = imaps://imap.gmail.com
  user = user@gmail.com
  pass = YX]8g76G_2^sFbd
  port = 993
  sslverify = false
```
Without SSL, drop the last two lines and use `imap://`. Then `cat *.patch | git imap-send`, fill in To/CC in Drafts, send.

Or via SMTP:
```
[sendemail]
  smtpencryption = tls
  smtpserver = smtp.gmail.com
  smtpuser = user@gmail.com
  smtpserverport = 587
```
```
$ git send-email *.patch
```
It prompts for From, To, and an In-Reply-To Message-ID. Per-client instructions are at the end of `Documentation/SubmittingPatches`; a practice sandbox is at git-send-email.io.

## Maintaining a project

### Try every contribution in a topic branch
- A temporary branch per incoming change, easy to tweak or park. Name it by theme; the Git maintainer namespaces by contributor initials:
  ```
  $ git branch sc/ruby_client master
  $ git checkout -b sc/ruby_client master   # create and switch
  ```

### Applying emailed patches: `apply` vs `am`

| | `git apply` | `git am` |
|---|---|---|
| Input | Output of `git diff` / Unix `diff` (legacy patches) | `format-patch` output / mbox |
| Result | Changes working directory only; you stage and commit | Creates commits with author, date and message from the email |
| Notes | Like `patch -p1` but stricter (fewer fuzzy matches), handles adds/deletes/renames, all-or-nothing | Name = "apply a series of patches from a mailbox" |

```
$ git apply /tmp/patch-ruby-client.patch
$ git apply --check 0001-see-if-this-helps-the-gem.patch   # dry run; silent = clean; non-zero exit on failure (scriptable)
$ git am 0001-limit-log-function.patch
```
- Encourage contributors to use `format-patch`, not `diff`.
- After `am`, `git log --pretty=fuller -1` shows **Author** (who wrote the patch, when) separately from **Commit** (who applied it, when).
- Point `git am` at a whole mbox file to apply a saved patch series.

When `am` fails it leaves conflict markers, like a conflicted merge/rebase:
```
$ (fix the file)
$ git add ticgit.gemspec
$ git am --resolved          # continue   (also: git am --skip, git am --abort)
```
- `git am -3` tries a three-way merge. Not default because it only works if the patch's base commit exists in your repo (i.e. it was based on a public commit); when it does, it's much smarter (it can even detect "Patch already applied").
- `git am -3 -i mbox` — interactive: per patch, `[y]es/[n]o/[e]dit/[v]iew patch/[a]ccept all`.

### Pulling from contributors' repositories
```
$ git remote add jessica https://github.com/jessica/myproject.git
$ git fetch jessica
$ git checkout -b rubyclient jessica/ruby-client
```
- Best for people you work with repeatedly; you also get their real history, so a proper three-way merge is the default (no need for `-3` and hoping the base is public).
- For occasional one-patch contributors, email is less overhead than maintaining hundreds of remotes.
- One-time pull without saving a remote:
  ```
  $ git pull https://github.com/onetimeguy/project
  ```

### Determine what a branch introduces
```
$ git log contrib --not master        # same as master..contrib
$ git log -p contrib --not master     # plus each commit's diff
$ git diff master...contrib           # only what contrib added since the common ancestor
```
- **Gotcha:** `git diff master` from the topic branch compares the two tip snapshots. If `master` moved on, anything new on `master` shows up as if your topic were deleting it. Diff against the merge base instead:
  ```
  $ git merge-base contrib master
  $ git diff $(git merge-base contrib master)
  ```
  The triple-dot form above is the shorthand — remember it.

### Integration workflows

- **Simple merge**: `master` holds stable code; merge each finished/verified topic into it, delete the topic, repeat. Simplest, but risky for large/stable projects.
- **Two-phase merge cycle**: long-running `master` (only advanced when a very stable release is cut) and `develop` (all new code). Merge topics into `develop`; at release, tag and **fast-forward** `master` to `develop`. Users can track `master` for stable or `develop` for cutting edge. Extension: add an `integrate` branch → once stable and tests pass, merge into `develop` → after proven, fast-forward `master`.
- **Large-merging (Git project itself)**: long-running `master`, `next`, `seen` (formerly `pu`, "proposed updates"), and `maint`.
  - Safe topics → merged into `next` and published for testing together.
  - Topics needing more work → merged into `seen`.
  - Fully stable → re-merged into `master`; `next` and `seen` are then rebuilt from `master`.
  - So `master` almost always moves forward, `next` is rebased occasionally, `seen` even more often. Topics are deleted once in `master`.
  - `maint` is forked from the last release for backported maintenance fixes. See the Git Maintainer's guide for details.
- **Rebase / cherry-pick (linear history)**: rebase the topic onto `master` (or `develop`) then fast-forward. Or cherry-pick single commits — "a rebase for a single commit":
  ```
  $ git cherry-pick e43a6
  ```
  The change is reapplied with a **new SHA-1** (different apply date). Useful to take one commit out of many, or instead of rebasing a one-commit topic. Then delete the topic, dropping unwanted commits.

### Rerere ("reuse recorded resolution")
- Records pre/post images of conflict resolutions; when an identical conflict reappears, Git reuses your earlier fix automatically. Helpful with frequent merging/rebasing or long-lived topic branches.
  ```
  $ git config --global rerere.enabled true
  $ git rerere        # manually match current conflicts against the cache (automatic if enabled)
  ```
  Subcommands exist to show what will be recorded, forget one resolution, and clear the cache. Detail: `chapters/07-git-tools.md`, Rerere.

### Tagging releases (and distributing your signing key)
```
$ git tag -s v1.5 -m 'my signed 1.5 tag'
```
Publish your public PGP key inside the repo, as the Git maintainer does:
```
$ gpg --list-keys
$ gpg -a --export F721C45A | git hash-object -w --stdin      # stores key as a blob, prints its SHA-1
$ git tag -a maintainer-pgp-pub 659ef797d181633c87ec71ac3f9ba29fe5775b92
$ git push --tags
# users:
$ git show maintainer-pgp-pub | gpg --import
```
Put verification instructions in the tag message so `git show <tag>` displays them.

### Build numbers with `git describe`
```
$ git describe master
v1.6.2-rc1-20-g8c5b85c
```
- Format: nearest earlier tag – commits since that tag – `g` + abbreviated SHA-1. On a tagged commit it prints just the tag name. `git --version` of a source-built Git looks like this.
- Requires **annotated** tags (`-a`/`-s`) by default; add `--tags` to also use lightweight tags.
- Usable as a target for `git checkout`/`git show`, but **not forever**: it depends on the abbreviated SHA-1, which may become ambiguous (the Linux kernel went from 8 to 10 characters, invalidating older describe names).

### Preparing a release archive
```
$ git archive master --prefix='project/' | gzip > `git describe master`.tar.gz
$ git archive master --prefix='project/' --format=zip > `git describe master`.zip
```
Extracts the snapshot under a `project/` directory, for people who don't use Git.

### Changelog for the mailing list
```
$ git shortlog --no-merges master --not v1.0.1
```
Summarizes all commits since `v1.0.1`, grouped by author with counts.

## Anti-patterns and gotchas (quick list)
- Expecting the server to merge different-file changes like Subversion — Git rejects the push; merge locally.
- Treating `git fetch` as a merge — it only updates `origin/*`.
- Committing a big multi-issue blob; past-tense or run-together commit messages.
- Pushing your merged `master` to your fork instead of a topic branch.
- Building a second contribution on top of the first topic branch instead of `origin/master`.
- Pasting patches into a mail client that rewrites whitespace.
- Generating patches with plain `diff` when `format-patch` would preserve authorship and message.
- Reviewing with `git diff master` after `master` has moved — use `master...topic`.
- Relying on old `git describe` strings as permanent identifiers.
