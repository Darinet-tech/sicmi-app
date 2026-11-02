import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { dinero } from '../recursos/estados'
import { MESES } from './estados'
import { Anillo, GraficoBarras, GraficoLineas } from './Graficos'

const VERDE = '#04B818'
const AZUL = '#031999'
const AMBAR = '#f59e0b'
const GRIS = '#8a93a3'
const ROJO = '#c62828'

const colorPct = (v) => (v === null || v === undefined ? GRIS : v >= 90 ? VERDE : v >= 60 ? AMBAR : ROJO)

function Indicador({ titulo, valor, color, lineas }) {
  return (
    <div className="indicador">
      <Anillo valor={valor} color={color} />
      <div>
        <h4>{titulo}</h4>
        {lineas.map((l) => <p key={l}>{l}</p>)}
      </div>
    </div>
  )
}

export default function Resumen() {
  const { usuario } = useAuth()
  const hoy = new Date()
  const esCentral = usuario.rol === 'CENTRAL'

  const [periodo, setPeriodo] = useState('mes')
  const [anio, setAnio] = useState(hoy.getFullYear())
  const [mes, setMes] = useState(hoy.getMonth() + 1)
  const [uo, setUo] = useState('')
  const [uos, setUos] = useState([])
  const [datos, setDatos] = useState(null)
  const [ind, setInd] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (esCentral) api.get('reportes/unidades/').then((r) => setUos(r.data)).catch(() => {})
  }, [esCentral])

  useEffect(() => {
    api
      .get('reportes/series/', { params: { periodo, anio, uo } })
      .then((r) => { setDatos(r.data); setError('') })
      .catch((e) => setError(textoError(e)))
  }, [periodo, anio, uo])

  useEffect(() => {
    api
      .get('reportes/indicadores/', { params: { anio, mes, uo } })
      .then((r) => setInd(r.data))
      .catch((e) => setError(textoError(e)))
  }, [anio, mes, uo])

  const S = datos?.series
  const titulos = {
    semana: 'Últimas 8 semanas (semana que comienza el...)',
    mes: `Meses de ${anio}`,
    anio: 'Últimos 5 años',
  }

  const conteo = S && [
    { nombre: 'Solicitudes recibidas', valores: S.solicitudes, color: AZUL },
    { nombre: 'Correctivas cerradas', valores: S.correctivas, color: VERDE },
    { nombre: 'Preventivas cerradas', valores: S.preventivas, color: AMBAR },
    ...(datos.tiene_plan ? [{ nombre: 'Preventivas planificadas', valores: S.plan, color: GRIS }] : []),
  ]

  return (
    <>
      <div className="tarjeta">
        <div className="controles">
          <div className="segmentos">
            {[['semana', 'Semanal'], ['mes', 'Mensual'], ['anio', 'Anual']].map(([v, t]) => (
              <button key={v} className={periodo === v ? 'activo' : ''} onClick={() => setPeriodo(v)}>{t}</button>
            ))}
          </div>
          <div>
            <label style={{ marginTop: 0 }}>Año</label>
            <input type="number" min="2000" max="2100" value={anio} style={{ width: 100 }}
              onChange={(e) => setAnio(Number(e.target.value) || hoy.getFullYear())} />
          </div>
          <div>
            <label style={{ marginTop: 0 }}>Mes de los indicadores</label>
            <select value={mes} onChange={(e) => setMes(Number(e.target.value))}>
              {MESES.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
            </select>
          </div>
          {esCentral && (
            <div>
              <label style={{ marginTop: 0 }}>Unidad Organizativa</label>
              <select value={uo} onChange={(e) => setUo(e.target.value)}>
                <option value="">Todas</option>
                {uos.map((u) => <option key={u.id} value={u.id}>{u.acronimo}</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <h3 className="seccion-titulo">Indicadores de medición · {MESES[mes - 1]} {anio}</h3>
      {ind && (
        <div className="indicadores">
          <Indicador
            titulo="Cumplimiento del plan en físico (preventivo)"
            valor={ind.plan_fisico.mes.pct}
            color={colorPct(ind.plan_fisico.mes.pct)}
            lineas={[
              `Mes: ${ind.plan_fisico.mes.a} ejecutadas de ${ind.plan_fisico.mes.b} planificadas`,
              `Acumulado del año: ${ind.plan_fisico.anio.a} de ${ind.plan_fisico.anio.b} (${ind.plan_fisico.anio.pct ?? '—'}${ind.plan_fisico.anio.pct === null ? '' : ' %'})`,
            ]}
          />
          <Indicador
            titulo="Satisfacción de los servicios (correctivo)"
            valor={ind.satisfaccion.mes.pct}
            color={colorPct(ind.satisfaccion.mes.pct)}
            lineas={[
              `Mes: ${ind.satisfaccion.mes.a} resueltas de ${ind.satisfaccion.mes.b} solicitudes recibidas`,
              `Acumulado del año: ${ind.satisfaccion.anio.a} de ${ind.satisfaccion.anio.b} (${ind.satisfaccion.anio.pct ?? '—'}${ind.satisfaccion.anio.pct === null ? '' : ' %'})`,
            ]}
          />
          <Indicador
            titulo="Cumplimiento del plan de gastos"
            valor={ind.gastos.pct}
            color={AZUL}
            lineas={[
              `Gastado en el año: ${dinero(ind.gastos.gastado)} de ${dinero(ind.gastos.presupuesto)} CUP`,
              `Gastado en el mes: ${dinero(ind.gastos.gastado_mes)} CUP`,
            ]}
          />
        </div>
      )}

      {S && (
        <>
          <h3 className="seccion-titulo">{titulos[periodo]}</h3>
          <div className="tarjeta">
            <h3>Solicitudes y órdenes cerradas</h3>
            <GraficoBarras etiquetas={datos.etiquetas} series={conteo} />
          </div>
          <div className="tarjeta">
            <h3>Gasto en materiales, neto de devoluciones (CUP)</h3>
            <GraficoBarras etiquetas={datos.etiquetas} series={[{ nombre: 'Gasto (CUP)', valores: S.gasto, color: AZUL }]} />
          </div>
          <div className="tarjeta">
            <h3>Asistencia del personal y disponibilidad del transporte</h3>
            <p style={{ marginTop: 0, color: 'var(--gris)', fontSize: '0.85rem' }}>
              Porcentaje de días registrados en el pase de lista y en el parte de transporte como «Trabajando» y «Disponible».
            </p>
            <GraficoLineas
              etiquetas={datos.etiquetas}
              series={[
                { nombre: 'Personal trabajando', valores: S.asistencia, color: VERDE },
                { nombre: 'Vehículos disponibles', valores: S.disponibilidad, color: AZUL },
              ]}
            />
          </div>
        </>
      )}
    </>
  )
}