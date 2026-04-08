import { useState, useEffect, useRef } from "react";
import {
  Youtube,
  Sparkles,
  Brain,
  Loader2,
  Send,
  MessageCircle,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { summarizeVideo, sendChatMessage } from "./api";
import ReactMarkdown from "react-markdown";

function App() {
  const [url, setUrl] = useState("");
  const [videoData, setVideoData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [input, setInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatLoading]);

  const onSummarize = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await summarizeVideo(url);
      setVideoData(res);
      setChatHistory([]);
    } catch (err) {
      setError(err.response?.data?.detail || "Connection Error");
    } finally {
      setLoading(false);
    }
  };

  const onChat = async (e) => {
    e.preventDefault();
    if (!input.trim() || !videoData?.video_id) return;
    const userMessage = { role: "user", content: input };
    setChatHistory((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setChatLoading(true);
    try {
      const res = await sendChatMessage(
        videoData.video_id,
        currentInput,
        chatHistory,
      );
      setChatHistory((prev) => [
        ...prev,
        { role: "model", content: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      let msg;
      if (status === 404) {
        msg = "Session expired. Please re-summarize the video.";
      } else if (status === 502) {
        msg = "AI service is temporarily unavailable. Try again in a moment.";
      } else if (detail) {
        msg = detail;
      } else {
        msg = "Connection error. Check that the backend is running.";
      }
      setChatHistory((prev) => [
        ...prev,
        { role: "model", content: `Error: ${msg}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-50 overflow-hidden">
      {/* 1. NAVBAR */}
      <nav className="h-14 px-6 border-b border-slate-200 bg-white flex items-center justify-between z-50 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="bg-red-600 p-1 rounded-md">
            <Youtube className="text-white w-4 h-4" />
          </div>
          <span className="font-black text-slate-800 tracking-tight">
            RAG <span className="text-blue-600">Analyst</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold text-slate-400 border border-slate-200 px-2 py-0.5 rounded-full">
            V2.0 STABLE
          </span>
        </div>
      </nav>

      {/* 2. MAIN CONTAINER */}
      <div className="flex-1 flex overflow-hidden max-w-[1600px] mx-auto w-full bg-white shadow-2xl shadow-slate-200">
        {/* LEFT PANEL: ANALYSIS */}
        <div className="flex-1 overflow-y-auto p-8 lg:p-12 scroll-smooth border-r border-slate-100">
          <div className="max-w-2xl mx-auto">
            <header className="mb-10 text-center lg:text-left">
              <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-3">
                Analyze Knowledge
              </h1>
              <p className="text-slate-500 font-medium">
                Deep-dive into video transcripts with contextual AI.
              </p>
            </header>

            <form onSubmit={onSummarize} className="mb-12">
              <div className="flex flex-col sm:flex-row gap-2 bg-slate-50 p-2 rounded-2xl border border-slate-200 focus-within:border-blue-500 transition-all">
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste YouTube Link..."
                  className="flex-1 bg-transparent p-3 outline-none text-slate-700 font-medium text-sm"
                />
                <button
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-100 disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="animate-spin w-4 h-4" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Summarize
                </button>
              </div>
              {error && (
                <p className="mt-3 text-red-500 text-xs font-bold text-center italic">
                  {error}
                </p>
              )}
            </form>

            {videoData ? (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-2 text-blue-600 font-bold text-[10px] uppercase tracking-widest mb-4">
                  <ShieldCheck className="w-4 h-4" /> Source Verified & Indexed
                </div>
                <h2 className="text-3xl font-black text-slate-900 mb-6 leading-tight uppercase italic underline decoration-blue-500 decoration-4 underline-offset-8">
                  {videoData.title}
                </h2>

                {/* Markdown for Summary */}
                <div className="text-slate-600 leading-relaxed mb-12 text-lg font-medium italic opacity-80 prose prose-slate max-w-none">
                  <ReactMarkdown>{videoData.summary}</ReactMarkdown>
                </div>

                <h3 className="font-bold text-slate-900 text-sm mb-6 flex items-center gap-2 border-b border-slate-100 pb-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-500" /> Key
                  Insights
                </h3>
                <div className="space-y-4">
                  {videoData.insights.map((ins, i) => (
                    <div
                      key={i}
                      className="p-6 bg-slate-50 rounded-2xl border border-slate-100 hover:border-blue-200 transition-colors group"
                    >
                      <div className="flex gap-4">
                        <span className="bg-white w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-xl shadow-sm text-xs font-black text-blue-600 border border-slate-100">
                          {i + 1}
                        </span>
                        <p className="text-sm font-semibold text-slate-700 leading-snug">
                          {ins}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-300 opacity-20">
                <Brain size={80} strokeWidth={1} />
                <p className="mt-4 font-bold uppercase tracking-widest text-xs">
                  Waiting for Analysis
                </p>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: RAG CHAT */}
        <div className="hidden lg:flex w-[450px] flex-col bg-slate-50">
          <div className="p-6 bg-white border-b border-slate-200 flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg text-white shadow-lg shadow-blue-100">
              <MessageCircle size={18} />
            </div>
            <div>
              <h3 className="font-black text-sm text-slate-800">
                Contextual Chat
              </h3>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">
                Powered by Gemini RAG
              </p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {!videoData && (
              <div className="h-full flex flex-col items-center justify-center opacity-10">
                <Youtube size={100} />
              </div>
            )}
            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[90%] p-4 rounded-2xl text-[13px] leading-relaxed shadow-md ${
                    msg.role === "user"
                      ? "bg-slate-900 text-white"
                      : "bg-white border border-slate-200 text-slate-700"
                  }`}
                >
                  {/* SENIOR FIX: Render user text as plain, AI text as Markdown */}
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <div className="prose prose-sm prose-slate max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2 px-1">
                    {msg.sources.map((sourceText, idx) => (
                      <div key={idx} className="group relative">
                        <div className="flex items-center gap-1 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-md cursor-help hover:bg-blue-100 transition-colors">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                          <span className="text-[9px] font-bold text-blue-600 uppercase tracking-tighter">
                            Source {idx + 1}
                          </span>
                        </div>
                        {/* Hover Tooltip */}
                        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block w-64 p-3 bg-slate-900 text-white text-[10px] rounded-xl shadow-2xl z-50 leading-relaxed border border-white/10 pointer-events-none">
                          <p className="opacity-60 mb-1 font-bold uppercase tracking-widest text-[8px]">
                            Transcript Excerpt:
                          </p>
                          "
                          {sourceText.length > 150
                            ? sourceText.substring(0, 150) + "..."
                            : sourceText}
                          "
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="flex flex-col items-start gap-2">
                <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" />
                  </div>
                </div>
                <span className="text-[9px] font-black text-blue-500 uppercase ml-2 tracking-widest">
                  Retrieving Knowledge...
                </span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* CHAT INPUT BAR FIX */}
          <div className="p-4 bg-white border-t border-slate-200 flex-shrink-0">
            <form
              onSubmit={onChat}
              className="flex items-center gap-2 p-1 bg-slate-100 rounded-2xl border border-slate-200 focus-within:border-blue-500 transition-all"
            >
              <input
                disabled={!videoData || chatLoading}
                className="flex-1 bg-transparent p-3 text-sm outline-none disabled:opacity-50"
                placeholder="Ask about a detail..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button
                disabled={!videoData || chatLoading}
                className="bg-blue-600 text-white p-3 rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-100 disabled:opacity-50 flex-shrink-0"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
