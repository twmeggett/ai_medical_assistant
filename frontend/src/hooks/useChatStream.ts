import { useCallback, useState } from "react";
import { streamChatResponse } from "../api/chat";

export function useChatStream() {
    const [text, setText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    const sendMessage = useCallback(async (
        conversationId: string,
        message: string,
    ): Promise<string> => {
        setText('');
        setIsStreaming(true);

        let accumulated = '';
        for await (const chunk of streamChatResponse(conversationId, message)) {
            accumulated += chunk;
            setText(prev => prev + chunk);
        }

        setIsStreaming(false);
        return accumulated;
    }, [])

    const clearText = () => setText('')

    return { text, isStreaming, sendMessage, clearText };
}
