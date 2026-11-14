"use client";
import { useCallback, useState } from "react";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VideoUploader({ onSuccess }: { onSuccess: (vid:string, jid:string)=>void }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onFile = async (file: File) => {
    setError(null);
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await axios.post(`${API}/api/videos`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) setProgress(Math.round((e.loaded * 100) / e.total));
        }
      });
      onSuccess(res.data.video_id, res.data.job_id);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
      <div
        className="border-2 border-dashed border-slate-700 rounded-xl p-12 text-center hover:border-cyan-500/50 transition"
        onDragOver={(e)=>e.preventDefault()}
        onDrop={(e)=>{e.preventDefault(); const f=e.dataTransfer.files[0]; if(f) onFile(f);}}
      >
        <div className="text-3xl mb-4">🎬</div>
        <p className="text-slate-300 font-medium">Drag & drop video here</p>
        <p className="text-slate-500 text-sm mt-1">MP4, MOV, MKV, WebM, AVI — up to 500MB</p>
        <label className="inline-block mt-4 bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg cursor-pointer text-sm font-medium">
          Browse Files
          <input type="file" className="hidden" accept="video/*" onChange={(e)=>{const f=e.target.files?.[0]; if(f) onFile(f);}} />
        </label>
        {uploading && <div className="mt-4"><div className="w-full bg-slate-800 rounded h-2"><div className="bg-cyan-500 h-2 rounded" style={{width:`${progress}%`}} /></div><p className="text-xs text-slate-400 mt-2">{progress}% uploading…</p></div>}
        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
      </div>
      <div className="mt-6 bg-slate-800/50 rounded-lg p-4 text-xs text-slate-400">
        <p className="font-semibold text-slate-300 mb-1">What happens next?</p>
        <ol className="list-decimal ml-4 space-y-1">
          <li>FFmpeg extracts audio → Whisper transcribes with timestamps</li>
          <li>OpenCV samples frames → Vision model describes scenes</li>
          <li>YOLO detects objects → Events indexed</li>
          <li>Embeddings → pgvector hybrid RAG ready for chat</li>
        </ol>
      </div>
    </div>
  );
}
