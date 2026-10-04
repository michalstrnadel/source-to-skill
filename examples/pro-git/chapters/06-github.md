# Chapter 6 — GitHub

*Load for questions about working with GitHub: forks and the GitHub Flow, opening/updating/merging Pull Requests, syncing a fork, PR refs, references and Markdown in comments, notifications, organizations/teams, webhooks and the REST API. Note: the book warns GitHub's UI changes over time — treat screen names as approximate.*

## Core mental models

- **A fork is just your copy of the project in your namespace**, which you can push to. Unlike the historical, negative sense of "fork" (a competing split), on GitHub it's the normal way to contribute without the owner granting you push access.
- **GitHub Flow = the Integration-Manager workflow** (see `chapters/05-distributed-git.md`) with web-based review instead of email, built on topic branches (`chapters/03-git-branching.md`).
- **A Pull Request is an iterative conversation, not a perfect patch queue.** Unlike mailing-list projects that re-roll patch series, GitHub projects usually push follow-up commits to the same branch, so the PR keeps the full context of why decisions were made. Open PRs early — internally they're often opened at the start of work to iterate as a team.
- **GitHub links commits to accounts by email address.** Add every address you commit with to your account.
- **A PR shows the unified diff `git diff master...<branch>`** — what the topic adds since the common ancestor.

## Account setup essentials

- Sign up at https://github.com (username, email, password) and **verify the email** — it matters later. Almost everything works on a free account.
- HTTPS remotes work immediately with username/password; cloning public projects needs no account at all. The account matters once you fork and push.
- **SSH access**: Account settings → "SSH keys" → "Add an SSH key", paste `~/.ssh/id_rsa.pub` (or your key file). Name keys recognizably ("My Laptop", "Work Account") so you know which to revoke. Key generation: `chapters/04-git-on-the-server.md`.
- **Avatar**: Profile tab → "Upload new picture"; a Gravatar avatar is used automatically if you have one.
- **Emails**: add all commit emails in the Emails section. States: verified + primary (gets notifications/receipts), verified (can become primary), unverified (cannot be primary). Commits using any listed address link to you.
- **2FA**: Security tab → "Set up two-factor authentication"; choose a phone app (time-based one-time password) or SMS codes. Then a code is required at login in addition to the password.

## The GitHub Flow

1. Fork the project.
2. Create a topic branch from `master`.
3. Commit improvements.
4. Push the branch to your GitHub fork.
5. Open a Pull Request.
6. Discuss; optionally keep committing.
7. Owner merges or closes the PR.
8. Sync the updated `master` back to your fork.

Worked example (forked `schacon/blink` as `tonychacon`):
```
$ git clone https://github.com/tonychacon/blink
$ cd blink
$ git checkout -b slow-blink
$ sed -i '' 's/1000/3000/' blink.ino        # macOS
# $ sed -i 's/1000/3000/' blink.ino         # Linux
$ git diff --word-diff                      # sanity-check the change
$ git commit -a -m 'Change delay to 3 seconds'
$ git push origin slow-blink
```
- After pushing, GitHub offers a green button to open a PR; alternatively use `https://github.com/<user>/<project>/branches`.
- Write a real **title and description** — it helps the owner judge intent, correctness and value. The creation page lists commits "ahead" of `master` and the unified diff.
- The official **GitHub CLI** can do most web-UI tasks on Windows, macOS and Linux.
- **Not only forks**: with write access you can open a PR between two branches of the same repository to start review — no fork needed.

### Iterating on a PR
- Reviewers can comment on any diff line, on whole commits, or on the PR; watchers and the author get notified (email if enabled).
- To address feedback: commit to the topic branch and push — the PR updates automatically. Comments on lines that have since changed get collapsed.
- **Gotcha:** pushing new commits to a PR does **not** notify anyone — leave a comment saying you've made the change.
- "Files Changed" tab = aggregate diff that merging would introduce.

### Merging a PR
- GitHub checks mergeability. The **Merge button** appears only with write access when the merge is trivial, and it always does a **non-fast-forward merge** (creates a merge commit even if a fast-forward was possible). That merge commit references the PR, making the original discussion easy to find later.
- Alternatively pull the branch and merge locally; pushing the merged `master` to GitHub closes the PR automatically.
- Declining = close the PR; the author is notified.

## Keeping a PR mergeable (keeping up with upstream)

If GitHub reports the PR doesn't merge cleanly, fix your branch so the maintainer has no extra work. Two options: rebase onto the target branch, or merge the target branch into yours. Most GitHub developers **merge**: rebasing only buys a slightly cleaner history and is harder and more error-prone; what matters is the history and the final merge.

```
$ git remote add upstream https://github.com/schacon/blink
$ git fetch upstream
$ git merge upstream/master
# resolve conflict
$ vim blink.ino
$ git add blink.ino
$ git commit
$ git push origin slow-blink
```
- The PR updates and is rechecked automatically. You can repeat this indefinitely on long-running work, only resolving conflicts new since the last merge.
- **Anti-pattern: force-pushing a rebased branch that already has an open PR** — others may have pulled it (see The Perils of Rebasing, `chapters/03-git-branching.md`). Instead push the rebased work to a **new branch**, open a new PR referencing the old one, and close the original.

