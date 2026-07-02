import type { User } from '../types'

export async function getUser(): Promise<User> {
    return {
        id: '00000000-0000-0000-0000-000000000001',
        createdAt: new Date().toISOString(),
    }
}
