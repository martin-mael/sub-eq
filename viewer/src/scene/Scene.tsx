import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import * as THREE from 'three'
import { useFrame, useThree, type ThreeEvent } from '@react-three/fiber'
import { ContactShadows, Environment, Html, Lightformer, OrbitControls } from '@react-three/drei'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { BACK, CENTER, FEET, FOOT_H, FRONT, HOLES, POT_LABELS, SIZE, Y_BACK_OUT, Y_FRONT_OUT, Z_PCB_TOP, axisZ } from './dims'
import { EnclosurePart } from './EnclosurePart'
import { Pcb, ledMat } from './Pcb'
import { ConnectorFrame, CountersunkScrew, DcDcModule, DcJack, HeatInsert, JackNut, Knob, PhoneJack, PotNut, Potentiometer, RubberFoot } from './Connectors'

export type ViewName = 'front34' | 'back34' | 'top' | 'closeFront'

export type SceneSettings = {
  explode: number
  showLid: boolean
  showPanels: boolean
  showPcb: boolean
  xray: boolean
  power: boolean
  bands: number[] // dB, −12..+12, one per pot (31 / 40 / 50 / 63 / 80 Hz)
  color: string
  knobColor: string
  labels: boolean
  view: { name: ViewName; n: number }
}

// ------------------------------------------------------------------ étiquettes
type LabelDef = { key: string; text: string; info: string; side: 'back' | 'front'; x: number; z: number; w: number; h: number }
const LABELS: LabelDef[] = [
  { key: 'in', text: 'IN', info: 'Entrée jack 6,35 mono (TS), niveau ligne +4 dBu', side: 'back', x: BACK.in.x, z: axisZ(BACK.in.h), w: 14, h: 14 },
  { key: 'out', text: 'OUT', info: 'Sortie jack 6,35 mono (TS) vers le caisson', side: 'back', x: BACK.out.x, z: axisZ(BACK.out.h), w: 14, h: 14 },
  { key: 'dc', text: '12V DC', info: 'Alimentation 12 V continu, 5,5 / 2,1 mm, positif au centre', side: 'back', x: BACK.dc.x, z: axisZ(BACK.dc.h), w: 10, h: 11 },
  ...FRONT.pots.map(
    (p, i): LabelDef => ({
      key: 'pot' + i,
      text: POT_LABELS[i] + ' Hz',
      info: `Bande ${POT_LABELS[i]} Hz, ±12 dB, cran central à 0 dB`,
      side: 'front',
      x: p.x,
      z: axisZ(p.h),
      w: 12,
      h: 12,
    }),
  ),
  { key: 'led', text: 'ON', info: 'Témoin de mise sous tension', side: 'front', x: FRONT.led.x, z: axisZ(FRONT.led.h), w: 6, h: 6 },
]

function ConnectorLabel({
  def,
  offsetY,
  visible,
  detailed,
  onHover,
}: {
  def: LabelDef
  offsetY: number
  visible: boolean
  detailed: boolean
  onHover: (k: string | null) => void
}) {
  const yFace = def.side === 'back' ? Y_BACK_OUT : Y_FRONT_OUT
  const out = def.side === 'back' ? 1 : -1
  const over = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    onHover(def.key)
  }
  return (
    <group position={[def.x, yFace + offsetY, def.z]}>
      {/* zone de survol invisible devant le connecteur */}
      <mesh position={[0, out * 4, 0]} onPointerOver={over} onPointerOut={() => onHover(null)}>
        <boxGeometry args={[def.w, 8, def.h]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
      {visible && (
        <Html position={[0, out * 3, def.h / 2 + 5]} center zIndexRange={[20, 0]} style={{ pointerEvents: 'none' }}>
          <div className={detailed ? 'tag' : 'tag small'}>
            <b>{def.text}</b>
            {detailed && <span>{def.info}</span>}
          </div>
        </Html>
      )}
    </group>
  )
}

// ------------------------------------------------------------------ caméra
// same framing as audio-box, scaled to the size of this enclosure
const K = SIZE / 176.3
const FRONT_Z = -(Y_FRONT_OUT - CENTER.y) // three.js Z of the front face
const VIEWS: Record<ViewName, { pos: [number, number, number]; target: [number, number, number] }> = {
  front34: { pos: [165 * K, 135 * K, 235 * K], target: [0, 10, 0] },
  back34: { pos: [-165 * K, 125 * K, -235 * K], target: [0, 11, 0] },
  top: { pos: [0, 330 * K, 0.1], target: [0, 0, 0] },
  closeFront: { pos: [40, 34, FRONT_Z + 95], target: [6, 12, FRONT_Z] },
}

