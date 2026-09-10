"""Command-line interface for the local transcription AI.

Usage (from the project root):
    python backend/cli.py path/to/audio.mp3
    python backend/cli.py interview.m4a -o transcript.txt
    python backend/cli.py meeting.wav --timestamps
"""

import argparse
import sys
from pathlib import Path

from transcriber import (
    MODEL_DOWNLOAD_SIZE,
    MODEL_NAME,
    TranscriptionError,
    model_is_downloaded,
    transcribe_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Transcribe an audio file locally with Whisper {MODEL_NAME}. No API key needed."
    )
    parser.add_argument("audio", help="Path to the audio file (mp3, wav, m4a, flac, ogg, ...)")
    parser.add_argument("-o", "--output", help="Write the transcript to this file instead of stdout")
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Prefix each line with its [MM:SS] start time",
    )
    args = parser.parse_args()

    note = ""
    if not model_is_downloaded():
        note = f" (first use downloads about {MODEL_DOWNLOAD_SIZE})"
    print(f"Transcribing {args.audio} with Whisper {MODEL_NAME}{note}...", file=sys.stderr)
    try:
        result = transcribe_file(args.audio, timestamps=args.timestamps)
    except TranscriptionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    confidence = int(result.language_probability * 100)
    print(
        f"Detected language: {result.language_name} ({confidence}% confidence), "
        f"audio length {result.duration}s",
        file=sys.stderr,
    )

    if args.output:
        Path(args.output).write_text(result.text + "\n", encoding="utf-8")
        print(f"Transcript written to {args.output}", file=sys.stderr)
    else:
        print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