## Keeping your fork's master up to date

GitHub tells you "This branch is N commits behind ..." but never updates your fork for you.

No configuration:
```
$ git checkout master
$ git pull https://github.com/progit/progit2.git
$ git push origin master
```
One-time setup so plain `pull`/`push` do the right thing:
```
$ git remote add progit https://github.com/progit/progit2.git
$ git fetch progit
$ git branch --set-upstream-to=progit/master master   # master pulls from upstream
$ git config --local remote.pushDefault origin        # pushes go to your fork
```
Then: `git checkout master && git pull && git push`.
- **Gotcha:** Git won't warn you if you commit to `master`, pull from upstream and push to `origin` — all valid. **Never commit directly to `master`**; with this setup it effectively belongs to upstream.

## References and GitHub Flavored Markdown

Cross-references (work in almost any text box):
- `#<num>` — Issue or PR in this repo. Issues and PRs share one number space (no PR #3 *and* Issue #3).
- `username#<num>` — in a fork of this repo.
- `username/repo#<num>` — in another repository.
- Full 40-character SHA-1 — links to the commit (also works with fork/repo prefixes). Pasted full GitHub URLs are shortened when rendered.
- Mentioning a PR creates a **trackback** in the referenced PR's timeline, so a closed PR links to the one that superseded it.

GFM extras:
- **Task lists** — clickable checkboxes; progress is shown in PR/Issue list views. Great for PRs opened early to track remaining work.
  ```
  - [X] Write the code
  - [ ] Write all the tests
  - [ ] Document the code
  ```
- **Fenced code** with triple backticks; add a language name (e.g. ` ```java `) for syntax highlighting.
- **Quoting** — prefix lines with `>`; highlight text in a comment and press `r` to quote it into your reply.
- **Emoji** — `:<name>:` (e.g. `:+1:`, `:ship:`); typing `:` opens an autocompleter.
- **Images** — drag and drop into a text area to upload and embed. The "Parsed as Markdown" hint links to a full cheat sheet.

## Maintaining a project

### Creating a repository and sharing URLs
- "New repository" (dashboard or `+` menu); only the name is required → `<user>/<project_name>`.
- URLs: `https://github.com/<user>/<project_name>` and `git@github.com:<user>/<project_name>`; both fetch/push, access-controlled by the connecting user's credentials.
- **Share the HTTPS URL for public projects**: no GitHub account needed to clone, and it's the same URL as the web page. SSH requires an account and an uploaded key.

### Collaborators
- Settings → Collaborators → type username → "Add collaborator". Grants push (read + write). Revoke with the "X" on their row.

### Handling incoming PRs
- PRs come from a fork (usually neither side can push to the other's branch) or from another branch in the same repo (both usually can).
- The notification email includes a diffstat, the PR link, and command-line options:
  - `git pull <url> patch-1` — merge the remote branch without adding a remote (ideally into a fresh topic branch).
  - `.diff` and `.patch` URLs of the PR, e.g.
    ```
    $ curl https://github.com/tonychacon/fade/pull/1.patch | git am
    ```
- Replying to notification emails posts into the PR thread.
- To merge: pull locally (`git pull <url> <branch>`, or add the fork as a remote, fetch, merge) or press Merge (always a merge commit). The hint link shows manual merge instructions.

### Pull Request refs (review many PRs without many remotes)
GitHub exposes PRs as hidden refs that a normal clone/fetch ignores because they're not under `refs/heads/`:
```
$ git ls-remote https://github.com/schacon/blink
...  refs/pull/1/head
...  refs/pull/1/merge
```
- `refs/pull/<n>/head` — the PR branch's last commit.
- `refs/pull/<n>/merge` — the commit the Merge button would produce; lets you test the merge before pressing it.

Fetch one PR:
```
$ git fetch origin refs/pull/958/head      # lands in FETCH_HEAD; then git merge FETCH_HEAD (odd merge message)
```
Fetch all PRs on every fetch — add a refspec to `.git/config`:
```
[remote "origin"]
    url = https://github.com/libgit2/libgit2.git
    fetch = +refs/heads/*:refs/remotes/origin/*
    fetch = +refs/pull/*/head:refs/remotes/origin/pr/*
```
```
$ git fetch
$ git checkout pr/2
```
The `origin/pr/*` refs behave like read-only tracking branches refreshed on fetch. Refspecs in depth: `chapters/10-git-internals.md`. `ls-remote` is a plumbing command.

### PRs on PRs
You can target any branch in the network — even another PR's branch (e.g. dependent idea, uncertain change, or no push access to the target). On the PR page, "Edit" next to the base/compare box changes both branch and fork.

### Mentions and notifications
- `@username` (autocompletes for collaborators/contributors, but any user works) notifies and **subscribes** that person. You're also subscribed when you open, comment on, or watch something. "Unsubscribe" button stops updates.
- Notification center settings: "Email" and/or "Web", separately for things you participate in and repos you watch.
- **Web**: blue dot on the icon; grouped by project; checkmark to acknowledge (per item or per project group); mute to stop further notifications on an item. Many power users disable email entirely and triage here.
- **Email**: properly threaded; headers support filtering:
  - `Message-ID: <user/project/type/id@github.com>` — `type` is `pull` or `issues`.
  - `List-Post` / `List-Unsubscribe` — mail clients can reply or unsubscribe (equivalent to mute/Unsubscribe).
  - Reading the email marks the web notification read if the client loads images.

### Special files
- **README** (README, README.md, README.asciidoc, …) is rendered on the project landing page. Typical contents: purpose, install/config, usage example, license, how to contribute.
- **CONTRIBUTING** (any extension) — GitHub surfaces it to anyone starting a PR, so guidelines get read before submission.

### Project administration
- **Default branch**: Settings → Options; affects where PRs target, what's shown, and what's checked out on clone.
- **Transfer ownership** (bottom of Options): moves repo, watchers and stars to another user/org and sets up redirects for both web and Git clone/fetch.

## Organizations

- Shared-ownership accounts with their own namespace (open-source groups like "perl", "rails"; companies). Create via `+` → "New organization"; name + contact email; invite co-owners. Free if everything is open source.
- Owners can fork into the org namespace, create repos under it, and auto-watch new org repos. Orgs have an avatar and landing page.
- **Teams** group users and repos with an access level per team: **read only, read/write, or administrative**. Use them instead of per-repo collaborators (e.g. frontend devs → `frontend` + `backend`; ops → `backend` + `deployscripts`). Invitees get an email.
- Team mentions like `@acmecorp/frontend` subscribe all members — useful when you don't know whom to ask. Users can be in many teams; make interest teams too (`ux`, `css`, `refactoring`, `legal`, `colorblind`).
- **Audit Log** (owners): who did what, when, and from where; filterable by event type, place, person.

## Scripting GitHub

### Services and webhooks (Settings → "Webhooks and Services")
- **Services**: prebuilt integrations (CI, issue trackers, chat, docs). E.g. the Email service mails an address on every push; the Jenkins service triggers tests on push. Most services listen only for push events. Check here before building your own.
- **Webhooks**: GitHub POSTs an HTTP payload to your URL on chosen events. Configure URL + secret key; default event is **push** (to any branch).
- Handler pattern (Sinatra): parse `JSON.parse(request.body.read)`, read `push["pusher"]["name"]`, `push["ref"]`, and each commit's `added`/`modified`/`removed` files, then act.
- The hook settings page shows recent deliveries with request/response headers and bodies, success state, and lets you **redeliver** payloads — ideal for debugging.
- Docs: https://docs.github.com/en/webhooks-and-events/webhooks/about-webhooks

### REST API
- Unauthenticated GETs for public data:
  ```
  $ curl https://api.github.com/users/schacon
  $ curl https://api.github.com/gitignore/templates/Java
  ```
  (The API can even render Markdown or fetch `.gitignore` templates.)
- **Authenticate with a personal access token** (Settings → "Applications"), not username/password: choose scopes, give a clear description so you know when to revoke it, copy it immediately (shown only once). Tokens are scoped and revocable.
- **Rate limits**: 60 requests/hour unauthenticated; up to 5,000/hour authenticated.
- Comment on an issue:
  ```
  $ curl -H "Content-Type: application/json" \
         -H "Authorization: token TOKEN" \
         --data '{"body":"A new comment, :+1:"}' \
         https://api.github.com/repos/schacon/blink/issues/6/comments
  ```
- The API covers nearly everything in the UI: milestones, assignees, labels, commit data, creating commits/branches, opening/closing/merging PRs, teams, line comments, search.

### Commit statuses
- POST to `/repos/<user>/<repo>/statuses/<commit_sha>` with:
  - `state`: `success`, `failure`, or `error`
  - `description`
  - `target_url` (more info)
  - `context` — distinguishes multiple statuses on one commit (e.g. tests vs `validate/signoff`)
- Typical use: CI reports test results; or a webhook service checks each pushed commit message for `Signed-off-by` and posts success/failure.
- A PR takes the status of its **last commit** and warns if it failed — prevents merging a branch whose tip fails tests.

### Libraries
- **Octokit** (https://github.com/octokit) wraps the API idiomatically; at the time of writing: Go, Objective-C, Ruby, .NET. Full API docs: https://docs.github.com/

## Quick rules
- Contribute via topic branch in your fork; never commit directly to the `master` you sync from upstream.
- Update a stale PR by merging upstream into the topic branch; if you must rebase, open a new PR instead of force-pushing.
- Comment after pushing fixes — commits alone don't notify.
- Expect the Merge button to always create a merge commit.
- Use `refs/pull/*/head` refspecs to review many PRs locally; `refs/pull/<n>/merge` to test the would-be merge.
- Use tokens (scoped, revocable, higher rate limit) for API scripts.
