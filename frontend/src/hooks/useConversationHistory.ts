import { useEffect, useState } from "react";
import { fetchConversation } from "../api/conversations";

export function useConversationHistory(conversationId: string | null) {
    const [history, setHistory] = useState<Record<string, string>[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function refresh() {
        if (!conversationId) return;
        setIsLoading(true);
        setError(null);
        try {
            const data = await fetchConversation(conversationId);
            setHistory(data.messages ?? []);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to load history');
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        if (!conversationId) {
            setHistory([]);
            return;
        }
        refresh();
    }, [conversationId]);

    return { history, isLoading, error, refresh };
}
