import type { Conversation } from '../hooks/useUserConversations'

type SidePanelProps = {
    conversations: Conversation[]
    isLoading: boolean
    error: string | null
    activeConversationId: string | null
    onSelectConversation: (conversationId: string) => void
    onNewConversation: () => void
}

function conversationLabel(conversation: Conversation): string {
    if (conversation.title) return conversation.title
    const date = new Date(conversation.created_at)
    const formatted = date.toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
    return `Conversation created on - ${formatted}`
}

function SidePanel({ conversations, isLoading, error, activeConversationId, onSelectConversation, onNewConversation }: SidePanelProps) {
    return (
        <aside className="w-64 h-full flex flex-col p-4 border-r border-gray-200">
            {isLoading && <p className="text-sm text-gray-400">Loading...</p>}
            {error && <p className="text-sm text-red-400">{error}</p>}
            <ul className="flex flex-col gap-1 flex-1">
                {conversations.map(conversation => (
                    <li key={conversation.conversation_id}>
                        <button
                            onClick={() => onSelectConversation(conversation.conversation_id)}
                            className={`text-left text-sm w-full bg-transparent border-none cursor-pointer p-0 ${
                                activeConversationId === conversation.conversation_id
                                    ? 'underline'
                                    : ''
                            }`}
                        >
                            {conversationLabel(conversation)}
                        </button>
                    </li>
                ))}
            </ul>
            <button
                onClick={onNewConversation}
                className="mt-4 w-full text-sm py-2 px-3 rounded-md border border-gray-300 hover:bg-gray-100 transition-colors cursor-pointer"
            >
                + New Conversation
            </button>
        </aside>
    )
}

export default SidePanel
