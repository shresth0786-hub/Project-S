"use client";
import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function VideoPlayer({ videoId }: { videoId: string }) {
  const src = `${API}/api/videos/${videoId}/stream`;
  const [time, setTime] = useState(0);
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <video
        controls
        src={src}
        className="w-full aspect-video bg-black"
        onTimeUpdate={(e)=>setTime((e.target as HTMLVideoElement).currentTime)}
      />
      <div className="px-4 py-2 flex justify-between text-xs text-slate-400">
        <span>Current: {time.toFixed(1)}s</span>
        <a href={src} target="_blank" className="text-cyan-400 hover:underline">Open raw</a>
      </div>
    </div>
  );
}
