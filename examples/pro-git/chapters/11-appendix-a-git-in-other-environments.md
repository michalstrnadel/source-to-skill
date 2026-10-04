# Appendix A — Git in Other Environments

*Load when choosing or explaining a Git GUI or IDE integration, or setting up shell tab-completion and a Git-aware prompt in Bash, Zsh, or PowerShell.*

## Core principles

- **The command line is Git's native home.** New features appear there first, and only there is all of Git's power available. No GUI can do anything the CLI can't.
- **Judge a GUI by its fit for a workflow, not as "better" or "worse".** Clients deliberately expose a curated subset of Git that suits the way of working their author favors.
  - **Task-oriented tools** do one job well: `gitk` (history) and `git-gui` (making commits).
  - **Workflow-oriented tools** bundle a set of common operations around one way of working, e.g. GitHub's macOS/Windows clients built around the GitHub Flow.
- **Rule:** if your workflow differs from what a tool assumes, or you want control over when and how network operations happen, use another client or the CLI.

## gitk and git-gui (bundled with Git)

### gitk: history viewer
```console
$ gitk [git log options]
$ gitk --all          # show commits reachable from any ref, not just HEAD
```
- Think of it as a GUI over `git log` and `git grep`. Use it to find past events or visualize history.
- Most options pass straight through to `git log`.
- Layout: a graph on top (dots = commits, lines = parent links, colored boxes = refs; **yellow dot = HEAD**, **red dot = uncommitted changes**); the selected commit's message and patch at bottom left, summary at bottom right; search controls in between.

### git-gui: commit crafting
```console
$ git gui
```
- Left: the index, with unstaged changes on top and staged below. Click a file's icon to move it between states; click its name to view it.
- Top right: diff of the selected file. **Right-click to stage individual hunks or single lines.**
- Bottom right: message box and a "Commit" button (like `git commit`).
- **Amending:** pick the "Amend" radio button. Staged Changes fills with the last commit's contents; adjust what's staged and the message, then click Commit to replace the old commit.

## GitHub for macOS and Windows (desktop.github.com)

- Workflow-oriented; the two versions look and behave almost the same.
- "Changes" view: tracked repositories on the left ("+" adds one by cloning or attaching a local repo), commit message and file selection in the center (history below it on Windows, on a separate tab on macOS), diff on the right, **Sync** button at top right.
- **No GitHub account needed**; it works with any repository and any Git host.
- Download from https://desktop.github.com/. On first run it walks you through name/email setup and sets sensible defaults (credential caching, CRLF behavior).
- **Evergreen:** updates install in the background and include a bundled Git, so you rarely need to update Git yourself. On Windows there's a shortcut to PowerShell with posh-git.
- Add a local repo by dragging its folder from Finder or Explorer into the window.
- Branch creation: a button on macOS; on Windows you type the new name into the branch switcher.
- Commit shortcut: ctrl-enter / ⌘-enter.

### What "Sync" actually does
```console
git pull --rebase       # if this fails with a merge conflict → git pull --no-rebase
git push
```
It folds fetch, merge/rebase, and push into one step: the most common network sequence for the GitHub Flow (commit on a branch, sync with the remote often). See `chapters/06-github.md`.

## Other GUIs and IDEs

- Curated list of popular clients: https://git-scm.com/downloads/guis. A longer list lives on the Git wiki (archived at archive.kernel.org).
- **Visual Studio** (built in since 2019 v16.8): create/clone, browse history, branches and tags, stash/stage/commit, fetch/pull/push/sync, merge and rebase, resolve conflicts, view diffs.
- **Visual Studio Code** (built in; **requires Git 2.0.0 or newer**): diff markers in the gutter; status bar (lower left) with branch, dirty indicator, and incoming/outgoing commits; init, clone, branch/tag, stage/commit, push/pull/sync, conflict resolution, diffs. GitHub PRs need the `GitHub.vscode-pull-request-github` extension.
- **JetBrains IDEs** (IntelliJ IDEA, PyCharm, WebStorm, PhpStorm, RubyMine, …): a bundled Git Integration plugin with a dedicated Version Control tool window, including GitHub PRs. **It relies on a command-line Git being installed.**
- **Sublime Text** (3.2+): status badges in the sidebar, `.gitignore`d entries faded out, branch and modification count in the status bar, change markers in the gutter. Some Sublime Merge features work from inside the editor if Sublime Merge is installed.

