import { useEffect, useRef, useState } from 'react'

type Message = Record<string, string>

type ChatProps = {
  text: string
  isStreaming: boolean
  onSend: (message: string) => void
  history: Message[]
  historyLoading: boolean
}

function Chat({ text, isStreaming, onSend, history, historyLoading }: ChatProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [text, history])

  function handleSend() {
    if (!input.trim()) return
    onSend(input)
    setInput('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
        {historyLoading && <p className="text-sm text-gray-400">Loading...</p>}
        {history.map((msg, i) => (
          <p key={i} className={`text-sm px-3 py-2 rounded-lg w-fit whitespace-pre-wrap ${msg.role === 'user' ? 'self-end bg-gray-700 text-white' : 'self-start text-left'}`}>
            {msg.content}
          </p>
        ))}
        {text && <p className="text-sm text-left whitespace-pre-wrap">{text}</p>}
        {isStreaming && <span className="text-xs text-gray-400">Streaming...</span>}
        <div ref={bottomRef} />
      </div>
      <div className="relative p-4 pb-6">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          placeholder="Ask a medical question..."
          rows={3}
          className="w-full resize-none rounded-lg p-3 pb-12 bg-white/10 text-sm focus:outline-none"
        />
      </div>
    </div>
  )
}

export default Chat
