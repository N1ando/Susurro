import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import Reveal from "../components/Reveal.jsx";
import {
  LockIcon, CheckIcon, CrossIcon, ShieldIcon, GlobeIcon,
  ClockIcon, ChipIcon, MicIcon, CloudOffIcon, LaptopIcon,
} from "../components/Icons.jsx";
import "./landing.css";

const DEMO_LINES = [
  { t: "[00:00]", text: "Okay, quick recap before we ship the release." },
  { t: "[00:04]", text: "Perfecto. Yo termino la traducción esta noche." },
  { t: "[00:09]", text: "Great. Then we publish tomorrow at nine sharp." },
];

const LANGUAGES = [
  ["Hello", "ENGLISH"], ["Hola", "SPANISH"], ["Bonjour", "FRENCH"],
  ["Hallo", "GERMAN"], ["Ciao", "ITALIAN"], ["Olá", "PORTUGUESE"],
  ["Привет", "RUSSIAN"], ["مرحبا", "ARABIC"],
  ["नमस्ते", "HINDI"], ["こんにちは", "JAPANESE"],
  ["안녕하세요", "KOREAN"], ["你好", "CHINESE"],
  ["Xin chào", "VIETNAMESE"], ["Merhaba", "TURKISH"], ["Halo", "INDONESIAN"],
  ["Γειά", "GREEK"], ["שלום", "HEBREW"],
  ["สวัสดี", "THAI"],
];

const WAVE_DELAYS = [
  0, 0.12, 0.24, 0.06, 0.3, 0.18, 0.42, 0.09, 0.36, 0.21, 0.03, 0.27,
  0.15, 0.39, 0.33, 0.12, 0.45, 0.24, 0.06, 0.3, 0.18, 0, 0.36, 0.09,
];

const FEATURES = [
  {
    icon: <ShieldIcon />, title: "Private by design",
    text: "Audio is processed on your own hardware. Nothing is uploaded, logged, or shared. Unplug the internet and it still works.",
  },
  {
    icon: <MicIcon />, title: "Record or upload",
    text: "Speak straight into your microphone in the browser, or drop in a file. Either way the audio stays on your machine.",
  },
  {
    icon: <GlobeIcon />, title: "~100 languages, auto-detected",
    text: "Whisper recognizes the language on its own and transcribes it as spoken, with proper punctuation and spelling.",
  },
  {
    icon: <GlobeIcon />, title: "Pronunciation above the script",
    text: "Chinese gets pinyin, Japanese romaji, Korean, Russian, Greek, Hebrew, Arabic and Hindi a transliteration - printed above the original so you can read it aloud.",
  },
  {
    icon: <ClockIcon />, title: "Timestamps on demand",
    text: "Toggle [MM:SS] markers per line for subtitles, meeting notes, or jumping back to the exact moment something was said.",
  },
  {
    icon: <ChipIcon />, title: "Whisper large-v3 inside",
    text: "The most accurate open Whisper model, tuned for noisy rooms, heavy accents, and technical vocabulary. No settings to tweak.",
  },
];

const MODEL_STATS = [
  ["large-v3", "The most accurate open Whisper release"],
  ["~100", "Languages detected automatically"],
  ["3 GB", "Downloaded once, then fully offline"],
  ["0", "Bytes of audio that leave your device"],
];

