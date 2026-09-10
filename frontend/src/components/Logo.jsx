export default function Logo({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#131826" />
      <g stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round">
        <line x1="8" y1="13" x2="8" y2="19" />
        <line x1="13" y1="9" x2="13" y2="23" />
        <line x1="18" y1="12" x2="18" y2="20" />
        <line x1="23" y1="14" x2="23" y2="18" />
      </g>
    </svg>
  );
}
