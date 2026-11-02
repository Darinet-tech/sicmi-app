export default function LogoSiCMI({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="SiCMI">
      <defs>
        <linearGradient id="sicmi-fondo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#031999" />
          <stop offset="1" stopColor="#2b4de0" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="url(#sicmi-fondo)" />
      {/* Edificio con tejado */}
      <path d="M10 30 L32 12 L54 30 H50 V52 H14 V30 Z" fill="#fff" />
      <rect x="20" y="33" width="7" height="6" rx="1" fill="#031999" />
      <rect x="36" y="33" width="7" height="6" rx="1" fill="#031999" />
      <rect x="21" y="42" width="9" height="10" rx="1" fill="#031999" />
      {/* Insignia de control */}
      <circle cx="49" cy="49" r="10" fill="#04B818" stroke="#fff" strokeWidth="3" />
      <path
        d="M44 49 l4 4 l7 -8"
        stroke="#fff"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}