const FAQS = [
  ["What does it cost to run?",
   "Susurro runs the open-source Whisper large-v3 model on your own computer, so there is no service to pay for. The only cost is a one-time model download and your own CPU time."],
  ["Does my audio ever leave my computer?",
   "No. Files and microphone recordings are decoded and transcribed locally. The only network access the app ever makes is downloading the model on first use; after that it works completely offline."],
  ["Which audio formats are supported?",
   "mp3, wav, m4a, mp4 (audio), flac, ogg, opus, aac, aiff, webm, and wma. You can also record directly from your microphone in the browser. Recordings can be hours long; longer files simply take longer to process."],
  ["How accurate is it in other languages?",
   "Whisper large-v3 was trained on roughly 100 languages and detects the spoken language automatically. It is the strongest open Whisper model for accented, technical, and noisy speech alike."],
  ["I cannot read the script it transcribed. Can it show pronunciation?",
   "Yes. When a transcript comes back in a non-Latin script, a toggle appears above it that prints the reading over each word: pinyin for Chinese, romaji for Japanese, Revised Romanization for Korean, and a transliteration for Russian, Ukrainian, Greek, Hebrew, Arabic, Persian, Urdu and Hindi. Copy and Download include the readings too. This runs from local dictionaries, so it stays offline like everything else."],
  ["Why does transcription take a while?",
   "Large-v3 is a 3 GB neural network running entirely on your CPU rather than a data-center GPU. That trade is deliberate: your audio stays private, and a few extra seconds is the price. Short clips finish quickly; hour-long meetings take a coffee break."],
  ["Does it label different speakers?",
   "Not yet. Speaker diarization requires additional models that are not bundled here. The engine is modular, so diarization can be added later."],
];

