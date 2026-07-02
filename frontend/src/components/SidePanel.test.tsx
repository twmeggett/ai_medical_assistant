import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SidePanel from './SidePanel'
import type { Conversation } from '../types'

const makeConversation = (id: string, overrides: Partial<Conversation> = {}): Conversation => ({
  conversationId: id,
  title: null,
  createdAt: '2024-06-15T10:30:00Z',
  updatedAt: '2024-06-15T10:30:00Z',
  ...overrides,
})

const defaultProps = {
  conversations: [],
  isLoading: false,
  error: null,
  activeConversationId: null,
  onSelectConversation: vi.fn(),
  onNewConversation: vi.fn(),
  onRename: vi.fn(),
  onDelete: vi.fn(),
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SidePanel', () => {
  it('renders the New Conversation button', () => {
    render(<SidePanel {...defaultProps} />)
    expect(screen.getByText('+ New Conversation')).toBeInTheDocument()
  })

  it('calls onNewConversation when button is clicked', () => {
    const onNewConversation = vi.fn()
    render(<SidePanel {...defaultProps} onNewConversation={onNewConversation} />)
    fireEvent.click(screen.getByText('+ New Conversation'))
    expect(onNewConversation).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<SidePanel {...defaultProps} isLoading={true} />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(<SidePanel {...defaultProps} error="Failed to load" />)
    expect(screen.getByText('Failed to load')).toBeInTheDocument()
  })

  it('renders a conversation button with a label', () => {
    const conversations = [makeConversation('conv_1')]
    render(<SidePanel {...defaultProps} conversations={conversations} />)
    expect(screen.getByText(/Conversation created on/i)).toBeInTheDocument()
  })

  it('renders conversation title when set', () => {
    const conversations = [makeConversation('conv_1', { title: 'Metformin dosing' })]
    render(<SidePanel {...defaultProps} conversations={conversations} />)
    expect(screen.getByText('Metformin dosing')).toBeInTheDocument()
  })

  it('calls onSelectConversation with the correct id when clicked', () => {
    const onSelect = vi.fn()
    const conversations = [makeConversation('conv_42')]
    render(<SidePanel {...defaultProps} conversations={conversations} onSelectConversation={onSelect} />)
    fireEvent.click(screen.getByText(/Conversation created on/i))
    expect(onSelect).toHaveBeenCalledWith('conv_42')
  })

  it('underlines the active conversation', () => {
    const conversations = [makeConversation('conv_1'), makeConversation('conv_2', { title: 'Second' })]
    render(<SidePanel {...defaultProps} conversations={conversations} activeConversationId="conv_1" />)
    const firstButton = screen.getByText(/Conversation created on/i)
    expect(firstButton).toHaveClass('underline')
    const secondButton = screen.getByText('Second')
    expect(secondButton).not.toHaveClass('underline')
  })

  it('renders multiple conversations', () => {
    const conversations = [
      makeConversation('conv_1', { title: 'First' }),
      makeConversation('conv_2', { title: 'Second' }),
      makeConversation('conv_3', { title: 'Third' }),
    ]
    render(<SidePanel {...defaultProps} conversations={conversations} />)
    expect(screen.getAllByRole('button').length).toBe(7) // 3 conversations + 3 menu buttons + New Conversation
  })
})
