import { useEffect, useMemo } from 'react'
import * as THREE from 'three'
import { useGLTF, useTexture } from '@react-three/drei'
import { PCB_D, PCB_W, Z_PCB_BOT } from './dims'

const BASE = import.meta.env.BASE_URL + 'models/'

/** Les GLB sont en glTF standard (Y-up, m) : on revient en mm / Z-up (repère boîtier). */
export const GLTF_TO_ENCLOSURE = { rotation: [Math.PI / 2, 0, 0] as [number, number, number], scale: 1000 }

const maskMat = new THREE.MeshPhysicalMaterial({
  color: '#ffffff',
  vertexColors: true,
  roughness: 0.42,
  metalness: 0,
  clearcoat: 0.35,
  clearcoatRoughness: 0.35,
})

export const ledMat = new THREE.MeshPhysicalMaterial({
  color: '#c0141a',
  roughness: 0.35,
  transmission: 0.25,
  thickness: 1,
  emissive: new THREE.Color('#ff1a14'),
  emissiveIntensity: 0,
})

function isNode(o: THREE.Object3D, name: string) {
  let p: THREE.Object3D | null = o
  while (p) {
    if (p.name === name) return true
    p = p.parent
  }
  return false
}

export function Pcb({ boardTop }: { boardTop: (z: number) => void }) {
  const { scene } = useGLTF(BASE + 'pcb.glb')
  const [color, rm] = useTexture([BASE + 'pcb_top_color.png', BASE + 'pcb_top_rm.png'])

  const { root, topZ } = useMemo(() => {
    const root = scene.clone(true)
    root.updateMatrixWorld(true)
    let topZ = Z_PCB_BOT + 1.6
    const box = new THREE.Box3()
    const size = new THREE.Vector3()
    root.traverse((o) => {
      const m = o as THREE.Mesh
      if (!m.isMesh) return
      m.castShadow = true
      m.receiveShadow = true
      box.setFromObject(m)
      box.getSize(size)
      // carte nue : ~0.139 x 0.0015 x 0.090 m (Y-up)
      if (Math.abs(size.x - PCB_W / 1000) < 0.001 && Math.abs(size.z - PCB_D / 1000) < 0.001 && size.y < 0.0025) {
        topZ = box.max.y * 1000
        const g = m.geometry.clone()
        const nor = g.attributes.normal
        const cols = new Float32Array(nor.count * 3)
        const mask = new THREE.Color('#0c0d0e').convertSRGBToLinear()
        const fr4 = new THREE.Color('#8f8664').convertSRGBToLinear()
        for (let i = 0; i < nor.count; i++) {
          const c = Math.abs(nor.getY(i)) > 0.5 ? mask : fr4
          cols.set([c.r, c.g, c.b], i * 3)
        }
        g.setAttribute('color', new THREE.BufferAttribute(cols, 3))
        m.geometry = g
        m.material = maskMat
      } else if (isNode(m, 'D2')) {
        // LED 3 mm : corps diffusant rouge (le modèle KiCad est vert)
        const mat = m.material as THREE.MeshStandardMaterial
        const c = mat.color
        const hsl = { h: 0, s: 0, l: 0 }
        c.getHSL(hsl)
        if (hsl.s > 0.3) m.material = ledMat
      } else {
        const mat = m.material as THREE.MeshStandardMaterial
        if (mat && mat.isMeshStandardMaterial) {
          const mm = mat.clone()
          // les STEP KiCad n'ont pas de PBR : métal si gris clair peu saturé
          const hsl = { h: 0, s: 0, l: 0 }
          mm.color.getHSL(hsl)
          if (hsl.l > 0.5 && hsl.s < 0.25) {
            mm.metalness = 0.85
            mm.roughness = 0.3
          } else {
            mm.metalness = 0
            mm.roughness = 0.5
          }
          m.material = mm
        }
      }
    })
    return { root, topZ }
  }, [scene])

  useEffect(() => boardTop(topZ), [topZ, boardTop])

  useMemo(() => {
    color.colorSpace = THREE.SRGBColorSpace
    color.anisotropy = 8
    rm.anisotropy = 8
  }, [color, rm])

  return (
    <group>
      <group {...GLTF_TO_ENCLOSURE}>
        <primitive object={root} />
      </group>
      {/* face composants : cuivre, pastilles ENIG, sérigraphie (texture issue de kicad-cli) */}
      <mesh position={[PCB_W / 2, -PCB_D / 2, topZ + 0.02]} receiveShadow>
        <planeGeometry args={[PCB_W, PCB_D]} />
        <meshStandardMaterial
          map={color}
          roughnessMap={rm}
          metalnessMap={rm}
          metalness={1}
          roughness={1}
          alphaTest={0.5}
          polygonOffset
          polygonOffsetFactor={-1}
        />
      </mesh>
    </group>
  )
}

useGLTF.preload(BASE + 'pcb.glb')
