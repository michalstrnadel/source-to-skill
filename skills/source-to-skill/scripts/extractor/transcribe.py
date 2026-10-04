"""Local speech-to-text with Whisper: mlx-whisper, faster-whisper, whisper.

Everything runs on the user's machine - no API keys. The first backend
that imports wins (see config.WHISPER_BACKENDS for the order and models).
"""
import importlib
import os
import shutil
import sys

from . import config
from .utils import ExtractError


def available_backend():
    """Name of the first importable Whisper backend, or None."""
    for module in config.WHISPER_BACKENDS:
        try:
            importlib.import_module(module)
        except Exception:  # ImportError, or a broken native wheel
            continue
        return module
    return None


def install_hint() -> str:
    return (
        "Install a local Whisper backend: pip install mlx-whisper "
        "(Apple Silicon) or pip install faster-whisper (anywhere)."
    )


def model_for(backend: str) -> str:
    return (
        os.environ.get(config.WHISPER_MODEL_ENV)
        or config.WHISPER_BACKENDS[backend]["model"]
    )


def _require_backend() -> str:
    backend = available_backend()
    if backend is None:
        raise ExtractError(
            "Audio transcription needs a local Whisper backend.\n"
            + install_hint()
        )
    if config.WHISPER_BACKENDS[backend]["needs_ffmpeg"] and not shutil.which(
        "ffmpeg"
    ):
        raise ExtractError(
            f"{config.WHISPER_BACKENDS[backend]['pip']} needs ffmpeg to "
            "decode audio.\nInstall it: brew install ffmpeg (macOS), "
            "sudo apt install ffmpeg (Debian/Ubuntu), or "
            "winget install ffmpeg (Windows)."
        )
    return backend


def _run_mlx(module, path, model):
    result = module.transcribe(str(path), path_or_hf_repo=model)
    segments = [(seg["start"], seg["text"]) for seg in result["segments"]]
    return segments, result.get("language")


def _run_faster(module, path, model):
    whisper_model = module.WhisperModel(
        model, device="auto", compute_type="int8"
    )
    segments, info = whisper_model.transcribe(str(path), vad_filter=True)
    return [(seg.start, seg.text) for seg in segments], info.language


def _run_openai(module, path, model):
    result = module.load_model(model).transcribe(str(path))
    segments = [(seg["start"], seg["text"]) for seg in result["segments"]]
    return segments, result.get("language")


RUNNERS = {
    "mlx_whisper": _run_mlx,
    "faster_whisper": _run_faster,
    "whisper": _run_openai,
}


def transcribe(path):
    """Transcribe an audio/video file.

    Returns (cues, language, description) where cues follow the caption
    contract [{'start_s': float, 'text': str}] and description names the
    backend and model, e.g. "mlx-whisper (whisper-large-v3-turbo)".
    """
    backend = _require_backend()
    model = model_for(backend)
    label = f"{config.WHISPER_BACKENDS[backend]['pip']} ({model.split('/')[-1]})"
    print(
        f"Transcribing {getattr(path, 'name', path)} locally with {label} - "
        "this takes a few minutes per hour of audio...",
        file=sys.stderr,
    )
    module = importlib.import_module(backend)
    raw, language = RUNNERS[backend](module, path, model)
    cues = []
    for start, text in raw:
        text = " ".join(str(text).split())
        if text and not (cues and cues[-1]["text"] == text):
            cues.append({"start_s": float(start), "text": text})
    if not cues:
        raise ExtractError(
            f"Whisper found no speech in {path}.\n"
            "Check that the file has an audio track with spoken content."
        )
    return cues, language, label
