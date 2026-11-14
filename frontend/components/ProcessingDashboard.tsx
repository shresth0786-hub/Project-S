"use client";
import { useEffect, useState } from "react";
import axios from "axios";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function ProcessingDashboard({ jobId, videoId }: { jobId: string; videoId: string }) {
  const [job, setJob] = useState<any>(null);
  useEffect(()=>{
    let id = setInterval(async()=>{
      try {
        const res = await axios.get(`${API}/api/jobs/${jobId}`);
        setJob(res.data);
        if (res.data.status==="completed" || res.data.status==="failed") clearInterval(id);
      } catch {}
    }, 1500);
    return ()=>clearInterval(id);
  }, [jobId]);
  if (!job) return <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-400">Queued…</div>;
  const pct = job.progress || 0;
  const isDone = job.status==="completed";
  const isFailed = job.status==="failed";
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{job.current_step}</span>
        <span className={isDone?"text-green-400":isFailed?"text-red-400":"text-cyan-400"}>{job.status} — {pct}%</span>
      </div>
      <div className="w-full bg-slate-800 rounded h-2 mt-2"><div className={`h-2 rounded ${isFailed?"bg-red-500":isDone?"bg-green-500":"bg-cyan-500"}`} style={{width:`${pct}%`}} /></div>
      {job.error && <p className="text-xs text-red-400 mt-2">{job.error}</p>}
      {isDone && <p className="text-xs text-green-400 mt-2">✓ Ready for chat, timeline & reports</p>}
    </div>
  );
}
