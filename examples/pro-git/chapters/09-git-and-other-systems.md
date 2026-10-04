# Chapter 9 — Git and Other Systems

*Load this when Git must coexist with Subversion, Mercurial or Perforce (using Git as a client via a bridge), or when migrating a project into Git — including writing a custom importer with `git fast-import`.*

Two situations: (1) the project lives in another VCS and you want Git locally — use a **bridge**; (2) you're moving the project to Git for good — use an **importer**. The recurring theme: the further the other system is from Git's model, the more you must keep your Git history linear and avoid rewriting anything already shared.

## Bridge comparison at a glance

| System | Bridge | Where it runs | Merges OK? | Key rule |
|---|---|---|---|---|
| Subversion | `git svn` (built in) | your machine | No — keep history linear, rebase | `dcommit` rewrites SHA-1s; collaborate only via the SVN server |
| Mercurial | `git-remote-hg` (remote helper) | your machine | Yes | don't rewrite pushed history; can't delete bookmarks from Git |
| Perforce | Git Fusion | the Perforce server | Yes (recorded as an integration) | rewriting pushed history is rejected |
| Perforce | `git-p4` | your machine | Submitted as linearized changesets | rebase; Perforce stays the source of truth |

## Git and Subversion: `git svn`

A bidirectional bridge: use local Git features (branches, staging area, rebase, cherry-pick) and push to an SVN server as if you were an SVN client.

### Mental model

- SVN can hold only **one linear history**, and it is easy to confuse. Treat `git svn` as "crippled Git".
- Prefer rebasing over merging. Don't rewrite history and re-push. Don't simultaneously push to a parallel Git remote to collaborate. If a team is split between SVN and Git users, everyone collaborates through the SVN server.

### Test setup (optional)

To experiment, make a writable local copy of an SVN repo with `svnsync`:

```
$ mkdir /tmp/test-svn
$ svnadmin create /tmp/test-svn
# allow revprop changes: hooks/pre-revprop-change containing "#!/bin/sh" + "exit 0;", then chmod +x it
$ svnsync init file:///tmp/test-svn http://your-svn-server.example.org/svn/
$ svnsync sync file:///tmp/test-svn
```

SVN copies one revision at a time; syncing to another *remote* repo can take nearly an hour even for under 100 commits.

### Clone

```
$ git svn clone file:///tmp/test-svn -T trunk -b branches -t tags
$ git svn clone file:///tmp/test-svn -s          # same thing: -s = standard layout
```

- Equivalent to `git svn init` then `git svn fetch`.
- Slow: Git checks out and commits every revision individually — hours or days for thousands of commits.
- `-T/-b/-t` name the trunk/branches/tags directories; change them if the repo uses other names.
- SVN **tags become remote refs** (`refs/remotes/origin/tags/...`), unlike a normal Git clone where tags land in `refs/tags`. Inspect with `git show-ref`.

### Daily workflow

| Task | Command | Notes |
|---|---|---|
| Commit locally | `git commit` | Can make many offline commits |
| Push to SVN | `git svn dcommit` | One SVN commit per local commit, then rewrites each local commit to add a `git-svn-id:` line → **all SHA-1s change** |
| Get upstream changes + replay yours | `git svn rebase` | Needs a clean working dir — stash or temp-commit first, else it stops on a would-be conflict |
| Only download | `git svn fetch` | Doesn't update local commits |

- After `dcommit`, the commit message ends with e.g. `git-svn-id: file:///tmp/test-svn/trunk@77 0b684db3-...`; hash `4af61fd` became `95e0222`.
- **If you push to both an SVN server and a Git server, `dcommit` first**, because it changes commit data.
- A rejected `dcommit` (`Transaction is out of date`) is fixed by `git svn rebase`, then `dcommit` again.
- **Gotcha:** unlike Git, `git svn` only forces you to integrate upstream work when changes *conflict*. If someone changed a different file, your `dcommit` succeeds and produces a project state that never existed on either machine — incompatible-but-non-conflicting changes can cause hard-to-diagnose breakage. In Git you can test the exact state before publishing; in SVN you can't be sure pre- and post-commit states match.
- Run `git svn rebase` regularly even when not committing, to stay current.

### Branching pitfalls

