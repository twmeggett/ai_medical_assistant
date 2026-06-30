export type User = {
    id: string
    created_at: string
}

export async function getUser(): Promise<User> {
    return {
        id: '00000000-0000-0000-0000-000000000001',
        created_at: new Date().toISOString(),
    }
}
