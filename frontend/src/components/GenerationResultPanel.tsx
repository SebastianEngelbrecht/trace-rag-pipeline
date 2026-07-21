import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Quote, Sparkles, Layers, Code2, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { GenerationResponse } from '../models/types';

interface GenerationResultPanelProps {
    result: GenerationResponse | null;
    isDevMode: boolean;
}

export const GenerationResultPanel: React.FC<GenerationResultPanelProps> = ({ result, isDevMode }) => {
    if (!result) return null;

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="flex flex-col gap-12 mt-6"
            >
                {/* Answer Panel */}
                <div className="bg-slate-900 p-8 border-l-4 border-cyan-500 rounded-r-lg relative overflow-hidden group">
                    <Quote className="absolute right-6 top-6 w-24 h-24 text-slate-800 -z-10 -rotate-12 group-hover:rotate-0 transition-transform duration-700" />
                    <h3 className="text-heading text-[24px] m-0 mb-4 text-slate-100 flex items-center justify-between gap-2 relative z-10">
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-cyan-500" />
                            Synthesized Answer
                        </div>
                        {(result.response_time_ms || result.tokens_used) && (
                            <div className="flex items-center gap-4 text-caption font-mono text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded border border-slate-700">
                                {result.response_time_ms && (
                                    <span className="flex items-center gap-1.5" title="Generation Time">
                                        <Activity className="w-4 h-4 text-cyan-400" />
                                        {(result.response_time_ms / 1000).toFixed(2)}s
                                    </span>
                                )}
                                {result.tokens_used && (
                                    <span className="flex items-center gap-1.5 border-l border-slate-700 pl-4" title="Tokens Used">
                                        <Activity className="w-4 h-4 text-teal-400" />
                                        {result.tokens_used}
                                    </span>
                                )}
                            </div>
                        )}
                    </h3>
                    <div className="prose prose-invert max-w-none text-body text-slate-300 leading-relaxed relative z-10 w-full prose-p:leading-relaxed prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800">
                        <ReactMarkdown>{result.answer}</ReactMarkdown>
                    </div>
                </div>
                
                {/* Sources Panel */}
                <div className="flex flex-col gap-6">
                    <h3 className="text-heading text-[24px] m-0 text-slate-100 flex items-center gap-2">
                        <Layers className="w-6 h-6 text-teal-500" />
                        Source Attribution ({result.chunks.length})
                    </h3>
                    <div className="grid gap-4">
                        {result.chunks.map((chunk, idx) => (
                            <motion.div 
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                key={idx} 
                                className="border border-slate-700 p-6 rounded-lg bg-slate-900 hover:border-slate-600 transition-colors"
                            >
                                <div className="text-caption font-semibold mb-4 flex items-center gap-2">
                                    <div className="px-2 py-1 bg-teal-500/10 text-teal-400 rounded text-xs">
                                        C{chunk.chunk_index}
                                    </div>
                                    <a href={chunk.source_url} target="_blank" rel="noreferrer" className="text-cyan-500 hover:text-cyan-400 transition-colors truncate max-w-full">
                                        {chunk.source_url}
                                    </a>
                                </div>
                                <div className="text-caption whitespace-pre-wrap text-slate-400 leading-relaxed pl-8 border-l-2 border-slate-800">
                                    {chunk.content}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Prompt Panel */}
                <AnimatePresence>
                    {isDevMode && (
                        <motion.div
                            initial={{ opacity: 0, height: 0, marginTop: 0 }}
                            animate={{ opacity: 1, height: 'auto', marginTop: 24 }}
                            exit={{ opacity: 0, height: 0, marginTop: 0 }}
                            className="overflow-hidden"
                        >
                            <h3 className="text-heading text-[24px] m-0 mb-4 text-slate-100 flex items-center gap-2">
                                <Code2 className="w-5 h-5 text-teal-400" />
                                Telemetry & Payload <span className="text-caption text-teal-500 bg-teal-500/10 px-2 py-1 rounded ml-2">DEV</span>
                            </h3>
                            <div className="relative group">
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-950/80 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
                                <pre className="text-caption bg-slate-950 text-slate-400 p-6 overflow-x-auto rounded-lg border border-slate-800 border-l-2 border-l-teal-500 font-mono max-h-[300px] whitespace-pre-wrap word-break hover:max-h-none transition-all shadow-inner">
                                    {result.prompt}
                                </pre>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </AnimatePresence>
    );
};