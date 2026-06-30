import type { Conversation } from '../hooks/useUserConversations'

const BASE = 'http://127.0.0.1:8000/conversation'

export async function createConversation(userId: string): Promise<string> {
    const res = await fetch(BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
    })
    if (!res.ok) throw new Error(`Failed to create conversation: ${res.status}`)
    const data = await res.json()
    return data.conversation_id
}

export async function fetchUserConversations(userId: string): Promise<Conversation[]> {
    const res = await fetch(`${BASE}/user/${userId}`)
    if (!res.ok) throw new Error(`Failed to fetch conversations: ${res.status}`)
    return res.json()
}

export async function fetchConversation(conversationId: string): Promise<{ messages: Record<string, string>[] }> {
    const res = await fetch(`${BASE}/${conversationId}`)
    if (!res.ok) throw new Error(`Failed to fetch conversation: ${res.status}`)
    return res.json()
}
