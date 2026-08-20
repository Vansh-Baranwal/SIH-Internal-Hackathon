import React, { useState } from 'react';

interface OrbitalPlannerProps {
  onClose: () => void;
  onExecute: (x: number, z: number) => void;
}

export function OrbitalPlanner({ onClose, onExecute }: OrbitalPlannerProps) {
  const [targetX, setTargetX] = useState(0);
  const [targetZ, setTargetZ] = useState(0);

  const handleXChange = (e: any) => setTargetX(parseFloat(e.target.value));
  const handleZChange = (e: any) => setTargetZ(parseFloat(e.target.value));

  // SVG Drawing variables
  const cx = 300, cy = 300; 
  const r = 120; 
  
  const visualTargetX = cx + (targetX * 0.15); 
  const visualTargetY = cy - r - (targetZ * 0.05); 

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-[#050505]/80 backdrop-blur-xl p-8 font-sans">
      <div className="border border-white/10 bg-[#0a0a0a] w-full max-w-5xl h-full flex shadow-2xl rounded-2xl overflow-hidden">
        
        {/* LEFT PANEL: 2D Interactive Orbital Map */}
        <div className="flex-grow relative border-r border-white/5 bg-zinc-950">
          <h2 className="absolute top-6 left-6 text-zinc-300 font-bold tracking-wide text-lg">Lunar Orbital Dynamics Planner</h2>
          
          <svg width="100%" height="100%" viewBox="0 0 600 600" className="absolute inset-0">
            {/* Elliptical Parking Orbit */}
            <ellipse cx={cx} cy={cy} rx="250" ry="180" fill="none" stroke="#3b82f6" strokeWidth="1" strokeDasharray="6 6" opacity="0.4" />
            <text x="50" y="300" fill="#3b82f6" fontSize="10" opacity="0.6" className="font-medium tracking-widest">100km APOLUNE</text>
            <text x="300" y="110" fill="#3b82f6" fontSize="10" opacity="0.6" textAnchor="middle" className="font-medium tracking-widest">30km PERILUNE</text>
            
            {/* The Full Moon */}
            <circle cx={cx} cy={cy} r={r} fill="#18181b" stroke="#27272a" strokeWidth="2" />
            
            {/* Crater details */}
            <circle cx={cx-40} cy={cy-20} r="15" fill="none" stroke="#27272a" strokeWidth="1.5" />
            <circle cx={cx+30} cy={cy+40} r="25" fill="none" stroke="#27272a" strokeWidth="1.5" />
            <circle cx={cx+50} cy={cy-30} r="10" fill="none" stroke="#27272a" strokeWidth="1.5" />

            {/* Spacecraft */}
            <circle cx={50} cy={300} r="4" fill="#fff" className="drop-shadow-md" />
            <text x="62" y="303" fill="#fff" fontSize="10" className="font-medium tracking-wider drop-shadow-sm">ORBITER</text>

            {/* Descent Trajectory Curve */}
            <path 
              d={`M 50 300 Q ${cx} 100 ${visualTargetX} ${visualTargetY}`} 
              fill="none" 
              stroke="#10b981" 
              strokeWidth="2" 
              strokeDasharray="4 4"
            />

            {/* Landing Target Reticle */}
            <g transform={`translate(${visualTargetX}, ${visualTargetY})`}>
              <circle cx="0" cy="0" r="6" fill="none" stroke="#10b981" strokeWidth="2" />
              <line x1="-10" y1="0" x2="10" y2="0" stroke="#10b981" strokeWidth="1.5" />
              <line x1="0" y1="-10" x2="0" y2="10" stroke="#10b981" strokeWidth="1.5" />
            </g>
          </svg>
        </div>

        {/* RIGHT PANEL: Controls */}
        <div className="w-[400px] p-8 flex flex-col justify-between bg-zinc-950/50">
          <div>
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-zinc-300 font-semibold tracking-wide text-lg">Trajectory Override</h3>
              <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors bg-white/5 hover:bg-white/10 w-8 h-8 rounded-full flex items-center justify-center">✕</button>
            </div>

            <p className="text-sm text-zinc-500 mb-10 leading-relaxed font-medium">
              Use the orbital diversion parameters below to dynamically alter the descent trajectory. 
              The physics engine will recalculate the parabolic entry curve.
            </p>

            <div className="mb-8">
              <label className="flex justify-between text-zinc-400 text-xs mb-3 font-semibold tracking-wide uppercase">
                <span>Cross-Track (X)</span>
                <span className="font-mono text-zinc-300">{targetX.toFixed(1)} m</span>
              </label>
              <input 
                type="range" min="-400" max="400" step="1" 
                value={targetX} onChange={handleXChange}
                className="w-full accent-blue-500 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div className="mb-10">
              <label className="flex justify-between text-zinc-400 text-xs mb-3 font-semibold tracking-wide uppercase">
                <span>Downrange (Z)</span>
                <span className="font-mono text-zinc-300">{targetZ.toFixed(1)} m</span>
              </label>
              <input 
                type="range" min="-600" max="600" step="1" 
                value={targetZ} onChange={handleZChange}
                className="w-full accent-blue-500 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div className="p-5 border border-amber-500/20 bg-amber-500/5 rounded-xl">
              <h4 className="text-[11px] text-amber-500 font-bold tracking-widest uppercase mb-2">Awaiting Verification</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-medium">
                The 3D Raycaster will verify landing zone slope and altitude upon execution. 
                If the terrain exceeds 10° slope, the lander will crash.
              </p>
            </div>
          </div>

          <button 
            onClick={() => onExecute(targetX, targetZ)}
            className="w-full py-4 rounded-xl font-semibold tracking-wide text-sm transition-all shadow-lg bg-blue-600 hover:bg-blue-500 text-white"
          >
            Execute Divert Maneuver
          </button>
        </div>

      </div>
    </div>
  );
}
