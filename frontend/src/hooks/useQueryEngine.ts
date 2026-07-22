import { useState } from 'react';
import { GenerationResponse } from '../models/types';

export function useQueryEngine() {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<GenerationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const submitQuery = async (question: string, topK: number, temperature: number) => {
        if (!question.trim()) return;
        
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('http://127.0.0.1:8000/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, top_k: topK, temperature })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }

            const data: GenerationResponse = await response.json();
            setResult(data);
        } catch (err: any) {
            setError(err.message || 'An error occurred fetching the response.');
        } finally {
            setIsLoading(false);
        }
    };

    return {
        isLoading,
        result,
        error,
        submitQuery
    };
}