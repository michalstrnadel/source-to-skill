---
name: pro-git
description: Git mental models, commands and workflows distilled from Pro Git (2nd ed., Chacon & Straub). Load when explaining how Git works (snapshots, the three trees, branches as pointers, objects and refs), choosing between merge and rebase or a team workflow, undoing or rewriting history safely (reset, revert, rebase -i, reflog recovery), debugging with bisect/blame, setting up a Git server, hooks or .gitattributes, working with GitHub PRs, submodules, or bridging Git to SVN, Mercurial or Perforce.
---

# Pro Git

> Derived from *Pro Git*, 2nd edition, by Scott Chacon and Ben Straub, licensed CC BY-NC-SA 3.0 (https://creativecommons.org/licenses/by-nc-sa/3.0). This distillation carries the same license.

The book covers the CLI from first principles. Chapters 1–3 teach the model, 4–6 cover collaboration, 7–8 cover power tools and customization, 9 covers other VCSs and 10 covers internals. Load a chapter file when a question needs its detail. The models below answer most "why does Git do that?" questions.

## Core mental models

1. **Snapshots, not deltas.** Each commit records the full state of the project. Unchanged files are stored as references to the copy Git already has. Bringing a CVS/SVN "list of file changes" mental model into Git is the root of most confusion. → [Ch1](chapters/01-getting-started.md)
2. **Nearly everything is local, and content is checksummed.** The full history lives in your clone, so log, diff and commit work offline. Everything is addressed by SHA-1, so silent corruption is detectable. Git mostly *adds* data: anything committed is very hard to lose. Uncommitted work has no such protection.
3. **Three states and three trees.** A file is modified (working tree), staged (index) or committed (Git directory/HEAD). `git add` stages *the content as it is at that moment*. Edit the file again and it is both staged and unstaged. `git diff` compares working tree with index; `git diff --staged` compares index with last commit. → [Ch2](chapters/02-git-basics.md)
4. **A branch is a 41-byte file holding a commit SHA-1; HEAD points to the current branch.** Branching is nearly free, and committing moves the current branch forward. A fast-forward merge just moves a pointer. A diverged merge is a three-way merge (two tips plus their common ancestor) and makes a commit with multiple parents. → [Ch3](chapters/03-git-branching.md)
5. **Remote-tracking branches are bookmarks.** `origin/master` records where the remote was at your last fetch, and only network operations move it. `fetch` only downloads. `pull` = fetch + merge (or rebase). A push is refused when someone pushed first, because Git never merges on the server.
6. **Merge vs rebase gives the same snapshot and a different story.** Rebase replays commits to make linear history and creates *new* commits. The rule: rebase local work before pushing, and never rebase commits others may have built on. → [Ch3](chapters/03-git-branching.md), [Ch5](chapters/05-distributed-git.md)
7. **`reset` is three steps.** (1) Move the branch HEAD points to: `--soft` stops here. (2) Make the index match: the default `--mixed` stops here. (3) Make the working tree match: only `--hard`, the one form that can destroy uncommitted work. With a path, step 1 is skipped. `checkout`/`switch` moves HEAD itself, while `reset` moves the branch under it. → [Ch7](chapters/07-git-tools.md)
8. **Rewriting changes SHA-1s.** Amend, `rebase -i`, `filter-branch` and reset rewrite the target commit and every commit after it. For shared history use `git revert` (`-m 1` for a merge) instead.
9. **Git is a content-addressable store.** Blobs hold file contents with no names. Trees map names to blobs and subtrees. Commits point to a tree, parents and author info. Tags point to objects. Refs are files naming SHA-1s. Objects start loose and get delta-compressed into packfiles. Anything reachable stays in every clone, so removing a big file means rewriting history. → [Ch10](chapters/10-git-internals.md)
10. **Hooks are local convenience; server hooks are policy.** Client hooks are not cloned and `--no-verify` bypasses them. Enforce rules in `pre-receive`/`update` on the server. → [Ch8](chapters/08-customizing-git.md)

## Decision rules (most-asked)

- **Undo something:**
  - Unstage a file: `git restore --staged <f>`.
  - Discard working-tree edits: `git restore <f>`. This is permanent; stash or branch if unsure.
  - Fix the last unpushed commit: `git commit --amend`.
  - Undo pushed work: `git revert`.
  - Find "lost" commits: `git reflog`, then `git branch recover <sha>`.
- **Which workflow?**
  - Small team: one shared repo (centralized).
  - Open source: fork + pull request (integration manager).
  - Very large projects: lieutenants plus a benevolent dictator.
  → [Ch5](chapters/05-distributed-git.md)
- **Updating a stale PR or contribution:**
  - Merge upstream into your branch.
  - If you rebase, push to a new branch and open a new PR rather than force-pushing over an open one. → [Ch6](chapters/06-github.md)
- **Which protocol for a server?**
  - SSH: authenticated push.
  - Smart HTTPS: auth plus anonymous reads from one URL.
  - `git://`: fast anonymous reads, but no auth or encryption.
  - Avoid cloning over `git://` or plain `http://`, because of man-in-the-middle risk. → [Ch4](chapters/04-git-on-the-server.md)
- **Recurring conflicts:** `git config --global rerere.enabled true`. When conflicts are only whitespace, `git merge -Xignore-space-change`. → [Ch7](chapters/07-git-tools.md)
- **Bridging to SVN/Perforce:** keep history linear (rebase, no merges). Submit or dcommit before pushing to any Git remote, because the bridge rewrites commits. → [Ch9](chapters/09-git-and-other-systems.md)

## Chapter index

| # | Chapter | One-line takeaway | File |
|---|---|---|---|
| 1 | Getting Started | Git stores local, checksummed snapshots in three states; set your identity once, since it's baked into every commit. | [chapters/01-getting-started.md](chapters/01-getting-started.md) |
| 2 | Git Basics | The daily loop: stage exact content, inspect with status/diff, commit, read log, undo carefully, sync remotes, push tags explicitly. | [chapters/02-git-basics.md](chapters/02-git-basics.md) |
| 3 | Git Branching | Branches are cheap movable pointers; fast-forward vs three-way merge; rebase locally, never rebase shared commits. | [chapters/03-git-branching.md](chapters/03-git-branching.md) |
| 4 | Git on the Server | A bare repo plus SSH is enough; Smart HTTP covers authenticated and anonymous access on one URL; hosting trades control for zero maintenance. | [chapters/04-git-on-the-server.md](chapters/04-git-on-the-server.md) |
| 5 | Distributed Git | Pick a workflow, contribute via clean topic branches and good commit messages, maintain with patches, triple-dot review, tags, describe and archive. | [chapters/05-distributed-git.md](chapters/05-distributed-git.md) |
| 6 | GitHub | Fork, topic branch, PR as a conversation; keep PRs mergeable; PR refs, webhooks and the token API for automation. | [chapters/06-github.md](chapters/06-github.md) |
| 7 | Git Tools | Revision ranges, partial staging, stash/clean, signing, search, history rewriting, reset demystified, advanced merging, rerere, bisect, submodules, bundles, credentials. | [chapters/07-git-tools.md](chapters/07-git-tools.md) |
| 8 | Customizing Git | Config for preferences, .gitattributes for per-path behaviour (diff/filter/merge drivers), hooks for events; enforce policy server-side. | [chapters/08-customizing-git.md](chapters/08-customizing-git.md) |
| 9 | Git and Other Systems | Use git svn, git-remote-hg or git-p4 with linear history; migrate projects via importers or a custom `git fast-import` script. | [chapters/09-git-and-other-systems.md](chapters/09-git-and-other-systems.md) |
| 10 | Git Internals | Objects (blob/tree/commit/tag) keyed by SHA-1, refs, packfiles, refspecs, transfer protocols, maintenance, data recovery, env vars. | [chapters/10-git-internals.md](chapters/10-git-internals.md) |
| A | Git in Other Environments | No GUI exceeds the CLI; gitk/git-gui, IDE integrations, and shell completion and prompts for Bash, Zsh and PowerShell. | [chapters/11-appendix-a-git-in-other-environments.md](chapters/11-appendix-a-git-in-other-environments.md) |
| B | Embedding Git | Shell out to the CLI or embed Libgit2 (and bindings), JGit, go-git or Dulwich; their conventions and pitfalls. | [chapters/12-appendix-b-embedding-git.md](chapters/12-appendix-b-embedding-git.md) |
| C | Git Commands | Purpose-grouped index of porcelain commands and where the book covers them, plus `core.editor` values for ~20 editors. | [chapters/13-appendix-c-git-commands.md](chapters/13-appendix-c-git-commands.md) |

## Support files

- [cheatsheet.md](cheatsheet.md) — decision rules, named techniques, commands and anti-patterns from the whole book.
- [glossary.md](glossary.md) — key terms A–Z with the chapter each comes from.

Caveats: the book predates some newer Git features. GitHub UI details in Ch6 are dated, and the book itself recommends `git-filter-repo` over `filter-branch`. Figures are not reproduced.
