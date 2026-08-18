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
      // Must use explicit localhost if running separated, or relative if proxied
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
    return (
      <div className="absolute inset-0 z-50 flex items-center justify-center bg-black bg-opacity-95 text-white font-mono p-4">
        <div className="max-w-6xl w-full h-full overflow-y-auto">
          <h2 className="text-3xl text-cyan-400 mb-4">Lunar Hazard Mapper Pipeline Complete</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-cyan-300">SR Optical (M2)</p>
              <img src={`http://localhost:8000${result.sr_url}`} className="w-full h-auto border border-gray-600" alt="SR Optical" />
            </div>
            <div>
              <p className="text-cyan-300">Slope Map (M4)</p>
              {result.slope_url ? (
                <img src={`http://localhost:8000${result.slope_url}`} className="w-full h-auto border border-gray-600" alt="Slope Map" />
              ) : (
                <div className="w-full h-48 flex items-center justify-center border border-gray-600 text-gray-500">Not available</div>
              )}
            </div>
            <div>
              <p className="text-cyan-300">Risk Map (M4)</p>
              {result.risk_url ? (
                <img src={`http://localhost:8000${result.risk_url}`} className="w-full h-auto border border-gray-600" alt="Risk Map" />
              ) : (
                <div className="w-full h-48 flex items-center justify-center border border-gray-600 text-gray-500">Not available</div>
              )}
            </div>
            <div>
              <p className="text-cyan-300">Safe/Unsafe Map (M4)</p>
              {result.binary_url ? (
                <img src={`http://localhost:8000${result.binary_url}`} className="w-full h-auto border border-gray-600" alt="Binary Map" />
              ) : (
                <div className="w-full h-48 flex items-center justify-center border border-gray-600 text-gray-500">Not available</div>
              )}
            </div>
          </div>
          <div className="mt-4 p-4 bg-gray-900 border border-gray-700 grid grid-cols-2 gap-4">
            <div>
              <p>Inference Time: {result.inference_time_ms} ms</p>
              <p>M4 Max Slope: {result.pipeline.m4.max_slope}°</p>
              <p>M4 Max Risk: {result.pipeline.m4.max_risk}</p>
            </div>
            <div>
              <p>M6 Status: {result.pipeline.m6.status.toUpperCase()}</p>
              {result.pipeline.m6.trajectory?.reason && (
                <p className="text-red-400">{result.pipeline.m6.trajectory.reason}</p>
              )}
              <p>Maneuver Cost: {result.pipeline.m6.trajectory?.delta_v ? `${result.pipeline.m6.trajectory.delta_v.toFixed(1)} m/s` : "N/A"}</p>
            </div>
          </div>
          <button 
            className="mt-6 mb-10 px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white"
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

