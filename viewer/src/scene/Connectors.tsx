import { useMemo, type ComponentProps, type ReactNode } from 'react'
import * as THREE from 'three'
import { M, knurlNormal, textTexture } from './materials'
import { boxBounds, hexNut, holedBlock, revolve, yCyl, yDisc, yTube } from './geom'
import {
  DCDC_BOX,
  DCDC_H,
  DC_BODY,
  JACK_BODY,
  JACK_NOSE,
  POT_BODY,
  POT_BUSHING,
  POT_LUG_R,
  PANEL_T,
  Y_BACK_IN,
  Y_FRONT_IN,
  Z_PCB_TOP,
} from './dims'

// Parts without a KiCad 3D model (absent from the PCB STEP). Dimensions from enclosure/enclosure.py
// (envelopes(), which check_fit.py validates) and the manufacturer drawings; details are indicative.

/**
 * Connector frame: origin on the axis, in the plane of the panel inner face;
 * local +Y = out of the enclosure; +Z = up. `h` = axis height above the PCB top.
 */
export function ConnectorFrame({ x, h, side, children, ...rest }: { x: number; h: number; side: 'back' | 'front'; children: ReactNode } & JSX_Group) {
  const y = side === 'back' ? Y_BACK_IN : Y_FRONT_IN
  return (
    <group position={[x, y, Z_PCB_TOP + h]} rotation={[0, 0, side === 'back' ? 0 : Math.PI]} {...rest}>
      {children}
    </group>
  )
}
type JSX_Group = Omit<ComponentProps<'group'>, 'children' | 'position' | 'rotation'>

function Part({ geometry, material, shadow = true }: { geometry: THREE.BufferGeometry; material: THREE.Material; shadow?: boolean }) {
  return <mesh geometry={geometry} material={material} castShadow={shadow} receiveShadow />
}

/** Threaded sleeve profile (annular threads) between y0 and y1, for `revolve`. */
function threadProfile(ri: number, rRoot: number, rPeak: number, y0: number, y1: number, pitch: number): [number, number][] {
  const prof: [number, number][] = [
    [ri, y0],
    [rPeak, y0],
  ]
  for (let y = y0 + pitch / 2; y < y1 - pitch / 2; y += pitch) prof.push([rRoot, y], [rPeak, y + pitch / 2])
  prof.push([rPeak - 0.2, y1], [ri, y1])
  return prof
}

// ------------------------------------------------------------------ Jack 6,35 Neutrik NMJ4HCD2 (back panel)
/** `h` = axis height above the PCB (JACK_H). Body behind the panel, chrome threaded nose through it. */
export function PhoneJack({ h }: { h: number }) {
  const g = useMemo(() => {
    const [w, d, ht] = JACK_BODY
    const zb = -h + 0.05
    const rNose = JACK_NOSE.d / 2
    return {
      body: holedBlock(-w / 2, w / 2, zb, zb + ht - 0.05, 0, d, [{ x: 0, z: 0, r: 3.3 }], 0.4),
      nose: revolve(threadProfile(3.3, rNose - 0.3, rNose - 0.05, -0.6, JACK_NOSE.len, 0.5), 72),
      contact: yTube(2.9, 3.31, -12, -8, 32),
      bottom: yDisc(3.35, -16, 1, 32),
    }
  }, [h])
  return (
    <group>
      <Part geometry={g.body} material={M.blackPlastic} />
      <Part geometry={g.nose} material={M.chrome} />
      <Part geometry={g.contact} material={M.steel} shadow={false} />
      <Part geometry={g.bottom} material={M.cavity} shadow={false} />
    </group>
  )
}

/** Hex nut of the jack, 11 mm across flats, on the outer face of the back panel. */
export function JackNut() {
  const g = useMemo(() => hexNut(11.0, PANEL_T, PANEL_T + 2.0, JACK_NOSE.d / 2 - 0.02), [])
  return <Part geometry={g} material={M.nickel} />
}

