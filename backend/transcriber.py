"""Core transcription logic using a local Whisper model.

Runs entirely on this machine: no API key, no network calls after the
one-time model download, and audio never leaves the computer.
"""

import os
import threading
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

import romanize

# The product ships with a single model: Whisper large-v3, the most
# accurate open Whisper release. Override with WHISPER_MODEL if needed.
MODEL_NAME = os.environ.get("WHISPER_MODEL", "large-v3")
MODEL_DOWNLOAD_SIZE = "3 GB"

AUDIO_MIME_TYPES = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".aiff": "audio/aiff",
    ".aif": "audio/aiff",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".opus": "audio/opus",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".webm": "audio/webm",
    ".wma": "audio/x-ms-wma",
}

LANGUAGE_NAMES = {
    "en": "English", "zh": "Chinese", "de": "German", "es": "Spanish",
    "ru": "Russian", "ko": "Korean", "fr": "French", "ja": "Japanese",
    "pt": "Portuguese", "tr": "Turkish", "pl": "Polish", "ca": "Catalan",
    "nl": "Dutch", "ar": "Arabic", "sv": "Swedish", "it": "Italian",
    "id": "Indonesian", "hi": "Hindi", "fi": "Finnish", "vi": "Vietnamese",
    "he": "Hebrew", "uk": "Ukrainian", "el": "Greek", "ms": "Malay",
    "cs": "Czech", "ro": "Romanian", "da": "Danish", "hu": "Hungarian",
    "ta": "Tamil", "no": "Norwegian", "th": "Thai", "ur": "Urdu",
    "hr": "Croatian", "bg": "Bulgarian", "lt": "Lithuanian", "la": "Latin",
    "mi": "Maori", "ml": "Malayalam", "cy": "Welsh", "sk": "Slovak",
    "te": "Telugu", "fa": "Persian", "lv": "Latvian", "bn": "Bengali",
    "tl": "Tagalog", "sw": "Swahili", "jv": "Javanese", "su": "Sundanese",
}

# Pause length (seconds) between segments that starts a new paragraph.
PARAGRAPH_GAP_SECONDS = 2.0


class TranscriptionError(Exception):
    """Raised when transcription fails for a user-actionable reason."""


@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_name: str
    language_probability: float
    duration: float
    model: str
    # Pronunciation guide for non-Latin scripts, None when the transcript is
    # already readable (see romanize.romanize_transcript).
    romanization: list[list[dict]] | None = None
    romanization_system: str | None = None


_models: dict[str, WhisperModel] = {}
_models_lock = threading.Lock()


def _get_model(name: str) -> WhisperModel:
    """Load the Whisper model, caching it so repeat requests are fast.

    The first call downloads the model (about 3 GB for large-v3);
    afterwards it loads from the local cache and works offline.
    """
    with _models_lock:
        if name not in _models:
            _models[name] = WhisperModel(name, device="cpu", compute_type="int8")
        return _models[name]


def model_is_downloaded(name: str | None = None) -> bool:
    """True when the model already exists in the local HuggingFace cache."""
    name = name or MODEL_NAME
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    snapshots = hf_home / "hub" / f"models--Systran--faster-whisper-{name}" / "snapshots"
    if not snapshots.is_dir():
        return False
    return any(p.is_dir() and any(p.iterdir()) for p in snapshots.iterdir())


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def transcribe_file(
    path: str | os.PathLike,
    timestamps: bool = False,
    pronunciation: bool = False,
) -> TranscriptionResult:
    """Transcribe an audio file and return the transcript with metadata.

    With `pronunciation`, a transcript in a non-Latin script also carries a
    reading for each word so it can be displayed above the original text.
    """
    path = Path(path)
    if not path.is_file():
        raise TranscriptionError(f"File not found: {path}")
    if path.suffix.lower() not in AUDIO_MIME_TYPES:
        supported = ", ".join(sorted(AUDIO_MIME_TYPES))
        raise TranscriptionError(
            f"Unsupported audio format '{path.suffix}'. Supported extensions: {supported}"
        )

    whisper = _get_model(MODEL_NAME)

    try:
        segments, info = whisper.transcribe(
            str(path),
            beam_size=5,
            vad_filter=True,
        )

        lines: list[str] = []
        paragraph: list[str] = []
        prev_end = None
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            if timestamps:
                lines.append(f"[{_format_timestamp(segment.start)}] {text}")
            else:
                if prev_end is not None and segment.start - prev_end >= PARAGRAPH_GAP_SECONDS:
                    lines.append(" ".join(paragraph))
                    lines.append("")
                    paragraph = []
                paragraph.append(text)
            prev_end = segment.end
        if paragraph:
            lines.append(" ".join(paragraph))
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError(
            f"Could not process the audio file ({exc}). "
            "It may be corrupted or not a real audio file."
        ) from exc

    text = "\n".join(lines).strip()
    if not text:
        raise TranscriptionError(
            "No speech was detected in the audio. It may be silent or too noisy."
        )

    readings, system = (
        romanize.romanize_transcript(text, info.language)
        if pronunciation
        else (None, None)
    )

    return TranscriptionResult(
        text=text,
        language=info.language,
        language_name=LANGUAGE_NAMES.get(info.language, info.language),
        language_probability=round(info.language_probability, 3),
        duration=round(info.duration, 1),
        model=MODEL_NAME,
        romanization=readings,
        romanization_system=system,
    )
