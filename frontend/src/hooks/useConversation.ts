import { useEffect, useState } from 'react'
import { useChatStream } from './useChatStream'
import { useUserConversations } from './useUserConversations'
import { createConversation, deleteConversation, fetchConversation, updateConversationTitle } from '../api/conversations'
import type { Message } from '../types'

export function useConversation(userId: string | null) {
    const { text, isStreaming, sendMessage, clearText } = useChatStream()
    const { conversations, isLoading: conversationsLoading, error: conversationsError, refresh: refreshConversations } = useUserConversations(userId)

    const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
    const [localMessages, setLocalMessages] = useState<Message[]>([])
    const [historyLoading, setHistoryLoading] = useState(false)

    // Auto-select the most recently updated conversation on first load
    useEffect(() => {
        if (conversations.length > 0 && !activeConversationId) {
            selectConversation(conversations[0].conversation_id)
        }
    }, [conversations])

    // Fetch history from the DB and set it as the local message state
    async function selectConversation(conversationId: string) {
        setActiveConversationId(conversationId)
        clearText()
        setHistoryLoading(true)
        try {
            const data = await fetchConversation(conversationId)
            setLocalMessages(data.messages ?? [])
        } finally {
            setHistoryLoading(false)
        }
    }

    // Clear local state when starting a new conversation
    function newConversation() {
        setActiveConversationId(null)
        setLocalMessages([])
        clearText()
    }

    async function handleSend(message: string) {
        let conversationId = activeConversationId

        // Append the user message immediately — no separate optimistic state needed
        setLocalMessages(prev => [...prev, { role: 'user', content: message }])

        // Create a conversation if one doesn't exist yet
        if (!conversationId && userId) {
            conversationId = await createConversation(userId)
            setActiveConversationId(conversationId)
        }

        if (!conversationId) return

        // Stream the response, then atomically clear streaming text and append the
        // complete assistant message — React 18 batches both updates into one render
        const assistantText = await sendMessage(conversationId, message)
        setLocalMessages(prev => [...prev, { role: 'assistant', content: assistantText }])
        clearText()

        // Refresh sidebar to pick up the auto-generated title and updated ordering
        refreshConversations()
    }

    async function handleRename(conversationId: string, title: string) {
        await updateConversationTitle(conversationId, title)
        refreshConversations()
    }

    async function handleDelete(conversationId: string) {
        await deleteConversation(conversationId)
        if (activeConversationId === conversationId) {
            newConversation()
        }
        refreshConversations()
    }

    return {
        text,
        isStreaming,
        conversations,
        conversationsLoading,
        conversationsError,
        activeConversationId,
        selectConversation,
        newConversation,
        history: localMessages,
        historyLoading,
        handleSend,
        handleRename,
        handleDelete,
    }
}
