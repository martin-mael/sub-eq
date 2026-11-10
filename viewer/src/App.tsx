import { Suspense, useRef, useState } from 'react'
import * as THREE from 'three'
import { Canvas } from '@react-three/fiber'
import { Loader } from '@react-three/drei'
import { Leva, button, folder, useControls } from 'leva'
import { Scene, type SceneSettings, type ViewName } from './scene/Scene'
import { ENCLOSURE_PRESETS } from './scene/materials'
import { H_TOTAL, POT_LABELS, SIZE, X0, X1, Y0, Y1 } from './scene/dims'

const mm = (v: number) => (Math.round(v * 10) / 10).toLocaleString('fr-FR')
const K = SIZE / 176.3 // same initial framing as audio-box, scaled

const VIEW_BUTTONS: [ViewName, string][] = [
  ['front34', 'Avant ¾'],
  ['back34', 'Arrière ¾'],
  ['top', 'Dessus'],
  ['closeFront', 'Gros plan avant'],
]

export default function App() {
  const glRef = useRef<THREE.WebGLRenderer | null>(null)
  const [view, setView] = useState<{ name: ViewName; n: number }>({ name: 'front34', n: 0 })

  const saveScreenshot = () => {
    const gl = glRef.current
    if (!gl) return
    const a = document.createElement('a')
    a.href = gl.domElement.toDataURL('image/png')
    a.download = `sub-eq-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.png`
    a.click()
  }

  const [c, set] = useControls(() => ({
    'Vue éclatée': folder({
      explode: { label: 'Éclaté', value: 0, min: 0, max: 1, step: 0.01 },
    }),
    Affichage: folder({
      showLid: { label: 'Couvercle', value: true },
      showPanels: { label: 'Panneaux', value: true },
      showPcb: { label: 'PCB', value: true },
      xray: { label: 'Rayons X', value: false },
      labels: { label: 'Étiquettes', value: false },
    }),
    Fonctionnement: folder({
      power: { label: 'Sous tension', value: true },
      b0: { label: `${POT_LABELS[0]} Hz (dB)`, value: 6, min: -12, max: 12, step: 0.5 },
      b1: { label: `${POT_LABELS[1]} Hz (dB)`, value: 3, min: -12, max: 12, step: 0.5 },
      b2: { label: `${POT_LABELS[2]} Hz (dB)`, value: 0, min: -12, max: 12, step: 0.5 },
      b3: { label: `${POT_LABELS[3]} Hz (dB)`, value: -3, min: -12, max: 12, step: 0.5 },
      b4: { label: `${POT_LABELS[4]} Hz (dB)`, value: -6, min: -12, max: 12, step: 0.5 },
    }),
    Couleurs: folder({
      preset: {
        label: 'Filament',
        value: 'Anthracite',
        options: Object.keys(ENCLOSURE_PRESETS),
        onChange: (v: string, _path, ctx) => {
          if (!ctx.initial) set({ color: ENCLOSURE_PRESETS[v] })
        },
        transient: false,
      },
      color: { label: 'Couleur boîtier', value: ENCLOSURE_PRESETS.Anthracite },
      knobColor: { label: 'Boutons', value: '#18191b' },
    }),
    'Capture PNG': button(() => saveScreenshot()),
  }))

  // aide au debug / captures automatisées (dev uniquement)
  if (import.meta.env.DEV) {
    ;(window as unknown as Record<string, unknown>).__viewer = {
      set,
      view: (name: ViewName) => setView((v) => ({ name, n: v.n + 1 })),
      shot: async (name: string) => {
        const blob = await new Promise<Blob | null>((r) => glRef.current!.domElement.toBlob(r, 'image/png'))
        await fetch('/__screenshot?name=' + encodeURIComponent(name), { method: 'POST', body: blob })
        return blob?.size
      },
    }
  }

  const s: SceneSettings = {
    explode: c.explode,
    showLid: c.showLid,
    showPanels: c.showPanels,
    showPcb: c.showPcb,
    xray: c.xray,
    power: c.power,
    bands: [c.b0, c.b1, c.b2, c.b3, c.b4],
    color: c.color,
    knobColor: c.knobColor,
    labels: c.labels,
    view,
  }

  return (
    <>
      <Canvas
        shadows={{ type: THREE.PCFShadowMap }}
        dpr={[1, 2]}
        camera={{ position: [165 * K, 135 * K, 235 * K], fov: 35, near: 2, far: 4000 }}
        gl={{ preserveDrawingBuffer: true, antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.0 }}
        onCreated={({ gl }) => {
          glRef.current = gl
        }}
      >
        <Suspense fallback={null}>
          <Scene s={s} />
        </Suspense>
      </Canvas>
      <Loader dataInterpolation={(p) => `Chargement des modèles… ${p.toFixed(0)} %`} />
      <div className="title">
        <h1>Sub EQ</h1>
        <p>
          Égaliseur graphique 5 bandes pour caisson de basses — boîtier PETG {mm(X1 - X0)} × {mm(Y1 - Y0)} × {mm(H_TOTAL)} mm
        </p>
      </div>
      <div className="hint">Glisser : orbite · Molette : zoom · Clic droit : panoramique · Survol : connecteurs</div>
      <div className="views">
        {VIEW_BUTTONS.map(([k, label]) => (
          <button key={k} className={view.name === k ? 'active' : ''} onClick={() => setView((v) => ({ name: k, n: v.n + 1 }))}>
            {label}
          </button>
        ))}
        <div className="sep" />
        <button
          onClick={() => {
            set({ explode: c.explode > 0.5 ? 0 : 1 })
            setView((v) => ({ name: v.name, n: v.n + 1 }))
          }}
        >{c.explode > 0.5 ? 'Assembler' : 'Éclater'}</button>
        <button onClick={saveScreenshot}>Capture PNG</button>
      </div>
      <Leva titleBar={{ title: 'Réglages' }} theme={{ sizes: { rootWidth: '290px', controlWidth: '130px' } }} />
    </>
  )
}
