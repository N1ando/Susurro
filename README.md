# Susurro - local speech-to-text AI

Multilingual transcription that runs entirely on your own computer using
OpenAI's open-source Whisper model (via `faster-whisper`). No API key, no
account, no cloud: after a one-time model download everything works offline
and your audio never leaves your machine.

The project splits into a React frontend and a FastAPI backend:

- `/` - landing page (features, how it works, privacy, model guide, FAQ)
- `/app` - the transcription app:
  - **Upload file** - drag-and-drop any audio file
  - **Record voice** - speak into your microphone in the browser, with a
    live level meter, preview playback, then transcribe
- CLI - `backend/cli.py` for scripting and batch use

Features:

- Automatic language detection across ~100 languages, with punctuation
- **Pronunciation guide** - transcripts in a non-Latin script get their
  reading printed above the original text, so you can read back a language
  you cannot yet decode:

  ```
  nǐ hǎo shì jiè          nihongo wo benkyou           Privet
  你 好 世 界              日本語 を 勉強               Привет
  ```
- In-browser microphone recording (WebM/Opus in Chrome and Firefox,
  M4A in Safari), processed locally like any other file
- Custom dark-themed audio player for reviewing recordings before transcribing
- Clean paragraph formatting (breaks on long pauses)
- Optional `[MM:SS]` timestamps per line
- One model, the best one: Whisper large-v3, the most accurate open release

## Pronunciation guide

When a transcript comes back in a script you cannot read, a toggle appears
above it that prints the reading over each word. Nothing extra to install
beyond `requirements.txt`, and no network access: the readings come from
dictionaries bundled in the packages.

| Language | System | Engine |
| --- | --- | --- |
| Chinese | Pinyin, with tone marks | `pypinyin`, one reading per hanzi |
| Japanese | Romaji (Hepburn) | `pykakasi`, per word - kanji readings are context-dependent |
| Korean | Revised Romanization | built in, including the liaison rule (한국어 reads *han-gu-geo*, not *han-guk-eo*) |
| Russian, Ukrainian, Bulgarian, Serbian | Transliteration | built-in table |
| Greek | Transliteration | built-in table, including digraphs (μπ reads *b*) |
| Hebrew | Transliteration | built-in table, dagesh aware |
| Arabic, Persian, Urdu | Transliteration | built-in table, shadda aware |
| Hindi | Transliteration | built-in table, handles the inherent vowel and virama |

Copy and Download .txt follow the toggle: with it on, each line is written
out followed by its reading on the next line.

Limits, stated plainly:

- **Unvocalized Arabic and Hebrew show consonants only** (مرحبا reads
  `mrhba`), because short vowels are not written in the source text.
  Recovering them needs a dictionary lookup this does not do.
- **Thai, Tamil, Telugu, Bengali and Malayalam are deliberately excluded.**
  A character-by-character mapping of those scripts is actively wrong - Thai
  writes some vowels before the consonant they are pronounced after - and a
  wrong pronunciation is worse than none. Adding one properly means adding a
  table plus a branch in `backend/romanize.py`, in `_romanize_word`.
- Korean romanization applies the liaison rule but not the full set of
  assimilation rules, so a few consonant clusters read approximately.

## Setup (one time)

Backend:

```bash
cd "Voice to text ai"
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Run the website

From the project root:

```bash
source .venv/bin/activate
uvicorn app:app --app-dir backend
```

`--app-dir` puts `backend/` on the import path, so the server can be started
from the root without a `cd`. `cd backend && uvicorn app:app` works too.

Open http://127.0.0.1:8000 for the landing page, or go straight to
http://127.0.0.1:8000/app to transcribe (http://127.0.0.1:8000/app?tab=record
jumps straight to the microphone).

## Frontend development

For live-reload while editing the React code, run both servers:

```bash
uvicorn app:app --app-dir backend   # terminal 1: API on :8000
cd frontend && npm run dev          # terminal 2: Vite dev server on :5173
```

The dev server proxies `/api` to the backend. After making changes, run
`npm run build` so the production server picks them up.

## Command line

```bash
python backend/cli.py recording.mp3                   # print transcript to stdout
python backend/cli.py interview.m4a -o transcript.txt # save to a file
python backend/cli.py lecture.mp3 --timestamps        # [MM:SS] line timestamps
```

## Tests

```bash
pip install -r backend/requirements-dev.txt
pytest                  # 94 tests, about 4 seconds
pytest -m slow          # also run the real-model test (about 20 seconds)
```

`pytest.ini` puts `backend/` on the import path, so the tests import
`romanize`, `transcriber` and `app` exactly as the server does. Nothing in the
default run loads the Whisper model: `/api/transcribe` is tested with the
transcription function patched out, so the suite stays fast and works on a
machine that has never downloaded the weights.

```
tests/test_romanize.py      pronunciation guides for every supported script
tests/test_transcriber.py   timestamp formatting, upload validation, constants
tests/test_api.py           endpoints, error mapping, temp-file cleanup
```

The `slow` marker covers one end-to-end test that synthesizes speech with the
macOS `say` command and runs it through the real model. It is deselected by
default and skips itself when the model or the voice is unavailable.

## The model

Susurro runs a single model: Whisper `large-v3` (about 3 GB), the most
accurate open Whisper release. The first use downloads it once to
`~/.cache/huggingface/`; after that it loads locally and works offline.
Because it runs on your CPU, longer recordings take proportionally longer.

Power users can override the model with the `WHISPER_MODEL` environment
variable (e.g. `WHISPER_MODEL=small uvicorn app:app --app-dir backend`),
but the product is
designed and labeled around large-v3.

## Project structure

```
backend/                      Python API and transcription engine
  app.py                      FastAPI server: serves the built site + /api/transcribe
  transcriber.py              Whisper engine (transcribe_file)
  romanize.py                 Pronunciation guides for non-Latin scripts
  cli.py                      Command-line interface
  requirements.txt            Python dependencies
  requirements-dev.txt        Test dependencies (pytest, httpx)

tests/                        pytest suite (see Tests above)

frontend/                     React frontend (Vite)
  index.html                  Vite entry document
  package.json                Node dependencies and build scripts
  vite.config.js              Dev server + /api proxy to the backend
  src/theme.css               Design system (dark, Space Grotesk / DM Sans / JetBrains Mono)
  src/pages/Landing.jsx       Landing page
  src/pages/Transcribe.jsx    Transcription app (upload + record tabs)
  src/hooks/useRecorder.js    Microphone recording (MediaRecorder + level analyser)
  dist/                       Production build served by FastAPI (npm run build)
```

The backend serves `frontend/dist/` directly, so a production deployment is a
single uvicorn process - there is no separate web server to run.

## Supported formats

mp3, wav, m4a, mp4 (audio), flac, ogg, opus, aac, aiff, webm, wma.

## Notes and limitations

- Microphone access requires a secure context: localhost works out of the
  box; if you serve it to other devices you will need HTTPS.
- The pronunciation guide is a reading aid, not a translation, and not a
  substitute for a proper romanization standard in published work.
- Speaker diarization ([Speaker 1] / [Speaker 2] labels) is not included:
  open-source diarization models require a HuggingFace access token, which
  conflicts with the no-key promise.
- The Google Fonts used by the site load from the network; offline the pages
  fall back to system fonts and everything still works.
