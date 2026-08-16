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
      const res = await fetch('http://localhost:8000/api/upload_tmc', {
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
      <div className="absolute inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 text-white font-mono p-10">
        <div className="max-w-4xl w-full">
          <h2 className="text-3xl text-cyan-400 mb-4">M2: Lunar CSASR Super-Resolution Complete</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p>Original TMC (1x)</p>
              <img src={`http://localhost:8000${result.original_url}`} className="w-full h-auto border border-gray-600" />
            </div>
            <div>
              <p>Super-Resolved Output ({result.scale_factor})</p>
              <img src={`http://localhost:8000${result.sr_url}`} className="w-full h-auto border border-cyan-500" />
            </div>
          </div>
          <div className="mt-4 p-4 bg-gray-900 border border-gray-700">
            <p>Inference Time: {result.inference_time_ms} ms</p>
            <p>Status: {result.ready_for_m3 ? 'READY FOR M3 HAZARD DETECTION' : 'ERROR'}</p>
          </div>
          <button 
            className="mt-6 px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white"
            onClick={onUploadComplete}
          >
            CONTINUE TO M3 (MISSION DESCENT)
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
          {uploading ? 'RUNNING CSASR (M2)...' : 'PROCESS M2 SUPER-RESOLUTION'}
        </button>
      </div>
    </div>
  );
}
