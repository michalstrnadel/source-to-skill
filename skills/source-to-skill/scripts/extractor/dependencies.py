"""Optional-dependency probing and the `--check` report."""
import importlib

from . import config
from .utils import ExtractError


def probe() -> dict:
    report = {}
    for module, info in config.OPTIONAL_DEPS.items():
        try:
            importlib.import_module(module)
            available = True
        except ImportError:
            available = False
        report[module] = {"available": available, **info}
    return report


def require(module: str):
    """Import and return a module, or raise ExtractError with an install hint."""
    try:
        return importlib.import_module(module)
    except ImportError:
        info = config.OPTIONAL_DEPS.get(
            module, {"pip": module, "needed_for": "this source type"}
        )
        raise ExtractError(
            f"Missing dependency for {info['needed_for']}: {info['pip']}\n"
            f"Install it with: pip install {info['pip']}"
        ) from None


def check_report() -> str:
    lines = []
    for entry in probe().values():
        status = "OK     " if entry["available"] else "MISSING"
        hint = "" if entry["available"] else f"  -> pip install {entry['pip']}"
        lines.append(f"{status} {entry['pip']} ({entry['needed_for']}){hint}")
    return "\n".join(lines)
