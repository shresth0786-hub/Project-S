"use client";
import { useEffect, useState } from "react";
import axios from "axios";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function AnalyticsDashboard({ videoId }: { videoId: string }) {
  const [timeline, setTimeline] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  useEffect(()=>{ axios.get(`${API}/api/videos/${videoId}/timeline`).then(r=>setTimeline(r.data)).catch(()=>{}); }, [videoId]);
  const gen = async (type:string) => {
    setGenerating(true);
    try { const r=await axios.post(`${API}/api/videos/${videoId}/reports`, {report_type:type}); setReport(r.data); } catch(e){} finally{ setGenerating(false);}
  };
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
      <h3 className="font-medium text-sm">Analytics & Reports</h3>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-800 rounded p-3 text-center"><div className="text-lg font-bold text-cyan-400">{timeline?.events?.length ?? 0}</div>Events</div>
        <div className="bg-slate-800 rounded p-3 text-center"><div className="text-lg font-bold text-cyan-400">{timeline?.transcript_segments?.length ?? 0}</div>Transcript segments</div>
        <div className="bg-slate-800 rounded p-3 text-center"><div className="text-lg font-bold text-cyan-400">{timeline?.frames?.length ?? 0}</div>Frames analyzed</div>
        <div className="bg-slate-800 rounded p-3 text-center"><div className="text-lg font-bold">{timeline?.duration?.toFixed(0) ?? "?" }s</div>Duration</div>
      </div>
      <div className="flex gap-2">
        <button onClick={()=>gen("summary")} disabled={generating} className="flex-1 bg-cyan-600 hover:bg-cyan-500 py-2 rounded text-xs font-medium">Summary</button>
        <button onClick={()=>gen("analytics")} disabled={generating} className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded text-xs">Analytics</button>
        <button onClick={()=>gen("sports")} disabled={generating} className="flex-1 bg-amber-600 hover:bg-amber-500 py-2 rounded text-xs">Sports</button>
      </div>
      {generating && <p className="text-xs text-slate-400">Generating…</p>}
      {report && <div className="bg-slate-800 rounded p-3 text-xs"><p className="font-semibold text-cyan-400">{report.title}</p><p className="whitespace-pre-wrap mt-2 text-slate-300">{report.content.slice(0,2000)}</p></div>}
    </div>
  );
}
