import React from 'react';
import { Activity, Database, MessageSquare, Zap } from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry';
import { TelemetryCard } from '../components/TelemetryCard';

export const TokenUsageView: React.FC = () => {
    const stats = useTelemetry(3000);

    return (
        <div className="flex flex-col gap-8 p-8 bg-slate-800 rounded-2xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.3),0_2px_4px_-2px_rgba(0,0,0,0.3)] min-h-0">
            <h2 className="m-0 text-heading text-slate-50 flex items-center gap-3">
                <Activity className="w-8 h-8 text-cyan-500" />
                Pipeline Telemetry
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 xl:gap-6">
                {/* 1. Core Engagement: How much is the system being used? */}
                <TelemetryCard 
                    title="Total Queries" 
                    icon={<MessageSquare className="w-4 h-4 text-sky-400" />} 
                    value={stats.totalQueries} 
                    delay={0.0}
                />
                
                {/* 2. Performance: How fast is it? */}
                <TelemetryCard 
                    title="Avg Response" 
                    icon={<Activity className="w-4 h-4 text-emerald-400" />} 
                    value={`${stats.avgResponseTime}s`} 
                    delay={0.1}
                />

                {/* 3. Cost Metric 1: Chat Generation */}
                <TelemetryCard 
                    title="Generation Tokens" 
                    icon={<Zap className="w-4 h-4 text-amber-400" />} 
                    value={stats.totalTokens.toLocaleString()} 
                    delay={0.2}
                />

                {/* 4. Infrastructure: Size of the Database */}
                <TelemetryCard 
                    title="Ingested Chunks" 
                    icon={<Database className="w-4 h-4 text-indigo-400" />} 
                    value={stats.ingestedDocs.toLocaleString()} 
                    delay={0.3}
                />

                {/* 5. Cost Metric 2: Document Indexing */}
                <TelemetryCard 
                    title="Embedding Tokens" 
                    icon={<Database className="w-4 h-4 text-fuchsia-400" />} 
                    value={stats.totalDbTokens.toLocaleString()} 
                    delay={0.4}
                />

                {/* 6. Total Aggregate Summary */}
                <TelemetryCard 
                    title="Total Tokens" 
                    icon={<Activity className="w-4 h-4 text-rose-400" />} 
                    value={(stats.totalTokens + stats.totalDbTokens).toLocaleString()} 
                    delay={0.5}
                />
            </div>
        </div>
    );
};