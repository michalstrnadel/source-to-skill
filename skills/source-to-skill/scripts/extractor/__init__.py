"""source-to-skill extractor package.

Every submodule is imported at module level, never inside a function:
yt-dlp's plugin loader can rebind sys.modules["extractor"] to its own
`ytdlp_plugins.extractor` package once a YoutubeDL starts, after which a
deferred `from ..media import ...` would resolve against the wrong
package.
"""

__version__ = "0.6.0"
