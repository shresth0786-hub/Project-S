import "./globals.css";
export const metadata = { title: "VisionX - Video Intelligence", description: "Multimodal AI Video Intelligence & Agentic RAG" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <header className="border-b border-slate-800 sticky top-0 bg-slate-950/80 backdrop-blur z-10">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center font-bold">VX</div>
              <span className="text-xl font-semibold">VisionX</span>
              <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded">MVP</span>
            </div>
            <nav className="flex gap-4 text-sm text-slate-400">
              <a href="/" className="hover:text-white">Upload</a>
              <a href="/analytics" className="hover:text-white">Analytics</a>
              <a href="http://localhost:8000/docs" target="_blank" className="hover:text-white">API Docs</a>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