function useTypedDemo() {
  const [lines, setLines] = useState([]);
  const [lang, setLang] = useState("detecting language...");

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setLines(DEMO_LINES.map((l) => ({ ...l, done: true })));
      setLang("detected: EN + ES (code-switching)");
      return;
    }
    let cancelled = false;
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    (async () => {
      while (!cancelled) {
        setLines([]);
        setLang("detecting language...");
        for (let i = 0; i < DEMO_LINES.length && !cancelled; i++) {
          const line = DEMO_LINES[i];
          setLines((prev) => [...prev, { t: line.t, text: "", done: false }]);
          for (const ch of line.text) {
            if (cancelled) return;
            setLines((prev) => {
              const next = [...prev];
              next[i] = { ...next[i], text: next[i].text + ch };
              return next;
            });
            await sleep(26 + Math.random() * 30);
          }
          setLines((prev) => {
            const next = [...prev];
            next[i] = { ...next[i], done: true };
            return next;
          });
          if (i === 0) setLang("detected: EN");
          if (i === 1) setLang("detected: EN + ES (code-switching)");
          await sleep(550);
        }
        await sleep(4200);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return { lines, lang };
}

export default function Landing() {
  const { lines, lang } = useTypedDemo();

  return (
    <div className="landing">
      <Nav variant="landing" />

      <header className="hero">
        <div className="container hero-grid">
          <div>
            <span className="chip"><LockIcon />100% on-device. Zero cloud.</span>
            <h1>Every word transcribed, <span className="glow">nothing leaves your machine</span></h1>
            <p className="hero-sub">
              Susurro turns speech into clean, punctuated text using Whisper running locally
              on your computer. Speak into the mic or drop in a recording. Around 100 languages,
              automatic detection, optional timestamps.
            </p>
            <div className="hero-ctas">
              <Link to="/app" className="btn btn-primary">Start transcribing</Link>
              <a href="#how" className="btn btn-secondary">See how it works</a>
            </div>
            <div className="hero-meta">
              <span><CheckIcon />Works offline</span>
              <span><CheckIcon />~100 languages</span>
            </div>
          </div>

          <div className="demo" aria-label="Live transcription demo">
            <div className="demo-bar">
              <span className="demo-dot" /><span className="demo-dot" /><span className="demo-dot" />
              <span className="demo-title"><span className="rec-dot" aria-hidden="true" />standup-recording.m4a</span>
            </div>
            <div className="wave" aria-hidden="true">
              {WAVE_DELAYS.map((d, i) => (
                <i key={i} style={{ animationDelay: `${d}s` }} />
              ))}
            </div>
            <div className="demo-body">
              {lines.map((line, i) => (
                <div className="demo-line" key={i}>
                  <span className="demo-time">{line.t}</span>
                  <span className="demo-text">{line.text}</span>
                  {!line.done && <span className="caret" />}
                </div>
              ))}
            </div>
            <div className="demo-foot">
              <span>{lang}</span>
              <span>whisper: large-v3 - local</span>
            </div>
          </div>
        </div>
      </header>

      <div className="ticker-wrap" aria-hidden="true">
        <div className="ticker">
          {[...LANGUAGES, ...LANGUAGES].map(([word, name], i) => (
            <span key={i}>{word} <small>{name}</small></span>
          ))}
        </div>
      </div>

      <section id="features">
        <div className="container">
          <Reveal className="section-head">
            <span className="kicker">Features</span>
            <h2>A transcription engine that respects the recording</h2>
            <p>Accurate, multilingual, and private by construction. The model runs on your CPU, so there is nothing to configure and nothing to trust.</p>
          </Reveal>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <Reveal className="card feature" key={f.title}>
                <div className="icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="how">
        <div className="container">
          <Reveal className="section-head">
            <span className="kicker">How it works</span>
            <h2>Three steps, all of them on your computer</h2>
          </Reveal>
          <div className="steps">
            <Reveal className="card step">
              <span className="step-num">STEP 01</span>
              <h3>Speak or drop a file</h3>
              <p>Record straight from your microphone, or drop in mp3, wav, m4a, flac, ogg, aac, webm and more. Up to hours long.</p>
            </Reveal>
            <Reveal className="card step">
              <span className="step-num">STEP 02</span>
              <h3>Whisper runs locally</h3>
              <p>Whisper large-v3 decodes the audio on your CPU. The first run downloads the model once (about 3 GB); after that, fully offline.</p>
            </Reveal>
            <Reveal className="card step">
              <span className="step-num">STEP 03</span>
              <h3>Get clean text</h3>
              <p>Punctuated, paragraph-formatted, language-detected. Copy it to the clipboard or download it as a text file.</p>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="privacy">
        <div className="container">
          <Reveal as="span" className="kicker">Privacy</Reveal>
          <Reveal as="h2">Your voice <em>never leaves</em> this machine</Reveal>
          <Reveal as="p" className="lede">
            Cloud transcription services receive, store, and sometimes train on your recordings.
            Susurro takes the opposite approach: the model comes to your data, not the other way around.
          </Reveal>
          <div className="compare">
            <Reveal className="card card-cloud">
              <h3><CloudOffIcon />Cloud transcription</h3>
              <ul>
                {["Audio uploaded to third-party servers",
                  "Per-minute billing that grows with every recording",
                  "Retention policies you have to read and trust",
                  "Useless without a connection"].map((item) => (
                  <li key={item}><span className="no"><CrossIcon /></span>{item}</li>
                ))}
              </ul>
            </Reveal>
            <Reveal className="card card-local">
              <h3><LaptopIcon />Susurro, on-device</h3>
              <ul>
                {["Audio stays on your disk, full stop",
                  "Transcribe as much as you want, as often as you like",
                  "Nothing to trust: you can watch the network stay silent",
                  "Works on a plane, in a SCIF, or off the grid"].map((item) => (
                  <li key={item}><span className="yes"><CheckIcon size={14} /></span>{item}</li>
                ))}
              </ul>
            </Reveal>
          </div>
        </div>
      </section>

      <section id="model">
        <div className="container">
          <Reveal className="section-head">
            <span className="kicker">The model</span>
            <h2>One model. The best one.</h2>
            <p>No dropdown of trade-offs to study: Susurro runs Whisper large-v3, the most accurate open speech model, for every recording.</p>
          </Reveal>
          <div className="stats">
            {MODEL_STATS.map(([value, label]) => (
              <Reveal className="card stat" key={label}>
                <span className="stat-value">{value}</span>
                <span className="stat-label">{label}</span>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="faq">
        <div className="container">
          <Reveal className="section-head">
            <span className="kicker">FAQ</span>
            <h2>Questions, answered</h2>
          </Reveal>
          <Reveal className="faq">
            {FAQS.map(([q, a]) => (
              <details key={q}>
                <summary>{q}</summary>
                <p>{a}</p>
              </details>
            ))}
          </Reveal>
        </div>
      </section>

      <section className="cta-final">
        <div className="container">
          <h2>Ready when you are. Offline, even.</h2>
          <p>Say it or drop it in, and watch it become text, without it ever leaving your machine.</p>
          <Link to="/app" className="btn btn-primary">Open the app</Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
