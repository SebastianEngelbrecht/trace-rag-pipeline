import React from 'react';
import { motion } from 'framer-motion';

interface TelemetryCardProps {
    title: string;
    icon: React.ReactNode;
    value: string | number;
    delay?: number;
}

export const TelemetryCard: React.FC<TelemetryCardProps> = ({ title, icon, value, delay = 0 }) => {
    return (
        <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className="p-6 bg-slate-900 border border-slate-700 rounded-xl flex flex-col gap-2 min-w-0"
        >
            <div className="text-caption text-slate-400 flex items-center gap-2 whitespace-nowrap overflow-hidden text-ellipsis">
                <div className="shrink-0">{icon}</div>
                {title}
            </div>
            <div className="text-heading md:text-display text-slate-50 font-mono truncate">
                {value}
            </div>
        </motion.div>
    );
};