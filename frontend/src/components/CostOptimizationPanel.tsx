import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingDown, Zap, Info } from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry';

export const CostOptimizationPanel: React.FC = () => {
    const stats = useTelemetry(3000);
    const [showInfo, setShowInfo] = useState(false);
    
    // Real Data Strategy:
    // A pipeline without RAG forces you to stuff your entire ingested knowledge base into the context window for EVERY query.
    // Trace RAG only sends the top-K chunks.
    const totalDbTokens = stats.totalDbTokens > 0 
        ? stats.totalDbTokens 
        : stats.ingestedDocs * 125; // fallback to estimation if no specific token counts
    
    // Naive baseline: Total DB Tokens * Number of Queries
    const naiveTokens = totalDbTokens * stats.totalQueries;
    const actualTokens = stats.totalTokens;
    // Total Tokens is exactly what RAG consumed dynamically (Generation) + static cost of DB
    const actualTotalTokens = actualTokens + totalDbTokens;
    // RAG technically uses "Generation Tokens" + "Embedding Tokens" 
    const savedTokens = Math.max(0, naiveTokens - actualTotalTokens);
    
    // Standard blended API cost (e.g., $1.25 per 1M tokens for generation)
    // Embedding generally costs fractions of a cent ($0.02 per 1M tokens), so we will add it to the naive calculation
    const costPerMillion = 1.25;
    const embeddingCostPerMillion = 0.02; // Very cheap compared to generation

    // Actual cost: Generation tokens used in RAG + Embedding cost to build the DB
    const embeddingCost = (totalDbTokens / 1_000_000) * embeddingCostPerMillion;
    const currentCost = ((actualTokens / 1_000_000) * costPerMillion) + embeddingCost;
    
    // Naive cost: No DB built, but generating over the entire dataset every time
    const naiveCost = (naiveTokens / 1_000_000) * costPerMillion;
    
    const savedCost = Math.max(0, naiveCost - currentCost);

    const fillPercentage = naiveTokens > 0 ? (actualTokens / naiveTokens) * 100 : 0;

    return (
        <div className="flex flex-col gap-6 p-8 bg-slate-800 rounded-2xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.3),0_2px_4px_-2px_rgba(0,0,0,0.3)]">
            <h2 className="m-0 text-heading text-slate-50 flex items-center justify-between gap-3 text-2xl relative">
                <div className="flex items-center gap-3">
                    <TrendingDown className="w-6 h-6 text-emerald-400" />
                    Cost Optimisation
                    <button 
                        onMouseEnter={() => setShowInfo(true)}
                        onMouseLeave={() => setShowInfo(false)}
                        className="p-1 rounded-full text-slate-500 hover:text-cyan-400 transition-colors bg-transparent border-none cursor-help outline-none ml-1"
                    >
                        <Info className="w-4 h-4" />
                    </button>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-md text-emerald-400 text-caption font-semibold">
                    <Zap className="w-3.5 h-3.5 fill-current" /> Active
                </div>

                {/* Tooltip Hover Info */}
                <AnimatePresence>
                    {showInfo && (
                        <motion.div 
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            className="absolute top-10 left-0 w-[320px] p-4 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 text-caption text-slate-300 font-normal leading-relaxed pointer-events-none"
                        >
                            <div className="font-semibold text-cyan-400 mb-2">How is this calculated?</div>
                            Without Trace (a standard chat model), the AI has to read your <span className="text-emerald-400 font-medium whitespace-nowrap">entire knowledge base</span> every time you ask a question.<br/><br/>
                            Trace uses "Semantic Search" to quickly find and send <span className="text-teal-400 font-medium whitespace-nowrap">only the most relevant paragraphs</span> to the AI, saving you from paying for the AI to read everything else.<br/><br/>
                            <i>Calculation includes both AI reading costs (~$1.25/1M words) and the minor cost of embedding data for search (~$0.02/1M words).</i>
                        </motion.div>
                    )}
                </AnimatePresence>
            </h2>
            
            <div className="flex flex-col gap-5">
                {/* Comparative breakdown stats */}
                <div className="grid grid-cols-2 gap-4 border-b border-slate-700 pb-5">
                    {/* Trace Search Stats */}
                    <div className="flex flex-col gap-1 p-3 bg-cyan-900/20 border border-cyan-800/30 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                            <span className="text-caption text-slate-300 font-medium">With Trace Search</span>
                        </div>
                        <div className="text-xl text-cyan-400 font-mono">
                            ${currentCost.toFixed(4)}
                        </div>
                        <span className="text-xs text-slate-500 font-mono flex flex-col mt-0.5 opacity-90">
                            <span>{actualTokens.toLocaleString()} chat words</span>
                            <span>+ {totalDbTokens.toLocaleString()} search words</span>
                        </span>
                    </div>

                    {/* Standard Chat Stats */}
                    <div className="flex flex-col gap-1 p-3 bg-slate-900/50 border border-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 rounded-full bg-slate-500" />
                            <span className="text-caption text-slate-400 font-medium">Standard Chat (No Trace)</span>
                        </div>
                        <div className="text-xl text-slate-400 font-mono line-through opacity-70">
                            ${naiveCost.toFixed(4)}
                        </div>
                        <span className="text-xs text-slate-500 font-mono">
                            {naiveTokens.toLocaleString()} words read
                        </span>
                    </div>
                </div>

                <div className="flex justify-between items-end pb-2">
                    <div className="flex flex-col gap-1">
                        <span className="text-caption text-emerald-400 font-medium tracking-wide uppercase text-[10px]">Total Money Saved</span>
                        <div className="text-display text-emerald-400 font-mono text-4xl">
                            ${savedCost.toFixed(4)}
                        </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 mb-1">
                        <span className="text-caption text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded font-mono border border-emerald-500/20">
                            You saved {savedTokens.toLocaleString()} words!
                        </span>
                        <span className="text-xs text-slate-500">
                            That's a {naiveTokens > 0 ? (100 - fillPercentage).toFixed(1) : 0}% reduction
                        </span>
                    </div>
                </div>

                {/* Progress Bar Comparison Visual */}
                <div className="flex flex-col gap-3 pt-2">
                    <div className="flex justify-between text-caption mb-1">
                        <span className="text-slate-300 font-medium">Visual Comparison: Amount of data AI had to read</span>
                    </div>
                    
                    <div className="relative h-6 bg-slate-900 rounded-full overflow-hidden flex shadow-inner border border-slate-700">
                        {/* The "Naïve" Background Fill */}
                        <div className="absolute inset-0 bg-slate-600/40" />
                        
                        {/* The "Optimized" Foreground Fill */}
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${fillPercentage}%` }}
                            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }} // smooth ease-out CSS physics
                            className="h-full bg-cyan-500 relative z-10 shadow-[4px_0_12px_rgba(6,182,212,0.5)] border-r border-cyan-400"
                        />
                        
                        {/* Dotted pattern overlay for texture in the saved area */}
                        <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#94a3b8 1px, transparent 1px)', backgroundSize: '8px 8px' }} />
                        
                        {/* Text indicating the saved portion */}
                        {fillPercentage < 80 && (
                            <div className="absolute inset-y-0 right-4 flex items-center text-xs font-semibold text-slate-400 z-0">
                                Data skipped thanks to Trace
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};