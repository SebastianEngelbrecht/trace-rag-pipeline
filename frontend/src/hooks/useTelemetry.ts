import { useState, useEffect } from 'react';

export interface TelemetryStats {
    totalQueries: number;
    avgResponseTime: number;
    totalTokens: number;
    ingestedDocs: number;
    totalDbTokens: number;
}

export function useTelemetry(pollIntervalMs: number = 3000) {
    const [stats, setStats] = useState<TelemetryStats>({
        totalQueries: 0,
        avgResponseTime: 0,
        totalTokens: 0,
        ingestedDocs: 0,
        totalDbTokens: 0
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8000/api/v1/stats');
                if (response.ok) {
                    const data = await response.json();
                    setStats({
                        totalQueries: data.total_queries,
                        avgResponseTime: data.avg_response_time,
                        totalTokens: data.total_tokens,
                        ingestedDocs: data.ingested_chunks,
                        totalDbTokens: data.total_db_tokens || 0
                    });
                }
            } catch (err) {
                console.error("Failed to fetch telemetry stats", err);
            }
        };

        fetchStats();
        const intervalId = setInterval(fetchStats, pollIntervalMs);
        return () => clearInterval(intervalId);
    }, [pollIntervalMs]);

    return stats;
}