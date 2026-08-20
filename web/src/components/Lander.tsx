import { useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { getAssetUrl } from '../api/client';
import * as THREE from 'three';

// Updated interface to include velocities and attitude
interface ExtendedTrajectoryPoint {
  t: number; x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
  pitch?: number; yaw?: number; roll?: number;
}

interface LanderProps {
  trajectory: { points: ExtendedTrajectoryPoint[] } | null;
  animationTime: number; 
  onUpdateTelemetry: (point: ExtendedTrajectoryPoint) => void;
}

export function Lander({ trajectory, animationTime, onUpdateTelemetry }: LanderProps) {
  const glbUrl = getAssetUrl('vikram.glb');
  const { scene } = useGLTF(glbUrl);
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!trajectory || !groupRef.current) return;
    
    const points = trajectory.points;
    if (points.length === 0) return;

    let currentPoint = points[0];
    let nextPoint = points[points.length - 1];
    
    for (let i = 0; i < points.length - 1; i++) {
      if (points[i].t <= animationTime && points[i + 1].t >= animationTime) {
        currentPoint = points[i];
        nextPoint = points[i + 1];
        break;
      }
    }
    
    if (animationTime >= points[points.length - 1].t) {
      currentPoint = points[points.length - 1];
      nextPoint = currentPoint;
    }

    const tRange = nextPoint.t - currentPoint.t;
    const progress = tRange === 0 ? 0 : (animationTime - currentPoint.t) / tRange;
    
    const x = currentPoint.x + (nextPoint.x - currentPoint.x) * progress;
    const y = currentPoint.y + (nextPoint.y - currentPoint.y) * progress;
    const z = currentPoint.z + (nextPoint.z - currentPoint.z) * progress;
    
    // M6: X East, Y North, Z Up
    // ThreeJS: X Right, Y Up, Z Forward
    groupRef.current.position.set(x, z, -y);

    // Apply attitude (rotation)
    const curPitch = currentPoint.pitch || 0;
    const nextPitch = nextPoint.pitch || 0;
    const curYaw = currentPoint.yaw || 0;
    const nextYaw = nextPoint.yaw || 0;
    const curRoll = currentPoint.roll || 0;
    const nextRoll = nextPoint.roll || 0;

    const pitch = curPitch + (nextPitch - curPitch) * progress;
    const yaw = curYaw + (nextYaw - curYaw) * progress;
    const roll = curRoll + (nextRoll - curRoll) * progress;

    groupRef.current.rotation.set(pitch, yaw, roll);
    
    // Interpolate Velocities
    const vx = currentPoint.vx + (nextPoint.vx - currentPoint.vx) * progress;
    const vy = currentPoint.vy + (nextPoint.vy - currentPoint.vy) * progress;
    const vz = currentPoint.vz + (nextPoint.vz - currentPoint.vz) * progress;

    onUpdateTelemetry({
      t: animationTime,
      x, y, z,
      vx, vy, vz,
      pitch, yaw, roll
    });
  });

  return (
    <group ref={groupRef}>
      <primitive object={scene} scale={[20, 20, 20]} />
    </group>
  );
}
