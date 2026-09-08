import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const STATE_COLORS = {
  idle: {
    primary: '#06b6d4',
    secondary: '#3b82f6',
    emissive: '#0891b2',
    intensity: 1.2,
  },
  analyzing: {
    primary: '#38bdf8',
    secondary: '#f59e0b',
    emissive: '#0284c7',
    intensity: 2.0,
  },
  human: {
    primary: '#10b981',
    secondary: '#06b6d4',
    emissive: '#059669',
    intensity: 1.4,
  },
  synthetic: {
    primary: '#f43f5e',
    secondary: '#ef4444',
    emissive: '#be123c',
    intensity: 2.5,
  },
  unknown: {
    primary: '#f59e0b',
    secondary: '#ea580c',
    emissive: '#d97706',
    intensity: 1.6,
  },
  inconclusive: {
    primary: '#8b5cf6',
    secondary: '#64748b',
    emissive: '#6d28d9',
    intensity: 1.1,
  },
}

export default function AudioSphere({ state = 'idle' }) {
  const innerRef = useRef()
  const wireframeRef = useRef()
  const outerHaloRef = useRef()
  const waveformRingRef = useRef()

  const config = useMemo(() => {
    return STATE_COLORS[state.toLowerCase()] || STATE_COLORS.idle
  }, [state])

  // Create waveform ring points
  const waveformGeometry = useMemo(() => {
    const pointsCount = 128
    const positions = new Float32Array(pointsCount * 3)
    const radius = 2.1
    for (let i = 0; i < pointsCount; i++) {
      const theta = (i / pointsCount) * Math.PI * 2
      positions[i * 3] = Math.cos(theta) * radius
      positions[i * 3 + 1] = 0
      positions[i * 3 + 2] = Math.sin(theta) * radius
    }
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    return geometry
  }, [])

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()

    // Dynamics based on state
    let speed = 0.6
    let pulseFreq = 1.8
    let pulseAmp = 0.05

    if (state === 'analyzing') {
      speed = 1.8
      pulseFreq = 4.5
      pulseAmp = 0.12
    } else if (state === 'synthetic') {
      speed = 2.4
      pulseFreq = 7.0
      pulseAmp = 0.18
    } else if (state === 'human') {
      speed = 0.8
      pulseFreq = 2.0
      pulseAmp = 0.06
    } else if (state === 'unknown') {
      speed = 1.2
      pulseFreq = 3.5
      pulseAmp = 0.1
    } else if (state === 'inconclusive') {
      speed = 0.4
      pulseFreq = 1.2
      pulseAmp = 0.03
    }

    // Inner sphere rotation & pulse
    if (innerRef.current) {
      innerRef.current.rotation.y = t * speed * 0.4
      innerRef.current.rotation.x = t * speed * 0.2
      const s = 1 + Math.sin(t * pulseFreq) * pulseAmp
      innerRef.current.scale.set(s, s, s)
    }

    // Wireframe shell rotation & counter-pulse
    if (wireframeRef.current) {
      wireframeRef.current.rotation.y = -t * speed * 0.6
      wireframeRef.current.rotation.z = t * speed * 0.3
      const ws = 1.35 + Math.cos(t * (pulseFreq * 0.8)) * (pulseAmp * 0.8)
      wireframeRef.current.scale.set(ws, ws, ws)
    }

    // Outer halo subtle wobble
    if (outerHaloRef.current) {
      outerHaloRef.current.rotation.z = -t * 0.15
      outerHaloRef.current.rotation.x = Math.sin(t * 0.5) * 0.1
    }

    // Audio-reactive waveform ring displacement
    if (waveformRingRef.current) {
      waveformRingRef.current.rotation.y = t * speed * 0.5
      const pos = waveformRingRef.current.geometry.attributes.position
      const radius = 2.1
      const count = pos.count
      for (let i = 0; i < count; i++) {
        const theta = (i / count) * Math.PI * 2
        // harmonic displacement resembling voice frequency bands
        const wave =
          Math.sin(theta * 8 + t * (pulseFreq * 2)) * pulseAmp * 1.5 +
          Math.cos(theta * 4 - t * pulseFreq) * (pulseAmp * 0.8)
        pos.setXYZ(
          i,
          Math.cos(theta) * (radius + wave),
          wave * 1.8,
          Math.sin(theta) * (radius + wave)
        )
      }
      pos.needsUpdate = true
    }
  })

  return (
    <group>
      {/* Central Solid Core */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[0.9, 32, 32]} />
        <meshStandardMaterial
          color={config.primary}
          emissive={config.emissive}
          emissiveIntensity={config.intensity}
          roughness={0.25}
          metalness={0.7}
          wireframe={false}
        />
      </mesh>

      {/* Geometric Wireframe Shell */}
      <mesh ref={wireframeRef}>
        <icosahedronGeometry args={[0.9, 2]} />
        <meshStandardMaterial
          color={config.secondary}
          emissive={config.primary}
          emissiveIntensity={config.intensity * 0.6}
          wireframe={true}
          transparent={true}
          opacity={0.65}
        />
      </mesh>

      {/* Outer Halo Shell */}
      <mesh ref={outerHaloRef}>
        <sphereGeometry args={[1.55, 16, 16]} />
        <meshBasicMaterial
          color={config.primary}
          wireframe={true}
          transparent={true}
          opacity={0.12}
        />
      </mesh>

      {/* Surrounding Audio Waveform Ring */}
      <lineLoop ref={waveformRingRef} geometry={waveformGeometry}>
        <lineBasicMaterial
          color={config.primary}
          transparent={true}
          opacity={0.8}
          linewidth={1.5}
        />
      </lineLoop>
    </group>
  )
}
