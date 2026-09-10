import { Link } from "react-router-dom";
import Logo from "./Logo.jsx";
import { LockIcon } from "./Icons.jsx";

export default function Nav({ variant = "landing" }) {
  return (
    <nav className="nav" aria-label="Main">
      <div className="nav-inner">
        <Link className="brand" to="/">
          <Logo />
          Susurro
        </Link>
        <div className="nav-links">
          <a href="/#features">Features</a>
          <a href="/#how">How it works</a>
          <a href="/#faq">FAQ</a>
          {variant === "landing" ? (
            <Link to="/app" className="btn btn-primary btn-sm">Open the app</Link>
          ) : (
            <span className="chip" title="Audio is processed on this machine only">
              <LockIcon size={12} />
              local only
            </span>
          )}
        </div>
      </div>
    </nav>
  );
}
