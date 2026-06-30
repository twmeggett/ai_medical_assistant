import { useEffect, useState } from 'react'
import { getUser, type User } from '../api/user'

export function useUser() {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        getUser()
            .then(setUser)
            .catch(err => setError(err.message))
            .finally(() => setIsLoading(false))
    }, [])

    return { user, isLoading, error }
}
