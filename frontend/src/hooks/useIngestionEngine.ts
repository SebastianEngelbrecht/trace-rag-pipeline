import { useState, useRef, useEffect } from 'react';
import { IngestionConfig, WsMessage } from '../models/types';

export function useIngestionEngine() {
    const [messages, setMessages] = useState<WsMessage[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [ingestionTime, setIngestionTime] = useState<number | null>(null);
    
    const wsRef = useRef<WebSocket | null>(null);
    const startTimeRef = useRef<number | null>(null);

    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const startIngestion = (url: string, maxDepth: number, chunkSize: number, overlap: number) => {
        if (!url) return;
        
        setIsRunning(true);
        setMessages([]);
        setIngestionTime(null);
        startTimeRef.current = performance.now();

        const ws = new WebSocket('ws://127.0.0.1:8000/ws/ingest');
        wsRef.current = ws;

        ws.onopen = () => {
            const config: IngestionConfig = {
                url,
                max_depth: maxDepth,
                chunk_size: chunkSize,
                overlap,
            };
            ws.send(JSON.stringify(config));
        };

        ws.onmessage = (event) => {
            try {
                const data: WsMessage = JSON.parse(event.data);
                setMessages(prev => [...prev, data]);
                if (data.status === 'complete' || data.status === 'error') {
                    if (startTimeRef.current) {
                        setIngestionTime((performance.now() - startTimeRef.current) / 1000);
                    }
                    setIsRunning(false);
                    ws.close();
                }
            } catch (e) {
                console.error("Failed to parse websocket message", e);
            }
        };

        ws.onerror = () => {
            setMessages(prev => [...prev, { status: 'error', message: 'WebSocket connection error' }]);
            setIsRunning(false);
        };
        
        ws.onclose = () => {
            setIsRunning(false);
        };
    };

    return {
        messages,
        isRunning,
        ingestionTime,
        startIngestion
    };
}