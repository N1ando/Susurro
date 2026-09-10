import { useCallback, useEffect, useRef, useState } from "react";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import AudioPlayer from "../components/AudioPlayer.jsx";
import { MicIcon, StopIcon, UploadIcon } from "../components/Icons.jsx";
import { useRecorder } from "../hooks/useRecorder.js";
import "./transcribe.css";

const MODEL = "large-v3";
const MODEL_SIZE = "3 GB";

const ACCEPT = ".mp3,.wav,.m4a,.mp4,.flac,.ogg,.oga,.opus,.aac,.aiff,.aif,.webm,.wma,audio/*";

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatClock(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

/* Live microphone level bars drawn on a canvas. */
function LevelMeter({ registerDraw }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 420;
    const cssHeight = canvas.clientHeight || 56;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    ctx.scale(dpr, dpr);

    const BARS = 36;
    registerDraw((bins) => {
      ctx.clearRect(0, 0, cssWidth, cssHeight);
      const step = Math.floor(bins.length / BARS);
      const barWidth = cssWidth / BARS;
      for (let i = 0; i < BARS; i++) {
        let sum = 0;
        for (let j = 0; j < step; j++) sum += bins[i * step + j];
        const level = sum / step / 255;
        const h = Math.max(3, level * cssHeight);
        const x = i * barWidth + barWidth * 0.2;
        const y = (cssHeight - h) / 2;
        ctx.fillStyle = `rgba(74, 222, 128, ${0.35 + level * 0.65})`;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth * 0.6, h, 2);
        ctx.fill();
      }
    });
    return () => registerDraw(null);
  }, [registerDraw]);

  return <canvas ref={canvasRef} className="level-canvas" aria-hidden="true" />;
}

