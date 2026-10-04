# Pro Git — Cheatsheet

Decision rules, named techniques, commands and anti-patterns from across the book. Chapter numbers point to `chapters/`.

## Setup and configuration

- `git config --global user.name "John Doe"` and `git config --global user.email johndoe@example.com`. Every commit records your identity and it can't be changed afterwards. Inside one repo, the same command without `--global` overrides it. (Ch1)
- Precedence: local (`.git/config`) beats global (`~/.gitconfig`), which beats system (`[path]/etc/gitconfig`). To find where a surprising value comes from: `git config --show-origin <key>` or `git config --list --show-origin`. (Ch1, Ch8)
- `git config --global init.defaultBranch main` (Git 2.28+). `git config --global core.editor "code --wait"` (other editors: Appendix C). (Ch1, App C)
- Line endings: `core.autocrlf true` on Windows, `input` on macOS/Linux, `false` for Windows-only projects. (Ch8)
- One ignore file for all repos: `git config --global core.excludesfile ~/.gitignore_global`. Team commit template: `git config --global commit.template ~/.gitmessage.txt`. (Ch8)
- Help: `git help <verb>`, `git <verb> --help`, quick options with `git <verb> -h`. (Ch1)

## Daily loop

- Rule: if you edit a file after `git add`, re-add it. Otherwise the commit gets the older staged version. (Ch2)
- `git status -s`: left column = staging area, right column = working tree, `??` = untracked. (Ch2)
- `git diff` shows unstaged changes. `git diff --staged` (also `--cached`) shows what will be committed. (Ch2)
- `git commit -a -m 'msg'` skips staging for tracked files. Anti-pattern: it can sweep in changes you didn't mean to commit. (Ch2)
- `git rm --cached <file>` stops tracking a file but keeps it on disk. `git mv` is equivalent to mv + rm + add, and Git infers renames. (Ch2)
- Check for whitespace errors before committing: `git diff --check`. (Ch5)
- Commit messages: one logical change per commit. Summary of about 50 characters, blank line, body wrapped at about 72 characters explaining motivation versus previous behaviour, imperative mood ("Fix bug"). (Ch5)

## History and search

- `git log --oneline --decorate --graph --all` shows every branch and where history diverged. Plain `git log` shows only the current branch. (Ch3)
- Filters: `git log --since=2.weeks --author=X --grep=Y --no-merges -- path`. Add `--all-match` to require all `--grep` patterns. (Ch2)
- Pickaxe: `git log -S <string>` finds commits that changed how often a string occurs. `git log -L :func:file` shows a function's history. (Ch2, Ch7)
- Use `--pretty=format:"%h - %an, %ar : %s"` for machine parsing, because its output stays stable across Git versions. (Ch2)
- Ranges: `A..B` = in B but not A. `git log origin/master..HEAD` shows what a push would send. `A...B --left-right` = commits on one side or the other but not both. (Ch7)
- Ancestry: `HEAD^2` = second parent of a merge, `HEAD~3` = three first-parent steps back. `master@{yesterday}` and `HEAD@{n}` read the local reflog. (Ch7)
- `git blame -L 69,82 <file>` shows who last touched lines. Add `-C` to trace code that moved from other files. (Ch7)
- Bisect: `git bisect start HEAD v1.0 && git bisect run test-error.sh`, and always finish with `git bisect reset`. (Ch7)

## Undoing and rewriting

