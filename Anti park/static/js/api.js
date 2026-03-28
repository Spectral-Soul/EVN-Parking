// API Wrapper
const API = {
    async get(endpoint) {
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    async post(endpoint, data) {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    }
};

async function logout() {
    try {
        await API.post('/auth/logout', {});
        window.location.href = '/login';
    } catch (e) {
        console.error(e);
    }
}
