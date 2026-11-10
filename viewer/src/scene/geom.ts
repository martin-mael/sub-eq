import * as THREE from 'three'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'

/**
 * Solide de révolution autour de l'axe Y local.
 * `profile` = points (r, y) parcourus dans le sens trigonométrique (matière à gauche) :
 * chaque segment devient une bande indépendante => arêtes vives, normales exactes.
 */
export function revolve(profile: [number, number][], segments = 64, closed = true): THREE.BufferGeometry {
  const pts = closed ? [...profile, profile[0]] : profile
  const parts: THREE.BufferGeometry[] = []
  for (let i = 0; i < pts.length - 1; i++) {
    const [r0, y0] = pts[i]
    const [r1, y1] = pts[i + 1]
    if (Math.abs(r0 - r1) < 1e-9 && Math.abs(y0 - y1) < 1e-9) continue
    if (r0 < 1e-6 && r1 < 1e-6) continue // segment sur l'axe
    const g = new THREE.LatheGeometry([new THREE.Vector2(r0, y0), new THREE.Vector2(r1, y1)], segments)
    parts.push(g)
  }
  const merged = mergeGeometries(parts, false)!
  parts.forEach((p) => p.dispose())
  return merged
}

/** Cylindre (plein) d'axe Y entre y0 et y1. */
export function yCyl(r: number, y0: number, y1: number, seg = 48) {
  const g = new THREE.CylinderGeometry(r, r, Math.abs(y1 - y0), seg)
  g.translate(0, (y0 + y1) / 2, 0)
  return g
}

/** Tube d'axe Y. */
export function yTube(ri: number, ro: number, y0: number, y1: number, seg = 64) {
  return revolve(
    [
      [ri, y0],
      [ro, y0],
      [ro, y1],
      [ri, y1],
    ],
    seg,
  )
}

/** Disque d'axe Y orienté vers +Y (ou −Y). */
export function yDisc(r: number, y: number, facing: 1 | -1 = 1, seg = 48) {
  const g = new THREE.CircleGeometry(r, seg)
  g.rotateX(facing === 1 ? -Math.PI / 2 : Math.PI / 2)
  g.translate(0, y, 0)
  return g
}

/** Boîte définie par ses bornes. */
export function boxBounds(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number) {
  const g = new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0)
  g.translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
  return g
}

export type Hole = { x: number; z: number; r: number }

/**
 * Bloc rectangulaire (X × Z) percé de trous ronds le long de Y.
 * Face avant à y = yFront, profondeur vers −Y. Bords légèrement chanfreinés.
 */
export function holedBlock(x0: number, x1: number, z0: number, z1: number, yFront: number, depth: number, holes: Hole[], bevel = 0.25) {
  const s = new THREE.Shape()
  const b = bevel
  s.moveTo(x0 + b, z0 + b)
  s.lineTo(x1 - b, z0 + b)
  s.lineTo(x1 - b, z1 - b)
  s.lineTo(x0 + b, z1 - b)
  s.lineTo(x0 + b, z0 + b)
  for (const h of holes) {
    const p = new THREE.Path()
    p.absarc(h.x, h.z, h.r + b, 0, Math.PI * 2, true)
    s.holes.push(p)
  }
  const g = new THREE.ExtrudeGeometry(s, {
    depth: depth - 2 * b,
    bevelEnabled: b > 0,
    bevelThickness: b,
    bevelSize: b,
    bevelSegments: 1,
    curveSegments: 40,
  })
  // extrusion le long de +Z local -> vers −Y ; forme (x, y) -> (X, Z)
  g.rotateX(Math.PI / 2)
  g.translate(0, yFront - b, 0)
  g.computeVertexNormals()
  return g
}

/** Hexagone (écrou) d'axe Y. */
export function hexNut(af: number, y0: number, y1: number, bore: number) {
  const rc = af / Math.sqrt(3)
  const s = new THREE.Shape()
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 + Math.PI / 6
    const x = Math.cos(a) * rc
    const z = Math.sin(a) * rc
    if (i === 0) s.moveTo(x, z)
    else s.lineTo(x, z)
  }
  const p = new THREE.Path()
  p.absarc(0, 0, bore, 0, Math.PI * 2, true)
  s.holes.push(p)
  const t = y1 - y0
  const bv = 0.25
  const g = new THREE.ExtrudeGeometry(s, { depth: t - 2 * bv, bevelEnabled: true, bevelThickness: bv, bevelSize: -0.0, bevelSegments: 1, curveSegments: 32 })
  g.rotateX(-Math.PI / 2)
  g.translate(0, y0 + bv, 0)
  return g
}
