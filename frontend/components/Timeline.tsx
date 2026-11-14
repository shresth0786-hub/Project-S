"use client";
import { useEffect, useState } from "react";
import axios from "axios";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function Timeline({ videoId }: { videoId: string }) {
  const [data, setData] = useState<any>(null);
  useEffect(()=>{ axios.get(`${API}/api/videos/${videoId}/timeline`).then(r=>setData(r.data)).catch(()=>{}); }, [videoId]);
  if (!data) return <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs text-slate-500">Loading timeline…</div>;
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h3 className="font-medium text-sm mb-3">Event Timeline — {data.duration?.toFixed(1) ?? "?"}s</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {data.events.length===0 && <p className="text-xs text-slate-500">No events yet — processing may be ongoing</p>}
        {data.events.map((e:any)=>(
          <div key={e.id} className="flex gap-3 text-xs bg-slate-800 rounded p-2">
            <span className="text-cyan-400 font-mono">{e.start_time.toFixed(1)}s</span>
            <span className="bg-amber-500/20 text-amber-300 px-1 rounded text-[10px] h-fit">{e.event_type}</span>
            <span className="text-slate-300 truncate">{e.description}</span>
            <span className="text-slate-500">{e.confidence?.toFixed(2) ?? ""}</span>
          </div>
        ))}
        {data.frames.slice(0,4).map((f:any)=>(
          <div key={f.id} className="text-xs bg-slate-800/50 rounded p-2 flex gap-2">
            <span className="text-slate-400">{f.timestamp.toFixed(1)}s</span>
            <span className="text-slate-300 truncate">{f.description?.slice(0,120)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