// ------------------------------------------------------------------ Potentiometer Alps RK09L (front panel)
/** `depth` = body depth behind the bushing shoulder (POT_BODY[1], or POT2_DEPTH for the dual RK09L1220). */
export function Potentiometer({ h, depth = POT_BODY[1] }: { h: number; depth?: number }) {
  const g = useMemo(() => {
    const [w, , top] = POT_BODY
    const zb = -h + 0.05
    const zt = top - h
    const dual = depth > POT_BODY[1] + 0.5
    const bw = w / 2 - 1.2 // can width (the full width includes the side lugs)
    const deck = (y0: number, y1: number) => boxBounds(-bw + 0.15, bw - 0.15, y1, y0, zb + 0.2, zt - 0.4)
    const shaft = (() => {
      // Ø6 shaft with a flat (D), from the bushing end to 15 mm from the shoulder
      const s = new THREE.Shape()
      s.absarc(0, 0, 3, -Math.PI / 2 + 0.5, Math.PI * 1.5 - 0.5, false)
      s.closePath()
      const e = new THREE.ExtrudeGeometry(s, { depth: 15 - POT_BUSHING.len, bevelEnabled: false, curveSegments: 32 })
      e.rotateX(-Math.PI / 2)
      e.translate(0, POT_BUSHING.len, 0)
      return e
    })()
    return {
      frame: boxBounds(-w / 2 + 0.6, w / 2 - 0.6, -0.6, 0, zb, zt),
      lugs: [-1, 1].map((s) => boxBounds(s * (w / 2 - 0.6), s * (w / 2), -3.2, -0.6, zb, zb + 4.5)),
      can: boxBounds(-bw, bw, -depth + 0.8, -0.6, zb + 1.6, zt),
      decks: dual ? [deck(-0.6, -depth / 2 + 0.25), deck(-depth / 2 - 0.25, -depth)] : [deck(-0.6, -depth)],
      shim: dual ? boxBounds(-bw - 0.02, bw + 0.02,-depth / 2 - 0.25, -depth / 2 + 0.25, zb, zt) : null,
      // anti-rotation lug (2 x 0.8 mm) at POT_LUG_R from the axis, in a pocket of the panel inner face
      lug: boxBounds(-POT_LUG_R - 0.4, -POT_LUG_R + 0.4, 0, 0.8, -1.0, 1.0),
      bush: revolve(threadProfile(3.05, POT_BUSHING.d / 2 - 0.3, POT_BUSHING.d / 2, 0, POT_BUSHING.len, 0.75), 48),
      shaft,
    }
  }, [h, depth])
  return (
    <group>
      <Part geometry={g.frame} material={M.potCan} />
      {g.lugs.map((l, i) => (
        <Part key={i} geometry={l} material={M.potCan} />
      ))}
      {g.decks.map((d, i) => (
        <Part key={i} geometry={d} material={M.potDeck} />
      ))}
      {g.shim && <Part geometry={g.shim} material={M.potCan} />}
      <Part geometry={g.can} material={M.potCan} />
      <Part geometry={g.lug} material={M.potCan} shadow={false} />
      <Part geometry={g.bush} material={M.nickel} />
      <Part geometry={g.shaft} material={M.steel} />
    </group>
  )
}

/** Washer + M9 nut on the outer face of the front panel. */
export function PotNut() {
  const g = useMemo(
    () => ({
      washer: yTube(POT_BUSHING.d / 2 + 0.05, 6.0, PANEL_T, PANEL_T + 0.4, 48),
      nut: hexNut(12.0, PANEL_T + 0.4, POT_BUSHING.len, POT_BUSHING.d / 2 + 0.02),
    }),
    [],
  )
  return (
    <group>
      <Part geometry={g.washer} material={M.nickel} />
      <Part geometry={g.nut} material={M.nickel} />
    </group>
  )
}

// ------------------------------------------------------------------ Knob Same Sky SPK-016A (black ABS, Ø11 x 17.2)
export const KNOB = { d: 11.0, h: 17.2, y0: POT_BUSHING.len + 0.3 }

export function Knob({ angle, color }: { angle: number; color: string }) {
  const mats = useMemo(() => {
    const side = new THREE.MeshPhysicalMaterial({
      color,
      metalness: 0,
      roughness: 0.5,
      clearcoat: 0.1,
      normalMap: knurlNormal(),
      normalScale: new THREE.Vector2(0.45, 0.45),
    })
    const face = new THREE.MeshPhysicalMaterial({ color, metalness: 0, roughness: 0.45, clearcoat: 0.15 })
    return { side, face }
  }, [color])
  const g = useMemo(() => {
    const r0 = KNOB.d / 2
    const r1 = r0 - 0.35 // slight taper towards the front
    const y0 = KNOB.y0
    const y1 = y0 + KNOB.h
    const c = 0.7
    return {
      side: new THREE.LatheGeometry([new THREE.Vector2(r0, y0 + 0.3), new THREE.Vector2(r1, y1 - c)], 120),
      back: revolve(
        [
          [3.0, y0],
          [r0 - 0.3, y0],
          [r0, y0 + 0.3],
          [r0, y0 + 0.31],
          [3.0, y0 + 0.31],
        ],
        96,
      ),
      chamfer: revolve(
        [
          [r1, y1 - c],
          [r1 - c, y1],
          [r1 - c - 0.01, y1 - 0.01],
          [r1 - 0.01, y1 - c - 0.01],
        ],
        96,
      ),
      face: yDisc(r1 - c, y1, 1, 96),
      mark: boxBounds(-0.3, 0.3, y1, y1 + 0.03, 1.0, r1 - c - 0.4),
    }
  }, [])
  return (
    <group rotation={[0, angle, 0]}>
      <Part geometry={g.side} material={mats.side} />
      <Part geometry={g.back} material={mats.face} />
      <Part geometry={g.chamfer} material={mats.face} />
      <Part geometry={g.face} material={mats.face} />
      <mesh geometry={g.mark}>
        <meshStandardMaterial color="#f2f2ee" roughness={0.5} />
      </mesh>
    </group>
  )
}

