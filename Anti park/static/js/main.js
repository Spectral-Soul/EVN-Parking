// Global UI Handlers

function toggleSidebar() {
    const p = document.getElementById('ai-panel');
    if (p.classList.contains('scale-0')) {
        p.classList.remove('scale-0', 'opacity-0', 'pointer-events-none');
    } else {
        p.classList.add('scale-0', 'opacity-0', 'pointer-events-none');
    }
}

document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
    const sb = document.getElementById('sidebar');
    if (sb.classList.contains('-translate-x-full')) {
        sb.classList.remove('-translate-x-full');
    } else {
        sb.classList.add('-translate-x-full');
    }
});

// AI Chat Logic
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    appendMessage(msg, 'user');
    input.value = '';
    
    // show typing indicator optionally
    
    try {
        const data = await API.post('/api/ai/chat', { message: msg });
        appendMessage(data.reply, 'ai');
        // If the AI created/deleted a slot, reload the map
        if (data.action === 'reload_map' && typeof loadFloor === 'function') {
            setTimeout(() => loadFloor(currentFloor), 500);
        }
    } catch (e) {
        appendMessage("Sorry, I encountered an error connecting to my brain.", 'ai');
    }
}

function appendMessage(text, role) {
    const container = document.getElementById('chat-messages');
    if(!container) return;
    const div = document.createElement('div');
    
    if (role === 'user') {
        div.className = "flex justify-end";
        div.innerHTML = `<div class="bg-indigo-600 text-white px-4 py-2 rounded-2xl rounded-tr-sm text-sm max-w-[80%]">${text}</div>`;
    } else {
        div.className = "flex justify-start gap-2";
        div.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-indigo-500/20 flex-shrink-0 flex items-center justify-center text-indigo-400 mt-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <div class="bg-white/10 text-slate-200 px-4 py-2 rounded-2xl rounded-tl-sm text-sm max-w-[80%]">${text}</div>
        `;
    }
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Global enter key listener for chat input
document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});
