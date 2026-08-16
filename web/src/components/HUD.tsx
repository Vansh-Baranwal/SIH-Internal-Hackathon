import type { TargetSite, TrajectoryPoint } from '../types/api';

interface HUDProps {
  telemetry: TrajectoryPoint | null;
  status: string;
  target: TargetSite | null;
  deltaV: number;
}

export function HUD({ telemetry, status, target, deltaV }: HUDProps) {
  const speed = telemetry ? Math.sqrt(Math.pow(telemetry.vx, 2) + Math.pow(telemetry.vy, 2) + Math.pow(telemetry.vz, 2)) : 0;
  
  return (
    <div className="absolute top-0 left-0 p-6 pointer-events-none w-full flex justify-between items-start z-10 font-mono">
      {/* Telemetry Panel */}
      <div className="bg-black/80 border border-cyan-500/30 p-4 rounded text-cyan-400 min-w-[200px] backdrop-blur-sm shadow-[0_0_15px_rgba(0,255,255,0.1)]">
        <h2 className="text-sm font-bold text-cyan-200 mb-3 border-b border-cyan-500/30 pb-1">TELEMETRY</h2>
        
        <div className="mb-2">
          <div className="text-xs text-cyan-600">ALTITUDE</div>
          <div className="text-xl">{telemetry ? telemetry.z.toFixed(1) : '---'} <span className="text-xs text-cyan-500">m</span></div>
        </div>
        
        <div className="mb-2">
          <div className="text-xs text-cyan-600">VELOCITY</div>
          <div className="text-xl">{speed.toFixed(1)} <span className="text-xs text-cyan-500">m/s</span></div>
        </div>
        
        <div className="mb-2">
          <div className="text-xs text-cyan-600">Δv REMAINING (EST)</div>
          <div className="text-xl">{deltaV.toFixed(1)} <span className="text-xs text-cyan-500">m/s</span></div>
        </div>
      </div>

      {/* Mission Status Panel */}
      <div className="bg-black/80 border border-cyan-500/30 p-4 rounded min-w-[200px] text-right backdrop-blur-sm shadow-[0_0_15px_rgba(0,255,255,0.1)]">
        <h2 className="text-sm font-bold text-cyan-200 mb-3 border-b border-cyan-500/30 pb-1">MISSION CONTROL</h2>
        
        <div className="mb-2">
          <div className="text-xs text-cyan-600">TARGET</div>
          <div className={`text-xl ${status === 'REPLANNING' ? 'text-yellow-400' : 'text-cyan-400'}`}>
            {target ? target.siteId : '---'}
          </div>
        </div>
        
        <div className="mb-2">
          <div className="text-xs text-cyan-600">STATUS</div>
          <div className={`text-xl font-bold
            ${status === 'NORMAL DESCENT' ? 'text-green-400' : ''}
            ${status === 'HAZARD DETECTED' ? 'text-red-500 animate-pulse' : ''}
            ${status === 'REPLANNING' ? 'text-yellow-400 animate-pulse' : ''}
            ${status === 'DIVERSION' ? 'text-cyan-400' : ''}
            ${status === 'SAFE TOUCHDOWN' ? 'text-lime-400' : ''}
          `}>
            {status}
          </div>
        </div>
      </div>
    </div>
  );
}
