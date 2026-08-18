import { useState } from 'react';

export function UploadTMC({ onUploadComplete }: { onUploadComplete: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/pipeline/run', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setUploading(false);
    }
  };

  if (result) {
    const p = result.pipeline;
    const m5A = p.m5?.lander_A;
    const m5B = p.m5?.lander_B;
    const m6 = p.m6;

    return (
      <div className="absolute inset-0 z-50 flex items-center justify-center bg-black bg-opacity-95 text-white font-mono p-4">
        <div className="max-w-6xl w-full h-full overflow-y-auto pr-4 pb-20">
          <h1 className="text-4xl text-cyan-400 mb-8 font-bold border-b border-cyan-700 pb-2">LUNAR LANDING HAZARD ANALYSIS</h1>
          
          <div className="mb-8">
            <h2 className="text-2xl text-cyan-300 mb-2">INPUT</h2>
            <div className="flex gap-4">
              <span className="px-3 py-1 bg-gray-800 border border-gray-600">TMC Scene (Optical)</span>
              <span className="px-3 py-1 bg-gray-800 border border-gray-600">TMCDTM (Physical DEM Terrain)</span>
            </div>
          </div>

          <div className="mb-8 border-l-2 border-cyan-800 pl-4">
            <h2 className="text-2xl text-cyan-300 mb-2">SUPER RESOLUTION (M2)</h2>
            <p className="text-gray-300">CSASR Model (32x Optical Enhancement) - Inference: {result.inference_time_ms} ms</p>
          </div>

          <div className="mb-8 border-l-2 border-cyan-800 pl-4">
            <h2 className="text-2xl text-cyan-300 mb-2">TERRAIN (M3)</h2>
            <p className="text-gray-300">Physical DEM Generated. Dimensions: {p.m3?.dimensions} | Resolution: {(p.m3?.resolution || 0).toFixed(4)}m</p>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl text-cyan-300 mb-4">HAZARD (M4)</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 mb-1">SR Optical (M2)</p>
                <img src={`http://localhost:8000${result.sr_url}`} className="w-full h-auto border border-gray-600" alt="SR Optical" />
              </div>
              <div>
                <p className="text-gray-400 mb-1">Slope Map (Max: {p.m4?.max_slope}°)</p>
                {result.slope_url && <img src={`http://localhost:8000${result.slope_url}`} className="w-full h-auto border border-gray-600" alt="Slope Map" />}
              </div>
              <div>
                <p className="text-gray-400 mb-1">Risk Map (Max: {p.m4?.max_risk})</p>
                {result.risk_url && <img src={`http://localhost:8000${result.risk_url}`} className="w-full h-auto border border-gray-600" alt="Risk Map" />}
              </div>
              <div>
                <p className="text-gray-400 mb-1">Safe/Unsafe Map (Binary Mask)</p>
                {result.binary_url && <img src={`http://localhost:8000${result.binary_url}`} className="w-full h-auto border border-gray-600" alt="Binary Map" />}
              </div>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl text-cyan-300 mb-4">LANDER ANALYSIS (M5)</h2>
            
            <div className="mb-4">
                <p className="text-gray-300 mb-2 text-lg">Feasible Sites Map Overlay:</p>
                <div className="flex gap-6 mb-2 text-sm">
                    <span className="flex items-center gap-2"><span className="w-3 h-3 bg-green-500 rounded-full inline-block"></span> Lander A ({m5A?.name})</span>
                    <span className="flex items-center gap-2"><span className="w-3 h-3 bg-blue-500 rounded-full inline-block"></span> Lander B ({m5B?.name})</span>
                    <span className="flex items-center gap-2"><span className="w-3 h-3 bg-yellow-400 rounded-full inline-block"></span> Both</span>
                    <span className="flex items-center gap-2"><span className="w-4 h-4 text-white font-bold">+</span> Best Candidate</span>
                </div>
                {result.sites_url && <img src={`http://localhost:8000${result.sites_url}`} className="w-full max-w-2xl h-auto border border-cyan-700 shadow-[0_0_15px_rgba(0,255,255,0.2)]" alt="Sites Map" />}
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="p-4 bg-gray-900 border border-gray-700">
                <h3 className="text-xl text-cyan-200 mb-2 font-bold">LANDER A ({m5A?.name || 'Unknown'})</h3>
                <p className="mb-1">Feasible Sites: <span className="text-white font-bold">{m5A?.feasible_sites || 0}</span></p>
                <p className="mb-2">Status: <span className={m5A?.feasible_sites > 0 ? 'text-green-400' : 'text-red-400'}>{m5A?.feasible_sites > 0 ? 'FEASIBLE' : 'NO FEASIBLE SITE'}</span></p>
                {m5A?.best_site && (
                    <div className="text-sm text-gray-400">
                        <p>Best Candidate: {m5A.best_site.site_id}</p>
                        <p>Location: X={m5A.best_site.x.toFixed(1)}, Y={m5A.best_site.y.toFixed(1)}</p>
                        <p>Score: {m5A.best_site.score.toFixed(3)}</p>
                    </div>
                )}
              </div>
              <div className="p-4 bg-gray-900 border border-gray-700">
                <h3 className="text-xl text-cyan-200 mb-2 font-bold">LANDER B ({m5B?.name || 'Unknown'})</h3>
                <p className="mb-1">Feasible Sites: <span className="text-white font-bold">{m5B?.feasible_sites || 0}</span></p>
                <p className="mb-2">Status: <span className={m5B?.feasible_sites > 0 ? 'text-green-400' : 'text-red-400'}>{m5B?.feasible_sites > 0 ? 'FEASIBLE' : 'NO FEASIBLE SITE'}</span></p>
                {m5B?.best_site && (
                    <div className="text-sm text-gray-400">
                        <p>Best Candidate: {m5B.best_site.site_id}</p>
                        <p>Location: X={m5B.best_site.x.toFixed(1)}, Y={m5B.best_site.y.toFixed(1)}</p>
                        <p>Score: {m5B.best_site.score.toFixed(3)}</p>
                    </div>
                )}
              </div>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl text-cyan-300 mb-4">MISSION PLANNING (M6)</h2>
            <div className="p-4 bg-gray-900 border border-gray-700">
                <p className="mb-2"><span className="text-gray-400">Selected Lander:</span> {m5A?.name || 'Lander A'}</p>
                <p className="mb-2"><span className="text-gray-400">Selected Site:</span> {m6?.trajectory?.selected_site?.siteId || 'None'}</p>
                
                {m6?.status === 'blocked' || m6?.status === 'no_candidates' ? (
                    <div className="mt-4 border-l-4 border-red-500 pl-4 py-2 bg-red-900 bg-opacity-20">
                        <p className="text-xl text-red-400 font-bold mb-1">REACHABILITY: BLOCKED / INFEASIBLE</p>
                        <p className="text-gray-300 mb-1">TRAJECTORY NOT GENERATED</p>
                        <p className="text-gray-300">Reason: {m6?.trajectory?.reason || 'No feasible landing sites available'}</p>
                    </div>
                ) : (
                    <div className="mt-4 border-l-4 border-green-500 pl-4 py-2 bg-green-900 bg-opacity-20">
                        <p className="text-xl text-green-400 font-bold mb-1">REACHABILITY: SUCCESS</p>
                        <p className="text-gray-300 mb-1">Required Δv: {m6?.trajectory?.delta_v?.toFixed(1)} m/s</p>
                    </div>
                )}
            </div>
          </div>

          <button 
            className="mt-6 px-8 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold tracking-wide"
            onClick={onUploadComplete}
          >
            CONTINUE TO 3D MISSION DESCENT
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 text-white font-mono">
      <div className="p-8 border border-cyan-500 bg-gray-900 max-w-lg w-full">
        <h2 className="text-2xl mb-4 text-cyan-400">Initialize Mission: Upload TMC</h2>
        <input 
          type="file" 
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4"
          accept=".tif,.tiff,.png"
        />
        <button 
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-2 ${!file || uploading ? 'bg-gray-600' : 'bg-cyan-600 hover:bg-cyan-500'}`}
        >
          {uploading ? 'RUNNING DUAL PIPELINE (M2-M6)...' : 'PROCESS FULL PIPELINE'}
        </button>
      </div>
    </div>
  );
}
