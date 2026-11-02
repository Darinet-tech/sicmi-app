import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="tarjeta">
          <h3 style={{ color: '#c62828' }}>Ocurrió un error al dibujar esta pantalla</h3>
          <p>Copie el texto de abajo y envíemelo:</p>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#fdecea', padding: '1rem', borderRadius: 8, fontSize: 12 }}>
            {String(this.state.error?.stack || this.state.error)}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}