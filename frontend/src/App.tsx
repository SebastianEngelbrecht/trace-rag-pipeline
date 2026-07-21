import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IngestionView } from './views/IngestionView';
import { QueryView } from './views/QueryView';
import { TokenUsageView } from './views/TokenUsageView';
import { CostOptimizationPanel } from './components/CostOptimizationPanel';
import { Database, Search } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'query' | 'ingest'>('query');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6 lg:p-12">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-8">
        <header className="border-b border-slate-800 pb-6 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <h1 className="text-display m-0 text-slate-50 relative inline-block group text-4xl md:text-5xl">
              Trace 
              <span className="text-cyan-500 ml-2">Pipeline</span>
          </h1>
          
          {/* View Toggle Tabs */}
          <div className="flex p-1.5 bg-slate-900 rounded-lg border border-slate-700 w-fit shrink-0">
            <button 
              onClick={(e) => setActiveTab('query')}
              className={`relative px-6 py-2.5 rounded-md text-caption font-semibold transition-colors z-10 flex items-center gap-2 cursor-pointer border-none outline-none ${
                activeTab === 'query' ? 'text-slate-950' : 'text-slate-400 hover:text-slate-200 bg-transparent'
              }`}
            >
              {activeTab === 'query' && (
                <motion.div 
                  layoutId="activeTab" 
                  className="absolute inset-0 bg-cyan-500 rounded-md -z-10 shadow-[0_0_12px_rgba(6,182,212,0.4)]"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
              <Search className="w-4 h-4" />
              Query Engine
            </button>
            <button 
              onClick={(e) => setActiveTab('ingest')}
              className={`relative px-6 py-2.5 rounded-md text-caption font-semibold transition-colors z-10 flex items-center gap-2 cursor-pointer border-none outline-none ${
                activeTab === 'ingest' ? 'text-slate-950' : 'text-slate-400 hover:text-slate-200 bg-transparent'
              }`}
            >
              {activeTab === 'ingest' && (
                <motion.div 
                  layoutId="activeTab" 
                  className="absolute inset-0 bg-teal-500 rounded-md -z-10 shadow-[0_0_12px_rgba(20,184,166,0.4)]"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
              <Database className="w-4 h-4" />
              Data Ingestion
            </button>
          </div>
        </header>

        <main className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
          {/* Left Column: Primary Interactions - 8/12 width */}
          <div className="xl:col-span-8 flex flex-col gap-8 w-full min-w-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="w-full"
              >
                {activeTab === 'query' ? <QueryView /> : <IngestionView />}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Right Column: Telemetry & Status - 4/12 width */}
          <div className="xl:col-span-4 w-full flex flex-col gap-8 min-w-0">
             <div className="sticky top-8 flex flex-col gap-8">
                <TokenUsageView />
                <CostOptimizationPanel />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
