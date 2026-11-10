import * as THREE from 'three'

// ---------------------------------------------------------------- textures procédurales (canvas)

function canvasTexture(w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void, srgb = false) {
  const c = document.createElement('canvas')
  c.width = w
  c.height = h
  const ctx = c.getContext('2d')!
  draw(ctx)
  const t = new THREE.CanvasTexture(c)
  t.wrapS = t.wrapT = THREE.RepeatWrapping
  t.anisotropy = 8
  if (srgb) t.colorSpace = THREE.SRGBColorSpace
  return t
}

/** Normal map de stries parallèles (1 période par tuile, stries le long de U). */
function ridgeNormalMap(sharp = 1.0) {
  const N = 64
  return canvasTexture(4, N, (ctx) => {
    const img = ctx.createImageData(4, N)
    for (let y = 0; y < N; y++) {
      // profil de couche FDM : arrondi, dérivée d'un |sin|
      const t = (y / N) * Math.PI * 2
      const d = Math.cos(t) * sharp // pente
      const nx = 0
      const ny = -d
      const nz = 1
      const l = Math.hypot(nx, ny, nz)
      for (let x = 0; x < 4; x++) {
        const i = (y * 4 + x) * 4
        img.data[i] = ((nx / l) * 0.5 + 0.5) * 255
        img.data[i + 1] = ((ny / l) * 0.5 + 0.5) * 255
        img.data[i + 2] = ((nz / l) * 0.5 + 0.5) * 255
        img.data[i + 3] = 255
      }
    }
    ctx.putImageData(img, 0, 0)
  })
}

let _layerNormal: THREE.Texture | null = null
export function layerNormal() {
  return (_layerNormal ??= ridgeNormalMap(0.9))
}

let _knurl: THREE.Texture | null = null
/** Moletage droit : stries le long de V (axe du bouton) => on tourne la texture de 90°. */
export function knurlNormal() {
  if (_knurl) return _knurl
  const N = 32
  _knurl = canvasTexture(N, 4, (ctx) => {
    const img = ctx.createImageData(N, 4)
    for (let x = 0; x < N; x++) {
      const t = x / N
      const d = t < 0.5 ? 1 : -1 // dents triangulaires
      const nx = d * 1.4
      const l = Math.hypot(nx, 0, 1)
      for (let y = 0; y < 4; y++) {
        const i = (y * N + x) * 4
        img.data[i] = ((nx / l) * 0.5 + 0.5) * 255
        img.data[i + 1] = 128
        img.data[i + 2] = ((1 / l) * 0.5 + 0.5) * 255
        img.data[i + 3] = 255
      }
    }
    ctx.putImageData(img, 0, 0)
  })
  _knurl.repeat.set(60, 1)
  return _knurl
}

let _brushedRadial: THREE.Texture | null = null
/** Roughness map à cercles concentriques (face avant du bouton, aluminium tourné). */
export function radialBrushed() {
  if (_brushedRadial) return _brushedRadial
  _brushedRadial = canvasTexture(512, 512, (ctx) => {
    ctx.fillStyle = '#6a6a6a'
    ctx.fillRect(0, 0, 512, 512)
    for (let r = 2; r < 256; r += 1.3) {
      const v = 90 + Math.random() * 70
      ctx.strokeStyle = `rgb(${v},${v},${v})`
      ctx.lineWidth = 0.8
      ctx.beginPath()
      ctx.arc(256, 256, r, 0, Math.PI * 2)
      ctx.stroke()
    }
  })
  _brushedRadial.wrapS = _brushedRadial.wrapT = THREE.ClampToEdgeWrapping
  return _brushedRadial
}

let _brushedLinear: THREE.Texture | null = null
export function linearBrushed() {
  if (_brushedLinear) return _brushedLinear
  _brushedLinear = canvasTexture(256, 256, (ctx) => {
    ctx.fillStyle = '#707070'
    ctx.fillRect(0, 0, 256, 256)
    for (let i = 0; i < 1400; i++) {
      const v = 80 + Math.random() * 90
      ctx.strokeStyle = `rgba(${v},${v},${v},0.5)`
      ctx.lineWidth = Math.random() * 1.2
      const y = Math.random() * 256
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(256, y + (Math.random() - 0.5) * 2)
      ctx.stroke()
    }
  })
  return _brushedLinear
}

/** Étiquette imprimée (texte blanc sur fond transparent). */
export function textTexture(lines: string[], w = 512, h = 128, color = '#e8e8e2', font = 'bold 44px Helvetica, Arial, sans-serif') {
  return canvasTexture(
    w,
    h,
    (ctx) => {
      ctx.clearRect(0, 0, w, h)
      ctx.fillStyle = color
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.font = font
      const lh = h / (lines.length + 0.4)
      lines.forEach((l, i) => ctx.fillText(l, w / 2, lh * (i + 0.7)))
    },
    true,
  )
}

