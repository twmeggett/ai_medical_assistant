export interface Message {
    role: string
    content: string
}

export interface Conversation {
    conversationId: string
    title: string | null
    createdAt: string
    updatedAt: string
}

export interface User {
    id: string
    createdAt: string
}
