import { useUser } from './hooks/useUser'
import { useConversation } from './hooks/useConversation'
import Chat from './components/Chat'
import SidePanel from './components/SidePanel'

function App() {
  const { user } = useUser()
  const {
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
    handleRename,
    handleDelete,
  } = useConversation(user?.id ?? null)

  return (
    <div className="flex h-screen">
      <SidePanel
        conversations={conversations}
        isLoading={conversationsLoading}
        error={conversationsError}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewConversation={() => setActiveConversationId(null)}
        onRename={handleRename}
        onDelete={handleDelete}
      />
      <section className="flex flex-col flex-1 p-6">
        <Chat
          text={text}
          isStreaming={isStreaming}
          onSend={handleSend}
          history={history}
          historyLoading={historyLoading}
        />
      </section>
    </div>
  )
}

export default App