// ---------------------------------------------------------------- matériaux partagés

export const M = {
  nickel: new THREE.MeshPhysicalMaterial({ color: '#c9cbcc', metalness: 1, roughness: 0.28 }),
  chrome: new THREE.MeshPhysicalMaterial({ color: '#e6e8ea', metalness: 1, roughness: 0.08 }),
  steel: new THREE.MeshPhysicalMaterial({ color: '#b4b6b8', metalness: 1, roughness: 0.35 }),
  darkSteel: new THREE.MeshPhysicalMaterial({ color: '#3a3c3f', metalness: 0.9, roughness: 0.4 }),
  brass: new THREE.MeshPhysicalMaterial({ color: '#c9a45a', metalness: 1, roughness: 0.3 }),
  blackPlastic: new THREE.MeshPhysicalMaterial({ color: '#141516', metalness: 0, roughness: 0.55, clearcoat: 0.15 }),
  blackMatte: new THREE.MeshStandardMaterial({ color: '#0d0d0e', metalness: 0, roughness: 0.75 }),
  cavity: new THREE.MeshStandardMaterial({ color: '#050505', metalness: 0, roughness: 1, side: THREE.DoubleSide }),
  rubber: new THREE.MeshStandardMaterial({ color: '#111', metalness: 0, roughness: 0.92 }),
  whiteInsul: new THREE.MeshPhysicalMaterial({ color: '#e9e7e0', roughness: 0.45, clearcoat: 0.2 }),
  redInsul: new THREE.MeshPhysicalMaterial({ color: '#b3161b', roughness: 0.45, clearcoat: 0.2 }),
  potCan: new THREE.MeshPhysicalMaterial({ color: '#d5d7d8', metalness: 1, roughness: 0.32 }),
  potDeck: new THREE.MeshStandardMaterial({ color: '#2a2018', roughness: 0.7 }),
}

/** Aluminium anodisé brossé du bouton (couleur réglable). */
export function knobMaterials(color: string) {
  const side = new THREE.MeshPhysicalMaterial({
    color,
    metalness: 1,
    roughness: 0.34,
    normalMap: knurlNormal(),
    normalScale: new THREE.Vector2(0.55, 0.55),
  })
  const face = new THREE.MeshPhysicalMaterial({
    color,
    metalness: 1,
    roughness: 0.3,
    roughnessMap: radialBrushed(),
  })
  return { side, face }
}

/** PETG imprimé : légèrement satiné, lignes de couches en normal map. */
export function petgMaterial(color: string, panel = false) {
  const n = layerNormal().clone()
  n.needsUpdate = true
  if (panel) {
    n.rotation = Math.PI / 4
  }
  return new THREE.MeshPhysicalMaterial({
    color,
    metalness: 0,
    roughness: 0.62,
    sheen: 0.25,
    sheenRoughness: 0.6,
    sheenColor: new THREE.Color('#ffffff'),
    normalMap: n,
    normalScale: panel ? new THREE.Vector2(0.1, 0.1) : new THREE.Vector2(0.18, 0.18),
  })
}

/**
 * UV « boîte » en mm / pas : chaque face reçoit une projection planaire selon sa normale.
 * Les GLB du boîtier sont en Y-up (glTF) — l'axe vertical du boîtier est donc Y ici.
 */
export function boxUV(geom: THREE.BufferGeometry, pitchMm: number, scaleToMm: number) {
  const pos = geom.attributes.position as THREE.BufferAttribute
  const nor = geom.attributes.normal as THREE.BufferAttribute
  if (!pos || !nor) return
  const uv = new Float32Array(pos.count * 2)
  const k = scaleToMm / pitchMm
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) * k
    const y = pos.getY(i) * k // vertical (Z boîtier)
    const z = pos.getZ(i) * k
    const ax = Math.abs(nor.getX(i))
    const ay = Math.abs(nor.getY(i))
    const az = Math.abs(nor.getZ(i))
    if (ay >= ax && ay >= az) {
      uv[i * 2] = x
      uv[i * 2 + 1] = z
    } else if (ax >= az) {
      uv[i * 2] = z
      uv[i * 2 + 1] = y
    } else {
      uv[i * 2] = x
      uv[i * 2 + 1] = y
    }
  }
  geom.setAttribute('uv', new THREE.BufferAttribute(uv, 2))
}

export const ENCLOSURE_PRESETS: Record<string, string> = {
  Anthracite: '#2b2d31',
  Blanc: '#e4e2dc',
  Sable: '#c9b48f',
  Olive: '#5d6248',
}
