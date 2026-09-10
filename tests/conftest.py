"""Shared fixtures.

`pytest.ini` puts `backend/` on the import path, so the modules under test are
imported by their own names (`romanize`, `transcriber`, `app`) exactly as the
server imports them.
"""

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def fake_result():
    """A TranscriptionResult standing in for a real Whisper run.

    The tests that use this are about request handling and response shape, not
    about the model, so they must not pay the cost of loading 3 GB of weights.
    """
    from transcriber import TranscriptionResult

    return TranscriptionResult(
        text="你好世界",
        language="zh",
        language_name="Chinese",
        language_probability=0.99,
        duration=1.5,
        model="large-v3",
        romanization=[[{"t": "你", "r": "nǐ"}, {"t": "好", "r": "hǎo"},
                       {"t": "世", "r": "shì"}, {"t": "界", "r": "jiè"}]],
        romanization_system="Pinyin",
    )
