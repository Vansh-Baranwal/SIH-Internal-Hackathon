import { useState } from 'react';
import { useMission } from '../context/MissionContext';
import { useNavigate } from 'react-router-dom';

export function Imagery() {
  const { result, setResult } = useMission();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

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

  return (
    <div className="max-w-7xl mx-auto w-full pt-32 pb-16 px-8 font-sans">
      <div className="mb-16 pb-8 border-b border-white/5">
        <h1 className="text-2xl lg:text-3xl font-medium text-white tracking-[0.2em] uppercase mb-4">Optical Processing</h1>
        <p className="text-zinc-500 font-medium tracking-wide">Upload orbital imagery for AI Super-Resolution enhancement.</p>
      </div>

      {!result ? (
        <div className="flex flex-col items-start border-l border-white/5 pl-8 py-4">
          <h2 className="text-sm font-bold text-zinc-300 tracking-widest uppercase mb-8">Data Ingestion</h2>
          <input 
            type="file" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="mb-8 text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-500/10 file:text-blue-400 hover:file:bg-blue-500/20 cursor-pointer"
          />
          <button 
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`px-8 py-3 rounded font-bold tracking-wide uppercase transition-all ${
              !file || uploading 
                ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-500 text-white'
            }`}
          >
            {uploading ? 'Processing Data...' : 'Run Pipeline'}
          </button>
          {uploading && (
            <p className="mt-6 text-blue-400 font-mono text-sm animate-pulse tracking-widest">
              INITIALIZING NEURAL NETWORKS...
            </p>
          )}
        </div>
      ) : (
        <div className="w-full">
          <div className="flex justify-between items-end mb-12 border-b border-white/5 pb-6">
            <h2 className="text-2xl font-bold text-white tracking-tight">Enhancement Results</h2>
            <button 
              onClick={() => navigate('/hazard-map')}
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-6 rounded transition-colors"
            >
              Analyze Terrain Hazards →
            </button>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-16">
            {/* Original Input */}
            <div className="border-l border-white/5 pl-8">
              <h3 className="text-zinc-500 font-bold tracking-widest text-xs uppercase mb-6">Original Orbital Telemetry (32m/px)</h3>
              <div className="w-full bg-[#030303] flex items-center justify-center min-h-[400px]">
                <img 
                  src={`http://localhost:8000${(result.original_url || result.pipeline?.original_url)}`} 
                  alt="Original" 
                  className="max-h-[700px] object-contain opacity-75 grayscale" 
                />
              </div>
            </div>

            {/* Super Resolution */}
            <div className="border-l border-blue-500/30 pl-8 relative">
              <h3 className="text-blue-400 font-bold tracking-widest text-xs uppercase mb-6">Phase II: Super Resolution (1m/px)</h3>
              <div className="w-full bg-[#030303] flex items-center justify-center min-h-[400px]">
                <img 
                  src={`http://localhost:8000${(result.sr_url || result.pipeline?.sr_url)}`} 
                  alt="Super Resolution" 
                  className="max-h-[700px] object-contain" 
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


