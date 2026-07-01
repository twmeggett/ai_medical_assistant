import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chat from './Chat'

const defaultProps = {
  text: '',
  isStreaming: false,
  onSend: vi.fn(),
  history: [],
  historyLoading: false,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Chat', () => {
  it('renders the textarea placeholder', () => {
    render(<Chat {...defaultProps} />)
    expect(screen.getByPlaceholderText('Ask a medical question...')).toBeInTheDocument()
  })

  it('calls onSend with the input value when Send is triggered via Enter', async () => {
    const onSend = vi.fn()
    render(<Chat {...defaultProps} onSend={onSend} />)
    const textarea = screen.getByPlaceholderText('Ask a medical question...')
    await userEvent.type(textarea, 'What is metformin?')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalledWith('What is metformin?')
  })

  it('clears the input after sending', async () => {
    render(<Chat {...defaultProps} />)
    const textarea = screen.getByPlaceholderText('Ask a medical question...')
    await userEvent.type(textarea, 'hello')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect((textarea as HTMLTextAreaElement).value).toBe('')
  })

  it('does not call onSend with an empty or whitespace-only message', async () => {
    const onSend = vi.fn()
    render(<Chat {...defaultProps} onSend={onSend} />)
    const textarea = screen.getByPlaceholderText('Ask a medical question...')
    await userEvent.type(textarea, '   ')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('Shift+Enter does not send the message', async () => {
    const onSend = vi.fn()
    render(<Chat {...defaultProps} onSend={onSend} />)
    const textarea = screen.getByPlaceholderText('Ask a medical question...')
    await userEvent.type(textarea, 'hello')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables the textarea while streaming', () => {
    render(<Chat {...defaultProps} isStreaming={true} />)
    expect(screen.getByPlaceholderText('Ask a medical question...')).toBeDisabled()
  })

  it('renders history messages with correct styles', () => {
    const history = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there' },
    ]
    render(<Chat {...defaultProps} history={history} />)
    const userMsg = screen.getByText('Hello')
    const assistantMsg = screen.getByText('Hi there')
    expect(userMsg).toHaveClass('bg-gray-700')
    expect(assistantMsg).toHaveClass('self-start')
  })

  it('shows streaming text when provided', () => {
    render(<Chat {...defaultProps} text="Streaming..." />)
    expect(screen.getByText('Streaming...')).toBeInTheDocument()
  })

  it('shows the loading indicator while history is loading', () => {
    render(<Chat {...defaultProps} historyLoading={true} />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows Streaming... indicator while isStreaming', () => {
    render(<Chat {...defaultProps} isStreaming={true} />)
    expect(screen.getByText('Streaming...')).toBeInTheDocument()
  })
})