// ------------------------------------------------------------------ DC jack CUI PJ-102AH (back panel)
/** `h` = axis height above the PCB. Front face flush with the panel outer face (local y = PANEL_T). */
export function DcJack({ h }: { h: number }) {
  const g = useMemo(() => {
    const [w, d, ht] = DC_BODY
    const zb = -h + 0.05
    return {
      body: holedBlock(-w / 2, w / 2, zb, zb + ht - 0.05, PANEL_T, d, [{ x: 0, z: 0, r: 3.25 }], 0.3),
      bottom: yDisc(3.3, PANEL_T - 10, 1, 32),
      pin: yCyl(1.0, PANEL_T - 10, PANEL_T - 1.2, 24), // Ø2 centre pin
      spring: yTube(2.6, 3.26, PANEL_T - 9, PANEL_T - 5, 32),
    }
  }, [h])
  return (
    <group>
      <Part geometry={g.body} material={M.blackPlastic} />
      <Part geometry={g.bottom} material={M.cavity} shadow={false} />
      <Part geometry={g.pin} material={M.nickel} shadow={false} />
      <Part geometry={g.spring} material={M.steel} shadow={false} />
    </group>
  )
}

// ------------------------------------------------------------------ DC-DC Traco TMA 1212D (SIP-7)
export function DcDcModule() {
  const tex = useMemo(() => textTexture(['TRACO', 'TMA 1212D', '±12V  1W'], 512, 256, '#e9e9e4', 'bold 54px Helvetica, Arial, sans-serif'), [])
  const [x0, x1, py0, py1] = DCDC_BOX
  const y0 = -py1 // enclosure Y = −PCB y
  const y1 = -py0
  const body = useMemo(() => holedBlock(x0, x1, Z_PCB_TOP + 0.05, Z_PCB_TOP + DCDC_H, y1, y1 - y0, [], 0.3), [x0, x1, y0, y1])
  const alongY = x1 - x0 < y1 - y0
  const len = Math.max(x1 - x0, y1 - y0)
  const zc = Z_PCB_TOP + DCDC_H / 2
  return (
    <group>
      <mesh geometry={body} material={M.blackPlastic} castShadow receiveShadow />
      {/* marking on a large face: +X face when the module runs along Y, front (−Y) face otherwise */}
      <group position={alongY ? [x1 + 0.02, (y0 + y1) / 2, zc] : [(x0 + x1) / 2, y0 - 0.02, zc]} rotation={[0, 0, alongY ? Math.PI / 2 : 0]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <planeGeometry args={[len - 2.5, (len - 2.5) / 2]} />
          <meshStandardMaterial map={tex} transparent roughness={0.6} polygonOffset polygonOffsetFactor={-2} />
        </mesh>
      </group>
    </group>
  )
}

// ------------------------------------------------------------------ fasteners / feet
export function CountersunkScrew() {
  // M3x14 countersunk, from below (Z = 0 -> 14)
  const g = useMemo(
    () =>
      revolve(
        [
          [0, 0],
          [3.0, 0],
          [3.0, 0.1],
          [1.5, 1.7],
          [1.5, 14],
          [1.2, 14.3],
          [0, 14.3],
        ],
        32,
      ),
    [],
  )
  return <mesh geometry={g} material={M.darkSteel} rotation={[Math.PI / 2, 0, 0]} castShadow />
}

export function HeatInsert() {
  const g = useMemo(() => yTube(1.4, 2.0, 0, 5.7, 24), [])
  return <mesh geometry={g} material={M.brass} rotation={[Math.PI / 2, 0, 0]} />
}

export function RubberFoot() {
  const g = useMemo(() => {
    const prof: [number, number][] = [[0, 0]]
    for (let i = 0; i <= 8; i++) {
      const a = (i / 8) * (Math.PI / 2)
      prof.push([4.0 + 1.0 * Math.sin(a), 1.0 - 1.0 * Math.cos(a)])
    }
    prof.push([5.0, 2.0], [0, 2.0])
    return revolve(prof, 40)
  }, [])
  return <mesh geometry={g} material={M.rubber} rotation={[Math.PI / 2, 0, 0]} castShadow receiveShadow />
}
