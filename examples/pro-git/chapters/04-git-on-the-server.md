# Chapter 4 — Git on the Server

*Load this when choosing a transfer protocol (local, HTTP, SSH, git://), setting up a self-hosted Git server (bare repo, SSH keys, git-shell, git daemon, Smart HTTP, GitWeb, GitLab), or deciding between self-hosting and a hosted service.*

## Why a server, and what lives on it

- Collaboration needs a remote repository. Pushing to / pulling from individuals' personal repos is discouraged: it's easy to confuse what they're working on, and their machine may be offline. Preferred: an **intermediate shared repository** everyone pushes to and pulls from.
- Setup order: (1) pick protocols, (2) configure the server for them — or (3) skip it all and use a hosted service.
- A remote repo is normally a **bare repository**: no working directory, just the contents of a project's `.git` directory. It's only a collaboration point, so nothing needs to be checked out.
- Minimum viable private server for a few people: **an SSH server plus a bare repository** that all users can read and write. Nothing else is required.

## Protocol decision guide

Git transfers data over four protocols: **Local, HTTP (Smart/Dumb), SSH, Git**.

| Protocol | URL form | Auth | Anonymous read | Strengths | Weaknesses |
|---|---|---|---|---|---|
| Local | `/srv/git/project.git` or `file:///srv/git/project.git` | Filesystem permissions | n/a | Trivial if a shared filesystem exists; quick grabs from a colleague (`git pull /home/john/project`) | Hard to reach remotely (must mount disk); NFS often slower than SSH; no protection against users corrupting internal files |
| Smart HTTP | `https://example.com/gitproject.git` | HTTP auth (username/password) | Yes | One URL for read and write; no SSH keys needed; fast and efficient; HTTPS encrypts transfer; firewall-friendly | Can be trickier to set up than SSH on some servers; credential entry can be more fiddly than keys (use credential caching) |
| Dumb HTTP | same | none in itself | Yes (read-only) | Simplest: static files under a web root + `post-update` hook | Generally read-only; fallback only |
| SSH | `ssh://[user@]server/project.git` or `[user@]server:project.git` | SSH (encrypted, authenticated) | **No** | Daemons commonplace; secure; efficient (compacts data before transfer) | No anonymous access — poor fit for open source where people just want to clone |
| Git | `git://example.com/project.git` (port **9418**) | **None** | Yes | Often the fastest network protocol; good for heavy public read traffic or very large public projects | No auth or crypto; hardest to set up (own daemon via systemd/xinetd); port 9418 often blocked by corporate firewalls |

Decision rules:
- **Default choice for most needs: Smart HTTP(S)** — it can serve anonymous reads like `git://` and authenticated, encrypted pushes like SSH from a single URL. Hosts like GitHub use the same HTTPS URL for browsing, cloning and pushing.
- **Self-hosting inside a corporate network: SSH** may be the only protocol you need.
- **SSH for pushers + something else for anonymous readers** if you want public read-only access too.
- **Git daemon** for fast, unauthenticated read-only access: public projects, or internal CI/build servers when you don't want to add an SSH key for each.
- **Local** only with a shared filesystem (e.g. NFS mount). Everyone logging into one machine is a bad idea: all repository copies on one computer makes catastrophic loss far more likely.
- Typically you run *either* read/write Smart HTTP *or* read-only Dumb HTTP; mixing the two is rare.

### Security gotcha: unencrypted clones
- Cloning over `git://` or plain `http://` can lead to **arbitrary code execution**: an attacker controlling, say, your router can inject malicious code into the repo you clone; building/running it executes that code. Avoid both unless you know what you're doing.
- `https://` is safe from this unless the attacker can present a valid TLS certificate for the host.
- SSH (`git@example.com:project.git`) is affected only if you accept a wrong host key fingerprint.

### Local protocol details
```sh
git clone /srv/git/project.git              # plain path: hardlinks or direct file copy (fast)
git clone file:///srv/git/project.git       # runs network transfer machinery (slower)
git remote add local_proj /srv/git/project.git
```
- Use `file://` only when you want a **clean copy** without extraneous refs or objects — typically after importing from another VCS (maintenance: `chapters/10-git-internals.md`).

### Dumb HTTP setup (read-only)
```sh
cd /var/www/htdocs/
git clone --bare /path/to/git_project gitproject.git
cd gitproject.git
mv hooks/post-update.sample hooks/post-update
chmod a+x hooks/post-update
```
- The stock `post-update` hook runs `git update-server-info`, which makes HTTP fetch/clone work after each push (pushes go via e.g. SSH). Any static web server works. Clients then `git clone https://example.com/gitproject.git`.
- Clients automatically fall back to Dumb HTTP if the server offers no smart service.
- Smart HTTP arrived in **Git 1.6.6**; before that only the simple, generally read-only mode existed.

## Getting Git on a server

### Create and place a bare repository
```sh
git clone --bare my_project my_project.git     # convention: bare repo dirs end in .git
# roughly equivalent to: cp -Rf my_project/.git my_project.git  (minor config differences)

scp -r my_project.git user@git.example.com:/srv/git
git clone user@git.example.com:/srv/git/my_project.git
```
- Anyone with SSH read access to `/srv/git` can clone; anyone with **write access to the directory automatically has push access**.
- Fix group write permissions safely (doesn't destroy commits or refs):
  ```sh
  ssh user@git.example.com
  cd /srv/git/my_project.git
  git init --bare --shared
  ```

### Giving a team SSH access — three options
1. **Account per user** (`adduser`/`useradd`) — straightforward but cumbersome (temporary passwords for everyone). Access control can then use normal OS filesystem permissions.
2. **Single shared `git` account**: collect each user's SSH public key and append it to that account's `~/.ssh/authorized_keys`. The SSH user you connect as **does not affect commit data** (authorship is unchanged).
3. **Centralized auth** (e.g. LDAP) behind the SSH server — any SSH auth mechanism works as long as users can get shell access.

User management (e.g. read-only for some, read/write for others) is one of the hardest parts of running a Git server.

### Generating an SSH key (client side)
```sh
cd ~/.ssh && ls          # look for id_dsa / id_rsa plus matching .pub
ssh-keygen -o            # create a key pair if none exists
cat ~/.ssh/id_rsa.pub    # public key to send to the admin
```
- `.pub` = public key; the file without extension = private key.
- A passphrase is optional; if you set one, use **`-o`** to store the private key in a format more resistant to brute-force cracking than the default. `ssh-agent` avoids retyping it.
- `ssh-keygen` ships with SSH on Linux/macOS and with Git for Windows.

### Setting up the server (authorized_keys method)
```sh
sudo adduser git
su git
cd
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
cat /tmp/id_rsa.john.pub >> ~/.ssh/authorized_keys
cat /tmp/id_rsa.josie.pub >> ~/.ssh/authorized_keys
```
- `ssh-copy-id` can automate much of the key installation.

Create an empty repo (someone must shell in and do this **for every new project**):
```sh
cd /srv/git
mkdir project.git
cd project.git
git init --bare
```

First push and subsequent clones:
```sh
# on John's computer
cd myproject
git init
git add .
git commit -m 'Initial commit'
git remote add origin git@gitserver:/srv/git/project.git
git push origin master

# others
git clone git@gitserver:/srv/git/project.git
```

### Locking down the `git` account
By default every key holder can get a full shell as `git`. Restrict it with **`git-shell`**:
```sh
cat /etc/shells            # is git-shell listed?
which git-shell            # confirm it's installed
sudo -e /etc/shells        # add its full path if missing
sudo chsh git -s $(which git-shell)
```
- Push/pull over SSH still work; interactive login is rejected (`fatal: Interactive git shell is not enabled.`).
- Users can **still use SSH port forwarding** to reach hosts the server can reach. Prevent it by prefixing each key line in `authorized_keys` with:
  ```
  no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty
  ```
- A `~/git-shell-commands` directory in the git user's home can customize git-shell (restrict accepted Git commands, customize the login-refusal message). See `git help shell`.

## Git daemon (git:// protocol)

- Unauthenticated: everything served is **public within its network**. Outside the firewall, use only for world-public projects; inside it, good for many read-only consumers (CI/build servers).

```sh
git daemon --reuseaddr --base-path=/srv/git/ /srv/git/
```
- `--reuseaddr`: restart without waiting for old connections to time out.
- `--base-path`: lets clients clone without specifying the full path.
- Trailing path: where to look for repos to export.
- Open **port 9418** in the firewall.

systemd unit at `/etc/systemd/system/git-daemon.service`:
```ini
[Unit]
Description=Start Git Daemon

[Service]
ExecStart=/usr/bin/git daemon --reuseaddr --base-path=/srv/git/ /srv/git/

Restart=always
RestartSec=500ms

StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=git-daemon

User=git
Group=git

[Install]
WantedBy=multi-user.target
```
- Make sure the `git` user exists and the binary really is at `/usr/bin/git`.
- `systemctl enable git-daemon` (start on boot), `systemctl start git-daemon`, `systemctl stop git-daemon`. Elsewhere use xinetd, a sysvinit script, etc.

Opt each repo in — the daemon refuses to serve a repo without this file:
```sh
cd /path/to/project.git
touch git-daemon-export-ok
```
Pushing over git:// can be enabled but, with no authentication, anyone who finds the URL could push — so it's rare.

## Smart HTTP server (authenticated + anonymous at once)

- Enable the CGI script **`git-http-backend`** shipped with Git. It inspects the path and headers of a `git fetch`/`git push` and talks smart protocol to capable clients (any since 1.6.6), falling back to dumb behavior otherwise (backward compatible for reads).
- `git-http-backend` **implements no authentication**; enforce auth in the web server that invokes it. Any CGI-capable web server works.

Apache example:
```sh
sudo apt-get install apache2 apache2-utils
a2enmod cgi alias env           # mod_cgi, mod_alias, mod_env
chgrp -R www-data /srv/git      # Apache runs the CGI as www-data and needs read/write
```
```apache
SetEnv GIT_PROJECT_ROOT /srv/git
SetEnv GIT_HTTP_EXPORT_ALL
ScriptAlias /git/ /usr/lib/git-core/git-http-backend/
```
- Omit `GIT_HTTP_EXPORT_ALL` and unauthenticated clients only get repos containing `git-daemon-export-ok` (same as the daemon).

Require auth only for pushes (`git-receive-pack`):
```apache
<Files "git-http-backend">
AuthType Basic
AuthName "Git Access"
AuthUserFile /srv/git/.htpasswd
Require expr !(%{QUERY_STRING} -strmatch '*service=git-receive-pack*' || %{REQUEST_URI} =~ m#/git-receive-pack$#)
Require valid-user
</Files>
```
```sh
htpasswd -c /srv/git/.htpasswd schacon
```
- Run it over SSL so the data (and credentials) are encrypted.

## GitWeb (simple web viewer)

- Git ships a CGI web visualizer, GitWeb.
- Quick temporary preview from a project directory:
  ```sh
  git instaweb                       # uses lighttpd by default (common on Linux)
  git instaweb --httpd=webrick       # alternative handler
  git instaweb --httpd=webrick --stop
  ```
  Serves on **port 1234** and opens a browser.
- Permanent install: try your distro's `gitweb` package (apt/dnf) first, or build it:
  ```sh
  git clone https://git.kernel.org/pub/scm/git/git.git
  cd git/
  make GITWEB_PROJECTROOT="/srv/git" prefix=/usr gitweb
  sudo cp -Rf gitweb /var/www/
  ```
  `GITWEB_PROJECTROOT` tells it where the repos are. Then serve it via CGI:
  ```apache
  <VirtualHost *:80>
  ServerName gitserver
  DocumentRoot /var/www/gitweb
  <Directory /var/www/gitweb>
  Options +ExecCGI +FollowSymLinks +SymLinksIfOwnerMatch
  AllowOverride All
  order allow,deny
  Allow from all
  AddHandler cgi-script cgi
  DirectoryIndex gitweb.cgi
  </Directory>
  </VirtualHost>
  ```
  Any CGI- or Perl-capable server works.

## GitLab (full-featured self-hosted server)

Harder to install and maintain than GitWeb, but fully featured; afterwards most admin happens in the browser, rarely via config files or SSH.

- **Install**: database-backed web app. Officially recommended: the **Omnibus GitLab** package. Alternatives: Helm chart (Kubernetes), Docker images, from source, cloud providers (AWS, GCP, Azure, OpenShift, Digital Ocean).
- **Admin**: browse to the host, log in as `root`. Omnibus auto-generates the password into `/etc/gitlab/initial_root_password` (kept at least 24 hours). Use the "Admin area" menu item.
- **Users**: each has a **namespace**; user `jane`'s `project` lives at `http://server/jane/project`.
  - **Block** = cannot log in; namespace data kept; commits still link to profile.
  - **Destroy** = removed from database and filesystem with all their projects and owned groups. Rarely needed.
- **Groups**: collections of projects with access rules and their own namespace (`http://server/training/materials`). Per-user permission levels range from **Guest** (issues and chat only) to **Owner** (full control).
- **Projects**: ≈ one Git repo, in exactly one namespace (user or group). User-owned → owner controls access; group-owned → group permissions apply.
  - Visibility: **Private** (explicit grants only), **Internal** (any logged-in user), **Public** (anyone). Governs both `git fetch` and web UI access.
- **Hooks**: project- or system-level; GitLab sends an HTTP POST with descriptive JSON on events — integrate CI, chat, deployment tools.
- **Usage**: create a project via "+" (name, namespace, visibility — mostly changeable later). Connect over HTTPS or SSH:
  ```sh
  git remote add gitlab https://server/namespace/project.git
  git clone https://server/namespace/project.git
  ```
- **Collaboration models**:
  - Direct push: add the user under project "Members" with **Developer** access or higher.
  - **Merge requests**: users with access push a branch and open an MR; users without push rights **fork**, push to their copy, and open an MR back. Owner keeps full control while accepting untrusted contributions.
  - MRs and issues are the main long-lived discussion units: line-by-line review plus a general thread; assignable to users and milestones. GitLab also has wikis and maintenance tools.

## Self-hosted vs. third-party hosted

| | Own server | Hosted service |
|---|---|---|
| Control | High; can live inside your firewall | Code sits on someone else's servers (some organizations forbid this) |
| Effort | Significant setup and maintenance time | Quick to set up; no maintenance or monitoring |
| Open source | Possible | Easier for the community to find and help |

- You can mix: internal server for private code plus a public host for open source.
- GitHub is the largest host — see `chapters/06-github.md`. Workflow patterns for using whichever remote you choose: `chapters/05-distributed-git.md`.
- Credential caching for HTTPS (macOS Keychain, Windows Credential Manager): "Credential Storage" in `chapters/07-git-tools.md`.
