"use client";
import { useState } from "react";
import axios from "axios";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function ChatInterface({ videoId }: { videoId: string }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input };
    setMessages((m)=>[...m, userMsg]);
    const q = input;
    setInput("");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/videos/${videoId}/chat`, { message: q, session_id: sessionId, top_k: 5 });
      setSessionId(res.data.session_id);
      setMessages((m)=>[...m, { role: "assistant", content: res.data.answer, citations: res.data.citations, has_evidence: res.data.has_sufficient_evidence }]);
    } catch (e:any) {
      setMessages((m)=>[...m, { role:"assistant", content: "Error: "+(e?.response?.data?.detail||e.message)}]);
    } finally { setLoading(false); }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl flex flex-col h-[520px]">
      <div className="p-3 border-b border-slate-800 text-sm font-medium">AI Chat — Evidence-Grounded</div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length===0 && <div className="text-xs text-slate-500 space-y-1"><p>Try:</p><ul className="list-disc ml-4"><li>What happened at 12:45?</li><li>Summarize the key events</li><li>Show me all goals (sports mode)</li><li>What did the speaker say about…?</li></ul></div>}
        {messages.map((m,i)=>(
          <div key={i} className={`${m.role==="user"?"bg-cyan-600/20 ml-8":"bg-slate-800 mr-2"} rounded-lg p-3 text-sm`}>
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.citations && m.citations.length>0 && (
              <div className="mt-2 border-t border-slate-700 pt-2 space-y-1">
                <p className="text-xs font-semibold text-cyan-400">Evidence ({m.citations.length}):</p>
                {m.citations.map((c:any, idx:number)=>(
                  <div key={idx} className="text-xs bg-slate-900 rounded p-2">
                    <span className="text-cyan-300">[{c.timestamp ?? c.start_time ?? "?"}s]</span> <span className="text-slate-500">({c.chunk_type})</span> {c.content.slice(0,180)}
                  </div>
                ))}
                {!m.has_evidence && <p className="text-xs text-amber-400">⚠ Insufficient evidence — answer may be uncertain</p>}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="text-xs text-slate-400">VisionX agents reasoning…</div>}
      </div>
      <div className="p-3 border-t border-slate-800 flex gap-2">
        <input value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={(e)=>e.key==="Enter"&&send()} placeholder="Ask about video content with timestamps…" className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-cyan-500" />
        <button onClick={send} disabled={loading} className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">Send</button>
      </div>
    </div>
  );
}
