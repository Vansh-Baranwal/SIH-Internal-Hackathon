import { useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { fetchMissionData } from './api/client';
import type { MissionData, TrajectoryPoint, TargetSite } from './types/api';
import { Terrain } from './components/Terrain';
import { Lander } from './components/Lander';
import { HUD } from './components/HUD';
import { UploadTMC } from './components/UploadTMC';

type MissionStatus = 'LOADING' | 'NORMAL DESCENT' | 'HAZARD DETECTED' | 'REPLANNING' | 'DIVERSION' | 'SAFE TOUCHDOWN' | 'ERROR';

function App() {
  const [missionData, setMissionData] = useState<MissionData | null>(null);
  const [status, setStatus] = useState<MissionStatus>('LOADING');
  const [animationTime, setAnimationTime] = useState<number>(0);
  const [telemetry, setTelemetry] = useState<TrajectoryPoint | null>(null);
  const [currentTarget, setCurrentTarget] = useState<TargetSite | null>(null);
  const [activeTrajectory, setActiveTrajectory] = useState<any>(null);
  const [replanTriggered, setReplanTriggered] = useState<boolean>(false);
  const [m2Completed, setM2Completed] = useState<boolean>(false);

  useEffect(() => {
    if (!m2Completed) return;
    fetchMissionData()
      .then(data => {
        setMissionData(data);
        setActiveTrajectory(data.trajectory_primary);
        setCurrentTarget(data.target);
        setStatus('NORMAL DESCENT');
      })
      .catch(err => {
        console.error(err);
        setStatus('ERROR');
      });
  }, [m2Completed]);

  // Animation Loop
  useEffect(() => {
    if (status === 'LOADING' || status === 'ERROR' || status === 'SAFE TOUCHDOWN') return;

    let lastTime = performance.now();
    let frameId: number;

    const loop = (time: number) => {
      const dt = (time - lastTime) / 1000.0;
      lastTime = time;

      setAnimationTime(prev => {
        const newTime = prev + dt;
        
        if (missionData && missionData.replan_event && !replanTriggered) {
          if (newTime >= missionData.replan_event.timestamp) {
            // Trigger replan
            setReplanTriggered(true);
            setStatus('HAZARD DETECTED');
            
            setTimeout(() => {
              setStatus('REPLANNING');
              setTimeout(() => {
                // Switch trajectory and target
                setActiveTrajectory(missionData.trajectory_replanned);
                
                const fallbackSite = missionData.replan_event!.candidates.find(
                  c => c.siteId === missionData.replan_event!.newSite
                );
                
                setCurrentTarget(fallbackSite || null);
                setStatus('DIVERSION');
              }, 1500); // 1.5s thinking time for dramatic effect
            }, 1000); // 1s hazard detected flash
            
            return newTime; // keep advancing time
          }
        }

        // Check for touchdown
        if (activeTrajectory && activeTrajectory.points.length > 0) {
          const finalPoint = activeTrajectory.points[activeTrajectory.points.length - 1];
          if (newTime >= finalPoint.t) {
            setStatus('SAFE TOUCHDOWN');
            return finalPoint.t; // Clamp to end
          }
        }

        return newTime;
      });

      frameId = requestAnimationFrame(loop);
    };

    frameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameId);
  }, [status, missionData, activeTrajectory, replanTriggered]);

  if (status === 'LOADING' && m2Completed) return <div className="flex h-screen items-center justify-center text-cyan-500 font-mono text-2xl">LOADING MISSION DATA...</div>;
  if (status === 'ERROR') return <div className="flex h-screen items-center justify-center text-red-500 font-mono text-2xl">ERROR LOADING MISSION DATA</div>;

  const fallbackSite = missionData?.replan_event?.candidates.find(c => c.siteId === missionData.replan_event?.newSite) || null;

  return (
    <div className="w-full h-full relative bg-black">
      {!m2Completed && <UploadTMC onUploadComplete={() => setM2Completed(true)} />}
      <HUD 
        telemetry={telemetry} 
        status={status} 
        target={currentTarget} 
        deltaV={missionData?.replan_event?.maneuverCost || 14.6} // mock or from event
      />
      
      <Canvas camera={{ position: [50, 150, 150], fov: 60 }}>
        <color attach="background" args={['#050505']} />
        <ambientLight intensity={0.2} />
        <directionalLight position={[100, 100, 50]} intensity={1.5} castShadow />
        
        <Environment preset="night" />

        <Terrain 
          primaryTarget={missionData?.target || null} 
          replannedTarget={fallbackSite}
          replanTriggered={replanTriggered}
        />
        
        <Lander 
          trajectory={activeTrajectory} 
          animationTime={animationTime} 
          onUpdateTelemetry={setTelemetry}
        />
        
        <OrbitControls target={[100, 0, -100]} />
      </Canvas>
    </div>
  );
}

export default App;
