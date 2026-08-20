import { useMission } from '../context/MissionContext';
import { useNavigate } from 'react-router-dom';

export function HazardMap() {
  const { result } = useMission();
  const navigate = useNavigate();

  const globalHazardMap = (
    <div className="w-full mb-16">
        <h3 className="text-zinc-500 tracking-widest uppercase mb-8 text-xs font-bold border-b border-white/5 pb-4">Global Hazard Map Overview</h3>
        <div className="w-full bg-[#030303]">
            <img src="/global_hazard_map.png" alt="Global Hazard Map" className="w-full h-auto opacity-75 hover:opacity-100 transition-opacity" />
        </div>
    </div>
  );

  if (!result) {
    return (
      <div className="max-w-7xl mx-auto w-full py-16 px-8">
        {globalHazardMap}
        <div className="flex-grow flex items-center justify-center text-zinc-500 font-medium tracking-widest text-sm uppercase mt-12 py-12 border-t border-white/5">
          Please process a dataset in the Imagery tab to view local hazards.
        </div>
      </div>
    );
  }

  const p = result.pipeline;

  return (
    <div className="max-w-7xl mx-auto w-full pt-32 pb-16 px-8 font-sans">
      {globalHazardMap}

      <div className="mb-16 flex justify-between items-end border-b border-white/5 pb-6">
        <div>
          <h2 className="text-2xl lg:text-3xl font-medium text-white tracking-[0.2em] uppercase mb-4">Hazard Classification</h2>
          <p className="text-zinc-500 font-medium tracking-wide">Phase IV: Computed Safety Parameters</p>
        </div>
        <button 
          onClick={() => navigate('/landing-sites')}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold tracking-widest text-xs uppercase py-3 px-6 transition-colors"
        >
          View Feasible Sites →
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-16 mb-12">
        <div className="border-l border-white/5 pl-8">
          <h3 className="text-zinc-300 font-bold tracking-widest text-xs uppercase mb-8">Slope Gradient Map</h3>
          <div className="w-full bg-[#030303] flex items-center justify-center min-h-[500px]">
            <img src={`http://localhost:8000${result.slope_url || p.slope_url}`} alt="Slope Map" className="max-h-[480px] object-contain" />
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex justify-between text-xs font-bold tracking-widest uppercase">
            <span className="text-zinc-500">Threshold: &lt; {p?.m4?.max_slope || '15.4'}°</span>
            <span className="text-amber-500">Warning: Steep Terrain</span>
          </div>
        </div>
        
        <div className="border-l border-white/5 pl-8">
          <h3 className="text-zinc-300 font-bold tracking-widest text-xs uppercase mb-8">Crater/Boulder Risk Analysis</h3>
          <div className="w-full bg-[#030303] flex items-center justify-center min-h-[500px]">
            <img src={`http://localhost:8000${result.risk_url || p.risk_url}`} alt="Risk Map" className="max-h-[480px] object-contain" />
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex justify-between text-xs font-bold tracking-widest uppercase">
            <span className="text-zinc-500">Safety Threshold: {parseFloat(p?.m4?.max_risk || '0.85') * 100}%</span>
            <span className="text-rose-500">High Density Roughness</span>
          </div>
        </div>

        <div className="border-l border-blue-500/30 pl-8">
          <h3 className="text-blue-400 font-bold tracking-widest text-xs uppercase mb-8">Combined Binary Mask</h3>
          <div className="w-full bg-[#030303] flex items-center justify-center min-h-[500px]">
            <img src={`http://localhost:8000${result.binary_url || p?.binary_url || '/static/sr/binary_fallback.png'}`} alt="Binary Mask" className="max-h-[480px] object-contain" />
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex justify-between text-xs font-bold tracking-widest uppercase">
            <span className="text-zinc-500">Logical AND Filter</span>
            <span className="text-emerald-500">Safe Zones Isolated</span>
          </div>
        </div>
      </div>
    </div>
  );
}


