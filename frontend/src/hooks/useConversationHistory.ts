import { useEffect, useState } from "react";

export function useConversationHistory(conversationId: string | null) {
    const [history, setHistory] = useState<Record<string, string>[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!conversationId) return;

        setIsLoading(true);
        setError(null);

        fetch(`http://127.0.0.1:8000/conversation/${conversationId}`)
            .then(res => {
                if (!res.ok) throw new Error(`Failed to fetch history: ${res.status}`);
                return res.json();
            })
            .then(data => setHistory(data.messages ?? []))
            .catch(err => setError(err.message))
            .finally(() => setIsLoading(false));
    }, [conversationId]);

    return { history, isLoading, error };
}
