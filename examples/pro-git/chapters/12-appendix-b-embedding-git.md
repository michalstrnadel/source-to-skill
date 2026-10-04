# Appendix B — Embedding Git in your Applications

*Load when a program needs to work with Git repositories: deciding between shelling out to `git` and using a library, or getting started with Libgit2 (and its Ruby, .NET, Objective-C, and Python bindings), JGit, go-git, or Dulwich.*

## Decision: shell out or embed a library?

| Option | Pros | Cons |
|---|---|---|
| Spawn the `git` CLI | Canonical; every feature supported; easy to invoke from most runtimes | Plain-text output whose format changes occasionally, so parsing is inefficient and fragile; poor error recovery (a corrupt repo or bad config value makes Git refuse many operations); you must manage separate shell processes, which gets hard when several touch the same repo |
| Embed a library | Native API in your language (objects instead of text parsing, the language's own error handling); some libraries add pluggable storage backends | Not the canonical implementation; coverage varies (go-git, for example, documents which plumbing APIs it supports) |

Library by runtime:

| Runtime | Library |
|---|---|
| C, or any language with bindings | **Libgit2** (dependency-free; https://libgit2.org) |
| Ruby | Rugged (Libgit2) |
| .NET / Mono | LibGit2Sharp (Libgit2; NuGet package available) |
| Objective-C / Swift | objective-git (Libgit2) |
| Python | pygit2 (Libgit2), or **Dulwich** (pure Python, optional C extensions) |
| Java / JVM | **JGit** (native Java, Eclipse project) |
| Go | **go-git** (pure Go) |

Libgit2 bindings also exist for C++, Go, Node.js, Erlang, and the JVM, at varying maturity. The official list is at https://github.com/libgit2.

## Libgit2 (C API)

```c
// Open a repository
git_repository *repo;
int error = git_repository_open(&repo, "/path/to/repository");

// Dereference HEAD to a commit
git_object *head_commit;
error = git_revparse_single(&head_commit, repo, "HEAD^{commit}");
git_commit *commit = (git_commit*)head_commit;

// Print some of the commit's properties
printf("%s", git_commit_message(commit));
const git_signature *author = git_commit_author(commit);
printf("%s <%s>\n", author->name, author->email);
const git_oid *tree_id = git_commit_tree_id(commit);

// Cleanup
git_commit_free(commit);
git_repository_free(repo);
```

- `git_repository` — a repository handle with an in-memory cache. Other ways to get one: `git_repository_open_ext` (with search options), `git_clone` and related calls (clone a remote), `git_repository_init` (create a new repo).
- `git_revparse_single` takes rev-parse syntax (e.g. `HEAD^{commit}`) and returns a `git_object`.
- `git_object` is a "parent" type: every child type shares its memory layout, so you can cast once you've checked the type (`git_object_type()` returns `GIT_OBJ_COMMIT` → cast to `git_commit*`).
- `git_oid` is Libgit2's representation of a SHA-1.

**API conventions (rules of thumb):**
- You pass a reference to a pointer and get back an `int` error code: **0 means success, anything below 0 is an error.**
- **If Libgit2 fills in a pointer for you, you free it.**
- **A `const` pointer returned to you must not be freed**, and it becomes invalid once the object that owns it is freed.
- Writing C is painful, so in practice you'll use a language binding.

## Rugged (Ruby)

```ruby
repo = Rugged::Repository.new('path/to/repository')
commit = repo.head.target
puts commit.message
puts "#{commit.author[:name]} <#{commit.author[:email]}>"
tree = commit.tree
```
- Errors are raised as exceptions (e.g. `ConfigError`, `ObjectError`); garbage collection means no explicit freeing.

**Building a commit from scratch** (the same steps as the internals in `chapters/10-git-internals.md`: blob → index → tree → commit → ref):
```ruby
blob_id = repo.write("Blob contents", :blob)               # 1. new blob

index = repo.index
index.read_tree(repo.head.target.tree)                      # 2. index = HEAD's tree
index.add(:path => 'newfile.txt', :oid => blob_id)          #    + the new file

sig = {
    :email => "bob@example.com",
    :name => "Bob User",
    :time => Time.now,
}

commit_id = Rugged::Commit.create(repo,
    :tree => index.write_tree(repo),                        # 3. write tree to the ODB
    :author => sig,
    :committer => sig,                                      # 4. same signature for both
    :message => "Add newfile.txt",                          # 5. message
    :parents => repo.empty? ? [] : [ repo.head.target ].compact,  # 6. parent = HEAD tip
    :update_ref => 'HEAD',                                  # 7. optionally move a ref
)
commit = repo.lookup(commit_id)                             # 8. SHA-1 -> Commit object
```
Libgit2 does the heavy lifting, so this is fast as well as concise.

## Libgit2 advanced: pluggable backends

Libgit2 lets you supply custom **backends** for configuration, ref storage, the object database (ODB), and more, so data can be stored differently from stock Git. Examples: https://github.com/libgit2/libgit2-backends.

```c
git_odb *odb;
int error = git_odb_new(&odb);                       // empty ODB "frontend" (container)

git_odb_backend *my_backend;
error = git_odb_backend_mine(&my_backend, /*…*/);    // your backend constructor

error = git_odb_add_backend(odb, my_backend, 1);     // attach backend to frontend

git_repository *repo;
error = git_repository_open(&repo, "some-path");
error = git_repository_set_odb(repo, odb);           // repo now reads objects via your ODB
```

Implementing the backend:
```c
typedef struct {
    git_odb_backend parent;
    // Some other stuff
    void *custom_context;
} my_backend_struct;

int git_odb_backend_mine(git_odb_backend **backend_out, /*…*/)
{
    my_backend_struct *backend;
    backend = calloc(1, sizeof (my_backend_struct));
    backend->custom_context = …;
    backend->parent.read = &my_backend__read;
    backend->parent.read_prefix = &my_backend__read_prefix;
    backend->parent.read_header = &my_backend__read_header;
    // …
    *backend_out = (git_odb_backend *) backend;
    return GIT_SUCCESS;
}
```
- **Key constraint:** the struct's **first member must be a `git_odb_backend`**, so the memory layout matches what Libgit2 expects. Everything after it is yours.
- Fill in only the callbacks your use case needs. Full signatures are in `include/git2/sys/odb_backend.h`.
- (The book's sample captures errors without handling them. Handle them in real code.)

## Other Libgit2 bindings: "message of the commit HEAD points to"

```csharp
// LibGit2Sharp (.NET / Mono)
new Repository(@"C:\path\to\repo").Head.Tip.Message;
```
```objc
// objective-git (Apple platforms; fully interoperable with Swift)
GTRepository *repo =
    [[GTRepository alloc] initWithURL:[NSURL fileURLWithPath: @"/path/to/repo"] error:NULL];
NSString *msg = [[[repo headReferenceWithError:NULL] resolvedTarget] message];
```
```python
# pygit2 (https://www.pygit2.org)
pygit2.Repository("/path/to/repo") # open repository
    .head                          # get the current branch
    .peel(pygit2.Commit)           # walk down to the commit
    .message                       # read the message
```
More: Libgit2 API docs at https://libgit2.github.com/libgit2, guides at https://libgit2.github.com/docs, and each binding's README and tests.

## JGit (Java)

Full-featured, native Java, widely used, under the Eclipse umbrella (https://projects.eclipse.org/projects/technology.jgit).

**Setup with Maven** (inside `<dependencies>`; the version will have moved on, see mvnrepository.com):
```xml
<dependency>
    <groupId>org.eclipse.jgit</groupId>
    <artifactId>org.eclipse.jgit</artifactId>
    <version>3.5.0.201409260305-r</version>
</dependency>
```
Or with prebuilt jars:
```console
javac -cp .:org.eclipse.jgit-3.5.0.201409260305-r.jar App.java
java -cp .:org.eclipse.jgit-3.5.0.201409260305-r.jar App
```

**Two API levels**, named after Git's own: *plumbing* (low-level repository objects) and *porcelain* (user-level actions).

### Plumbing
```java
// Create a new repository
Repository newlyCreatedRepo = FileRepositoryBuilder.create(
    new File("/tmp/new_repo/.git"));
newlyCreatedRepo.create();

// Open an existing repository
Repository existingRepo = new FileRepositoryBuilder()
    .setGitDir(new File("my_repo/.git"))
    .build();
```
- `FileRepositoryBuilder` is fluent. It can read environment variables (`.readEnvironment()`), search from a working directory (`.setWorkTree(…).findGitDir()`), or open a known `.git` directory. JGit also supports storage models other than the filesystem.

```java
Ref master = repo.getRef("master");                 // resolves refs/heads/master
ObjectId masterTip = master.getObjectId();          // SHA-1 (object may not exist)
ObjectId obj = repo.resolve("HEAD^{tree}");         // rev-parse; null if unresolvable
ObjectLoader loader = repo.open(masterTip);
loader.copyTo(System.out);                          // stream raw object contents

RefUpdate createBranch1 = repo.updateRef("refs/heads/branch1");
createBranch1.setNewObjectId(masterTip);
createBranch1.update();                             // create branch

RefUpdate deleteBranch1 = repo.updateRef("refs/heads/branch1");
deleteBranch1.setForceUpdate(true);                 // REQUIRED, else delete() returns REJECTED
deleteBranch1.delete();

Config cfg = repo.getConfig();
String name = cfg.getString("user", null, "name");  // also reads global + system config
```
- `Ref`: `.getName()`, `.getObjectId()` (direct ref), `.getTarget()` (symbolic ref). Tag refs can report whether they're **peeled**, i.e. point to the final target of a chain of tag objects.
- `ObjectLoader` can also give the type, the size, or a byte array. **For large objects (`.isLarge()`), use `.openStream()`** to read without loading everything into memory.
- **Gotcha:** deleting a ref without `.setForceUpdate(true)` silently does nothing (the result is `REJECTED`).
- Errors are exceptions: standard Java ones (`IOException`) plus JGit-specific ones (`NoRemoteRepositoryException`, `CorruptObjectException`, `NoMergeBaseException`).

### Porcelain
Entry point: `Git git = new Git(repo);`. Methods return command objects; chain setters, then `.call()` runs it.

```java
CredentialsProvider cp = new UsernamePasswordCredentialsProvider("username", "p4ssw0rd");
Collection<Ref> remoteRefs = git.lsRemote()
    .setCredentialsProvider(cp)
    .setRemote("origin")
    .setTags(true)
    .setHeads(false)
    .call();
for (Ref ref : remoteRefs) {
    System.out.println(ref.getName() + " -> " + ref.getObjectId().name());
}
```
That's the equivalent of `git ls-remote` for tags only, with credentials. Also available: add, blame, commit, clean, push, rebase, revert, reset, and more.
Docs: the JGit User Guide on help.eclipse.org (standard Javadoc, so IDEs can install it locally) and the JGit Cookbook (https://github.com/centic9/jgit-cookbook).

## go-git (Go)

- Pure Go with no native dependencies, so no manual memory-management bugs. It works with Go's standard profilers and race detector.
- Focused on extensibility and compatibility; supports most plumbing APIs (see `COMPATIBILITY.md` in the repo).

```go
import "github.com/go-git/go-git/v5"

r, err := git.PlainClone("/tmp/foo", false, &git.CloneOptions{
    URL:      "https://github.com/go-git/go-git",
    Progress: os.Stdout,
})

ref, err := r.Head()                        // branch HEAD points to
commit, err := r.CommitObject(ref.Hash())   // its commit
history, err := commit.History()            // commit history
for _, c := range history {
    fmt.Println(c)
}
```

**Advanced:**
- **Pluggable storage**, similar to Libgit2 backends. In-memory storage is very fast: `git.Clone(memory.NewStorage(), nil, &git.CloneOptions{URL: "..."})`. An example in the repo stores refs, objects, and config in Aerospike.
- **Filesystem abstraction** via go-billy (`Filesystem`): pack all files into a single archive, keep them in memory, and so on.
- **Custom HTTP client:**
```go
customClient := &http.Client{
    Transport: &http.Transport{ // accept any certificate (might be useful for testing)
        TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
    },
    Timeout: 15 * time.Second,  // 15 second timeout
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
        return http.ErrUseLastResponse // don't follow redirect
    },
}
client.InstallProtocol("https", githttp.NewClient(customClient))  // override https
r, err := git.Clone(memory.NewStorage(), nil, &git.CloneOptions{URL: url})
```
Docs: https://pkg.go.dev/github.com/go-git/go-git/v5 and the `_examples` directory in the repo.

## Dulwich (pure Python)

- Talks to local and remote repositories without calling out to `git`. Optional C extensions improve performance considerably. Plumbing and porcelain levels, like Git. Home: https://www.dulwich.io/.

```python
from dulwich.repo import Repo
r = Repo('.')
r.head()            # '57fbe010446356833a6ad1600059d80b1e731e15'
c = r[r.head()]     # <Commit ...>
c.message           # 'Add note about encoding.\n'

from dulwich import porcelain
porcelain.log('.', max_entries=1)   # prints commit, Author, Date like git log
```
