import { useState } from 'react'
import { useChatStream } from '../hooks/useChatStream'

type ChatProps = {
  text: string
  isStreaming: boolean
  sendMessage: ReturnType<typeof useChatStream>["sendMessage"]
  conversationId: string
}

function Chat({ text, isStreaming, sendMessage, conversationId }: ChatProps) {
  const [input, setInput] = useState('')

  function handleSend() {
    if (!input.trim()) return
    sendMessage(conversationId, input)
    setInput('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat">
      <div className="chat-response">
        {text && <p>{text}</p>}
        {isStreaming && <span className="streaming-indicator">Streaming...</span>}
      </div>
      <div className="chat-input">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          placeholder="Ask a medical question..."
          rows={3}
        />
        <button onClick={handleSend} disabled={isStreaming || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}

export default Chat
