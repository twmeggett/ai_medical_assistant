import { useEffect, useState } from 'react'
import { useChatStream } from './useChatStream'
import { useUserConversations } from './useUserConversations'
import { useConversationHistory } from './useConversationHistory'
import { createConversation } from '../api/conversations'

export function useConversation(userId: string | null) {
    // Streaming text and state from the Claude API
    const { text, isStreaming, sendMessage, clearText } = useChatStream()

    // List of conversations for the sidebar
    const { conversations, isLoading: conversationsLoading, error: conversationsError, refresh: refreshConversations } = useUserConversations(userId)

    // The conversation currently open in the chat view
    const [activeConversationId, setActiveConversationId] = useState<string | null>(null)

    // Persisted messages for the active conversation, fetched from the DB
    const { history, isLoading: historyLoading, refresh: refreshHistory } = useConversationHistory(activeConversationId)

    // Shown immediately after the user sends, before the DB re-fetch confirms it
    const [optimisticMessage, setOptimisticMessage] = useState<string | null>(null)

    // Auto-select the most recently updated conversation on first load
    useEffect(() => {
        if (conversations.length > 0 && !activeConversationId) {
            setActiveConversationId(conversations[0].conversation_id)
        }
    }, [conversations])

    // Clear streaming text and the optimistic message whenever the active conversation changes
    useEffect(() => {
        clearText()
        setOptimisticMessage(null)
    }, [activeConversationId])

    async function handleSend(message: string) {
        let conversationId = activeConversationId

        // Show the user's message immediately while the rest of the flow runs
        setOptimisticMessage(message)

        // If there is no active conversation, create one before streaming
        if (!conversationId && userId) {
            conversationId = await createConversation(userId)
            setActiveConversationId(conversationId)
            refreshConversations()
        }

        if (conversationId) {
            // Stream the assistant response, then re-fetch history so the DB
            // version (user + assistant messages) replaces the optimistic message
            await sendMessage(conversationId, message)
            await refreshHistory()
            setOptimisticMessage(null)
        }
    }

    // Append the optimistic message to the end of DB history until the re-fetch resolves
    const displayHistory = optimisticMessage
        ? [...history, { role: 'user', content: optimisticMessage }]
        : history

    return {
        text,
        isStreaming,
        conversations,
        conversationsLoading,
        conversationsError,
        activeConversationId,
        setActiveConversationId,
        history: displayHistory,
        historyLoading,
        handleSend,
    }
}
