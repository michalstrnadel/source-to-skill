"""source-to-skill extractor entrypoint.

Usage:
  python3 scripts/extract.py <source> [--type youtube|paper|book]
  python3 scripts/extract.py --check     # report optional dependencies

Sources: YouTube URLs, arXiv URLs, local .pdf files, local .epub books.
`--type` overrides auto-detection (e.g. `--type book` for a PDF book).
Writes full_text.txt + metadata.json into the work dir and prints a JSON
summary with the work dir path.
"""
import json
import sys

from extractor import config, dependencies, utils
from extractor.parsers import book, paper, youtube

PARSERS = {"youtube": youtube, "paper": paper, "book": book}


def _parse_type_flag(rest):
    """Return the --type value from the args after <source>, or None."""
    if not rest:
        return None
    if rest == ["--type"]:
        raise utils.ExtractError(
            "--type requires a value: youtube, paper, or book."
        )
    if len(rest) == 2 and rest[0] == "--type":
        return rest[1]
    raise utils.ExtractError(
        f"Unrecognized arguments: {' '.join(rest)}\n"
        "Usage: extract.py <source> [--type youtube|paper|book]"
    )


def main(argv) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--check":
        print(dependencies.check_report())
        return 0
    source = argv[0]
    try:
        forced = _parse_type_flag(list(argv[1:]))
        kind = utils.detect_source(source, forced)
        full_text, metadata = PARSERS[kind].parse(source)
        work = config.work_dir()
        utils.write_outputs(work, full_text, metadata)
    except utils.ExtractError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    except Exception as err:  # network, yt-dlp, PDF library failures
        print(
            f"ERROR: extraction failed for {source} "
            f"({type(err).__name__}: {err}).\n"
            "Check the URL or path and your network connection, then retry.",
            file=sys.stderr,
        )
        return 1
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
