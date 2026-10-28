import { Link } from 'react-router-dom'

// Encabezado común a todas las pantallas de un módulo
export default function PaginaModulo({ icono: Icono, titulo, descripcion, acciones, children }) {
  return (
    <>
      <div className="migas">
        <Link to="/">Inicio</Link> / {titulo}
      </div>
      <div className="pagina-cab">
        {Icono && (
          <div className="modulo-icono">
            <Icono size={26} />
          </div>
        )}
        <div>
          <h2>{titulo}</h2>
          {descripcion && <p>{descripcion}</p>}
        </div>
        {acciones && <div className="acciones">{acciones}</div>}
      </div>
      {children}
    </>
  )
}