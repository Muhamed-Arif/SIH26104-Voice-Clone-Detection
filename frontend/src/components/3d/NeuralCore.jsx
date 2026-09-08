import React, { Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Float } from '@react-three/drei'
import AudioSphere from './AudioSphere'
import DataFlow from './DataFlow'
import ScanEffect from './ScanEffect'

// Smooth camera responder
function CameraRig({ state }) {
  useFrame(({ camera, clock }) => {
    const t = clock.getElapsedTime()
    // Subtle breathing camera motion
    const wobbleSpeed = state === 'synthetic' ? 1.8 : state === 'analyzing' ? 1.2 : 0.6
    const amp = state === 'synthetic' ? 0.2 : 0.08

    camera.position.x = Math.sin(t * wobbleSpeed * 0.5) * amp
    camera.position.y = Math.cos(t * wobbleSpeed * 0.3) * (amp * 0.5)
    camera.lookAt(0, 0, 0)
  })
  return null
}

const LIGHT_CONFIGS = {
  idle: { light1: '#06b6d4', light2: '#3b82f6', intensity: 2 },
  analyzing: { light1: '#38bdf8', light2: '#f59e0b', intensity: 3 },
  human: { light1: '#10b981', light2: '#06b6d4', intensity: 2.2 },
  synthetic: { light1: '#f43f5e', light2: '#ef4444', intensity: 3.5 },
  unknown: { light1: '#f59e0b', light2: '#ea580c', intensity: 2.4 },
  inconclusive: { light1: '#8b5cf6', light2: '#64748b', intensity: 1.8 },
}

export default function NeuralCore({ state = 'idle', className = '' }) {
  const currentKey = (state || 'idle').toLowerCase()
  const lights = LIGHT_CONFIGS[currentKey] || LIGHT_CONFIGS.idle

  return (
    <div className={`relative w-full h-full min-h-[380px] select-none ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 5.8], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        style={{ pointerEvents: 'auto' }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.4} />
          <pointLight
            position={[10, 10, 10]}
            color={lights.light1}
            intensity={lights.intensity}
            distance={20}
          />
          <pointLight
            position={[-10, -10, -10]}
            color={lights.light2}
            intensity={lights.intensity * 0.7}
            distance={20}
          />
          <pointLight
            position={[0, 5, 2]}
            color="#ffffff"
            intensity={0.6}
            distance={10}
          />

          <CameraRig state={currentKey} />

          <Float
            speed={currentKey === 'synthetic' ? 4 : currentKey === 'analyzing' ? 2.5 : 1.5}
            rotationIntensity={0.3}
            floatIntensity={0.3}
          >
            <group position={[0, 0, 0]}>
              <AudioSphere state={currentKey} />
              <DataFlow state={currentKey} />
              <ScanEffect state={currentKey} />
            </group>
          </Float>

          <OrbitControls
            enableZoom={false}
            enablePan={false}
            rotateSpeed={0.5}
            dampingFactor={0.05}
            maxPolarAngle={Math.PI / 1.6}
            minPolarAngle={Math.PI / 2.5}
          />
        </Suspense>
      </Canvas>

      {/* Cyber Reticle Overlay (Decorative HUD) */}
      <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-4 text-[10px] font-mono text-cyan-500/60">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span>NEURAL CORE : ACTIVE</span>
          </div>
          <span>LIVE AUDIO // 2s ANALYSIS WINDOWS</span>
        </div>

        <div className="flex justify-between items-end">
          <div className="space-y-0.5">
            <div>CORE STATUS: [{currentKey.toUpperCase()}]</div>
            <div className="text-slate-500">AETHERVOICE AUTHENTICITY ENGINE</div>
          </div>
          <div className="text-right text-slate-500">
            <span>AZ: 042° // EL: 12°</span>
            <div className="text-cyan-400/80">RENDER: THREE-WebGL</div>
          </div>
        </div>
      </div>
    </div>
  )
}
