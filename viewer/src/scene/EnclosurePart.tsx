import { useEffect, useMemo } from 'react'
import * as THREE from 'three'
import { useGLTF } from '@react-three/drei'
import { boxUV, petgMaterial } from './materials'
import { GLTF_TO_ENCLOSURE } from './Pcb'

const BASE = import.meta.env.BASE_URL + 'models/'
export const ENCLOSURE_PARTS = ['tray', 'lid', 'back_panel', 'front_panel'] as const
export type EnclosurePartName = (typeof ENCLOSURE_PARTS)[number]

/** Pièce imprimée (PETG). `xray` = semi-transparente. */
export function EnclosurePart({ name, color, xray }: { name: EnclosurePartName; color: string; xray: boolean }) {
  const { scene } = useGLTF(BASE + name + '.glb')
  const panel = name.endsWith('panel')
  const material = useMemo(() => petgMaterial('#2b2d31', panel), [panel])

  const root = useMemo(() => {
    const r = scene.clone(true)
    r.traverse((o) => {
      const m = o as THREE.Mesh
      if (!m.isMesh) return
      const g = m.geometry.clone()
      // pas des couches FDM : 0,2 mm (UV en mètres -> mm)
      boxUV(g, panel ? 0.42 : 0.2, 1000)
      m.geometry = g
      m.material = material
      m.castShadow = true
      m.receiveShadow = true
    })
    return r
  }, [scene, material, panel])

  useEffect(() => {
    material.color.set(color)
    material.transparent = xray
    material.opacity = xray ? 0.16 : 1
    material.depthWrite = !xray
    material.needsUpdate = true
    root.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.isMesh) m.castShadow = !xray
    })
  }, [color, xray, material, root])

  return (
    <group {...GLTF_TO_ENCLOSURE}>
      <primitive object={root} />
    </group>
  )
}

ENCLOSURE_PARTS.forEach((p) => useGLTF.preload(BASE + p + '.glb'))
