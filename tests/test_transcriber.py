"""Tests for the transcription engine's pure logic and its guard clauses.

Nothing here loads the Whisper model: the validation branches run before the
model is ever touched, which is exactly what makes them cheap to test.
"""

import pytest

import romanize
import transcriber
from transcriber import TranscriptionError, TranscriptionResult


class TestFormatTimestamp:
    @pytest.mark.parametrize("seconds,expected", [
        (0, "00:00"),
        (5, "00:05"),
        (61, "01:01"),
        (599.9, "09:59"),      # truncated, not rounded up
        (3600, "1:00:00"),     # the hour field only appears once needed
        (3661, "1:01:01"),
        (7322.4, "2:02:02"),
    ])
    def test_formats(self, seconds, expected):
        assert transcriber._format_timestamp(seconds) == expected


class TestTranscribeFileValidation:
    def test_missing_file_is_reported_before_the_model_loads(self, tmp_path):
        missing = tmp_path / "nope.mp3"
        with pytest.raises(TranscriptionError, match="File not found"):
            transcriber.transcribe_file(missing)

    def test_unsupported_extension_is_rejected(self, tmp_path):
        text_file = tmp_path / "notes.txt"
        text_file.write_text("this is not audio")
        with pytest.raises(TranscriptionError, match="Unsupported audio format"):
            transcriber.transcribe_file(text_file)

    def test_rejection_message_lists_what_is_supported(self, tmp_path):
        bad = tmp_path / "clip.xyz"
        bad.write_text("x")
        with pytest.raises(TranscriptionError) as excinfo:
            transcriber.transcribe_file(bad)
        assert ".mp3" in str(excinfo.value)
        assert ".wav" in str(excinfo.value)

    def test_extension_check_is_case_insensitive(self, tmp_path):
        # An uppercase extension must get past the format guard. It then fails
        # on the audio decode instead, which is a different error entirely.
        upper = tmp_path / "clip.MP3"
        upper.write_bytes(b"not really an mp3")
        with pytest.raises(TranscriptionError) as excinfo:
            transcriber.transcribe_file(upper)
        assert "Unsupported audio format" not in str(excinfo.value)


class TestTranscriptionResult:
    def test_pronunciation_fields_default_to_absent(self):
        # The CLI does not ask for readings, so the fields must be optional.
        result = TranscriptionResult(
            text="hello", language="en", language_name="English",
            language_probability=0.99, duration=1.0, model="large-v3",
        )
        assert result.romanization is None
        assert result.romanization_system is None


class TestModuleConstants:
    def test_supported_extensions_all_start_with_a_dot(self):
        assert all(ext.startswith(".") for ext in transcriber.AUDIO_MIME_TYPES)

    def test_documented_formats_are_actually_accepted(self):
        # These are the formats the README and the landing page promise.
        promised = {".mp3", ".wav", ".m4a", ".mp4", ".flac", ".ogg",
                    ".opus", ".aac", ".aiff", ".webm", ".wma"}
        assert promised <= set(transcriber.AUDIO_MIME_TYPES)

    def test_every_romanizable_language_has_a_display_name(self):
        # A language that gets a pronunciation guide but shows up as a bare
        # code in the UI would look broken.
        assert set(romanize.SYSTEM_NAMES) <= set(transcriber.LANGUAGE_NAMES)

    def test_paragraph_gap_is_a_positive_duration(self):
        assert transcriber.PARAGRAPH_GAP_SECONDS > 0


@pytest.mark.slow
class TestRealTranscription:
    """End-to-end against the real model. Run with `pytest -m slow`."""

    def test_transcribes_generated_speech_with_a_pronunciation_guide(self, tmp_path):
        import subprocess

        if not transcriber.model_is_downloaded():
            pytest.skip("Whisper model not downloaded")
        audio = tmp_path / "zh.aiff"
        try:
            subprocess.run(["say", "-v", "Tingting", "你好世界", "-o", str(audio)],
                           check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("macOS `say` with a Chinese voice is unavailable")

        result = transcriber.transcribe_file(audio, pronunciation=True)
        assert result.language == "zh"
        assert result.romanization_system == "Pinyin"
        assert "nǐ" in [tok.get("r") for tok in result.romanization[0]]