export default function Transcribe() {
  const [tab, setTab] = useState(() =>
    new URLSearchParams(window.location.search).get("tab") === "record" ? "record" : "upload"
  );
  const [uploadFile, setUploadFile] = useState(null);
  const [dragover, setDragover] = useState(false);
  const [timestamps, setTimestamps] = useState(false);
  const [showPronunciation, setShowPronunciation] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busySeconds, setBusySeconds] = useState(0);
  const [modelReady, setModelReady] = useState(true);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);
  const resultRef = useRef(null);

  const drawRef = useRef(null);
  const registerDraw = useCallback((fn) => { drawRef.current = fn; }, []);
  const handleLevel = useCallback((bins) => { drawRef.current?.(bins); }, []);

  const recorder = useRecorder({ onLevel: handleLevel });

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((cfg) => setModelReady(Boolean(cfg.model_downloaded)))
      .catch(() => {});
  }, []);

  // Elapsed counter while transcribing, so slow jobs show visible progress.
  useEffect(() => {
    if (!busy) return;
    setBusySeconds(0);
    const startedAt = Date.now();
    const id = setInterval(() => {
      setBusySeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [busy]);

  // Bring the transcript into view when it arrives.
  useEffect(() => {
    if (result && resultRef.current) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      resultRef.current.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
    }
  }, [result]);

  const activeFile = tab === "upload" ? uploadFile : recorder.recordedFile;

  const pickFile = (file) => {
    setUploadFile(file);
    setError(null);
  };

  const transcribe = async () => {
    if (!activeFile || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", activeFile, activeFile.name);
      formData.append("timestamps", timestamps);
      formData.append("pronunciation", true);
      const res = await fetch("/api/transcribe", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Request failed with status ${res.status}`);
      setResult(data);
      setModelReady(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  /* Ruby markup cannot survive a copy or a .txt file, so the reading is
     written on its own line under the original instead. */
  const transcriptText = () => {
    if (!result.romanization || !showPronunciation) return result.transcript;
    return result.romanization
      .map((line) => {
        const original = line.map((tok) => tok.t).join("");
        if (!original.trim()) return "";
        if (!line.some((tok) => tok.r)) return original;
        const reading = line
          .map((tok) => tok.r || tok.t.trim())
          .filter(Boolean)
          .join(" ")
          .replace(/\s+/g, " ")
          .trim();
        return `${original}\n${reading}`;
      })
      .join("\n");
  };

  const copyTranscript = async (e) => {
    await navigator.clipboard.writeText(transcriptText());
    const btn = e.currentTarget;
    btn.textContent = "Copied";
    setTimeout(() => { btn.textContent = "Copy"; }, 1500);
  };

  const downloadTranscript = () => {
    const blob = new Blob([transcriptText()], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const base = result.filename ? result.filename.replace(/\.[^.]+$/, "") : "transcript";
    a.download = `${base}-transcript.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <>
      <Nav variant="app" />
      <main className="transcribe-main">
        <div className="page-head">
          <div>
            <h1>Transcribe audio</h1>
            <p>Everything runs on this machine with Whisper large-v3, the most accurate open model.</p>
          </div>
          <span className="chip chip-neutral model-chip" title="The only network access is the one-time model download">
            whisper {MODEL}
          </span>
        </div>

        <div className="tabs" role="tablist" aria-label="Audio source">
          <button
            className={`tab ${tab === "upload" ? "active" : ""}`}
            role="tab" aria-selected={tab === "upload"}
            onClick={() => setTab("upload")}
          >
            <UploadIcon size={16} /> Upload file
          </button>
          <button
            className={`tab ${tab === "record" ? "active" : ""}`}
            role="tab" aria-selected={tab === "record"}
            onClick={() => setTab("record")}
          >
            <MicIcon size={16} /> Record voice
          </button>
        </div>

        <div className="card">
          {tab === "upload" ? (
            <div
              className={`dropzone ${dragover ? "dragover" : ""} ${uploadFile ? "has-file" : ""}`}
              role="button" tabIndex={0}
              aria-label="Choose an audio file"
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInputRef.current?.click(); }
              }}
              onDragEnter={(e) => { e.preventDefault(); setDragover(true); }}
              onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
              onDragLeave={(e) => { e.preventDefault(); setDragover(false); }}
              onDrop={(e) => {
                e.preventDefault();
                setDragover(false);
                if (e.dataTransfer.files.length) pickFile(e.dataTransfer.files[0]);
              }}
            >
              <div className="dz-icon"><UploadIcon /></div>
              <p className="primary">{uploadFile ? uploadFile.name : "Drag and drop an audio file"}</p>
              <p className="hint">or <span className="browse">browse</span> - mp3, wav, m4a, flac, ogg, aac, webm...</p>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPT}
                hidden
                onChange={(e) => { if (e.target.files.length) pickFile(e.target.files[0]); }}
              />
            </div>
          ) : (
            <div className={`recorder ${recorder.recording ? "live" : ""} ${recorder.recordedFile ? "done" : ""}`}>
              {!recorder.supported ? (
                <p className="hint">This browser does not support microphone recording. Use the Upload tab instead.</p>
              ) : recorder.recording ? (
                <div className="rec-live">
                  <LevelMeter registerDraw={registerDraw} />
                  <span className="rec-timer"><span className="dot" aria-hidden="true" />{formatClock(recorder.elapsed)}</span>
                  <button className="mic-btn stop" onClick={recorder.stop} aria-label="Stop recording">
                    <StopIcon size={26} />
                  </button>
                  <p className="hint">Recording from your microphone. Click stop when you are done speaking.</p>
                </div>
              ) : recorder.recordedFile ? (
                <div className="rec-done">
                  <AudioPlayer src={recorder.previewUrl} fallbackDuration={recorder.elapsed} />
                  <span className="rec-timer">{formatClock(recorder.elapsed)} recorded - {formatSize(recorder.recordedFile.size)}</span>
                  <div className="rec-done-actions">
                    <button className="btn btn-secondary btn-sm" onClick={recorder.start}>Re-record</button>
                    <button className="btn btn-secondary btn-sm" onClick={recorder.discard}>Discard</button>
                  </div>
                  <p className="hint">Sounds good? Hit Transcribe below.</p>
                </div>
              ) : (
                <>
                  <button className="mic-btn" onClick={recorder.start} aria-label="Start recording">
                    <MicIcon size={30} />
                  </button>
                  <p className="primary">Tap to start recording</p>
                  <p className="hint">Speak in any language. The audio is captured and transcribed entirely on this machine.</p>
                </>
              )}
            </div>
          )}

          <div className="controls">
            <span className="file-info">
              {activeFile
                ? <><strong>{activeFile.name}</strong> ({formatSize(activeFile.size)})</>
                : tab === "upload" ? "No file selected" : "No recording yet"}
            </span>
            <span className="spacer" />
            <label className="switch-label">
              <span className="switch">
                <input
                  type="checkbox"
                  checked={timestamps}
                  onChange={(e) => setTimestamps(e.target.checked)}
                  aria-label="Add timestamps to each line"
                />
                <span className="switch-track" aria-hidden="true" />
              </span>
              Timestamps
            </label>
            <button className="btn btn-primary" onClick={transcribe} disabled={!activeFile || busy}>
              {busy ? "Transcribing..." : "Transcribe"}
            </button>
          </div>

          {busy && (
            <div className="status" role="status">
              <div className="eq" aria-hidden="true"><i /><i /><i /><i /></div>
              <span>
                {modelReady
                  ? `Transcribing ${activeFile?.name} with Whisper ${MODEL}. The model runs on your CPU, so longer recordings take longer.`
                  : `First run: downloading Whisper ${MODEL} (about ${MODEL_SIZE}, one time only), then transcribing ${activeFile?.name}.`}
              </span>
              <span className="busy-clock mono">{formatClock(busySeconds)}</span>
            </div>
          )}
        </div>

        {(error || recorder.error) && (
          <div className="error-box" role="alert">{error || recorder.error}</div>
        )}

        {result && (
          <div className="card result" ref={resultRef}>
            <div className="result-head">
              <div>
                <h2>Transcript</h2>
                <div className="result-meta">
                  {result.filename} | {result.language_name}{" "}
                  ({Math.round(result.language_probability * 100)}% confidence) | {formatDuration(result.duration)}
                  {result.romanization_system ? ` | ${result.romanization_system} available` : ""}
                </div>
              </div>
              <div className="result-actions">
                {result.romanization && (
                  <button
                    className={`btn btn-sm pron-toggle ${showPronunciation ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => setShowPronunciation((on) => !on)}
                    aria-pressed={showPronunciation}
                    title={`Show ${result.romanization_system} above the original script`}
                  >
                    {result.romanization_system}
                  </button>
                )}
                <button className="btn btn-secondary btn-sm" onClick={copyTranscript}>Copy</button>
                <button className="btn btn-secondary btn-sm" onClick={downloadTranscript}>Download .txt</button>
              </div>
            </div>
            {result.romanization && showPronunciation ? (
              <div className="transcript with-ruby" lang={result.language}>
                {result.romanization.map((line, i) =>
                  line.length === 0 ? (
                    <div key={i} className="t-break" />
                  ) : (
                    <p key={i} className="t-line">
                      {line.map((tok, j) =>
                        tok.r ? (
                          <ruby key={j}>
                            {tok.t}
                            <rt>{tok.r}</rt>
                          </ruby>
                        ) : (
                          <span key={j}>{tok.t}</span>
                        )
                      )}
                    </p>
                  )
                )}
              </div>
            ) : (
              <div className="transcript">{result.transcript}</div>
            )}
          </div>
        )}
      </main>
      <Footer />
    </>
  );
}
