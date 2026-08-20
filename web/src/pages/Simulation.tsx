import { useState, useEffect, Suspense } from 'react';
import { useMission } from '../context/MissionContext';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Terrain } from '../components/Terrain';
import { Lander } from '../components/Lander';
import { HUD } from '../components/HUD';
import { OrbitalPlanner } from '../components/OrbitalPlanner';
import * as THREE from 'three';

// A helper component inside the Canvas that can raycast the 3D terrain
function TerrainRaycaster({ command, onResult }: { command: {x: number, z: number, id: number} | null, onResult: (x: number, y: number, z: number, isSafe: boolean) => void }) {
  const { scene } = useThree();
  
  useEffect(() => {
    if (command) {
      const { x, z } = command;
      const raycaster = new THREE.Raycaster();
      // Cast a ray from high above the map directly downward
      raycaster.set(new THREE.Vector3(x, 5000, z), new THREE.Vector3(0, -1, 0));
      
      const intersects = raycaster.intersectObject(scene, true);
      
      let altitude = 0;
      let isSafe = true;

      if (intersects.length > 0) {
        // Find the first intersection that is the actual terrain (not a marker or lander)
        const hit = intersects.find(i => i.object.type === 'Mesh' && !i.object.name.includes('marker'));
        if (hit) {
            altitude = hit.point.y;
            if (hit.face) {
                const normal = hit.face.normal.clone();
                const normalMatrix = new THREE.Matrix3().getNormalMatrix(hit.object.matrixWorld);
                normal.applyMatrix3(normalMatrix).normalize();
                
                const slope = Math.acos(Math.abs(normal.y)) * (180 / Math.PI);
                isSafe = slope <= 10.0;
            }
        }
      }
      
      onResult(x, altitude, z, isSafe);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [command?.id, scene]);
  
  return null;
}

export function Simulation() {
  const { result } = useMission();
  
  const [target, setTarget] = useState<{x: number, y: number, z: number} | null>(null);
  const [trajectory, setTrajectory] = useState<any>(null);
  const [animationTime, setAnimationTime] = useState(0);
  const [status, setStatus] = useState('STANDBY');
  const [isCrashing, setIsCrashing] = useState(false);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [isPlannerOpen, setIsPlannerOpen] = useState(false);
  
  // State to trigger the 3D raycaster from the 2D planner
  const [divertCommand, setDivertCommand] = useState<{x: number, z: number, id: number} | null>(null);
  
  useEffect(() => {
    if (result?.pipeline?.binary_url) {
        setStatus('AWAITING TARGET');
    }
  }, [result]);

  const initiateDescent = (x: number, altitude: number, z: number, isSafe: boolean) => {
    setTarget({x, y: altitude, z});
    
    if (isSafe) {
        setStatus('DESCENDING (SAFE TRAJECTORY)');
        setIsCrashing(false);
    } else {
        setStatus('WARNING: STEEP SLOPE DETECTED - CRASH IMMINENT');
        setIsCrashing(true);
    }
    
    const points = [];
    const steps = 600; 
    
    const startAltitude = Math.max(altitude + 400, 400);
    const startX = x + 600;      
    const startY = -z + 400;     
    const initialVx = 1680.0; 
    
    for(let i=0; i<=steps; i++) {
        const t = (i / steps) * 10; 
        const progress = i / steps; 
        
        let ease = progress;
        let pitch = 0, yaw = 0, roll = 0;
        let currentAltitude = 0;
        let currentX = x;
        let currentY = -z;
        let vx = 0, vy = 0, vz = 0;

        if (isSafe) {
            ease = 1 - (1 - progress) * (1 - progress); 
            
            currentX = startX - (startX - x) * ease;
            currentY = startY - (startY - (-z)) * ease;
            currentAltitude = startAltitude - (startAltitude - altitude) * ease;
            
            pitch = (1 - ease) * (Math.PI / 3); 
            yaw = Math.atan2((startX - x), (startY - (-z))) * 0.5; 
            roll = Math.cos(progress * Math.PI * 2) * 0.02; 
            
            vx = initialVx * (1 - progress); 
            vy = (startAltitude - altitude) * -0.5 * (1 - progress); 
        } else {
            if (progress < 0.9) {
                const p = progress / 0.9;
                ease = p * p * p; 
                
                const horizEase = p * p; 
                
                currentX = startX - (startX - x) * horizEase;
                currentY = startY - (startY - (-z)) * horizEase;
                currentAltitude = startAltitude - (startAltitude - altitude) * ease;
                
                pitch = p * Math.PI * 6; 
                roll = p * Math.PI * 4;
                yaw = p * Math.PI * 2;
                
                vx = initialVx * (1 - p * 0.2); 
                vy = (startAltitude - altitude) * -2.0 * p; 
            } else {
                const p = (progress - 0.9) / 0.1;
                const bounce = Math.abs(Math.sin(p * Math.PI * 2)) * 30 * (1 - p);
                
                currentX = x - (startX - x) * 0.1 * p;
                currentY = -z - (startY - (-z)) * 0.1 * p;
                currentAltitude = altitude + bounce;
                
                pitch = (0.9 * Math.PI * 6) + (p * Math.PI / 2);
                roll = (0.9 * Math.PI * 4) + (p * Math.PI / 2);
                
                vx = initialVx * 0.2 * (1 - p); 
                vy = bounce > 0.1 ? 15 : 0;
            }
        }
        
        points.push({
            t: t,
            x: currentX, 
            y: currentY, 
            z: currentAltitude, 
            vx, vy, vz,
            pitch, yaw, roll
        });
    }
    
    setTrajectory({ points });
    setAnimationTime(0);
  };

  const handleTerrainClick = (x: number, altitude: number, z: number, isSafe: boolean) => {
    initiateDescent(x, altitude, z, isSafe);
  };

  const handlePlannerExecute = (x: number, z: number) => {
    // Instead of immediately executing, we send a command to the 3D Raycaster inside the Canvas.
    // The Raycaster will find the exact 3D altitude and slope, and then call initiateDescent!
    setDivertCommand({ x, z, id: Date.now() });
    setIsPlannerOpen(false);
  };

  const TimeUpdater = () => {
    useFrame((state, delta) => {
        if (status.includes('DESCENDING') || status.includes('CRASH IMMINENT')) {
            setAnimationTime(prev => {
                const speed = 1.5; 
                const next = prev + delta * speed; 
                if (next > 10) {
                    if (isCrashing) {
                        setStatus('CATASTROPHIC FAILURE (CRASH)');
                    } else {
                        setStatus('TOUCHDOWN - NOMINAL');
                    }
                    return 10;
                }
                return next;
            });
        }
    });
    return null;
  };

  if (!result) return <div className="text-white flex-grow flex items-center justify-center font-mono">Run Pipeline first</div>;

  return (
    <div className="w-full relative bg-black flex flex-col pt-24" style={{ height: '100vh', overflow: 'hidden' }}>
      
      {/* 3D Scene */}
      <div className="absolute inset-0 pt-24 w-full h-full cursor-crosshair z-0">
          <Canvas camera={{ position: [0, 600, 400], fov: 60, far: 50000 }}>
            <TimeUpdater />
            
            <TerrainRaycaster 
                command={divertCommand} 
                onResult={(x, alt, z, isSafe) => initiateDescent(x, alt, z, isSafe)} 
            />

            <color attach="background" args={['#050505']} />
            <ambientLight intensity={5.0} />
            <directionalLight position={[100, 500, 100]} intensity={10.0} />
            
            <Suspense fallback={null}>
                <Terrain onClick={handleTerrainClick} target={target} />
            </Suspense>
            
            <Suspense fallback={null}>
                {trajectory && (
                    <Lander 
                      trajectory={trajectory} 
                      animationTime={animationTime} 
                      onUpdateTelemetry={(point) => setTelemetry(point)} 
                    />
                )}
            </Suspense>
            
            <OrbitControls target={[0, 0, 0]} maxPolarAngle={Math.PI / 2.1} />
          </Canvas>
      </div>

      <HUD 
        telemetry={telemetry} 
        status={status} 
        target={target} 
        isCrashing={isCrashing} 
        animationTime={animationTime} 
        onOpenPlanner={() => setIsPlannerOpen(true)}
      />

      {isPlannerOpen && (
        <OrbitalPlanner 
            onClose={() => setIsPlannerOpen(false)} 
            onExecute={handlePlannerExecute} 
        />
      )}
    </div>
  );
}
