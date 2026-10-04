"""source-to-skill extractor entrypoint.

Usage:
  python3 scripts/extract.py <source> [options]
  python3 scripts/extract.py --check     # report optional dependencies

Sources: YouTube video, playlist and channel URLs, podcast and audio/video
URLs or local files, arXiv URLs, GitHub repo URLs, web article URLs, local
.pdf files, local .epub books.

Options:
  --type T          override auto-detection: youtube|playlist|audio|paper|
                    book|article|repo (e.g. `--type book` for a PDF book,
                    `--type playlist` for a watch?v=...&list=... URL,
                    `--type audio` for any page yt-dlp can download)
  --limit N         playlists and channels: only the first N videos
                    (channels default to the latest 20)
  --transcribe      YouTube: transcribe the audio with Whisper even when
                    captions exist
  --work-dir PATH   where to write the outputs (default: the system temp
                    dir's source_skill_work/)

Writes full_text.txt + metadata.json + source.json into the work dir and
prints a JSON summary with the work dir path.
"""
import json
import sys
from pathlib import Path

from extractor import config, dependencies, utils
from extractor.parsers import (
    article, audio, book, paper, playlist, repo, youtube,
)

PARSERS = {
    "youtube": youtube,
    "playlist": playlist,
    "audio": audio,
    "paper": paper,
    "book": book,
    "article": article,
    "repo": repo,
}


def _usage_error(rest) -> utils.ExtractError:
    return utils.ExtractError(
        f"Unrecognized arguments: {' '.join(rest)}\n"
        "Usage: extract.py <source> [--type "
        f"{'|'.join(config.SOURCE_TYPES)}] [--limit N] [--transcribe] "
        "[--work-dir PATH]"
    )


def _parse_options(rest) -> dict:
    """Parse the flags after <source> into an options dict."""
    options = {
        "type": None, "limit": None, "transcribe": False, "work_dir": None,
    }
    args = list(rest)
    while args:
        flag = args.pop(0)
        if flag == "--transcribe":
            options["transcribe"] = True
            continue
        if flag not in ("--type", "--limit", "--work-dir"):
            raise _usage_error(rest)
        if not args or args[0].startswith("--"):
            if flag == "--type":
                raise utils.ExtractError(
                    "--type requires a value: "
                    f"{', '.join(config.SOURCE_TYPES)}."
                )
            raise utils.ExtractError(f"{flag} requires a value.")
        value = args.pop(0)
        if flag == "--limit":
            if not value.isdigit() or int(value) < 1:
                raise utils.ExtractError(
                    f"--limit needs a positive whole number, got {value!r}."
                )
            options["limit"] = int(value)
        else:
            options[flag[2:].replace("-", "_")] = value
    return options


def _parser_kwargs(kind: str, options: dict) -> dict:
    """Keyword arguments the chosen parser accepts, only when set."""
    if options["limit"] is not None and kind != "playlist":
        raise utils.ExtractError(
            "--limit only applies to playlists and channels."
        )
    if options["transcribe"] and kind not in ("youtube", "playlist"):
        raise utils.ExtractError(
            "--transcribe only applies to YouTube videos and playlists "
            "(audio sources are always transcribed)."
        )
    kwargs = {}
    if options["limit"] is not None:
        kwargs["limit"] = options["limit"]
    if options["transcribe"]:
        kwargs["transcribe"] = True
    return kwargs


def _hint_for(err: Exception) -> str:
    """Next step for an unexpected failure, specific where we can tell."""
    message = str(err)
    if "429" in message or "Too Many Requests" in message:
        return (
            "The site is rate-limiting this machine. Wait 10-30 minutes "
            "and retry; avoid running several YouTube extractions at once."
        )
    if "confirm you" in message and "bot" in message:
        return (
            "YouTube asked for a sign-in (bot check). Update yt-dlp "
            "(pip install -U yt-dlp) and retry later or from another network."
        )
    return "Check the URL or path and your network connection, then retry."


def main(argv) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--check":
        print(dependencies.check_report())
        return 0
    source = argv[0]
    try:
        options = _parse_options(argv[1:])
        kind = utils.detect_source(source, options["type"])
        kwargs = _parser_kwargs(kind, options)
        if options["work_dir"]:
            work = Path(options["work_dir"]).expanduser().resolve()
        else:
            work = config.work_dir()
        config.set_work_dir(work)
        full_text, metadata = PARSERS[kind].parse(source, **kwargs)
        utils.write_outputs(work, full_text, metadata)
        utils.write_manifest(work, source, metadata, options)
    except utils.ExtractError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    except Exception as err:  # network, yt-dlp, PDF library failures
        print(
            f"ERROR: extraction failed for {source} "
            f"({type(err).__name__}: {err}).\n" + _hint_for(err),
            file=sys.stderr,
        )
        return 1
    finally:
        config.set_work_dir(None)
    print(
        json.dumps(
            {
                "work_dir": str(work),
                "source_type": metadata["source_type"],
                "title": metadata["title"],
                "words": metadata["words"],
                "est_tokens": metadata["est_tokens"],
                "segments": len(metadata["segments"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
