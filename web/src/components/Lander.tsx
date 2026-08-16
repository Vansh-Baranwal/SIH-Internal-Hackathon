import { useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { getAssetUrl } from '../api/client';
import type { Trajectory, TrajectoryPoint } from '../types/api';
import * as THREE from 'three';

interface LanderProps {
  trajectory: Trajectory | null;
  animationTime: number; // Controlled from the top level
  onUpdateTelemetry: (point: TrajectoryPoint) => void;
}

export function Lander({ trajectory, animationTime, onUpdateTelemetry }: LanderProps) {
  const glbUrl = getAssetUrl('vikram.glb');
  const { scene } = useGLTF(glbUrl);
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!trajectory || !groupRef.current) return;
    
    // Find current position in trajectory based on animationTime
    const points = trajectory.points;
    if (points.length === 0) return;

    let currentPoint = points[0];
    let nextPoint = points[points.length - 1];
    
    // Simple linear interpolation
    for (let i = 0; i < points.length - 1; i++) {
      if (points[i].t <= animationTime && points[i + 1].t >= animationTime) {
        currentPoint = points[i];
        nextPoint = points[i + 1];
        break;
      }
    }
    
    // If past end of trajectory, stay at last point
    if (animationTime >= points[points.length - 1].t) {
      currentPoint = points[points.length - 1];
      nextPoint = currentPoint;
    }

    const tRange = nextPoint.t - currentPoint.t;
    const progress = tRange === 0 ? 0 : (animationTime - currentPoint.t) / tRange;
    
    // Interpolate coordinates
    const x = currentPoint.x + (nextPoint.x - currentPoint.x) * progress;
    const y = currentPoint.y + (nextPoint.y - currentPoint.y) * progress;
    const z = currentPoint.z + (nextPoint.z - currentPoint.z) * progress;
    
    // Map M6 coordinate system to ThreeJS coordinate system
    // M6: X East, Y North, Z Up
    // ThreeJS: X Right, Y Up, Z Forward
    groupRef.current.position.set(x, z, -y);
    
    // Report back current telemetry
    onUpdateTelemetry({
      t: animationTime,
      x,
      y,
      z,
      vx: currentPoint.vx + (nextPoint.vx - currentPoint.vx) * progress,
      vy: currentPoint.vy + (nextPoint.vy - currentPoint.vy) * progress,
      vz: currentPoint.vz + (nextPoint.vz - currentPoint.vz) * progress,
      attitude: null
    });
  });

  // Scale down the Vikram model appropriately since it might be huge, or use as is
  return (
    <group ref={groupRef}>
      <primitive object={scene} scale={[1, 1, 1]} />
    </group>
  );
}
