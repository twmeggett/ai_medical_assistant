import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConversationMenu from './ConversationMenu'

const defaultProps = {
  onRename: vi.fn(),
  onDelete: vi.fn(),
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ConversationMenu', () => {
  it('does not show the dropdown by default', () => {
    render(<ConversationMenu {...defaultProps} />)
    expect(screen.queryByText('Rename')).not.toBeInTheDocument()
    expect(screen.queryByText('Delete')).not.toBeInTheDocument()
  })

  it('opens the dropdown when the icon button is clicked', () => {
    render(<ConversationMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /conversation actions/i }))
    expect(screen.getByText('Rename')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('closes the dropdown when the icon button is clicked again', () => {
    render(<ConversationMenu {...defaultProps} />)
    const trigger = screen.getByRole('button', { name: /conversation actions/i })
    fireEvent.click(trigger)
    fireEvent.click(trigger)
    expect(screen.queryByText('Rename')).not.toBeInTheDocument()
  })

  it('calls onRename and closes the dropdown when Rename is clicked', () => {
    render(<ConversationMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /conversation actions/i }))
    fireEvent.click(screen.getByText('Rename'))
    expect(defaultProps.onRename).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('Rename')).not.toBeInTheDocument()
  })

  it('calls onDelete and closes the dropdown when Delete is clicked', () => {
    render(<ConversationMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /conversation actions/i }))
    fireEvent.click(screen.getByText('Delete'))
    expect(defaultProps.onDelete).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('Delete')).not.toBeInTheDocument()
  })

  it('closes the dropdown when clicking outside', () => {
    render(
      <div>
        <ConversationMenu {...defaultProps} />
        <div data-testid="outside">Outside</div>
      </div>
    )
    fireEvent.click(screen.getByRole('button', { name: /conversation actions/i }))
    expect(screen.getByText('Rename')).toBeInTheDocument()
    fireEvent.mouseDown(screen.getByTestId('outside'))
    expect(screen.queryByText('Rename')).not.toBeInTheDocument()
  })
})