- `git svn` follows only the **first parent** when converting to SVN commits. If you merge a local `experiment` branch into `master` and `dcommit`, the experiment commits aren't rewritten; their changes show up in SVN as one squashed merge commit (like `git merge --squash`) — others lose the authorship/timing detail. So: **rebase topic work onto the mainline instead of merging.**
- Create an SVN branch on the server (like `svn copy trunk branches/opera`):

  ```
  $ git svn branch opera
  ```

  It does **not** switch you to it — your next `dcommit` still goes to trunk.
- `dcommit` targets the SVN branch whose tip is the most recent commit with a `git-svn-id` in your current branch's history (there should be exactly one).
- To work on an SVN branch locally:

  ```
  $ git branch opera remotes/origin/opera
  ```

- Merging `opera` into `master` with `git merge` works (Git finds the merge base), but give it a real message with `-m`. After `dcommit` the merge looks squashed, parent info is erased, and later merge-base calculations will be wrong. **Delete the local branch after merging it into trunk.**

### SVN-flavoured commands (all offline)

| Command | Equivalent | Caveat |
|---|---|---|
| `git svn log` | `svn log` | Shows only commits already on the SVN server as of last contact; not your un-dcommitted work or newer server commits |
| `git svn blame <file>` | `svn annotate` | Same staleness caveat |
| `git svn info` | `svn info` | Current as of last server contact |
| `git svn create-ignore` | — | Creates `.gitignore` files from `svn:ignore` properties for committing |
| `git svn show-ignore > .git/info/exclude` | — | Ignore SVN-ignored files locally without adding `.gitignore` files — good when you're the lone Git user |

### `git svn` rules of thumb

- Keep a linear history with no `git merge` merge commits; rebase non-mainline work onto mainline.
- Don't run a separate collaborative Git server. One for faster clones is fine, but push nothing to it lacking a `git-svn-id`; consider a `pre-receive` hook that rejects commits without `git-svn-id`.
- If you can move to a real Git server, do.

## Git and Mercurial: `git-remote-hg`

