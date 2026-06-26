export async function* consumeStream(url: string, body: Record<string, any>): AsyncGenerator<string> {
    let response: Response;

    try {
        response = await fetch(url, {
            method: 'POST', // Works for GET or POST requests
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
    } catch (err) {
        console.error(`Network error calling ${url}:`, err)
        return;
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
        console.error(`Stream request to ${url} returned no readable body (status ${response.status}: ${response.statusText})`)
        return;
    }

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            yield decoder.decode(value);
        }
    } catch (err) {
        console.error(`Error reading stream from ${url}:`, err)
    }
}
