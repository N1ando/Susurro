"""FastAPI web server for the local transcription AI.

Run from the project root with:
    uvicorn app:app --app-dir backend
Then open http://127.0.0.1:8000
"""

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from transcriber import (
    AUDIO_MIME_TYPES,
    MODEL_DOWNLOAD_SIZE,
    MODEL_NAME,
    TranscriptionError,
    model_is_downloaded,
    transcribe_file,
)

app = FastAPI(title="Susurro - local speech-to-text")

DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


def _spa():
    index = DIST_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built. Run: cd frontend && npm install && npm run build",
        )
    return FileResponse(index)


@app.get("/")
def landing():
    return _spa()


@app.get("/app")
def transcribe_app():
    return _spa()


@app.get("/api/config")
def config():
    return {
        "model": MODEL_NAME,
        "model_downloaded": model_is_downloaded(),
        "download_size": MODEL_DOWNLOAD_SIZE,
        "supported_extensions": sorted(AUDIO_MIME_TYPES),
    }


@app.post("/api/transcribe")
def transcribe(
    file: UploadFile = File(...),
    timestamps: bool = Form(False),
    pronunciation: bool = Form(True),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix or 'unknown'}'. "
            f"Supported: {', '.join(sorted(AUDIO_MIME_TYPES))}",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp, length=1024 * 1024)
            tmp_path = tmp.name
        if os.path.getsize(tmp_path) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large (2 GB limit).")

        result = transcribe_file(
            tmp_path, timestamps=timestamps, pronunciation=pronunciation
        )
        return {
            "filename": file.filename,
            "model": result.model,
            "language": result.language,
            "language_name": result.language_name,
            "language_probability": result.language_probability,
            "duration": result.duration,
            "transcript": result.text,
            "romanization": result.romanization,
            "romanization_system": result.romanization_system,
        }
    except TranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
