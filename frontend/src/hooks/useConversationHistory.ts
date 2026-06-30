import { useEffect, useState } from "react";
import { fetchConversation } from "../api/conversations";

export function useConversationHistory(conversationId: string | null) {
    const [history, setHistory] = useState<Record<string, string>[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        if (!conversationId) {
            setHistory([]);
            return;
        }

        setIsLoading(true);
        setError(null);
        setHistory([])

        fetchConversation(conversationId)
            .then(data => setHistory(data.messages ?? []))
            .catch(err => setError(err.message))
            .finally(() => setIsLoading(false));
    }, [conversationId]);

    return { history, isLoading, error };
}
