import { useEffect, useState } from 'react'
import { useChatStream } from './useChatStream'
import { useUserConversations } from './useUserConversations'
import { useConversationHistory } from './useConversationHistory'
import { createConversation } from '../api/conversations'

export function useConversation(userId: string | null) {
    const { text, isStreaming, sendMessage, clearText } = useChatStream()
    const { conversations, isLoading: conversationsLoading, error: conversationsError, refresh: refreshConversations } = useUserConversations(userId)
    const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
    const { history, isLoading: historyLoading } = useConversationHistory(activeConversationId)

    useEffect(() => {
        if (conversations.length > 0 && !activeConversationId) {
            setActiveConversationId(conversations[0].conversation_id)
        }
    }, [conversations])

    useEffect(() => {
        clearText()
    }, [activeConversationId])

    async function handleSend(message: string) {
        let conversationId = activeConversationId

        if (!conversationId && userId) {
            conversationId = await createConversation(userId)
            setActiveConversationId(conversationId)
            refreshConversations()
        }

        if (conversationId) sendMessage(conversationId, message)
    }

    return {
        text,
        isStreaming,
        conversations,
        conversationsLoading,
        conversationsError,
        activeConversationId,
        setActiveConversationId,
        history,
        historyLoading,
        handleSend,
    }
}
