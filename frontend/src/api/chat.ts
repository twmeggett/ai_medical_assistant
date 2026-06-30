import { consumeStream } from '../utils/consumeStream'

const BASE = 'http://127.0.0.1:8000/chat'

export function streamChatResponse(conversationId: string, message: string): AsyncGenerator<string> {
    return consumeStream(`${BASE}/stream`, { conversation_id: conversationId, message })
}
