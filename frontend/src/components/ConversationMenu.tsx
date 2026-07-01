import { useEffect, useRef, useState } from 'react'

type ConversationMenuProps = {
  onRename: () => void
  onDelete: () => void
}

function ConversationMenu({ onRename, onDelete }: ConversationMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleMenuClick(e: React.MouseEvent) {
    e.stopPropagation()
    setIsOpen(prev => !prev)
  }

  function handleRename() {
    setIsOpen(false)
    onRename()
  }

  function handleDelete() {
    setIsOpen(false)
    onDelete()
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={handleMenuClick}
        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-800 transition-opacity"
        aria-label="Conversation actions"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="5" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="19" r="2" />
        </svg>
      </button>
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-10 w-36 rounded-md border border-gray-200 bg-white shadow-md py-1">
          <button
            onClick={handleRename}
            className="w-full text-left text-sm px-3 py-2 hover:bg-gray-100"
          >
            Rename
          </button>
          <button
            onClick={handleDelete}
            className="w-full text-left text-sm px-3 py-2 hover:bg-gray-100 text-red-600"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  )
}

export default ConversationMenu
