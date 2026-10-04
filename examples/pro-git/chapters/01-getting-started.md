# Chapter 1 — Getting Started

*Load this for the core mental model of Git (snapshots, local operations, integrity, the three states), installation, first-time `git config` setup, config scope/precedence, and how to get help.*

## The mental model that makes everything else easy

Unlearn habits from CVS, Subversion or Perforce. Git's commands look similar, but it stores and reasons about data differently, and carrying the old model over causes subtle confusion.

### Snapshots, not deltas

- Most other VCSs (CVS, Subversion, Perforce) are **delta-based**: they store a base version of each file plus a list of per-file changes over time.
- Git stores a **stream of snapshots** of a miniature filesystem. Each commit records what *all* tracked files look like at that moment and keeps a reference to that snapshot.
- Unchanged files are not stored again; the snapshot simply links to the identical file already stored.
- Consequence: Git behaves more like a small filesystem with powerful tools on top than a classic VCS. This design is what makes branching cheap (see `chapters/03-git-branching.md`).

### Nearly every operation is local

- The full project history lives on your disk, so browsing history, diffing a file against last month's version, and committing need no server round-trip and feel instant.
- You can commit offline (plane, train, broken VPN) and upload later.
- Contrast: in Perforce you can do little while disconnected; in Subversion and CVS you can edit but not commit while the server is unreachable.

### Git has integrity

- Everything is checksummed before storage and then referred to by that checksum, so file or directory contents cannot change without Git noticing. Corruption or loss in transit is detectable.
- The checksum is a **SHA-1 hash**: 40 hex characters (0–9, a–f) computed from the content, e.g. `24b9da6552252987aa493b52f8696cd6d3b00373`.
- Git's database is keyed by content hash, not by file name.

### Git generally only adds data

- Nearly every action appends to the database; it is hard to make Git do something irreversible or erase data.
- Uncommitted changes can be lost like in any VCS. Once committed, a snapshot is very hard to lose, especially if you regularly push to another repository.
- Practical implication: committing is the safety net. Experiment freely after committing. (Recovery techniques: Undoing Things in `chapters/02-git-basics.md`.)

## The three states and three areas (the most important idea in this chapter)

| File state | Meaning | Lives in |
|---|---|---|
| **Modified** | Changed, but not yet committed | Working tree |
| **Staged** | A modified file marked, in its current version, to go into the next commit | Staging area (the **index**) |
| **Committed** | Safely stored in your local database | Git directory (`.git`) |

- **Working tree**: one checked-out version of the project, extracted from the compressed database for you to edit.
- **Staging area / index**: a file, usually inside the Git directory, describing what goes into the next commit. "Index" is the technical name; "staging area" means the same.
- **Git directory**: metadata plus the object database. The most important part of Git, and what is copied when you clone.

Basic workflow:

1. Edit files in the working tree.
2. Selectively stage only the changes you want in the next commit.
3. Commit: the snapshot *as staged* is stored permanently in the Git directory.

Classification rule: in the Git directory -> committed; modified and added to staging -> staged; changed since checkout but not staged -> modified. Chapter 2 shows how to exploit the staging step or skip it.

## Why version control, and the three VCS generations

Version control records changes to files over time so you can recall specific versions later. It works for nearly any file type (designers can version images and layouts). It lets you revert files or the whole project, compare changes over time, find who last modified something that broke and when, and recover from mistakes, at very little overhead.

| Generation | Examples | How it works | Weakness |
|---|---|---|---|
| Copy directories (ad hoc) | time-stamped folders | Copy files elsewhere | Very error prone: wrong directory, accidental overwrites |
| Local VCS | RCS | Local database of patch sets; rebuilds any version by adding up patches | No collaboration; entire history in one place |
| Centralized VCS (CVCS) | CVS, Subversion, Perforce | One server holds all versions; clients check out files | Single point of failure: server down = nobody can collaborate or save versioned changes; lost disk without backups = lost history |
| Distributed VCS (DVCS) | Git, Mercurial, Darcs | Every client mirrors the full repository including history | — |

- CVCS strengths: everyone sees roughly what others are doing; admins get fine-grained access control; easier to administer than per-client databases.
- DVCS strengths: every clone is a full backup; any clone can restore a dead server. Multiple remotes let you collaborate with different groups in different ways in one project, enabling workflows impossible with a central server, such as hierarchical models.

## Why Git exists (short history)

- Linux kernel changes circulated as patches and archives from 1991 to 2002; in 2002 the project moved to the proprietary DVCS BitKeeper.
- In 2005 the relationship with BitKeeper's company broke down and its free-of-charge status was revoked. The community, led by Linus Torvalds, built their own tool.
- Design goals: speed; simple design; strong support for non-linear development (thousands of parallel branches); fully distributed; efficient on Linux-kernel-sized projects (speed and data size).

## The command line

- The book uses the CLI because it is the only place you can run *all* Git commands; most GUIs implement a subset.
- Knowing the CLI usually lets you figure out a GUI, but not the reverse. The CLI tools are installed for every user regardless of GUI choice.
- Prerequisite: be able to open Terminal (macOS) or Command Prompt / PowerShell (Windows).

## Installing Git

The book targets Git 2; Git preserves backward compatibility well, so any recent version works, though very old versions may lack some commands or behave slightly differently. Updating even an existing install is recommended.

**Linux (binary packages):**

