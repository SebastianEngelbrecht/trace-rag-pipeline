import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, MessageSquare, Send, FileText, Terminal, Layers } from 'lucide-react';
import { Switch } from '@base-ui-components/react/switch';
import { useQueryEngine } from '../hooks/useQueryEngine';
import { GenerationResultPanel } from '../components/GenerationResultPanel';

export const QueryView: React.FC = () => {
    const [question, setQuestion] = useState('');
    const [topK, setTopK] = useState(5);
    const [temperature, setTemperature] = useState(0.7);
    const [vectorWeight, setVectorWeight] = useState(0.5);
    const [isDevMode, setIsDevMode] = useState(false);
    
    // Abstracted Logic
    const { isLoading, result, error, submitQuery } = useQueryEngine();

    const handleQuery = () => {
        submitQuery(question, topK, temperature, vectorWeight);
    };

    return (
        <div className="flex flex-col gap-8 p-8 bg-slate-800 rounded-2xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.3),0_2px_4px_-2px_rgba(0,0,0,0.3)]">
            <h2 className="m-0 text-heading text-slate-50 flex justify-between items-center gap-3">
                <div className="flex items-center gap-3">
                    <Sparkles className="w-8 h-8 text-cyan-500" />
                    Query Intelligence Engine
                </div>
                <div className="flex items-center gap-3">
                    <span className={`text-caption transition-colors font-medium ${isDevMode ? 'text-teal-400' : 'text-slate-500'}`}>Dev Mode</span>
                    <Switch.Root 
                        checked={isDevMode} 
                        onCheckedChange={setIsDevMode} 
                        className="w-[60px] h-8 bg-slate-700 rounded-full cursor-pointer data-[checked]:bg-teal-500 transition-colors duration-300 ease-out flex items-center px-1 relative focus:outline-none focus:ring-2 focus:ring-teal-500/50 group"
                    >
                        <span className="absolute left-2.5 text-[10px] font-bold text-teal-50 opacity-0 group-data-[checked]:opacity-100 transition-opacity duration-300 ease-out">ON</span>
                        <span className="absolute right-2 text-[10px] font-bold text-slate-400 opacity-100 group-data-[checked]:opacity-0 transition-opacity duration-300 ease-out">OFF</span>
                        <Switch.Thumb className="block w-6 h-6 bg-slate-200 rounded-full shadow-[0_2px_4px_rgba(0,0,0,0.4)] group-data-[checked]:bg-white group-data-[checked]:shadow-[0_0_12px_rgba(20,184,166,0.8),_0_2px_4px_rgba(0,0,0,0.3)] transition-transform duration-300 ease-out translate-x-0 group-data-[checked]:translate-x-[28px] z-10" />
                    </Switch.Root>
                </div>
            </h2>
            
            <div className="flex flex-col gap-4">
                <div className="relative">
                    <MessageSquare className="absolute left-4 top-5 w-5 h-5 text-slate-400" />
                    <textarea 
                        value={question} 
                        onChange={e => setQuestion(e.target.value)} 
                        placeholder="Ask a question..."
                        className="w-full text-body pl-12 pr-4 py-4 min-h-[120px] resize-y border border-slate-700 rounded-lg text-slate-100 bg-slate-900 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-500"
                        disabled={isLoading}
                    />
                </div>
                
                <div className="flex justify-between items-center bg-slate-900 border border-slate-700 p-4 rounded-lg flex-wrap gap-4">
                    <div className="flex gap-6 items-center flex-wrap">
                        <label className="text-caption flex gap-2 items-center text-slate-400">
                            <FileText className="w-4 h-4 text-emerald-500" />
                            Top K:
                            <input 
                                type="number" 
                                min="1"
                                max="5"
                                value={topK} 
                                onChange={e => {
                                    const val = parseInt(e.target.value);
                                    if(val > 5) setTopK(5);
                                    else if(val < 1) setTopK(1);
                                    else setTopK(val);
                                }} 
                                disabled={isLoading} 
                                className="w-[60px] p-2 rounded border border-slate-700 bg-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium" 
                            />
                        </label>
                        <label className="flex gap-4 items-center text-caption text-slate-400">
                            <span className="flex items-center gap-2 w-24">
                                <Terminal className="w-4 h-4 text-cyan-500" />
                                Temp ({temperature.toFixed(1)})
                            </span>
                            <div className="relative flex items-center w-32">
                                <input 
                                    type="range" 
                                    min="0" 
                                    max="1" 
                                    step="0.1" 
                                    value={temperature} 
                                    onChange={e => setTemperature(parseFloat(e.target.value))}
                                    disabled={isLoading}
                                    className="w-full accent-cyan-500 transition-all duration-300 ease-out cursor-pointer disabled:cursor-not-allowed"
                                />
                            </div>
                        </label>
                        <label className="flex gap-4 items-center text-caption text-slate-400">
                            <span className="flex items-center gap-2 w-32">
                                <Layers className="w-4 h-4 text-purple-500" />
                                Vector W. ({vectorWeight.toFixed(1)})
                            </span>
                            <div className="relative flex items-center w-32">
                                <input 
                                    type="range" 
                                    min="0" 
                                    max="1" 
                                    step="0.1" 
                                    value={vectorWeight} 
                                    onChange={e => setVectorWeight(parseFloat(e.target.value))}
                                    disabled={isLoading}
                                    className="w-full accent-purple-500 transition-all duration-300 ease-out cursor-pointer disabled:cursor-not-allowed"
                                />
                            </div>
                        </label>
                    </div>

                    <button 
                        onClick={handleQuery} 
                        disabled={isLoading || !question.trim()}
                        className={`relative overflow-hidden flex items-center gap-2 px-8 py-3 text-body rounded-lg font-semibold border-none transition-all duration-300 ease-out active:scale-95 ${
                            isLoading || !question.trim() 
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed hidden' 
                                : 'bg-cyan-500 text-slate-950 cursor-pointer hover:bg-cyan-400 shadow-sm hover:shadow-cyan-500/20 hover:-translate-y-0.5 group'
                        }`}
                        onPointerDown={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            const y = e.clientY - rect.top;
                            const span = document.createElement("span");
                            span.className = "absolute bg-white/30 rounded-full w-0 h-0 pointer-events-none -translate-x-1/2 -translate-y-1/2 animate-ripple";
                            span.style.left = `${x}px`;
                            span.style.top = `${y}px`;
                            e.currentTarget.appendChild(span);
                            setTimeout(() => span.remove(), 600);
                        }}
                    >
                        <Send className={`w-5 h-5 ${isLoading ? 'animate-bounce' : ''}`} />
                        {isLoading ? 'Synthesizing...' : 'Generate Insights'}
                    </button>
                    {(isLoading || !question.trim()) && (
                         <button 
                         disabled
                         className="flex items-center gap-2 px-8 py-3 text-body rounded-lg font-semibold border-none bg-slate-700 text-slate-500 cursor-not-allowed"
                     >
                         <Send className={`w-5 h-5 ${isLoading ? 'animate-bounce' : ''}`} />
                         {isLoading ? 'Synthesizing...' : 'Generate Insights'}
                     </button>
                    )}
                </div>
            </div>

            <AnimatePresence>
                {error && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-caption text-red-400 bg-red-900/30 p-4 rounded-lg border border-red-900/50 flex items-center gap-3"
                    >
                        <div className="bg-red-500 rounded-full w-2 h-2 shrink-0" />
                        {error}
                    </motion.div>
                )}
            </AnimatePresence>

            <GenerationResultPanel result={result} isDevMode={isDevMode} />
        </div>
    );
};