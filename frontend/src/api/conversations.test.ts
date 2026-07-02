import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchUserConversations } from './conversations'

const mockConversations = [
    {
        conversation_id: 'abc-123',
        title: 'Metformin dosing',
        created_at: '2024-06-15T10:30:00Z',
        updated_at: '2024-06-15T11:00:00Z',
    },
    {
        conversation_id: 'def-456',
        title: null,
        created_at: '2024-06-16T09:00:00Z',
        updated_at: '2024-06-16T09:00:00Z',
    },
]

function mockFetch(data: unknown, status = 200) {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: status >= 200 && status < 300,
        status,
        json: () => Promise.resolve(data),
    }))
}

beforeEach(() => vi.stubGlobal('fetch', vi.fn()))
afterEach(() => vi.unstubAllGlobals())

describe('fetchUserConversations', () => {
    it('maps snake_case fields to camelCase', async () => {
        mockFetch(mockConversations)
        const result = await fetchUserConversations('user_1')
        expect(result[0].conversationId).toBe('abc-123')
        expect(result[0].createdAt).toBe('2024-06-15T10:30:00Z')
        expect(result[0].updatedAt).toBe('2024-06-15T11:00:00Z')
    })

    it('preserves title when set', async () => {
        mockFetch(mockConversations)
        const result = await fetchUserConversations('user_1')
        expect(result[0].title).toBe('Metformin dosing')
    })

    it('returns null title when missing', async () => {
        mockFetch(mockConversations)
        const result = await fetchUserConversations('user_1')
        expect(result[1].title).toBeNull()
    })

    it('returns an empty array when the user has no conversations', async () => {
        mockFetch([])
        const result = await fetchUserConversations('user_1')
        expect(result).toEqual([])
    })

    it('throws when the response is not ok', async () => {
        mockFetch(null, 500)
        await expect(fetchUserConversations('user_1')).rejects.toThrow('Failed to fetch conversations: 500')
    })
})
