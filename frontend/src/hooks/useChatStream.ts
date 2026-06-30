import { useCallback, useState } from "react";
import { streamChatResponse } from "../api/chat";

export function useChatStream() {
    const [text, setText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    const sendMessage = useCallback(async (conversationId: string, message: string) => {
        setText('');
        setIsStreaming(true);

        for await (const chunk of streamChatResponse(conversationId, message)) {
            setText(prev => prev + chunk);
        }

        setIsStreaming(false);
    }, [])

    const clearText = () => setText('')

    return { text, isStreaming, sendMessage, clearText };
}
