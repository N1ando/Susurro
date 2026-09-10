"""Tests for the HTTP surface.

`/api/transcribe` is exercised with the transcription function patched out:
these tests are about request validation, response shape and error mapping,
none of which should depend on a 3 GB model being present.
"""

import io

import pytest

import app as app_module
from transcriber import TranscriptionError


def _audio_upload(name="clip.mp3"):
    return {"file": (name, io.BytesIO(b"fake audio bytes"), "audio/mpeg")}


class TestConfigEndpoint:
    def test_reports_the_model_and_supported_extensions(self, client):
        body = client.get("/api/config").json()
        assert body["model"]
        assert body["download_size"]
        assert ".mp3" in body["supported_extensions"]
        assert isinstance(body["model_downloaded"], bool)

    def test_extensions_are_sorted(self, client):
        extensions = client.get("/api/config").json()["supported_extensions"]
        assert extensions == sorted(extensions)


class TestTranscribeEndpoint:
    def test_rejects_an_unsupported_file_type(self, client):
        response = client.post("/api/transcribe", files=_audio_upload("notes.txt"))
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_rejects_a_file_with_no_extension(self, client):
        response = client.post("/api/transcribe", files=_audio_upload("recording"))
        assert response.status_code == 400

    def test_returns_the_transcript_and_the_pronunciation_guide(
        self, client, monkeypatch, fake_result
    ):
        monkeypatch.setattr(app_module, "transcribe_file",
                            lambda *a, **k: fake_result)
        body = client.post("/api/transcribe", files=_audio_upload()).json()
        assert body["transcript"] == "你好世界"
        assert body["language_name"] == "Chinese"
        assert body["romanization_system"] == "Pinyin"
        assert body["romanization"][0][0] == {"t": "你", "r": "nǐ"}
        assert body["filename"] == "clip.mp3"

    def test_pronunciation_is_requested_by_default(
        self, client, monkeypatch, fake_result
    ):
        seen = {}

        def spy(path, timestamps=False, pronunciation=False):
            seen.update(timestamps=timestamps, pronunciation=pronunciation)
            return fake_result

        monkeypatch.setattr(app_module, "transcribe_file", spy)
        client.post("/api/transcribe", files=_audio_upload())
        assert seen == {"timestamps": False, "pronunciation": True}

    def test_form_flags_are_forwarded(self, client, monkeypatch, fake_result):
        seen = {}

        def spy(path, timestamps=False, pronunciation=False):
            seen.update(timestamps=timestamps, pronunciation=pronunciation)
            return fake_result

        monkeypatch.setattr(app_module, "transcribe_file", spy)
        client.post("/api/transcribe", files=_audio_upload(),
                    data={"timestamps": "true", "pronunciation": "false"})
        assert seen == {"timestamps": True, "pronunciation": False}

    def test_a_transcription_error_becomes_422_not_500(
        self, client, monkeypatch
    ):
        def boom(*args, **kwargs):
            raise TranscriptionError("No speech was detected in the audio.")

        monkeypatch.setattr(app_module, "transcribe_file", boom)
        response = client.post("/api/transcribe", files=_audio_upload())
        assert response.status_code == 422
        assert response.json()["detail"] == "No speech was detected in the audio."

    def test_the_temporary_upload_is_deleted_afterwards(
        self, client, monkeypatch, fake_result
    ):
        captured = {}

        def spy(path, **kwargs):
            captured["path"] = path
            return fake_result

        monkeypatch.setattr(app_module, "transcribe_file", spy)
        client.post("/api/transcribe", files=_audio_upload())
        import os
        assert not os.path.exists(captured["path"])

    def test_the_temporary_upload_is_deleted_even_on_failure(
        self, client, monkeypatch
    ):
        captured = {}

        def boom(path, **kwargs):
            captured["path"] = path
            raise TranscriptionError("nope")

        monkeypatch.setattr(app_module, "transcribe_file", boom)
        client.post("/api/transcribe", files=_audio_upload())
        import os
        assert not os.path.exists(captured["path"])


class TestFrontendRoutes:
    @pytest.mark.parametrize("path", ["/", "/app"])
    def test_both_routes_serve_the_built_single_page_app(self, client, path):
        response = client.get(path)
        if response.status_code == 503:
            pytest.skip("frontend not built - run: cd frontend && npm run build")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dist_dir_points_at_the_frontend_folder(self):
        # Guards the relative path that the backend/frontend split depends on.
        assert app_module.DIST_DIR.name == "dist"
        assert app_module.DIST_DIR.parent.name == "frontend"
