"use client";
import { useState, useCallback } from "react";
import VideoUploader from "@/components/VideoUploader";
import ProcessingDashboard from "@/components/ProcessingDashboard";
import VideoPlayer from "@/components/VideoPlayer";
import ChatInterface from "@/components/ChatInterface";
import Timeline from "@/components/Timeline";
import AnalyticsDashboard from "@/components/AnalyticsDashboard";

export default function Home() {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "analytics">("chat");

  const handleUploadSuccess = useCallback((vid: string, jid: string) => {
    setVideoId(vid);
    setJobId(jid);
  }, []);

  return (
    <div className="space-y-8">
      <div className="text-center py-6">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">VisionX</h1>
        <p className="text-slate-400 mt-2">Upload any video → Get timestamped, evidence-grounded answers</p>
      </div>

      {!videoId ? (
        <VideoUploader onSuccess={handleUploadSuccess} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <VideoPlayer videoId={videoId} />
            {jobId && <ProcessingDashboard jobId={jobId} videoId={videoId} />}
            <Timeline videoId={videoId} />
          </div>
          <div className="space-y-4">
            <div className="flex gap-2">
              <button onClick={() => setActiveTab("chat")} className={`px-4 py-2 rounded text-sm ${activeTab==="chat"?"bg-cyan-600":"bg-slate-800"}`}>Chat</button>
              <button onClick={() => setActiveTab("analytics")} className={`px-4 py-2 rounded text-sm ${activeTab==="analytics"?"bg-cyan-600":"bg-slate-800"}`}>Analytics</button>
              <button onClick={() => {setVideoId(null); setJobId(null);}} className="px-4 py-2 rounded text-sm bg-slate-800">New Upload</button>
            </div>
            {activeTab==="chat" ? <ChatInterface videoId={videoId} /> : <AnalyticsDashboard videoId={videoId} />}
          </div>
        </div>
      )}
      <div className="grid grid-cols-3 gap-4 text-center text-xs text-slate-500 pt-8 border-t border-slate-800">
        <div><div className="text-cyan-400 font-semibold">Multimodal RAG</div>pgvector + hybrid + rerank</div>
        <div><div className="text-cyan-400 font-semibold">Agentic</div>LangGraph Supervisor → 5 agents</div>
        <div><div className="text-cyan-400 font-semibold">Evidence-Grounded</div>Never hallucinate timestamps</div>
      </div>
    </div>
  );
}
