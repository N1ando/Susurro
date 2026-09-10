import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span>Susurro - local speech-to-text. Built with Whisper (faster-whisper), FastAPI, and React.</span>
        <div className="footer-links">
          <a href="/#features">Features</a>
          <a href="/#faq">FAQ</a>
          <Link to="/app">Open the app</Link>
          <Link to="/app?tab=record">Record voice</Link>
        </div>
      </div>
    </footer>
  );
}
