import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { useIngestionEngine } from '../hooks/useIngestionEngine';

export const IngestionView: React.FC = () => {
    const [url, setUrl] = useState('');
    const [maxDepth, setMaxDepth] = useState(3);
    const [chunkSize, setChunkSize] = useState(500);
    const [overlap, setOverlap] = useState(50);
    
    const { messages, isRunning, ingestionTime, startIngestion } = useIngestionEngine();

    const handleStart = () => {
        startIngestion(url, maxDepth, chunkSize, overlap);
    };

    return (
        <div className="flex flex-col gap-8 p-8 bg-slate-800 rounded-2xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.3),0_2px_4px_-2px_rgba(0,0,0,0.3)]">
            <h2 className="m-0 text-heading text-slate-50">Ingestion Config</h2>
            
            <div className="flex flex-col gap-6">
                <input 
                    type="text" 
                    value={url} 
                    onChange={e => setUrl(e.target.value)} 
                    placeholder="Enter starting URL (e.g., https://example.com)"
                    className="text-body p-4 border border-slate-700 rounded-lg text-slate-100 bg-slate-900 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
                    disabled={isRunning}
                />
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <label className="flex flex-col gap-2 text-caption text-slate-400">
                        <div className="flex justify-between">
                            <span>Max Crawl Depth</span>
                            <span className="text-slate-50 font-medium">{maxDepth}</span>
                        </div>
                        <input 
                            type="range" 
                            min="1" 
                            max="3" 
                            step="1"
                            value={maxDepth} 
                            onChange={e => setMaxDepth(parseInt(e.target.value))} 
                            disabled={isRunning} 
                            className="w-full accent-cyan-500 transition-all duration-300 ease-out cursor-pointer disabled:cursor-not-allowed"
                        />
                    </label>
                    <label className="flex flex-col gap-2 text-caption text-slate-400">
                        <div className="flex justify-between">
                            <span>Chunk Size (chars)</span>
                            <span className="text-slate-50 font-medium">{chunkSize}</span>
                        </div>
                        <input 
                            type="range" 
                            min="100" 
                            max="1000" 
                            step="50"
                            value={chunkSize} 
                            onChange={e => setChunkSize(parseInt(e.target.value))} 
                            disabled={isRunning} 
                            className="w-full accent-cyan-500 transition-all duration-300 ease-out cursor-pointer disabled:cursor-not-allowed"
                        />
                    </label>
                    <label className="flex flex-col gap-2 text-caption text-slate-400">
                        <div className="flex justify-between">
                            <span>Overlap (chars)</span>
                            <span className="text-slate-50 font-medium">{overlap}</span>
                        </div>
                        <input 
                            type="range" 
                            min="0" 
                            max="100" 
                            step="10"
                            value={overlap} 
                            onChange={e => setOverlap(parseInt(e.target.value))} 
                            disabled={isRunning} 
                            className="w-full accent-cyan-500 transition-all duration-300 ease-out cursor-pointer disabled:cursor-not-allowed"
                        />
                    </label>
                </div>

                <div>
                    <button 
                        onClick={handleStart} 
                        disabled={isRunning || !url}
                        className={`px-8 py-4 text-body rounded-lg font-semibold border-none transition-all duration-300 ease-out active:scale-95 ${
                            isRunning || !url 
                                ? 'bg-slate-600 text-slate-400 cursor-not-allowed' 
                                : 'bg-cyan-500 text-white cursor-pointer hover:bg-cyan-400 shadow-sm hover:shadow-cyan-500/20 hover:shadow-lg'
                        }`}
                    >
                        {isRunning ? 'Processing...' : 'Run Pipeline'}
                    </button>                    {ingestionTime !== null && !isRunning && (
                        <span className="ml-4 text-caption text-slate-400 font-mono">
                            Completed in {ingestionTime.toFixed(2)}s
                        </span>
                    )}                </div>
            </div>

            <div className="flex flex-col gap-2 bg-slate-900 border border-slate-700 p-6 rounded-lg h-[400px] overflow-y-auto">
                <h3 className="m-0 mb-4 text-body text-slate-300">Real-time Logs</h3>
                {messages.length === 0 && <div className="text-caption text-slate-500">Awaiting operations...</div>}
                {messages.map((msg, idx) => (
                    <div key={idx} className={`text-caption ${
                        msg.status === 'error' ? 'text-red-400' : 
                        msg.status === 'complete' ? 'text-emerald-400' : 
                        'text-cyan-400'
                    }`}>
                        <span className="font-semibold">[{msg.status.toUpperCase()}]</span> {msg.message}
                    </div>
                ))}
            </div>
        </div>
    );
};