Implemented as a **remote helper** (same mechanism as Git's HTTP/S transport), so you use ordinary `git clone/fetch/push`. Project: https://github.com/felipec/git-remote-hg.

### Install

```
$ curl -o ~/bin/git-remote-hg \
  https://raw.githubusercontent.com/felipec/git-remote-hg/master/git-remote-hg
$ chmod +x ~/bin/git-remote-hg        # ~/bin must be on $PATH
$ pip install mercurial                # Python mercurial library
```

Also install the Mercurial client.

### Use

```
$ git clone hg::/tmp/hello /tmp/hello-git
$ cp .hgignore .git/info/exclude     # reuse hg ignores without committing a .gitignore
```

- Full clone with complete history, fairly fast (both are DVCSs).
- `.hgignore` format is compatible; `.git/info/exclude` acts like `.gitignore` but is never committed.
- Under the hood: `refs/hg/origin/...` holds the real remote refs (like a fake `refs/remotes/origin` that distinguishes **bookmarks** and **branches**); `refs/notes/hg` maps Git commit hashes to Mercurial changeset IDs (a notes tree whose blobs named after Git commits contain the hg changeset ID). `git log --all` will show these "Notes for ..." commits — ignore them.
- Normal workflow: `git fetch`, `git merge origin/master` (Mercurial handles merges fine), `git push`. Commits pushed from Git appear as ordinary changesets in `hg log`.

### Branches vs bookmarks

- Git has one kind of branch. Mercurial's **bookmark** behaves like a Git branch. A Mercurial **branch** is heavyweight: its name is recorded in each changeset permanently.
- Create a bookmark: `git checkout -b featureA` then `git push origin featureA`.
- Create a Mercurial branch: name it in the `branches/` namespace, e.g. `git checkout -b branches/permanent` … `git push origin branches/permanent`.
- Limitation: you **can't delete a bookmark from the Git side** (remote-helper limitation).
- **Mercurial never rewrites history, only adds.** After an interactive rebase + force-push, the new changesets appear *alongside* the old ones — confusing for hg teammates. Avoid rewriting pushed history.

## Git and Perforce

Perforce (since 1995) assumes a single always-connected central server and only one version on local disk. Two bridges:

### Git Fusion (server-side)

Perforce's product that syncs a Perforce server with Git repositories, exposing depot subtrees as read-write Git repos (https://www.perforce.com/manuals/git-fusion/).

Trial setup from the book: download the VM image (Perforce daemon + Git Fusion), import it into e.g. VirtualBox, set passwords for `root`, `perforce`, `git` and an instance name; note the IP shown. Create a user as root:

```
$ p4 -p localhost:1666 -u super user -f john    # opens vi; accept defaults with :wq
$ p4 -p localhost:1666 -u john passwd
```

The bundled certificate won't match the VM's IP, so for the demo only: `export GIT_SSL_NO_VERIFY=true` (install a proper certificate for a permanent setup). Then `git clone https://10.0.1.254/Talkhouse`.

**Configuration** — map `//.git-fusion` from the Perforce server into a workspace:

- `objects/` — internal Perforce↔Git mapping; don't touch.
- `p4gf_config` (root) — global INI-style options (sections like `[repo-creation]`, `[git-to-perforce]`, `[perforce-to-git]`, `[@features]`, `[authentication]`).
- `repos/<Repo>/p4gf_config` — per-repo overrides (`[@repo]` section) plus branch mappings:

  ```ini
  [Talkhouse-master]
  git-branch-name = master
  view = //depot/Talkhouse/main-dev/... ...
  ```

  Section name is arbitrary but unique; `git-branch-name` gives a friendly Git name; `view` uses standard Perforce view-mapping syntax and may list several mappings (e.g. `//depot/project1/main/... project1/...` and `//depot/project2/mainline/... project2/...`).
- `users/p4gf_usermap` — optional; lines of `<user> <email> "<full name>"`.
  - Default without it: Perforce→Git uses the Perforce user's stored name/email; Git→Perforce finds the Perforce user by the commit author's email and submits as them (permissions apply).
  - Several lines for one user map multiple emails to one account; the **first** matching line supplies Git authorship.
  - Can mask real names/emails (e.g. before open-sourcing). Keep emails/names unique unless you want all commits attributed to one fictional author.

**Workflow:** looks like any Git remote. First clone converts history on the server (can take time); later fetches are incremental. Commits from Perforce users appear as normal commits. Merge commits push fine; Perforce stores unnamed-branch commits in an "anonymous" branch under `.git-fusion` (mappable to a named Perforce branch later). Submodules work (look odd to Perforce users); merges become integrations. Rewriting already-pushed history is rejected.

### git-p4 (client-side)

Runs entirely in your Git repo; needs only Perforce credentials and the `p4` CLI on `PATH`. Less flexible than Git Fusion, but non-invasive.

```
$ export P4PORT=10.0.1.254:1666
$ export P4USER=john
$ git p4 clone //depot/www/live www-shallow
```

- Default clone is effectively **shallow**: only the latest Perforce revision (`#head`). Enough to act as a client.
- The `p4/master` refs look like remote-tracking refs, but `git remote -v` shows **no remotes** — git-p4 manages these refs; you can't push to them.

| Task | Command |
|---|---|
| Fetch new Perforce changes | `git p4 sync` |
| Fetch + rebase onto them | `git p4 rebase` (≈ `git p4 sync` + `git rebase p4/master`, smarter with multiple branches) |
| Submit commits | `git p4 submit` — one Perforce changeset per Git commit between `p4/master` and `master`; opens editor per changeset (save and quit each) |
| Preview submit | `git p4 submit -n` (`--dry-run`) |

- The submit form is the usual `p4 submit` spec plus git-p4 notes and the diff. If the Git author doesn't match your p4 account it says so; `--preserve-user` modifies authorship; `git-p4.skipUserNameCheck` hides the message.
- Want one changeset? Squash with interactive rebase before `git p4 submit`.
- Submitted commits get a trailer like `[git-p4: depot-paths = "//depot/www/live/": change = 12144]`, so their SHA-1s change.
- **Merge commits:** submit skips the merge and creates changesets for the non-merge commits, effectively rebasing — history becomes linear. "If you can rebase it, you can contribute it."

**Branches:**

```
$ git p4 clone --detect-branches //depot/project@all
```

- `@all` imports every changeset that touched the path (closer to a real clone; slow on long histories).
- `--detect-branches` uses Perforce branch specs to create Git refs (e.g. `p4/project/dev`).
- No branch specs on the server? Declare them: `git config git-p4.branchList main:dev` (dev is a child of main), then clone with `--detect-branches`.
- After `git checkout -b dev p4/project/dev`, `git p4 submit` targets the right branch.
- Limits: can't combine shallow clones with multiple branches (clone once per branch on huge projects); can't create or integrate Perforce branches (use a Perforce client); a Git merge submits only file changes — integration metadata is lost.

**Rule:** Perforce owns the source. If others share a Git remote with you, push only commits already submitted to Perforce. For free mixing of Git and Perforce clients, get Git Fusion installed.

## Migrating to Git

### From Subversion

1. **Author map** `users.txt`:

   ```
   schacon = Scott Chacon <schacon@geemail.com>
   selse = Someo Nelse <selse@geemail.com>
   ```

   List SVN authors (needs grep/sort/perl; Windows users see Microsoft's guide at https://learn.microsoft.com/en-us/azure/devops/repos/git/perform-migration-from-svn-to-git):

   ```
   $ svn log --xml --quiet | grep author | sort -u | \
     perl -pe 's/.*>(.*?)<.*/$1 = /'
   ```

2. **Import:**

   ```
   $ git svn clone http://my-project.googlecode.com/svn/ \
     --authors-file=users.txt --no-metadata --prefix "" -s my_project
   $ cd my_project
   ```

   `--no-metadata` drops the `git-svn-id` lines (less log clutter). **Keep metadata if you'll mirror commits back into SVN.**

3. **Clean up refs:**

   ```
   # remote "tags" -> real lightweight tags
   $ for t in $(git for-each-ref --format='%(refname:short)' refs/remotes/tags); do git tag ${t/tags\//} $t && git branch -D -r $t; done
   # remaining remote refs -> local branches
   $ for b in $(git for-each-ref --format='%(refname:short)' refs/remotes); do git branch $b refs/remotes/$b && git branch -D -r $b; done
   # optional: drop @<number> peg-revision branches
   $ for p in $(git for-each-ref --format='%(refname:short)' | grep @); do git branch -D $p; done
   # redundant trunk branch (same commit as master)
   $ git branch -d trunk
   ```

   Branches suffixed `@xxx` come from SVN **peg-revisions**, which Git can't express; git svn appends the revision number.

4. **Publish:**

   ```
   $ git remote add origin git@my-git-server:myrepository.git
   $ git push origin --all
   $ git push origin --tags
   ```

### From Mercurial (`hg-fast-export`)

```
$ git clone https://github.com/frej/fast-export.git
$ hg clone <remote repo URL> /tmp/hg-repo
$ cd /tmp/hg-repo
$ hg log | grep user: | sort | uniq | sed 's/user: *//' > ../authors
```

- Mercurial is lax about author strings, so clean them up. Mapping rule format `"<input>"="<output>"` (Python `string_escape` escapes allowed); unmatched authors pass through unchanged; if all look fine, skip the file:

  ```
  "bob"="Bob Jones <bob@company.com>"
  "bob@localhost"="Bob Jones <bob@company.com>"
  "bob <bob@company.com>"="Bob Jones <bob@company.com>"
  "bob jones <bob <AT> company <DOT> com>"="Bob Jones <bob@company.com>"
  ```

  The same format can rename branches/tags whose hg names Git doesn't allow.
- Convert:

  ```
  $ git init /tmp/converted
  $ cd /tmp/converted
  $ /tmp/fast-export/hg-fast-export.sh -r /tmp/hg-repo -A /tmp/authors
  ```

  `-r` = hg repo, `-A` = author map, `-B` / `-T` = branch / tag maps. It emits a `git fast-import` stream. Verify authors with `git shortlog -sn`.
- Result: hg tags → Git tags; hg branches and bookmarks → Git branches. Then `git remote add origin ...` and `git push origin --all`.

### From Perforce

- **Git Fusion:** configure project, users and branches, clone — you get a native-looking Git repo ready to push anywhere (or keep Perforce as the Git host).
- **git-p4:**

  ```
  $ export P4PORT=public.perforce.com:1666
  $ git-p4 clone //guest/perforce_software/jam@all p4import
  ```

  Add `--detect-branches` for multi-branch depots. Each commit carries a `[git-p4: depot-paths = ...: change = N]` line — useful for later reference. To strip it, do so **before** starting new work (it rewrites all SHA-1s):

  ```
  $ git filter-branch --msg-filter 'sed -e "/^\[git-p4:/d"'
  ```

### Anything else

First search for an existing importer (they exist for CVS, Clear Case, Visual Source Safe, even directories of archives). Otherwise write one for `git fast-import`.

## Custom importer with `git fast-import`

`git fast-import` reads simple text instructions on stdin and writes Git objects — far easier than raw commands or hand-built objects. Write a program that reads the old system and prints instructions, then pipe: `program | git fast-import`.

Model: Git history is a linked list of commits pointing at snapshots. Tell fast-import each snapshot, its commit metadata, and its order.

### Stream format essentials

Two commits as the example importer emits them (the message has no trailing newline, so the next command follows immediately; the first commit has no `from`):

```
commit refs/heads/master
mark :1
committer John Doe <john@example.com> 1388649600 -0700
data 29
imported from back_2014_01_02deleteall
M 644 inline README.md
data 28
# Hello

This is my readme.
commit refs/heads/master
mark :2
committer John Doe <john@example.com> 1388822400 -0700
data 29
imported from back_2014_01_04from :1
deleteall
M 644 inline main.rb
...
```

- **mark** — an integer ID you assign to a commit so later commits can reference it (`from :<mark>`).
- **committer** — name/email, Unix timestamp, and an explicit timezone offset.
- **data** — `data <size>\n<contents>`; used for both commit messages and file contents. Size must be exact.
- **`deleteall`** + one `M <mode> inline <path>` per file = full snapshot. Mode `644`, or `755` for executables.
- Alternative: send only per-commit adds/modifies/removes (see the fast-import man page) — more work; giving full snapshots lets Git work out the differences.
- **LF only.** fast-import rejects CRLF; on Windows, in Ruby call `$stdout.binmode`.

### Example: importing dated backup directories

Source: `/opt/import_from/` with `back_2014_01_02`, `back_2014_01_04`, … and `current`. Strategy: one commit per directory, each parented on the previous. Key helpers of the Ruby script:

```ruby
$stdout.binmode
$author = "John Doe <john@example.com>"

$marks = []
def convert_dir_to_mark(dir)          # mark = 1-based index of the dir
  $marks << dir unless $marks.include?(dir)
  ($marks.index(dir)+1).to_s
end

def convert_dir_to_date(dir)          # parse date from name; 'current' = now
  if dir == 'current'
    return Time.now().to_i
  else
    (year, month, day) = dir.gsub('back_', '').split('_')
    return Time.local(year, month, day).to_i
  end
end

def export_data(string)
  print "data #{string.size}\n#{string}"
end

def inline_data(file, code='M', mode='644')
  content = File.read(file)
  puts "#{code} #{mode} inline #{file}"
  export_data(content)
end

def print_export(dir, last_mark)
  date = convert_dir_to_date(dir)
  mark = convert_dir_to_mark(dir)
  puts 'commit refs/heads/master'
  puts "mark :#{mark}"
  puts "committer #{$author} #{date} -0700"
  export_data("imported from #{dir}")
  puts "from :#{last_mark}" if last_mark
  puts 'deleteall'
  Dir.glob("**/*").each do |file|
    next if !File.file?(file)
    inline_data(file)
  end
  mark
end

last_mark = nil
Dir.chdir(ARGV[0]) do
  Dir.glob("*").each do |dir|
    next if File.file?(dir)
    Dir.chdir(dir) { last_mark = print_export(dir, last_mark) }
  end
end
```

Run it:

```
$ git init
$ ruby import.rb /opt/import_from | git fast-import
$ git log -2
$ git reset --hard master     # nothing is checked out after import
```

- On success fast-import prints statistics (here: 13 objects, 4 commits, 1 branch).
- **Gotcha:** the working directory is empty after import; `git reset --hard master` populates it.
- fast-import also handles modes, binary data, multiple branches and merges, tags, and progress indicators; see `contrib/fast-import` in the Git source for complex examples.

See also: `chapters/08-customizing-git.md` (hooks such as `pre-receive`), `chapters/10-git-internals.md` (objects that fast-import writes), `chapters/03-git-branching.md` (rebasing).
