import React from 'react';

interface HUDProps {
  telemetry: any;
  status: string;
  target: any;
  isCrashing: boolean;
  animationTime: number;
  onOpenPlanner: () => void;
}

export function HUD({ telemetry, status, target, isCrashing, animationTime, onOpenPlanner }: HUDProps) {
  
  const alt = telemetry ? Math.max(0, telemetry.z - (target?.y || 0)) : 0;
  const currentVel = telemetry ? Math.sqrt(Math.pow(telemetry.vx, 2) + Math.pow(telemetry.vy, 2) + Math.pow(telemetry.vz, 2)) : 1680.0;
  
  let neededVel = 1680.0;
  if (telemetry && !isCrashing) {
      if (alt < 10) neededVel = 2.0; 
      else if (alt < 50) neededVel = 20.0; 
      else if (alt < 300) neededVel = 150.0; 
  } else if (isCrashing) {
      neededVel = 0; 
  }

  let phase = "Orbital Standby";
  if (telemetry) {
      if (animationTime >= 10) phase = isCrashing ? "System Failure" : "Surface Operations";
      else if (alt > 200) phase = "Powered Descent Initiated";
      else if (alt > 50) phase = "Rough Braking Phase";
      else if (alt > 10) phase = "Fine Braking Phase";
      else phase = "Terminal Descent";
  }

  const tProgress = Math.min(10, Math.max(0, animationTime)) / 10;
  const svgW = 200;
  const svgH = 100;
  const dotX = tProgress * svgW;
  const dotY = isCrashing 
      ? (tProgress < 0.9 ? Math.pow(tProgress/0.9, 3) * svgH : svgH - Math.abs(Math.sin((tProgress-0.9)*10 * Math.PI*2))*20)
      : (1 - Math.pow(1 - tProgress, 2)) * svgH;

  const statusColor = isCrashing ? 'text-rose-500' : 'text-emerald-400';
  const borderColor = isCrashing ? 'border-rose-500/20' : 'border-white/10';
  const bgColor = isCrashing ? 'bg-rose-950/20' : 'bg-[#0a0a0a]/60';

  return (
    <div className="absolute inset-0 pointer-events-none z-10 flex flex-col justify-between p-6">
      
      {/* TOP ROW */}
      <div className="flex justify-between items-start">
        {/* Top Left: Status & Controls */}
        <div className={`p-5 rounded-2xl border backdrop-blur-xl shadow-2xl flex flex-col pointer-events-auto ${borderColor} ${bgColor}`}>
            <h2 className="text-zinc-400 tracking-widest font-bold text-[10px] uppercase mb-1">Flight Dynamics</h2>
            <p className={`text-sm font-semibold tracking-wide ${statusColor}`}>{status}</p>
            <p className="text-zinc-500 mt-1 text-[11px] mb-5">Click on feasible terrain to set target.</p>
            
            <button 
                onClick={onOpenPlanner}
                className="bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-200 font-medium py-2 px-4 text-xs rounded-lg transition-all shadow-sm"
            >
                Open Orbital Replanner
            </button>
        </div>

        {/* Top Right: 2D Trajectory View */}
        {target && (
            <div className={`p-5 rounded-2xl border backdrop-blur-xl shadow-2xl w-[260px] ${borderColor} ${bgColor}`}>
                <h3 className="text-zinc-400 font-bold mb-3 text-[10px] tracking-widest uppercase border-b border-white/10 pb-2">Trajectory Plot</h3>
                <div className="relative w-full h-[100px] bg-black/40 rounded-lg overflow-hidden border border-white/5 shadow-inner">
                    <svg width="100%" height="100%" className="absolute inset-0">
                        <path d={`M 0 0 Q ${svgW/2} 0 ${svgW} ${svgH}`} fill="none" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.3" />
                        <path d={`M 0 0 C ${svgW/2} 0 ${svgW*0.9} ${svgH*0.2} ${svgW*0.9} ${svgH}`} fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.3" />
                        
                        <circle cx={dotX} cy={dotY} r="3" fill={isCrashing ? "#f43f5e" : "#10b981"} className="drop-shadow-lg" />
                        <line x1={dotX} y1={dotY} x2={dotX} y2={svgH} stroke={isCrashing ? "#f43f5e" : "#10b981"} strokeWidth="1" opacity="0.4" />
                    </svg>
                    
                    <div className="absolute bottom-1.5 left-2 text-[9px] font-mono text-zinc-500">ALT: {alt.toFixed(0)}m</div>
                    <div className="absolute bottom-1.5 right-2 text-[9px] font-mono text-zinc-500">TGT: {target.x.toFixed(0)}, {target.z.toFixed(0)}</div>
                </div>
            </div>
        )}
      </div>

      {/* BOTTOM ROW */}
      <div className="flex justify-between items-end">
        {telemetry && (
            <div className={`p-6 rounded-2xl border backdrop-blur-xl shadow-2xl min-w-[320px] ${borderColor} ${bgColor}`}>
                <h3 className="text-zinc-400 font-bold mb-4 text-[10px] tracking-widest uppercase border-b border-white/10 pb-2">Live Telemetry</h3>
                
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                    <div>
                        <div className="text-[10px] text-zinc-500 font-medium mb-1">ALTITUDE (AGL)</div>
                        <div className="text-2xl text-white font-light font-mono tracking-tight">{alt.toFixed(1)}<span className="text-sm text-zinc-600 ml-1">m</span></div>
                    </div>
                    <div>
                        <div className="text-[10px] text-zinc-500 font-medium mb-1">VELOCITY</div>
                        <div className={`text-2xl font-light font-mono tracking-tight ${currentVel > neededVel * 1.5 ? 'text-rose-400' : 'text-white'}`}>{currentVel.toFixed(1)}<span className="text-sm text-zinc-600 ml-1">m/s</span></div>
                    </div>
                    <div>
                        <div className="text-[10px] text-zinc-500 font-medium mb-1">PITCH / YAW / ROLL</div>
                        <div className="text-sm text-zinc-300 font-mono tracking-tight mt-1">
                            {(telemetry.pitch * (180/Math.PI)).toFixed(1)}° / {(telemetry.yaw * (180/Math.PI)).toFixed(1)}° / {(telemetry.roll * (180/Math.PI)).toFixed(1)}°
                        </div>
                    </div>
                    <div>
                        <div className="text-[10px] text-zinc-500 font-medium mb-1">MISSION PHASE</div>
                        <div className={`text-xs font-semibold ${isCrashing ? 'text-rose-500' : 'text-blue-400'} mt-1.5`}>{phase}</div>
                    </div>
                </div>
            </div>
        )}

        {telemetry && (
            <div className={`p-6 rounded-2xl border backdrop-blur-xl shadow-2xl min-w-[220px] text-right ${borderColor} ${bgColor}`}>
                <h3 className="text-zinc-400 font-bold mb-4 text-[10px] tracking-widest uppercase border-b border-white/10 pb-2">Guidance & Nav</h3>
                
                <div className="mb-4">
                    <div className="text-[10px] text-zinc-500 font-medium mb-1">TARGET VELOCITY</div>
                    <div className="text-xl text-white font-light font-mono tracking-tight">{neededVel.toFixed(1)}<span className="text-xs text-zinc-600 ml-1">m/s</span></div>
                </div>
                
                <div className="mb-4">
                    <div className="text-[10px] text-zinc-500 font-medium mb-1">PROPELLANT MARGIN</div>
                    <div className="text-xl text-white font-light font-mono tracking-tight">14.2<span className="text-xs text-zinc-600 ml-1">%</span></div>
                </div>

                <div>
                    <div className="text-[10px] text-zinc-500 font-medium mb-1">ENGINE THRUST</div>
                    <div className="text-xl text-white font-light font-mono tracking-tight">
                        {isCrashing ? '0.0' : (alt < 5 ? '15.0' : '85.4')}<span className="text-xs text-zinc-600 ml-1">%</span>
                    </div>
                </div>
            </div>
        )}
      </div>

    </div>
  );
}
