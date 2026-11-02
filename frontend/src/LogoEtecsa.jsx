import logo from './assets/LogoETECSAOK.png'

// Dibuja la silueta del logo con el color que se indique
export default function LogoEtecsa({ size = 44, color = '#fff' }) {
  return (
    <span
      role="img"
      aria-label="ETECSA"
      style={{
        display: 'inline-block',
        width: size,
        height: size,
        flexShrink: 0,
        backgroundColor: color,
        WebkitMaskImage: `url(${logo})`,
        maskImage: `url(${logo})`,
        WebkitMaskSize: 'contain',
        maskSize: 'contain',
        WebkitMaskRepeat: 'no-repeat',
        maskRepeat: 'no-repeat',
        WebkitMaskPosition: 'center',
        maskPosition: 'center',
      }}
    />
  )
}