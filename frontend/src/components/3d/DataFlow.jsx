import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const RING_PALETTES = {
  idle: { color1: '#06b6d4', color2: '#3b82f6', node: '#38bdf8' },
  analyzing: { color1: '#38bdf8', color2: '#f59e0b', node: '#fbbf24' },
  human: { color1: '#10b981', color2: '#06b6d4', node: '#34d399' },
  synthetic: { color1: '#f43f5e', color2: '#ef4444', node: '#fb7185' },
  unknown: { color1: '#f59e0b', color2: '#ea580c', node: '#fdba74' },
  inconclusive: { color1: '#8b5cf6', color2: '#64748b', node: '#c084fc' },
}

// Deterministic pseudo-random generator
function pseudoRandom(seed) {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

function generateParticles(count = 180) {
  const positions = new Float32Array(count * 3)
  const initial = []
  for (let i = 0; i < count; i++) {
    const r1 = pseudoRandom(i * 3.1415 + 1)
    const r2 = pseudoRandom(i * 2.7182 + 2)
    const r3 = pseudoRandom(i * 1.4142 + 3)

    const theta = r1 * Math.PI * 2
    const phi = Math.acos(r2 * 2 - 1)
    const radius = 1.6 + r3 * 1.5

    const x = radius * Math.sin(phi) * Math.cos(theta)
    const y = radius * Math.sin(phi) * Math.sin(theta)
    const z = radius * Math.cos(phi)

    positions[i * 3] = x
    positions[i * 3 + 1] = y
    positions[i * 3 + 2] = z

    initial.push({ radius, theta, phi, speed: 0.2 + r3 * 0.8 })
  }
  return { particlePositions: positions, particleInitial: initial }
}

const { particlePositions, particleInitial } = generateParticles(180)

export default function DataFlow({ state = 'idle' }) {
  const ring1Ref = useRef()
  const ring2Ref = useRef()
  const ring3Ref = useRef()
  const particlesRef = useRef()
  const nodesGroupRef = useRef()

  const palette = useMemo(() => {
    return RING_PALETTES[state.toLowerCase()] || RING_PALETTES.idle
  }, [state])

  // Neural nodes positioned around orbital paths
  const neuralNodes = useMemo(() => {
    const nodes = []
    const count = 14
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2
      const r = 2.4 + (i % 2 === 0 ? 0.3 : -0.2)
      nodes.push({
        position: [Math.cos(angle) * r, Math.sin(angle * 2) * 0.4, Math.sin(angle) * r],
        scale: 0.045 + (i % 3) * 0.015,
      })
    }
    return nodes
  }, [])

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()

    let speedMult = 0.5
    if (state === 'analyzing') speedMult = 1.6
    else if (state === 'synthetic') speedMult = 2.2
    else if (state === 'human') speedMult = 0.7
    else if (state === 'unknown') speedMult = 1.1
    else if (state === 'inconclusive') speedMult = 0.35

    // Multi-axis rotating rings
    if (ring1Ref.current) {
      ring1Ref.current.rotation.x = 0.6 + Math.sin(t * 0.2 * speedMult) * 0.1
      ring1Ref.current.rotation.y = t * 0.4 * speedMult
      ring1Ref.current.rotation.z = Math.cos(t * 0.15 * speedMult) * 0.1
    }

    if (ring2Ref.current) {
      ring2Ref.current.rotation.x = -0.7 + Math.cos(t * 0.25 * speedMult) * 0.1
      ring2Ref.current.rotation.y = -t * 0.5 * speedMult
      ring2Ref.current.rotation.z = 0.4
    }

    if (ring3Ref.current) {
      ring3Ref.current.rotation.x = t * 0.3 * speedMult
      ring3Ref.current.rotation.z = -t * 0.35 * speedMult
    }

    // Nodes group slow movement
    if (nodesGroupRef.current) {
      nodesGroupRef.current.rotation.y = t * 0.25 * speedMult
      nodesGroupRef.current.rotation.x = Math.sin(t * 0.3 * speedMult) * 0.15
    }

    // Particle flow
    if (particlesRef.current) {
      const attr = particlesRef.current.geometry.attributes.position
      const count = particleInitial.length
      for (let i = 0; i < count; i++) {
        const p = particleInitial[i]
        const currentTheta = p.theta + t * p.speed * 0.3 * speedMult
        const x = p.radius * Math.sin(p.phi) * Math.cos(currentTheta)
        const y = p.radius * Math.sin(p.phi) * Math.sin(currentTheta)
        const z = p.radius * Math.cos(p.phi)
        attr.setXYZ(i, x, y, z)
      }
      attr.needsUpdate = true
    }
  })

  return (
    <group>
      {/* Orbital Ring 1 - Equator tilt */}
      <mesh ref={ring1Ref}>
        <torusGeometry args={[2.3, 0.015, 16, 100]} />
        <meshBasicMaterial
          color={palette.color1}
          transparent={true}
          opacity={0.65}
        />
      </mesh>

      {/* Orbital Ring 2 - Polar tilt */}
      <mesh ref={ring2Ref}>
        <torusGeometry args={[2.7, 0.012, 16, 100]} />
        <meshBasicMaterial
          color={palette.color2}
          transparent={true}
          opacity={0.5}
        />
      </mesh>

      {/* Orbital Ring 3 - Outer wide ring */}
      <mesh ref={ring3Ref}>
        <torusGeometry args={[3.1, 0.009, 16, 100]} />
        <meshBasicMaterial
          color={palette.color1}
          transparent={true}
          opacity={0.35}
        />
      </mesh>

      {/* Neural Nodes along orbit */}
      <group ref={nodesGroupRef}>
        {neuralNodes.map((node, i) => (
          <mesh key={i} position={node.position}>
            <sphereGeometry args={[node.scale, 16, 16]} />
            <meshStandardMaterial
              color={palette.node}
              emissive={palette.node}
              emissiveIntensity={1.8}
              roughness={0.2}
            />
          </mesh>
        ))}
      </group>

      {/* Data Flow Particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[particlePositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.035}
          color={palette.color1}
          transparent={true}
          opacity={0.7}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  )
}