```console
$ sudo dnf install git-all        # Fedora / RHEL / CentOS (RPM-based)
$ sudo apt install git-all        # Debian / Ubuntu
```

More distributions: https://git-scm.com/download/linux

**macOS:** easiest path is the Xcode Command Line Tools. On Mavericks (10.9)+ just run git once and you will be prompted to install:

```console
$ git --version
```

For a newer build, use the installer at https://git-scm.com/download/mac.

**Windows:** official build at https://git-scm.com/download/win (this is the separate *Git for Windows* project, https://gitforwindows.org). For automated installs there is a community-maintained Chocolatey package.

**From source** (gets the newest version; binary installers lag a bit, though less so now). Needs autotools, curl, zlib, openssl, expat, libiconv:

```console
$ sudo dnf install dh-autoreconf curl-devel expat-devel gettext-devel \
  openssl-devel perl-devel zlib-devel
$ sudo apt-get install dh-autoreconf libcurl4-gnutls-dev libexpat1-dev \
  gettext libz-dev libssl-dev
```

Docs in doc/html/info formats additionally need:

```console
$ sudo dnf install asciidoc xmlto docbook2X
$ sudo apt-get install asciidoc xmlto docbook2x
$ sudo apt-get install install-info                  # Debian-based only
$ sudo dnf install getopt                            # RPM-based only
$ sudo ln -s /usr/bin/db2x_docbook2texi /usr/bin/docbook2x-texi   # Fedora/RHEL: binary name difference
```

- RHEL, CentOS and Scientific Linux must enable the EPEL repository to get docbook2X.
- Tarballs: https://www.kernel.org/pub/software/scm/git (has release signatures for verification) or https://github.com/git/git/tags (latest version is easier to spot).

```console
$ tar -zxf git-2.8.0.tar.gz
$ cd git-2.8.0
$ make configure
$ ./configure --prefix=/usr
$ make all doc info
$ sudo make install install-doc install-html install-info
```

Afterwards, update Git using Git itself:

```console
$ git clone https://git.kernel.org/pub/scm/git/git.git
```

## First-time setup with `git config`

Do this once per machine; settings survive upgrades and can be changed any time by rerunning the commands.

### Where config lives and who wins

| Scope | File | Flag | Notes |
|---|---|---|---|
| System | `[path]/etc/gitconfig` | `--system` | All users and repos; needs admin/superuser rights to change |
| Global (user) | `~/.gitconfig` or `~/.config/git/config` | `--global` | All your repos on this system |
| Local (repo) | `.git/config` | `--local` (the default) | One repository; you must be inside a repo |

- **Rule: each level overrides the previous one** — local beats global beats system.
- Windows: `.gitconfig` is looked up in `$HOME` (usually `C:\Users\$USER`); `[path]/etc/gitconfig` is relative to the MSys root (the install location). Git for Windows 2.x+ also has a system-level file at `C:\Documents and Settings\All Users\Application Data\Git\config` (Windows XP) or `C:\ProgramData\Git\config` (Vista and newer), changeable only via `git config -f <file>` as admin.
- See every setting and which file it came from:

```console
$ git config --list --show-origin
```

### Identity (do this first)

Every commit records your name and email, and they are baked into commits immutably:

```console
$ git config --global user.name "John Doe"
$ git config --global user.email johndoe@example.com
```

To use a different identity for one project, run the same commands *without* `--global` inside that project.

### Editor

Used whenever Git asks for a message; if unset, Git uses the system default editor.

```console
$ git config --global core.editor emacs
```

- On Windows you must give the full path to the editor executable. Notepad++ example (the book suggests the 32-bit build since the 64-bit one lacked some plug-ins at the time):

```console
$ git config --global core.editor "'C:/Program Files/Notepad++/notepad++.exe' -multiInst -notabbar -nosession -noPlugin"
```

- Gotcha: a misconfigured editor can leave you in a confusing state when Git launches it — on Windows, for example, a Git operation can terminate prematurely during a Git-initiated edit.

### Default branch name

`git init` creates a branch named `master` by default. Since Git 2.28 you can change the initial branch name:

```console
$ git config --global init.defaultBranch main
```

### Checking settings

```console
$ git config --list            # everything Git can see right now
$ git config user.name         # the effective value of one key
$ git config --show-origin rerere.autoUpdate   # which file set this key
file:/home/johndoe/.gitconfig	false
```

- The same key can appear several times in `--list` because Git reads multiple files; **the last value seen for a key wins**.
- When a value is surprising, use `--show-origin` to find the file that had the final say.

## Getting help

Three equivalent ways to open the full manpage (work offline):

```console
$ git help <verb>
$ git <verb> --help
$ man git-<verb>
$ git help config        # example
```

- Quick option summary instead of the full manpage: `-h`, e.g. `git add -h` (prints usage plus a compact option list such as `-n/--dry-run`, `-p/--patch`, `-A/--all`, `-N/--intent-to-add`).
- Human help: `#git`, `#github`, `#gitlab` channels on the Libera Chat IRC server (https://libera.chat/).

## Gotchas checklist

- Don't think in per-file deltas — think in whole-project snapshots.
- Set `user.name` / `user.email` before your first commit; they can't be changed in existing commits.
- If a config value looks wrong, check precedence (local > global > system) and use `--show-origin`.
- Uncommitted work is the only work Git can't protect — commit (and push) to make it durable.
- `git init` names the first branch `master` unless `init.defaultBranch` is set (Git 2.28+).
