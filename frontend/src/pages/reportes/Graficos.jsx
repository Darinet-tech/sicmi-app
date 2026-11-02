const num = (v, dec = 0) => Number(v).toLocaleString('es', { maximumFractionDigits: dec })

// Techo "redondo" del eje: 4 divisiones con pasos 1, 2, 5, 10...
function escala(max, entero) {
  if (!(max > 0)) return 4
  const crudo = max / 4
  const exp = Math.pow(10, Math.floor(Math.log10(crudo)))
  const f = crudo / exp
  const pasos = entero ? [1, 2, 5, 10] : [1, 2, 2.5, 5, 10]
  let paso = (pasos.find((p) => f <= p) ?? 10) * exp
  if (entero) paso = Math.max(1, Math.ceil(paso))
  return paso * 4
}

export function Leyenda({ series }) {
  return (
    <div className="leyenda">
      {series.map((s) => (
        <span key={s.nombre}><i style={{ background: s.color }} />{s.nombre}</span>
      ))}
    </div>
  )
}

export function GraficoBarras({ etiquetas, series, altura = 250, decimales = 0 }) {
  const W = 640
  const m = { t: 16, r: 12, b: 30, l: 56 }
  const w = W - m.l - m.r
  const h = altura - m.t - m.b
  const valores = series.flatMap((s) => s.valores).filter((v) => v !== null && v !== undefined)
  const alto = escala(Math.max(0, ...valores), decimales === 0)
  const y = (v) => m.t + h - (v / alto) * h
  const gw = w / etiquetas.length
  const bw = (gw * 0.78) / series.length
  const conValor = etiquetas.length * series.length <= 24

  return (
    <div className="grafico">
      <svg viewBox={`0 0 ${W} ${altura}`} role="img" aria-label="Gráfico de barras">
        {[0, 1, 2, 3, 4].map((i) => {
          const v = (alto * i) / 4
          return (
            <g key={i}>
              <line x1={m.l} x2={W - m.r} y1={y(v)} y2={y(v)} stroke="#e3e6ec" />
              <text x={m.l - 6} y={y(v) + 3} textAnchor="end" fontSize="10" fill="#5b6475">{num(v, decimales)}</text>
            </g>
          )
        })}
        {etiquetas.map((e, i) => (
          <text key={i} x={m.l + gw * i + gw / 2} y={altura - 10} textAnchor="middle" fontSize="10.5" fill="#5b6475">{e}</text>
        ))}
        {series.map((s, si) =>
          s.valores.map((v, i) => {
            if (v === null || v === undefined) return null
            const x = m.l + gw * i + (gw - bw * series.length) / 2 + bw * si
            return (
              <g key={`${si}-${i}`}>
                <rect x={x} y={y(v)} width={bw} height={Math.max(0, m.t + h - y(v))} rx="2" fill={s.color}>
                  <title>{`${s.nombre} · ${etiquetas[i]}: ${num(v, decimales)}`}</title>
                </rect>
                {conValor && v > 0 && (
                  <text x={x + bw / 2} y={y(v) - 4} textAnchor="middle" fontSize="9" fill="#1c2330">{num(v, decimales)}</text>
                )}
              </g>
            )
          })
        )}
      </svg>
      <Leyenda series={series} />
    </div>
  )
}

// Líneas para porcentajes (eje fijo de 0 a 100)
export function GraficoLineas({ etiquetas, series, altura = 230 }) {
  const W = 640
  const m = { t: 16, r: 12, b: 30, l: 44 }
  const w = W - m.l - m.r
  const h = altura - m.t - m.b
  const gw = w / etiquetas.length
  const x = (i) => m.l + gw * i + gw / 2
  const y = (v) => m.t + h - (v / 100) * h

  return (
    <div className="grafico">
      <svg viewBox={`0 0 ${W} ${altura}`} role="img" aria-label="Gráfico de líneas">
        {[0, 25, 50, 75, 100].map((v) => (
          <g key={v}>
            <line x1={m.l} x2={W - m.r} y1={y(v)} y2={y(v)} stroke="#e3e6ec" />
            <text x={m.l - 6} y={y(v) + 3} textAnchor="end" fontSize="10" fill="#5b6475">{v}%</text>
          </g>
        ))}
        {etiquetas.map((e, i) => (
          <text key={i} x={x(i)} y={altura - 10} textAnchor="middle" fontSize="10.5" fill="#5b6475">{e}</text>
        ))}
        {series.map((s) => {
          let d = ''
          let abierto = false
          s.valores.forEach((v, i) => {
            if (v === null || v === undefined) { abierto = false; return }
            d += `${abierto ? 'L' : 'M'}${x(i)},${y(v)} `
            abierto = true
          })
          return (
            <g key={s.nombre}>
              <path d={d} fill="none" stroke={s.color} strokeWidth="2.5" strokeLinejoin="round" />
              {s.valores.map((v, i) =>
                v === null || v === undefined ? null : (
                  <circle key={i} cx={x(i)} cy={y(v)} r="3.5" fill={s.color}>
                    <title>{`${s.nombre} · ${etiquetas[i]}: ${num(v, 1)} %`}</title>
                  </circle>
                )
              )}
            </g>
          )
        })}
      </svg>
      <Leyenda series={series} />
    </div>
  )
}

export function Anillo({ valor, color = '#04B818' }) {
  const r = 42
  const c = 2 * Math.PI * r
  const vacio = valor === null || valor === undefined
  const p = vacio ? 0 : Math.max(0, Math.min(100, valor))
  return (
    <svg viewBox="0 0 100 100" width="104" height="104" role="img" aria-label="Indicador">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#e3e6ec" strokeWidth="10" />
      <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={`${(p / 100) * c} ${c}`} transform="rotate(-90 50 50)" />
      <text x="50" y="56" textAnchor="middle" fontSize="20" fontWeight="700" fill="#1c2330">
        {vacio ? '—' : `${valor}%`}
      </text>
    </svg>
  )
}