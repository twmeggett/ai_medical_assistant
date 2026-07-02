import { useState } from 'react'
import ConversationMenu from './ConversationMenu'
import type { Conversation } from '../types'

type SidePanelProps = {
    conversations: Conversation[]
    isLoading: boolean
    error: string | null
    activeConversationId: string | null
    onSelectConversation: (conversationId: string) => void
    onNewConversation: () => void
    onRename: (conversationId: string, title: string) => void
    onDelete: (conversationId: string) => void
}

function conversationLabel(conversation: Conversation): string {
    if (conversation.title) return conversation.title
    const date = new Date(conversation.createdAt)
    const formatted = date.toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
    return `Conversation created on - ${formatted}`
}

function SidePanel({ conversations, isLoading, error, activeConversationId, onSelectConversation, onNewConversation, onRename, onDelete }: SidePanelProps) {
    const [editingId, setEditingId] = useState<string | null>(null)
    const [editTitle, setEditTitle] = useState('')

    function startRename(conversation: Conversation) {
        setEditingId(conversation.conversationId)
        setEditTitle(conversationLabel(conversation))
    }

    function commitRename(conversationId: string) {
        if (editTitle.trim()) {
            onRename(conversationId, editTitle.trim())
        }
        setEditingId(null)
    }

    function handleRenameKeyDown(e: React.KeyboardEvent<HTMLInputElement>, conversationId: string) {
        if (e.key === 'Enter') commitRename(conversationId)
        if (e.key === 'Escape') setEditingId(null)
    }

    return (
        <aside className="w-64 h-full flex flex-col p-4 border-r border-gray-200">
            {isLoading && <p className="text-sm text-gray-400">Loading...</p>}
            {error && <p className="text-sm text-red-400">{error}</p>}
            <ul className="flex flex-col gap-1 flex-1">
                {conversations.map(conversation => (
                    <li key={conversation.conversationId} className="group flex items-center justify-between gap-1">
                        {editingId === conversation.conversationId ? (
                            <input
                                autoFocus
                                value={editTitle}
                                onChange={e => setEditTitle(e.target.value)}
                                onBlur={() => commitRename(conversation.conversationId)}
                                onKeyDown={e => handleRenameKeyDown(e, conversation.conversationId)}
                                className="flex-1 text-sm bg-white border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-gray-400"
                            />
                        ) : (
                            <>
                                <button
                                    onClick={() => onSelectConversation(conversation.conversationId)}
                                    className={`flex-1 text-left text-sm bg-transparent border-none cursor-pointer p-0 truncate ${
                                        activeConversationId === conversation.conversationId ? 'underline' : ''
                                    }`}
                                >
                                    {conversationLabel(conversation)}
                                </button>
                                <ConversationMenu
                                    onRename={() => startRename(conversation)}
                                    onDelete={() => onDelete(conversation.conversationId)}
                                />
                            </>
                        )}
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
