import { useCallback, useEffect, useRef, useState } from "react";

function pickMimeType() {
  if (typeof MediaRecorder === "undefined") return null;
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c)) return c;
  }
  return "";
}

function extensionFor(mime) {
  if (mime && mime.includes("mp4")) return "m4a";
  return "webm";
}

/**
 * Microphone recording with a live level analyser.
 * Returns a File named recording.<ext> when the user stops.
 */
export function useRecorder({ onLevel } = {}) {
  const [supported] = useState(() => pickMimeType() !== null);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [recordedFile, setRecordedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState(null);

  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const rafRef = useRef(0);
  const timerRef = useRef(0);
  const onLevelRef = useRef(onLevel);
  onLevelRef.current = onLevel;

  const cleanupStream = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    clearInterval(timerRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
  }, []);

  const discard = useCallback(() => {
    setRecordedFile(null);
    setPreviewUrl((url) => {
      if (url) URL.revokeObjectURL(url);
      return null;
    });
    setElapsed(0);
  }, []);

  const start = useCallback(async () => {
    setError(null);
    discard();
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setError(
        err.name === "NotAllowedError"
          ? "Microphone access was denied. Allow the microphone for this site in your browser settings and try again."
          : "Could not open the microphone: " + err.message
      );
      return;
    }
    streamRef.current = stream;

    // Level analyser drives the live waveform.
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const audioCtx = new AudioCtx();
    audioCtxRef.current = audioCtx;
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.75;
    source.connect(analyser);
    const bins = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(bins);
      onLevelRef.current?.(bins);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);

    const mime = pickMimeType();
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    recorderRef.current = recorder;
    chunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const type = recorder.mimeType || mime || "audio/webm";
      const blob = new Blob(chunksRef.current, { type });
      const ext = extensionFor(type);
      const file = new File([blob], `recording.${ext}`, { type });
      setRecordedFile(file);
      setPreviewUrl(URL.createObjectURL(blob));
      cleanupStream();
      setRecording(false);
    };

    recorder.start(250);
    setElapsed(0);
    const startedAt = Date.now();
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    }, 250);
    setRecording(true);
  }, [cleanupStream, discard]);

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  }, []);

  useEffect(() => {
    return () => {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.onstop = null;
        recorderRef.current.stop();
      }
      cleanupStream();
    };
  }, [cleanupStream]);

  return { supported, recording, elapsed, recordedFile, previewUrl, error, start, stop, discard };
}
