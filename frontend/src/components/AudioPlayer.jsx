import { useEffect, useRef, useState } from "react";
import { PlayIcon, PauseIcon } from "./Icons.jsx";

function clock(seconds) {
  if (!isFinite(seconds) || seconds < 0) seconds = 0;
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * Dark-themed replacement for the native <audio controls> element.
 * fallbackDuration covers MediaRecorder webm blobs, which report
 * Infinity until the duration workaround below resolves.
 */
export default function AudioPlayer({ src, fallbackDuration = 0 }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(fallbackDuration);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setPlaying(false);
    setCurrent(0);
    setDuration(fallbackDuration);

    const onLoaded = () => {
      if (isFinite(audio.duration) && audio.duration > 0) {
        setDuration(audio.duration);
      } else if (audio.duration === Infinity) {
        // Chrome reports Infinity for streamed webm; seeking far past the
        // end forces it to compute the real duration.
        const onDurationChange = () => {
          if (isFinite(audio.duration) && audio.duration > 0) {
            setDuration(audio.duration);
            audio.currentTime = 0;
            audio.removeEventListener("durationchange", onDurationChange);
          }
        };
        audio.addEventListener("durationchange", onDurationChange);
        audio.currentTime = 1e10;
      }
    };
    const onTime = () => {
      if (audio.currentTime < 1e9) setCurrent(audio.currentTime);
    };
    const onEnded = () => setPlaying(false);

    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("ended", onEnded);
    return () => {
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("ended", onEnded);
    };
  }, [src, fallbackDuration]);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play();
      setPlaying(true);
    }
  };

  const seek = (e) => {
    const audio = audioRef.current;
    const value = Number(e.target.value);
    audio.currentTime = value;
    setCurrent(value);
  };

  const max = duration > 0 ? duration : 1;
  const pct = Math.min(100, (current / max) * 100);

  return (
    <div className="player">
      <audio ref={audioRef} src={src} preload="metadata" />
      <button
        type="button"
        className="player-btn"
        onClick={toggle}
        aria-label={playing ? "Pause" : "Play"}
      >
        {playing ? <PauseIcon size={15} /> : <PlayIcon size={15} />}
      </button>
      <span className="player-time mono">{clock(current)}</span>
      <input
        type="range"
        className="player-seek"
        min="0"
        max={max}
        step="0.01"
        value={Math.min(current, max)}
        onChange={seek}
        aria-label="Seek"
        style={{
          background: `linear-gradient(to right, var(--accent) ${pct}%, var(--border-strong) ${pct}%)`,
        }}
      />
      <span className="player-time mono">{clock(duration)}</span>
    </div>
  );
}
