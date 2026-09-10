const base = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export const Icon = ({ children, size = 21, strokeWidth = 1.8, ...rest }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} strokeWidth={strokeWidth} aria-hidden="true" {...rest}>
    {children}
  </svg>
);

export const CheckIcon = (p) => (
  <Icon size={p.size ?? 13} strokeWidth={2.2}><path d="M20 6 9 17l-5-5" /></Icon>
);
export const CrossIcon = (p) => (
  <Icon size={p.size ?? 14} strokeWidth={2.2}><path d="M18 6 6 18M6 6l12 12" /></Icon>
);
export const LockIcon = (p) => (
  <Icon size={p.size ?? 13} strokeWidth={2.2}>
    <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </Icon>
);
export const ShieldIcon = () => (
  <Icon><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></Icon>
);
export const KeyOffIcon = () => (
  <Icon><path d="M15 7.5a4.5 4.5 0 1 1-4.5 4.5" /><path d="m10.5 12-8 8 2 2" /><path d="m5.5 17 2 2" /></Icon>
);
export const GlobeIcon = () => (
  <Icon>
    <circle cx="12" cy="12" r="10" /><path d="M2 12h20" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </Icon>
);
export const ClockIcon = () => (
  <Icon><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></Icon>
);
export const ChipIcon = () => (
  <Icon>
    <rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" />
    <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" />
  </Icon>
);
export const MicIcon = (p) => (
  <Icon size={p?.size ?? 21}>
    <rect x="9" y="2" width="6" height="12" rx="3" />
    <path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v4" />
  </Icon>
);
export const UploadIcon = (p) => (
  <Icon size={p?.size ?? 22}><path d="M12 19V5M5 12l7-7 7 7" /></Icon>
);
export const StopIcon = (p) => (
  <svg width={p?.size ?? 16} height={p?.size ?? 16} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);
export const PlayIcon = (p) => (
  <svg width={p?.size ?? 16} height={p?.size ?? 16} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M8 5.5v13a1 1 0 0 0 1.53.85l10.2-6.5a1 1 0 0 0 0-1.7L9.53 4.65A1 1 0 0 0 8 5.5z" />
  </svg>
);
export const PauseIcon = (p) => (
  <svg width={p?.size ?? 16} height={p?.size ?? 16} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <rect x="6" y="5" width="4" height="14" rx="1.2" />
    <rect x="14" y="5" width="4" height="14" rx="1.2" />
  </svg>
);
export const CloudOffIcon = () => (
  <Icon size={18} stroke="#f87171"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z" /><path d="m2 2 20 20" /></Icon>
);
export const LaptopIcon = () => (
  <Icon size={18} stroke="#4ade80"><rect x="2" y="4" width="20" height="12" rx="2" /><path d="M6 20h12M12 16v4" /></Icon>
);
