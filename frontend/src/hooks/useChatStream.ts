import { useCallback, useState } from "react";
import { consumeStream } from "../utils/consumeStream";

export function useChatStream() {
    const [text, setText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    const sendMessage = useCallback(async (conversationId: string, message: string) => {
        setText('');
        setIsStreaming(true);

        for await (
            const chunk of consumeStream(
                'http://127.0.0.1:8000/chat/stream',
                { conversation_id: conversationId, message }
            )
        ) {
            setText(prev => prev + chunk);
        }

        setIsStreaming(false);
    }, [])

    return { text, isStreaming, sendMessage };
}