## Bash

Git ships shell plugins, but they're off by default.

**Tab completion:**
1. Run `git version`, check out the matching source tag (`git checkout tags/vX.Y.Z`), and copy `contrib/completion/git-completion.bash` somewhere such as `~`.
2. Add to `.bashrc`:
   ```bash
   . ~/git-completion.bash
   ```
3. `git chec<tab>` completes to `git checkout`. It also completes subcommands, parameters, remotes, and ref names.

**Prompt** (copy `contrib/completion/git-prompt.sh` to `~`):
```bash
. ~/git-prompt.sh
export GIT_PS1_SHOWDIRTYSTATE=1
export PS1='\w$(__git_ps1 " (%s)")\$ '
```
- `\w` = current directory, `\$` = the `$`, `__git_ps1 " (%s)"` = branch/status formatted by git-prompt.sh.
- Both scripts carry documentation in their source; read them for more options.

## Zsh

**Completion** (ships with Zsh): add to `.zshrc`:
```zsh
autoload -Uz compinit && compinit
```
Ambiguous completions are listed with descriptions and can be navigated by pressing tab repeatedly. It covers commands, arguments, refs, remotes, and filenames.

**Prompt via `vcs_info`** (branch shown on the right side):
```zsh
autoload -Uz vcs_info
precmd_vcs_info() { vcs_info }
precmd_functions+=( precmd_vcs_info )
setopt prompt_subst
RPROMPT='${vcs_info_msg_0_}'
# PROMPT='${vcs_info_msg_0_}%# '
zstyle ':vcs_info:git:*' formats '%b'
```
Uncomment the `PROMPT` line to show it on the left. Docs are in the `zshcontrib(1)` man page.

**Alternatives:** Git's own `git-prompt.sh` works in both Bash and Zsh. The oh-my-zsh framework (https://github.com/ohmyzsh/ohmyzsh) adds Git completion and many VCS-aware prompt themes.

## PowerShell (posh-git)

- `cmd.exe` can't really be customized for Git; PowerShell can, including PowerShell Core on Linux and macOS.
- **posh-git** (https://github.com/dahlbyk/posh-git) provides tab completion and a status-aware prompt.

**Prerequisite (Windows only): ExecutionPolicy.** It must be something other than `Undefined` or `Restricted`. Use `RemoteSigned`, which requires signatures only on scripts downloaded from the internet. `AllSigned` would make you sign your own local scripts too. Use `-Scope LocalMachine` (admin, all users) or `-Scope CurrentUser` (just you).
```powershell
> Set-ExecutionPolicy -Scope LocalMachine -ExecutionPolicy RemoteSigned -Force
```

**Install from PowerShell Gallery** (PowerShell 5, or PowerShell 4 with PackageManagement):
```powershell
> Install-Module posh-git -Scope CurrentUser -Force
> Install-Module posh-git -Scope CurrentUser -AllowPrerelease -Force # Newer beta version with PowerShell Core support
```
- For all users: `-Scope AllUsers` from an elevated console.
- **Gotcha:** if you get "Module 'PowerShellGet' was not installed by using Install-Module", first run the command below, then retry. The modules that ship with Windows PowerShell are signed with a different certificate.
  ```powershell
  > Install-Module PowerShellGet -Force -SkipPublisherCheck
  ```

**Load it in every session:**
```powershell
> Import-Module posh-git
> Add-PoshGitToProfile -AllHosts
```
There are several `$profile` scripts (e.g. one for the console and another for the ISE); `-AllHosts` covers all of them.

**From source:** download a release from https://github.com/dahlbyk/posh-git/releases, unpack it, then:
```powershell
> Import-Module <path-to-uncompress-folder>\src\posh-git.psd1
> Add-PoshGitToProfile -AllHosts
```
This adds the import line to `profile.ps1`. The posh-git README documents the prompt's status summary and its customization variables.
