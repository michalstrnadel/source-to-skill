"""source-to-skill extractor entrypoint.

Usage:
  python3 scripts/extract.py <youtube-url | arxiv-url | path/to/paper.pdf>
  python3 scripts/extract.py --check     # report optional dependencies

Writes full_text.txt + metadata.json into the work dir and prints a JSON
summary with the work dir path.
"""
import json
import sys

from extractor import config, dependencies, utils
from extractor.parsers import paper, youtube


def main(argv) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--check":
        print(dependencies.check_report())
        return 0
    source = argv[0]
    try:
        kind = utils.detect_source(source)
        parser = youtube if kind == "youtube" else paper
        full_text, metadata = parser.parse(source)
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
