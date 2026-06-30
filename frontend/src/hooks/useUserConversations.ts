import { useEffect, useState } from "react";
import { fetchUserConversations } from "../api/conversations";

export type Conversation = {
    conversation_id: string
    title: string | null
    created_at: string
    updated_at: string
}

export function useUserConversations(userId: string | null) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    function refresh() {
        if (!userId) return;

        setIsLoading(true);
        setError(null);

        fetchUserConversations(userId)
            .then(data => setConversations(data))
            .catch(err => setError(err.message))
            .finally(() => setIsLoading(false));
    }

    useEffect(() => {
        refresh();
    }, [userId]);

    return { conversations, isLoading, error, refresh };
}