function CameraRig({ view, explode }: { view: { name: ViewName; n: number }; explode: number }) {
  const camera = useThree((s) => s.camera)
  const controls = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null
  const anim = useRef<{ t: number; p0: THREE.Vector3; t0: THREE.Vector3; p1: THREE.Vector3; t1: THREE.Vector3 } | null>(null)
  useEffect(() => {
    if (!controls) return
    const v = VIEWS[view.name]
    // recul automatique en vue éclatée
    const t1 = new THREE.Vector3(...v.target)
    if (view.name !== 'closeFront') t1.y += explode * 8
    const p1 = new THREE.Vector3(...v.pos).sub(t1).multiplyScalar(1 + 0.5 * explode).add(t1)
    anim.current = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1, t1 }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, controls, camera])
  // dev only: window.__viewerCam([x, y, z], [tx, ty, tz]) places the camera (three.js frame, Y up), for checks
  useEffect(() => {
    if (!import.meta.env.DEV || !controls) return
    ;(window as unknown as Record<string, unknown>).__viewerCam = (p: [number, number, number], t: [number, number, number]) => {
      anim.current = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...p), t1: new THREE.Vector3(...t) }
    }
  }, [controls, camera])
  useFrame((_, dt) => {
    const a = anim.current
    if (!a || !controls) return
    a.t = Math.min(1, a.t + dt / 0.9)
    const k = a.t < 0.5 ? 4 * a.t ** 3 : 1 - (-2 * a.t + 2) ** 3 / 2
    camera.position.lerpVectors(a.p0, a.p1, k)
    controls.target.lerpVectors(a.t0, a.t1, k)
    controls.update()
    if (a.t >= 1) anim.current = null
  })
  return null
}

// ------------------------------------------------------------------ fond dégradé
function useGradientBackground() {
  const scene = useThree((s) => s.scene)
  useEffect(() => {
    const c = document.createElement('canvas')
    c.width = 16
    c.height = 512
    const ctx = c.getContext('2d')!
    const g = ctx.createLinearGradient(0, 0, 0, 512)
    g.addColorStop(0, '#eef0f3')
    g.addColorStop(0.6, '#d3d6db')
    g.addColorStop(1, '#bfc3c9')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, 16, 512)
    const t = new THREE.CanvasTexture(c)
    t.colorSpace = THREE.SRGBColorSpace
    scene.background = t
    return () => {
      scene.background = null
      t.dispose()
    }
  }, [scene])
}

function Studio() {
  useGradientBackground()
  return (
    <>
      <Environment resolution={256} frames={1}>
        {/* dôme gris neutre : les métaux reflètent un studio, pas du noir */}
        <mesh scale={2000}>
          <sphereGeometry args={[1, 32, 16]} />
          <meshBasicMaterial color="#5d6168" side={THREE.BackSide} />
        </mesh>
        <mesh position={[0, -300, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[3000, 3000]} />
          <meshBasicMaterial color="#8d9198" />
        </mesh>
        <Lightformer form="rect" intensity={2.2} color="#ffffff" scale={[600, 400, 1]} position={[0, 500, 0]} rotation={[Math.PI / 2, 0, 0]} />
        <Lightformer form="rect" intensity={3} color="#fff6ec" scale={[120, 500, 1]} position={[-420, 160, 120]} rotation={[0, Math.PI / 2, 0]} />
        <Lightformer form="rect" intensity={2.2} color="#eef4ff" scale={[120, 500, 1]} position={[420, 160, -60]} rotation={[0, -Math.PI / 2, 0]} />
        <Lightformer form="rect" intensity={1.6} color="#ffffff" scale={[500, 80, 1]} position={[0, 120, -450]} />
        <Lightformer form="rect" intensity={1.2} color="#ffffff" scale={[500, 80, 1]} position={[0, 80, 450]} rotation={[0, Math.PI, 0]} />
        <Lightformer form="ring" intensity={4} color="#ffffff" scale={120} position={[250, 300, 250]} target={[0, 0, 0]} />
      </Environment>
      <hemisphereLight args={['#ffffff', '#8a8f96', 0.35]} />
      <directionalLight
        position={[160, 320, 190]}
        intensity={1.7}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0002}
        shadow-radius={8}
        shadow-blurSamples={16}
        shadow-normalBias={0.35}
        shadow-camera-left={-170}
        shadow-camera-right={170}
        shadow-camera-top={170}
        shadow-camera-bottom={-170}
        shadow-camera-near={50}
        shadow-camera-far={900}
      />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[3000, 3000]} />
        <shadowMaterial opacity={0.12} />
      </mesh>
      <ContactShadows position={[0, 0.05, 0]} scale={520} far={90} blur={2.4} opacity={0.6} resolution={1024} color="#1d2026" />
    </>
  )
}

// ------------------------------------------------------------------ assemblage
function Move({ d, children, visible = true }: { d: [number, number, number]; children: ReactNode; visible?: boolean }) {
  return (
    <group position={d} visible={visible}>
      {children}
    </group>
  )
}

const EX = { lid: 40, tray: 24, panel: 30, nut: 42, knob: 58 }

