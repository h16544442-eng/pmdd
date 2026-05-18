import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Play, 
  Terminal, 
  FileText, 
  Download, 
  CheckCircle2, 
  Loader2, 
  BarChart3,
  Cpu,
  Layers,
  Database,
  ArrowRight,
  KeyRound,
  ShieldCheck
} from 'lucide-react';

const DEFAULT_API = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || window.location.origin;

const getErrorMessage = (err) => {
  const detail = err?.response?.data?.detail || err?.response?.data?.error || err?.message;
  return typeof detail === "string" ? detail : "Request failed.";
};

const App = () => {
  const [apiBase] = useState(DEFAULT_API);
  const [file, setFile] = useState(null);
  const [corpusName, setCorpusName] = useState("Political Speech Corpus");
  const [analysisLimit, setAnalysisLimit] = useState(5);
  const [sessionId, setSessionId] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [isSystemKeyConfigured, setIsSystemKeyConfigured] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiKeyStatus, setApiKeyStatus] = useState("idle"); // idle | checking | active | error
  const [apiKeyMessage, setApiKeyMessage] = useState("Enter your OpenAI key and activate it.");
  const [isUploading, setIsUploading] = useState(false);

  // Auto-check for system key when apiBase changes
  useEffect(() => {
    const checkKey = async () => {
      try {
        const res = await fetch(`${apiBase}/session/check-key`);
        const data = await res.json();
        setIsSystemKeyConfigured(data.configured);
      } catch (e) {
        setIsSystemKeyConfigured(false);
      }
    };
    if (apiBase) checkKey();
  }, [apiBase]);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const [activeTab, setActiveTab] = useState("synthesis"); // synthesis | agent1 | agent2 | agent3 | agent4
  const hasActiveKey = apiKeyStatus === "active" || isSystemKeyConfigured;
  
  const [agents, setAgents] = useState([
    { id: 1, name: "Preprocessor", icon: <Cpu />, status: "idle", description: "Cleaning & Segmentation", key: "agent1" },
    { id: 2, name: "Pragmatic Analyst", icon: <Layers />, status: "idle", description: "Meaning Drift Detection", key: "agent2" },
    { id: 3, name: "Semantic Detector", icon: <Database />, status: "idle", description: "Register Shift Analysis", key: "agent3" },
    { id: 4, name: "Statistical Analyst", icon: <BarChart3 />, status: "idle", description: "Quantitative Variance", key: "agent4" },
    { id: 5, name: "Orchestrator", icon: <FileText />, status: "idle", description: "Report Synthesis", key: "orchestrator" },
  ]);

  const logEndRef = useRef(null);

  useEffect(() => {
    initSession();
    checkApiKeyStatus();
  }, []);

  const checkApiKeyStatus = async () => {
    try {
      const res = await axios.get(`${apiBase}/config/api-key-status`);
      setIsSystemKeyConfigured(res.data.is_configured);
    } catch (err) {}
  };

  const initSession = async () => {
    try {
      const res = await axios.post(`${apiBase}/session/create`);
      setSessionId(res.data.session_id);
      return res.data.session_id;
    } catch (err) {
      console.error("Session init failed", err);
      return null;
    }
  };

  const ensureSession = async () => {
    if (sessionId) return sessionId;
    return await initSession();
  };

  const activateApiKey = async () => {
    const activeSessionId = await ensureSession();
    if (!activeSessionId) {
      setApiKeyStatus("error");
      setApiKeyMessage("Could not create an analysis session.");
      return;
    }
    if (!apiKey.trim()) {
      setApiKeyStatus("error");
      setApiKeyMessage("Paste your OpenAI API key first.");
      return;
    }

    setApiKeyStatus("checking");
    setApiKeyMessage("Checking key with OpenAI...");

    const formData = new FormData();
    formData.append("api_key", apiKey.trim());

    try {
      const res = await axios.post(`${apiBase}/session/${activeSessionId}/api-key`, formData);
      setApiKeyStatus(res.data.active ? "active" : "error");
      setApiKeyMessage(res.data.message || "API key is active.");
      await refreshSession(activeSessionId);
    } catch (err) {
      setApiKeyStatus("error");
      setApiKeyMessage(getErrorMessage(err));
      await refreshSession(activeSessionId);
    }
  };

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;
    const activeSessionId = await ensureSession();
    if (!activeSessionId) {
      alert("Could not create an analysis session.");
      return;
    }
    setFile(uploadedFile);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', uploadedFile);

    try {
      await axios.post(`${apiBase}/session/${activeSessionId}/upload`, formData);
      await refreshSession(activeSessionId);
    } catch (err) {
      setFile(null);
      alert(`File upload failed: ${getErrorMessage(err)}`);
    } finally {
      setIsUploading(false);
    }
  };

  const refreshSession = async (id = sessionId) => {
    if (!id) return;
    const res = await axios.get(`${apiBase}/session/${id}`);
    setSessionData(res.data);
  };

  const runAgent = async (agentId) => {
    if (!sessionId) return;
    if (!hasActiveKey) {
      alert("Please activate your OpenAI API key first.");
      return false;
    }
    setAgents(prev => prev.map(a => a.id === agentId ? { ...a, status: "loading" } : a));

    try {
      let endpoint = `${apiBase}/agent/${agentId}/${sessionId}`;
      let params = {};
      
      if (agentId === 2 || agentId === 3) params.limit = analysisLimit;
      if (agentId === 5) params.corpus_name = corpusName;

      const res = await axios.post(endpoint, null, { params });
      if (res.data?.error) {
        throw new Error(res.data.error);
      }
      
      setAgents(prev => prev.map(a => a.id === agentId ? { ...a, status: "completed" } : a));
      refreshSession();
      
      // Auto-switch tab to see result
      if (agentId === 1) setActiveTab("agent1");
      if (agentId === 2) setActiveTab("agent2");
      if (agentId === 3) setActiveTab("agent3");
      if (agentId === 4) setActiveTab("agent4");
      if (agentId === 5) setActiveTab("synthesis");

      return true;
    } catch (err) {
      setAgents(prev => prev.map(a => a.id === agentId ? { ...a, status: "error" } : a));
      await refreshSession();
      alert(`Agent ${agentId} failed: ${getErrorMessage(err)}`);
      return false;
    }
  };

  const runCompletePipeline = async () => {
    if (!hasActiveKey) {
      alert("Please activate your OpenAI API key first.");
      return;
    }
    if (!file) {
      alert("Please upload a corpus first.");
      return;
    }
    setIsPipelineRunning(true);
    
    // Execute agents in sequence
    const sequence = [1, 2, 4, 3, 5]; // Note: Agent 4 can run after 1, Agent 3 needs 2
    for (let id of sequence) {
      const success = await runAgent(id);
      if (!success) {
        setIsPipelineRunning(false);
        return;
      }
    }
    setIsPipelineRunning(false);
  };

  return (
    <div className="min-h-screen flex text-slate-100 overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-72 glass-panel m-4 flex flex-col items-center py-8 gap-6 border-r border-white/5">
        <div className="flex items-center gap-3 px-6">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
            <Cpu className="text-white" size={24} />
          </div>
          <span className="font-bold text-xl tracking-tight uppercase">PMDD <span className="text-primary">Core</span></span>
        </div>

        <div className="w-full px-6 space-y-4">
            {/* Server Connection Module */}
            <div className="bg-white/5 rounded-xl p-3 border border-white/5 space-y-2">
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${isSystemKeyConfigured ? "bg-emerald-400" : "bg-amber-400"}`} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Server Link</span>
              </div>
              <div className="w-full bg-black/30 border border-white/5 rounded-lg px-2 py-2 text-[10px] font-medium text-primary truncate">
                {apiBase}
              </div>
              <div className={`text-[8px] italic leading-tight ${isSystemKeyConfigured ? "text-emerald-400" : "text-amber-400"}`}>
                {hasActiveKey ? "OpenAI key is active." : "OpenAI key is not active."}
              </div>
            </div>
            <div className="bg-white/5 rounded-xl p-3 border border-white/5 space-y-3">
              <div className="flex items-center gap-2">
                <KeyRound size={14} className="text-primary" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">API Key</span>
                {apiKeyStatus === "active" && <ShieldCheck size={14} className="ml-auto text-emerald-400" />}
              </div>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  if (apiKeyStatus !== "idle") {
                    setApiKeyStatus("idle");
                    setApiKeyMessage("Activate the updated API key.");
                  }
                }}
                placeholder="sk-..."
                className="input-field w-full text-[11px] font-mono"
              />
              <button
                type="button"
                onClick={activateApiKey}
                disabled={apiKeyStatus === "checking"}
                className={`w-full py-2.5 rounded-lg flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest transition-all ${
                  apiKeyStatus === "active"
                    ? "bg-emerald-500 text-white"
                    : "bg-primary text-white hover:bg-primary/90"
                } disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400`}
              >
                {apiKeyStatus === "checking" ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />}
                {apiKeyStatus === "active" ? "API Key Active" : "Activate API Key"}
              </button>
              <p className={`text-[9px] leading-tight ${
                apiKeyStatus === "active" ? "text-emerald-400" :
                apiKeyStatus === "error" ? "text-red-400" :
                "text-slate-500"
              }`}>
                {apiKeyMessage}
              </p>
            </div>
            {/* Main Action Button */}
            <button 
              disabled={isPipelineRunning || !file || !hasActiveKey}
              onClick={runCompletePipeline}
              className={`w-full py-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-[10px] uppercase tracking-widest transition-all shadow-xl ${
                isPipelineRunning 
                ? "bg-slate-800 text-slate-500 cursor-not-allowed" 
                : "bg-primary text-white shadow-primary/20 hover:scale-[1.02] active:scale-95"
              }`}
            >
              {isPipelineRunning ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
              {isPipelineRunning ? "Pipeline in Progress..." : "Run Complete Pipeline"}
            </button>
        </div>
        
        <div className="flex flex-col w-full px-4 gap-4 mt-4">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] ml-2">Agentic Pipeline</h3>
          {agents.map(agent => (
            <div 
              key={agent.id}
              onClick={() => agent.status !== "loading" && runAgent(agent.id)}
              className={`flex items-center gap-4 px-4 py-4 rounded-2xl cursor-pointer transition-all border ${
                agent.status === "completed" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                agent.status === "loading" ? "bg-primary/10 border-primary/20 text-primary animate-pulse" :
                "bg-white/5 border-transparent text-slate-400 hover:border-white/10"
              }`}
            >
              <div className={agent.status === "completed" ? "text-emerald-400" : "text-primary"}>
                {React.cloneElement(agent.icon, { size: 18 })}
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold uppercase">{agent.name}</span>
                <span className="text-[10px] opacity-60 font-medium">{agent.description}</span>
              </div>
              {agent.status === "completed" && <CheckCircle2 size={14} className="ml-auto" />}
              {agent.status === "loading" && <Loader2 size={14} className="ml-auto animate-spin" />}
            </div>
          ))}
        </div>

        <div className="mt-auto p-4 w-full">
           <button 
            onClick={() => window.location.reload()}
            className="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-widest text-slate-500 hover:text-white transition-all"
           >
             Reset Analysis Session
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-bold mb-2">Multimodal <span className="text-primary italic">Linguistic Laboratory</span></h1>
            <p className="text-slate-400 text-sm font-medium">Session ID: <span className="font-mono text-primary/70">{sessionId || "Initializing..."}</span></p>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-8">
          {/* Config & Input */}
          <div className="col-span-12 lg:col-span-4 space-y-8">
            <motion.div initial={{opacity:0}} animate={{opacity:1}} className="glass-panel p-6 border-primary/10">
              <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-6">01. Source Configuration</h2>
              
              <div className="space-y-6">
                <div 
                  className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center gap-4 transition-all cursor-pointer ${file ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-white/5 hover:border-primary/20 bg-black/20'}`}
                  onClick={() => document.getElementById('file-upload').click()}
                >
                  <div className={`p-4 rounded-full ${file ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-500'}`}>
                    {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Upload size={24} />}
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-bold uppercase tracking-wide">{isUploading ? "Uploading..." : file ? file.name : "Select Document"}</p>
                    {!file && <p className="text-[10px] text-slate-600 mt-1 italic">Trained for .txt, .csv, .docx</p>}
                  </div>
                  <input id="file-upload" type="file" accept=".txt,.csv,.docx,.pdf" className="hidden" onChange={handleFileUpload} />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Corpus Metadata</label>
                  <input 
                    type="text" 
                    className="input-field w-full text-sm font-medium"
                    value={corpusName}
                    onChange={(e) => setCorpusName(e.target.value)}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center ml-1">
                    <label className="text-[10px] font-bold uppercase text-slate-500">Scan Intensity</label>
                    <span className="text-primary font-mono font-bold text-xs">{analysisLimit} Segments</span>
                  </div>
                  <input 
                    type="range" min="1" max="50" 
                    className="w-full h-1.5 bg-white/5 rounded-full appearance-none cursor-pointer accent-primary"
                    value={analysisLimit}
                    onChange={(e) => setAnalysisLimit(e.target.value)}
                  />
                </div>
              </div>
            </motion.div>

            <div className="glass-panel p-6 bg-gradient-to-br from-indigo-500/5 to-transparent">
               <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 mb-4">Neural Health</h2>
               <div className="grid grid-cols-2 gap-4">
                  <div className="bg-black/20 p-4 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold">Uptime</div>
                    <div className="text-lg font-bold font-mono text-emerald-400">99.9%</div>
                  </div>
                  <div className="bg-black/20 p-4 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold">API Latency</div>
                    <div className="text-lg font-bold font-mono text-primary">124ms</div>
                  </div>
               </div>
            </div>
          </div>

          {/* Execution & Output */}
          <div className="col-span-12 lg:col-span-8 space-y-8">
            <div className="glass-panel h-[350px] flex flex-col border-primary/5">
              <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                <div className="flex items-center gap-2">
                  <Terminal size={14} className="text-primary" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">Real-time Pulse Monitor</span>
                </div>
              </div>
              <div className="flex-1 p-6 overflow-y-auto font-mono text-[11px] space-y-1.5 bg-black/40">
                {sessionData?.logs?.map((log, i) => (
                  <div key={i} className={`flex gap-3 ${log.includes(">>>") ? "text-primary font-bold mt-2" : "text-indigo-200/70"}`}>
                    <span className="opacity-20">{i+1}</span>
                    <span>{log}</span>
                  </div>
                ))}
                {!sessionData?.logs && <div className="text-slate-700 italic">Initialize session to start pulse monitoring...</div>}
                <div ref={logEndRef} />
              </div>
            </div>

            <div className="glass-panel p-0 min-h-[450px] border-emerald-500/5 flex flex-col">
               {/* Tab Header */}
               <div className="flex border-b border-white/5 bg-white/5 p-1">
                  {[
                    { id: "agent1", name: "Preprocessing", icon: <Cpu size={14} /> },
                    { id: "agent2", name: "Pragmatic", icon: <Layers size={14} /> },
                    { id: "agent3", name: "Semantic", icon: <Database size={14} /> },
                    { id: "agent4", name: "Statistics", icon: <BarChart3 size={14} /> },
                    { id: "synthesis", name: "Final Synthesis", icon: <FileText size={14} /> },
                  ].map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex-1 flex items-center justify-center gap-2 py-3 text-[10px] font-bold uppercase tracking-widest transition-all rounded-lg ${
                        activeTab === tab.id 
                        ? "bg-primary text-white shadow-lg shadow-primary/20" 
                        : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                      }`}
                    >
                      {tab.icon}
                      <span className="hidden sm:inline">{tab.name}</span>
                    </button>
                  ))}
               </div>

               <div className="flex-1 p-8 overflow-y-auto max-h-[600px]">
                  {activeTab === "synthesis" && (
                    <div className="space-y-6">
                       <div className="flex justify-between items-center pb-4 border-b border-white/5">
                          <h2 className="text-lg font-bold flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.5)]" />
                            Scientific Report Synthesis
                          </h2>
                          {sessionData?.pdf_url && (
                            <a 
                              href={`${apiBase}/download/${sessionData.pdf_url}`} 
                              target="_blank"
                              className="flex items-center gap-2 bg-emerald-500 px-5 py-2 rounded-xl text-[10px] font-bold uppercase tracking-widest hover:scale-105 transition-all shadow-lg shadow-emerald-500/20"
                            >
                              <Download size={14} />
                              Export PDF
                            </a>
                          )}
                       </div>
                       <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-medium">
                          {sessionData?.report ? (
                            <div className="bg-white/5 p-8 rounded-2xl border border-white/5 font-serif text-base leading-relaxed">
                              {sessionData.report}
                            </div>
                          ) : (
                            <div className="flex flex-col items-center justify-center py-24 opacity-30 gap-4">
                              <FileText size={64} strokeWidth={1} />
                              <p className="text-[11px] font-bold uppercase tracking-widest text-center">
                                {isPipelineRunning ? "Synthesizing Multi-Agent Evidence..." : "Awaiting Orchestration (Agent 5)"}
                              </p>
                            </div>
                          )}
                       </div>
                    </div>
                  )}

                  {activeTab === "agent1" && (
                    <div className="space-y-4">
                      <h3 className="text-xs font-bold uppercase text-primary tracking-widest">Agent 1: Segmented Corpus Output</h3>
                      {sessionData?.a1_result?.segments ? (
                        <div className="grid gap-4">
                          {sessionData.a1_result.segments.map((seg, i) => (
                            <div key={i} className="bg-black/20 p-4 rounded-xl border border-white/5 font-mono text-[11px] text-indigo-200/80">
                              <div className="flex justify-between mb-2 pb-2 border-b border-white/5 opacity-50">
                                <span>SEGMENT {seg.seg_n}</span>
                                <span>{seg.word_count} WORDS</span>
                              </div>
                              {seg.text}
                            </div>
                          ))}
                        </div>
                      ) : <p className="text-center py-12 opacity-30 text-xs">No preprocessing data available.</p>}
                    </div>
                  )}

                  {activeTab === "agent2" && (
                    <div className="space-y-4">
                      <h3 className="text-xs font-bold uppercase text-primary tracking-widest">Agent 2: Pragmatic Enrichment</h3>
                      {sessionData?.a2_result ? (
                        <div className="grid gap-4">
                          {sessionData.a2_result.map((seg, i) => (
                            <div key={i} className="bg-black/20 p-4 rounded-xl border border-white/5">
                              <div className="text-[11px] font-mono text-indigo-200/60 mb-2 italic">"{seg.text}"</div>
                              <div className="grid grid-cols-2 gap-4 mt-4">
                                <div className="bg-white/5 p-3 rounded-lg">
                                  <div className="text-[9px] font-bold uppercase text-slate-500 mb-1">Speech Act</div>
                                  <div className="text-xs font-bold text-primary">{seg.pragmatics?.speech_act?.category} ({seg.pragmatics?.speech_act?.directness})</div>
                                </div>
                                <div className="bg-white/5 p-3 rounded-lg">
                                  <div className="text-[9px] font-bold uppercase text-slate-500 mb-1">Politeness</div>
                                  <div className="text-xs font-bold text-emerald-400">{seg.pragmatics?.politeness?.score}/10 — {seg.pragmatics?.politeness?.strategy}</div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : <p className="text-center py-12 opacity-30 text-xs">No pragmatic analysis available.</p>}
                    </div>
                  )}

                  {activeTab === "agent3" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-xs font-bold uppercase text-primary tracking-widest">Agent 3: Semantic Drift & Register</h3>
                        {!sessionData?.a3_result && <div className="text-[10px] text-amber-500 animate-pulse font-bold uppercase">Analysis Pending...</div>}
                      </div>
                      
                      {sessionData?.a3_result ? (
                        <div className="space-y-6">
                           <div className="grid grid-cols-3 gap-4">
                              <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-[9px] font-bold text-slate-500 uppercase mb-1">Dominant Register</div>
                                <div className="text-sm font-bold text-primary">{sessionData.a3_result.register_summary?.dominant_register || "N/A"}</div>
                              </div>
                              <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-[9px] font-bold text-slate-500 uppercase mb-1">Lexical Density</div>
                                <div className="text-sm font-bold text-emerald-400">{sessionData.a3_result.register_summary?.mean_lexical_density || 0}%</div>
                              </div>
                              <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-[9px] font-bold text-slate-500 uppercase mb-1">Register Shifts</div>
                                <div className="text-sm font-bold text-indigo-400">{sessionData.a3_result.register_summary?.register_shift_count || 0}</div>
                              </div>
                           </div>
                           
                           <div className="space-y-3">
                              <div className="text-[10px] font-bold uppercase text-slate-400 flex justify-between">
                                <span>Drift Map Highlights</span>
                                <span className="opacity-50 font-mono">{sessionData.a3_result.semantic_drift_map?.length || 0} Entities</span>
                              </div>
                              
                              {sessionData.a3_result.semantic_drift_map && sessionData.a3_result.semantic_drift_map.length > 0 ? (
                                sessionData.a3_result.semantic_drift_map.map((drift, i) => (
                                  <div key={i} className="bg-black/20 p-4 rounded-xl border border-white/5 flex justify-between items-center hover:bg-white/5 transition-colors">
                                    <div className="flex-1">
                                      <div className="text-xs font-bold text-slate-200">"{drift.lemma || "Unknown Lemma"}"</div>
                                      <div className="text-[10px] text-slate-500 font-medium">
                                        <span className="text-indigo-400/70">{drift.original_field || "Source"}</span> 
                                        <ArrowRight size={8} className="inline mx-2 opacity-30" />
                                        <span className="text-emerald-400/70">{drift.emergent_field || "Target"}</span>
                                      </div>
                                      {drift.evidence && <div className="text-[9px] text-slate-600 mt-1 italic line-clamp-1 opacity-60">Evidence: {drift.evidence}</div>}
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-[9px] font-bold uppercase ${
                                      drift.drift_severity === 'HIGH' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                                      drift.drift_severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                                      'bg-primary/10 text-primary border border-primary/20'
                                    }`}>
                                      {drift.drift_severity || "LOW"} SEVERITY
                                    </div>
                                  </div>
                                ))
                              ) : (
                                <div className="bg-white/5 border border-dashed border-white/10 rounded-xl py-12 flex flex-col items-center justify-center gap-3 opacity-40">
                                  <Database size={24} />
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-center px-6">
                                    Low Lexical Variance Detected<br/>
                                    <span className="text-[8px] opacity-60 font-medium normal-case mt-1 block italic">No significant semantic field shifts found in current segment sample.</span>
                                  </p>
                                </div>
                              )}
                           </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center py-24 opacity-30 gap-4">
                          <Database size={64} strokeWidth={1} />
                          <p className="text-[11px] font-bold uppercase tracking-widest text-center">
                            Awaiting Semantic Mapping (Agent 3)
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === "agent4" && (
                    <div className="space-y-4">
                      <h3 className="text-xs font-bold uppercase text-primary tracking-widest">Agent 4: Statistical Validation</h3>
                      {sessionData?.a4_result ? (
                        <div className="prose prose-invert max-w-none prose-sm text-xs opacity-80 leading-relaxed prose-p:mb-4 prose-th:bg-white/5 prose-th:p-2 prose-td:p-2 prose-table:border prose-table:border-white/5">
                          <div className="whitespace-pre-wrap font-mono">
                            {sessionData.a4_result.report_markdown}
                          </div>
                        </div>
                      ) : <p className="text-center py-12 opacity-30 text-xs">No statistical report available.</p>}
                    </div>
                  )}
               </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const NavItem = ({ icon, label, active = false }) => (
  <div className={`flex items-center gap-4 px-4 py-3 rounded-xl cursor-pointer transition-all ${active ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}>
    {icon}
    <span className="font-medium text-sm">{label}</span>
    {active && <ArrowRight size={14} className="ml-auto" />}
  </div>
);

export default App;
