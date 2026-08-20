import { useMission } from '../context/MissionContext';
import { useNavigate } from 'react-router-dom';

export function Terrain() {
  const { result } = useMission();
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="flex-grow flex items-center justify-center">
        <div className="text-zinc-500 font-medium tracking-widest text-sm uppercase">
          Data Unavailable. Please process a dataset first.
        </div>
      </div>
    );
  }

  const p = result.pipeline;

  return (
    <div className="max-w-7xl mx-auto w-full pt-32 pb-16 px-8 font-sans">
      <div className="flex justify-between items-end mb-16 border-b border-white/5 pb-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-medium text-white tracking-[0.2em] uppercase mb-4">Physical Terrain</h1>
          <p className="text-zinc-500 font-medium tracking-wide">Phase III: TMCDTM Topographic Integration</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-16">
        <div className="lg:col-span-1 space-y-12">
          <div className="border-l border-white/5 pl-8">
            <h2 className="text-zinc-300 font-bold tracking-widest uppercase mb-10 text-xs">Terrain Metadata</h2>
            
            <div className="space-y-8 text-sm font-medium">
              <div>
                <p className="text-zinc-600 tracking-widest uppercase text-[10px] font-bold mb-2">Data Source</p>
                <p className="text-zinc-100">TMCDTM (Physical DEM)</p>
              </div>
              <div>
                <p className="text-zinc-600 tracking-widest uppercase text-[10px] font-bold mb-2">Dimensions</p>
                <p className="text-zinc-300 font-mono">{p.m3?.dimensions || 'N/A'}</p>
              </div>
              <div>
                <p className="text-zinc-600 tracking-widest uppercase text-[10px] font-bold mb-2">Resolution</p>
                <p className="text-zinc-300 font-mono">{p.m3?.resolution ? `${p.m3.resolution.toFixed(6)} m/px` : 'N/A'}</p>
              </div>
              <div>
                <p className="text-zinc-600 tracking-widest uppercase text-[10px] font-bold mb-2">Elevation Range</p>
                <p className="text-zinc-300 font-mono">{p.m3?.elevation_range || 'N/A'}</p>
              </div>
              <div>
                <p className="text-zinc-600 tracking-widest uppercase text-[10px] font-bold mb-2">Integration Status</p>
                <p className="text-green-500 font-bold text-xs tracking-widest uppercase">
                  {p.m3?.status || 'N/A'}
                </p>
              </div>
            </div>
          </div>
          
          <button 
            onClick={() => navigate('/hazard-map')} 
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold tracking-widest uppercase text-xs py-4 px-8 transition-colors"
          >
            Compute Hazard Maps →
          </button>
        </div>

        <div className="lg:col-span-2 border-l border-blue-500/20 pl-12 flex flex-col justify-center min-h-[500px]">
            <div className="w-16 h-16 border-2 border-blue-500/20 border-t-blue-500 animate-spin mb-8"></div>
            <h3 className="text-white font-bold text-lg mb-2">Registration Complete</h3>
            <p className="text-zinc-500 font-medium leading-relaxed max-w-md">Physical DEM correlated in memory for Phase IV hazard extraction. The topographic mesh is now prepared for strict slope and surface roughness evaluations.</p>
        </div>
      </div>
    </div>
  );
}

