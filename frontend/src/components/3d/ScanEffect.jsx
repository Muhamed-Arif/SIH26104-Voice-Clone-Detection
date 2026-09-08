import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const SCAN_COLORS = {
  idle: { laser: '#06b6d4', grid: '#0891b2', opacity: 0.25 },
  analyzing: { laser: '#38bdf8', grid: '#f59e0b', opacity: 0.7 },
  human: { laser: '#10b981', grid: '#34d399', opacity: 0.35 },
  synthetic: { laser: '#f43f5e', grid: '#ef4444', opacity: 0.8 },
  unknown: { laser: '#f59e0b', grid: '#ea580c', opacity: 0.45 },
  inconclusive: { laser: '#8b5cf6', grid: '#64748b', opacity: 0.25 },
}

export default function ScanEffect({ state = 'idle' }) {
  const scanPlaneRef = useRef()
  const radarRingRef = useRef()

  const config = useMemo(() => {
    return SCAN_COLORS[state.toLowerCase()] || SCAN_COLORS.idle
  }, [state])

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()

    // Height oscillation of scanning laser disk
    if (scanPlaneRef.current) {
      let freq = 1.2
      let heightRange = 1.3
      if (state === 'analyzing') {
        freq = 3.5
        heightRange = 1.6
      } else if (state === 'synthetic') {
        freq = 5.0
        heightRange = 1.7
      } else if (state === 'inconclusive') {
        freq = 0.6
        heightRange = 0.9
      }

      scanPlaneRef.current.position.y = Math.sin(t * freq) * heightRange

      // Dynamic scale matching sphere diameter at that height
      const currentY = scanPlaneRef.current.position.y
      const r = Math.max(0.6, Math.sqrt(Math.max(0, 3.5 - currentY * currentY)))
      scanPlaneRef.current.scale.set(r, r, 1)
    }

    // Radar sweep rotation
    if (radarRingRef.current) {
      const rotSpeed = state === 'analyzing' ? 2.5 : state === 'synthetic' ? 3.2 : 0.8
      radarRingRef.current.rotation.z = -t * rotSpeed
    }
  })

  return (
    <group>
      {/* Horizontal Scanning Disk */}
      <group ref={scanPlaneRef}>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.01, 1.4, 64]} />
          <meshBasicMaterial
            color={config.laser}
            transparent={true}
            opacity={config.opacity * 0.4}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.35, 1.4, 64]} />
          <meshBasicMaterial
            color={config.laser}
            transparent={true}
            opacity={config.opacity}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>

      {/* Equatorial Radar Sweep Reticle */}
      <group position={[0, -1.8, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <mesh ref={radarRingRef}>
          <ringGeometry args={[1.8, 1.82, 64]} />
          <meshBasicMaterial
            color={config.grid}
            transparent={true}
            opacity={0.3}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
    </group>
  )
}