- Unstage: `git restore --staged <file>` (older form: `git reset HEAD <file>`). (Ch2)
- Anti-pattern: `git restore <file>` / `git checkout -- <file>` permanently discards local edits. Stash or branch instead if unsure. (Ch2)
- `git commit --amend` replaces the last commit. Rule: only amend local, unpushed commits. (Ch2)
- Reset modes: `--soft` keeps changes staged, the default `--mixed` keeps them unstaged, `--hard` discards them. Only `--hard` can destroy uncommitted work. (Ch7)
- To squash WIP commits: `git reset --soft HEAD~2 && git commit`. (Ch7)
- `git rebase -i HEAD~3` passes the parent of the oldest commit to edit. The todo list runs oldest first: pick/reword/edit/squash/fixup/exec/break/drop. (Ch7)
- To split a commit: mark it `edit`, run `git reset HEAD^`, make the partial commits, then `git rebase --continue`. (Ch7)
- Undo a shared merge: `git revert -m 1 HEAD`. Anti-pattern: merging that topic again without first reverting the revert. Git reports "Already up-to-date" or brings in only the newer commits. (Ch7)
- Recover lost commits: `git reflog` / `git log -g`, then `git branch recover-branch <sha>`. With no reflog: `git fsck --full` and look for dangling commits. (Ch10)
- Purge a big file from history: find it with `git verify-pack -v .git/objects/pack/pack-*.idx | sort -k 3 -n | tail -3` and `git rev-list --objects --all | grep <sha>`. Then run `git filter-branch --index-filter 'git rm --ignore-unmatch --cached <file>' -- <first-commit>^..`, remove `.git/refs/original` and `.git/logs/`, and run `git gc`. Prefer git-filter-repo over filter-branch. (Ch10, Ch7)
- Anti-pattern: deleting a big file in a later commit. The repo doesn't shrink, because history still holds the file. (Ch10)

## Stash and clean

- `git stash` / `git stash push`, then `git stash pop`. `git stash apply --index` restores the staged state too. `git add -p` and `git stash -p` work hunk by hunk. (Ch7)
- `git clean -d -n` is a dry run; follow it with `git clean -f -d`. `-x` also removes ignored files. `git stash --all` is the safer alternative. (Ch7)

## Branching and merging

- Create and switch: `git checkout -b <name>` or `git switch -c <name>`. Go back with `git switch -`. (Ch3)
- Rule: switch with a clean working state. Git refuses when uncommitted changes conflict with the target. (Ch3)
- Conflicts: remove the `<<<<<<< ======= >>>>>>>` markers, `git add`, `git commit` (or use `git mergetool`). `git checkout --conflict=diff3 <file>` shows the base version, or set `git config --global merge.conflictstyle diff3`. (Ch3, Ch7)
- Whitespace-only conflicts: `git merge --abort`, then `git merge -Xignore-space-change <branch>`. (Ch7)
- Turn on rerere so Git replays your earlier conflict resolutions: `git config --global rerere.enabled true`. (Ch5, Ch7)
- Cleanup: `git branch --merged` lists branches safe to delete with `-d`. `-D` on an unmerged branch throws work away. (Ch3)
- Move a sub-topic branch: `git rebase --onto master server client`. (Ch3)
- Anti-pattern: rebasing or force-pushing commits others may have based work on. If it happens to you, recover with `git pull --rebase`. (Ch3)
- `git merge --squash featureB` brings in the changes without a merge commit. `git cherry-pick <sha>` reapplies one commit, which gets a new SHA-1. (Ch5)

## Remotes, tags and sharing

- Track a remote branch: `git checkout --track origin/serverfix` or `git branch -u origin/serverfix`. `git branch -vv` ahead/behind counts are only as fresh as the last fetch, so run `git fetch --all` first. (Ch3)
- Push under a different remote name with tracking: `git push -u origin featureB:featureBee`. Delete a remote branch: `git push origin --delete <branch>`. (Ch5, Ch3)
- Rename a branch everywhere: `git branch --move old new`, `git push --set-upstream origin new`, `git push origin --delete old`. Before renaming master to main, update collaborators, CI, scripts, docs and open PRs. (Ch3)
- Tags are not pushed by default: `git push origin <tag>`, `--tags` (all) or `--follow-tags` (annotated only). Prefer annotated tags (`git tag -a`). (Ch2)
- To fix an old release, branch from its tag: `git checkout -b version2 v2.0.0`. (Ch2)
- Silence the pull warning (Git 2.27+) with `git config --global pull.rebase false|true`. (Ch2)

## Contributing and maintaining