export function Scene({ s }: { s: SceneSettings }) {
  const [hover, setHover] = useState<string | null>(null)
  const [, setTopZ] = useState(9.5)
  const onTop = useCallback((z: number) => setTopZ(z), [])
  // éclaté animé (amorti) vers la valeur demandée
  const [e, setE] = useState(s.explode)
  useFrame((_, dt) => {
    if (Math.abs(e - s.explode) < 1e-3) {
      if (e !== s.explode) setE(s.explode)
      return
    }
    setE(THREE.MathUtils.damp(e, s.explode, 7, dt))
  })
  const lift = FOOT_H + e * EX.tray

  useEffect(() => {
    ledMat.emissiveIntensity = s.power ? 3.2 : 0
    ledMat.color.set(s.power ? '#ff3a30' : '#a01016')
  }, [s.power])

  useEffect(() => {
    document.body.style.cursor = hover ? 'help' : 'auto'
  }, [hover])

  // knob angle: 300° travel, −12 dB => 7 o'clock, 0 dB => 12 o'clock, +12 dB => 5 o'clock (clockwise = boost)
  const knobAngles = useMemo(() => s.bands.map((db) => THREE.MathUtils.degToRad(150 - 300 * ((db + 12) / 24))), [s.bands])

  const xs = { color: s.color, xray: s.xray }
  const panelsVisible = s.showPanels

  return (
    <>
      <Studio />
      <OrbitControls makeDefault enableDamping dampingFactor={0.08} minDistance={25} maxDistance={900} maxPolarAngle={Math.PI * 0.495} />
      <CameraRig view={s.view} explode={s.explode} />

      <group position={[0, lift, 0]}>
        <group rotation={[-Math.PI / 2, 0, 0]}>
          <group position={[-CENTER.x, -CENTER.y, 0]}>
            {/* ---- fond (tray) + pieds + vis */}
            <Move d={[0, 0, -e * EX.tray]}>
              <EnclosurePart name="tray" {...xs} />
              {FEET.map(([x, y], i) => (
                <group key={i} position={[x, y, -FOOT_H]}>
                  <RubberFoot />
                </group>
              ))}
              {HOLES.map(([x, y], i) => (
                <group key={i} position={[x, -y, 0]}>
                  <CountersunkScrew />
                </group>
              ))}
            </Move>

            {/* ---- couvercle + inserts laiton */}
            <Move d={[0, 0, e * EX.lid]} visible={s.showLid}>
              <EnclosurePart name="lid" {...xs} />
              {HOLES.map(([x, y], i) => (
                <group key={i} position={[x, -y, Z_PCB_TOP]}>
                  <HeatInsert />
                </group>
              ))}
            </Move>

            {/* ---- panels (nuts and knobs come off further) */}
            <Move d={[0, e * EX.panel, 0]} visible={panelsVisible}>
              <EnclosurePart name="back_panel" {...xs} />
            </Move>
            <Move d={[0, e * EX.nut, 0]} visible={panelsVisible}>
              {[BACK.in, BACK.out].map((c, i) => (
                <ConnectorFrame key={i} x={c.x} h={c.h} side="back">
                  <JackNut />
                </ConnectorFrame>
              ))}
            </Move>
            <Move d={[0, -e * EX.panel, 0]} visible={panelsVisible}>
              <EnclosurePart name="front_panel" {...xs} />
            </Move>
            <Move d={[0, -e * EX.nut, 0]} visible={panelsVisible}>
              {FRONT.pots.map((c, i) => (
                <ConnectorFrame key={i} x={c.x} h={c.h} side="front">
                  <PotNut />
                </ConnectorFrame>
              ))}
            </Move>

            {/* ---- PCB and everything soldered on it (fixed) */}
            <group visible={s.showPcb}>
              <Pcb boardTop={onTop} />
              <DcDcModule />
              {[BACK.in, BACK.out].map((c, i) => (
                <ConnectorFrame key={i} x={c.x} h={c.h} side="back">
                  <PhoneJack h={c.h} />
                </ConnectorFrame>
              ))}
              <ConnectorFrame x={BACK.dc.x} h={BACK.dc.h} side="back">
                <DcJack h={BACK.dc.h} />
              </ConnectorFrame>
              {FRONT.pots.map((c, i) => (
                <ConnectorFrame key={i} x={c.x} h={c.h} side="front">
                  <Potentiometer h={c.h} />
                </ConnectorFrame>
              ))}
              <pointLight
                position={[FRONT.led.x, Y_FRONT_OUT - 3, axisZ(FRONT.led.h)]}
                color="#ff2a1a"
                intensity={s.power ? 300 : 0}
                distance={100}
                decay={2}
              />
            </group>
            <Move d={[0, -e * EX.knob, 0]} visible={s.showPcb}>
              {FRONT.pots.map((c, i) => (
                <ConnectorFrame key={i} x={c.x} h={c.h} side="front">
                  <Knob angle={knobAngles[i]} color={s.knobColor} />
                </ConnectorFrame>
              ))}
            </Move>

            {/* ---- étiquettes / survol */}
            {LABELS.map((d) => (
              <ConnectorLabel
                key={d.key}
                def={d}
                offsetY={(d.side === 'back' ? 1 : -1) * (panelsVisible ? e * EX.panel : 0)}
                visible={s.labels || hover === d.key}
                detailed={hover === d.key}
                onHover={setHover}
              />
            ))}
          </group>
        </group>
      </group>
    </>
  )
}