- Start every topic branch from `origin/master`, and push the topic branch to your fork, not a merged master. (Ch5)
- See what upstream has that you lack: `git log --no-merges issue54..origin/master`. (Ch5)
- Patches by email: `git format-patch -M origin/master`, then `git send-email *.patch`. Apply with `git am -3 file.patch`; `git apply --check` is a scriptable dry run. (Ch5)
- Review contributions with `git diff master...contrib`, which diffs against the merge-base. Anti-pattern: `git diff master` after master has moved. (Ch5)
- Release: `git archive master --prefix='project/' | gzip > \`git describe master\`.tar.gz`. Changelog: `git shortlog --no-merges master --not v1.0.1`. `git describe` needs annotated tags unless you pass `--tags`. (Ch5)
- GitHub: pushing new commits to a PR sends no notification, so add a comment. To update a stale PR, `git fetch upstream && git merge upstream/master` and push. If you rebased, open a new PR instead of force-pushing. (Ch6)
- Check out PRs locally: add `fetch = +refs/pull/*/head:refs/remotes/origin/pr/*` to the remote, then `git fetch` and `git checkout pr/2`. (Ch6)
- GitHub API: use personal access tokens, not passwords. Rate limits are 60 requests per hour unauthenticated and 5,000 authenticated. (Ch6)

## Servers and policy

- Make a bare repo: `git clone --bare my_project my_project.git`. Group-writable: `git init --bare --shared`. (Ch4)
- Shared `git` user: put each user's public key in `~/.ssh/authorized_keys`. Restrict logins with `git-shell`. (Ch4)
- Anti-pattern: cloning over `git://` or plain `http://`, which risks man-in-the-middle code injection. (Ch4)
- Server safety: `git config --system receive.denyNonFastForwards true` and `receive.denyDeletes true`. (Ch8)
- Enforce policy in the server `update` / `pre-receive` hooks. `exit 1` rejects the push, and anything printed reaches the client. Client `pre-commit` / `commit-msg` hooks are only a convenience mirror. (Ch8)
- A hook is enabled when the file has the exact hook name, no extension, and is executable. (Ch8)

## Attributes

- Readable diffs of binaries: `*.docx diff=word` plus `git config diff.word.textconv docx2txt`. (Ch8)
- `*.pbxproj binary` turns off line-ending fixes and diffs. `database.xml merge=ours` plus `git config --global merge.ours.driver true` keeps your side of the file on merge. (Ch8)
- Anti-pattern: a clean/smudge filter that breaks the build when its driver is missing. `.gitattributes` travels with the repo, but the driver config doesn't. (Ch8)

## Submodules, bundles and credentials

- `git clone --recurse-submodules <url>` or `git submodule update --init --recursive`. Push with `git push --recurse-submodules=on-demand`. (Ch7)
- After `git submodule update` the submodule is on a detached HEAD, so check out a branch inside it before working there. `git config submodule.recurse true`. (Ch7)
- Offline transfer: `git bundle create repo.bundle HEAD master`, then `git clone repo.bundle`. (Ch7)
- `credential.helper cache` keeps credentials in memory for 15 minutes by default. Anti-pattern: `store` writes them in plain text to `~/.git-credentials`. (Ch7)

## Other systems

- SVN: `git svn clone <url> -s`, then `git svn rebase` and `git svn dcommit`. Never merge before dcommit, because SVN follows only the first parent. Run dcommit before pushing to any Git remote. (Ch9)
- Perforce: `git p4 clone //depot/path@all`, `git p4 sync`, `git p4 rebase`, `git p4 submit -n` (dry run). (Ch9)
- Mercurial: `git clone hg::/path/to/repo`. Never force-push rewritten history to Mercurial. (Ch9)
- Custom import: `ruby import.rb <dir> | git fast-import`, then `git reset --hard master`. The stream must use LF line endings only. (Ch9)

## Internals and debugging

- Inspect objects: `git cat-file -p|-t|-s <sha>`. Store content: `echo x | git hash-object -w --stdin`. (Ch10)
- Edit refs with `git update-ref` / `git symbolic-ref`, not by hand, so the reflog gets updated. (Ch10)
- Auto gc runs at about 7,000 loose objects or more than 50 packfiles. `git count-objects -v` shows repository size. (Ch10)
- Tracing: `GIT_TRACE=1`, `GIT_TRACE_PACKET`, `GIT_TRACE_PERFORMANCE`. Use a specific SSH key with `GIT_SSH_COMMAND="ssh -i ~/.ssh/my_key" git clone ...`. (Ch10)
- Scripts: always use full option names, because abbreviations that are unique today may stop being unique. (App C)
