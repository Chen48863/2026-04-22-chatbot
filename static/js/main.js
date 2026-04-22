/**
 * 智慧聊天機器人 - 前端互動邏輯
 * 功能：聊天室管理、訊息收發、檔案上傳、回答控制、記憶機制
 */

// === 狀態管理 ===
let currentSessionId = null;
let isGenerating = false;

// === DOM 元素 ===
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const sessionList = document.getElementById('sessionList');
const chatMessages = document.getElementById('chatMessages');
const chatInputArea = document.getElementById('chatInputArea');
const chatTitle = document.getElementById('chatTitle');
const welcomeScreen = document.getElementById('welcomeScreen');
const messageInput = document.getElementById('messageInput');
const btnSend = document.getElementById('btnSend');
const btnStop = document.getElementById('btnStop');
const btnNewChat = document.getElementById('btnNewChat');
const btnAttach = document.getElementById('btnAttach');
const fileInput = document.getElementById('fileInput');
const btnSettings = document.getElementById('btnSettings');
const settingsModal = document.getElementById('settingsModal');
const renameModal = document.getElementById('renameModal');

// === 初始化 ===
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    setupEventListeners();
});

function setupEventListeners() {
    // 新增聊天室
    btnNewChat.addEventListener('click', createNewSession);

    // 發送訊息
    btnSend.addEventListener('click', sendMessage);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);

    // 中止生成
    btnStop.addEventListener('click', stopGeneration);

    // 檔案上傳
    btnAttach.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);

    // 側邊欄切換（手機版）
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

    // 設定面板
    btnSettings.addEventListener('click', openSettings);
    document.getElementById('btnCloseSettings').addEventListener('click', closeSettings);
    document.getElementById('btnCancelSettings').addEventListener('click', closeSettings);
    document.getElementById('btnSaveSettings').addEventListener('click', saveSettings);

    // 重新命名面板
    document.getElementById('btnCloseRename').addEventListener('click', closeRename);
    document.getElementById('btnCancelRename').addEventListener('click', closeRename);
    document.getElementById('btnConfirmRename').addEventListener('click', confirmRename);

    // 點擊 overlay 關閉 modal
    settingsModal.addEventListener('click', (e) => { if (e.target === settingsModal) closeSettings(); });
    renameModal.addEventListener('click', (e) => { if (e.target === renameModal) closeRename(); });
}

// === 聊天室管理 ===

async function loadSessions() {
    try {
        const res = await fetch('/api/sessions');
        const sessions = await res.json();
        renderSessionList(sessions);
    } catch (err) {
        console.error('載入聊天室失敗：', err);
    }
}

function renderSessionList(sessions) {
    sessionList.innerHTML = '';
    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = `session-item${s.id === currentSessionId ? ' active' : ''}`;
        item.dataset.id = s.id;
        item.innerHTML = `
            <span class="session-item-icon">💬</span>
            <div class="session-item-content">
                <div class="session-item-title">${escapeHtml(s.title)}</div>
                <div class="session-item-preview">${escapeHtml(s.last_message || '')}</div>
            </div>
            <div class="session-item-actions">
                <button class="btn-rename" title="重新命名" onclick="event.stopPropagation(); openRename(${s.id}, '${escapeHtml(s.title)}')">✏️</button>
                <button class="btn-delete" title="刪除" onclick="event.stopPropagation(); deleteSession(${s.id})">🗑️</button>
            </div>
        `;
        item.addEventListener('click', () => switchSession(s.id));
        sessionList.appendChild(item);
    });
}

async function createNewSession() {
    try {
        const res = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: '新對話' })
        });
        const session = await res.json();
        currentSessionId = session.id;
        await loadSessions();
        showChatArea(session.title);
        chatMessages.innerHTML = '';
        sidebar.classList.remove('open');
    } catch (err) {
        console.error('建立聊天室失敗：', err);
    }
}

async function switchSession(sessionId) {
    currentSessionId = sessionId;
    try {
        const res = await fetch(`/api/sessions/${sessionId}`);
        const data = await res.json();
        showChatArea(data.title);
        renderMessages(data.messages);
        await loadSessions();
        sidebar.classList.remove('open');
    } catch (err) {
        console.error('切換聊天室失敗：', err);
    }
}

async function deleteSession(sessionId) {
    if (!confirm('確定要刪除這個聊天室嗎？所有對話記錄將被永久刪除。')) return;
    try {
        await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            showWelcome();
        }
        await loadSessions();
    } catch (err) {
        console.error('刪除聊天室失敗：', err);
    }
}

// === 重新命名 ===
let renameTargetId = null;

function openRename(sessionId, currentTitle) {
    renameTargetId = sessionId;
    document.getElementById('renameInput').value = currentTitle;
    renameModal.style.display = 'flex';
    document.getElementById('renameInput').focus();
}

function closeRename() {
    renameModal.style.display = 'none';
    renameTargetId = null;
}

async function confirmRename() {
    const newTitle = document.getElementById('renameInput').value.trim();
    if (!newTitle || !renameTargetId) return;
    try {
        await fetch(`/api/sessions/${renameTargetId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (currentSessionId === renameTargetId) {
            chatTitle.querySelector('h2').textContent = newTitle;
        }
        closeRename();
        await loadSessions();
    } catch (err) {
        console.error('重新命名失敗：', err);
    }
}

// === UI 切換 ===

function showWelcome() {
    chatTitle.innerHTML = '<h2>歡迎使用智慧聊天機器人</h2><span class="chat-subtitle">選擇或建立一個對話開始聊天</span>';
    chatMessages.innerHTML = `
        <div class="welcome-screen">
            <div class="welcome-icon">🤖</div>
            <h1>智慧聊天機器人</h1>
            <p>點擊左上角「＋」建立新對話，開始聊天吧！</p>
            <div class="welcome-features">
                <div class="feature-card"><span class="feature-icon">💬</span><span>多輪對話</span></div>
                <div class="feature-card"><span class="feature-icon">📎</span><span>檔案上傳</span></div>
                <div class="feature-card"><span class="feature-icon">🔄</span><span>重新生成</span></div>
                <div class="feature-card"><span class="feature-icon">🧠</span><span>記憶機制</span></div>
            </div>
        </div>`;
    chatInputArea.style.display = 'none';
}

function showChatArea(title) {
    chatTitle.innerHTML = `<h2>${escapeHtml(title)}</h2>`;
    chatInputArea.style.display = 'block';
    messageInput.focus();
}

// === 訊息渲染 ===

function renderMessages(messages) {
    chatMessages.innerHTML = '';
    messages.forEach(msg => appendMessage(msg));
    scrollToBottom();
}

function appendMessage(msg) {
    const div = document.createElement('div');
    div.className = `message ${msg.role}`;
    div.dataset.id = msg.id;

    const avatar = msg.role === 'user' ? '👤' : '🤖';
    const roleName = msg.role === 'user' ? '您' : 'AI 助手';
    const time = new Date(msg.timestamp).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });

    let attachmentsHtml = '';
    if (msg.attachments && msg.attachments.length > 0) {
        msg.attachments.forEach(att => {
            if (att.file_type && att.file_type.startsWith('image/')) {
                attachmentsHtml += `<img class="attachment-image" src="${att.url}" alt="${escapeHtml(att.filename)}">`;
            } else {
                const size = (att.file_size / 1024).toFixed(1);
                attachmentsHtml += `
                    <div class="message-attachment">
                        <span class="attachment-icon">📄</span>
                        <div class="attachment-info">
                            <div class="attachment-name">${escapeHtml(att.filename)}</div>
                            <div class="attachment-size">${size} KB</div>
                        </div>
                    </div>`;
            }
        });
    }

    let actionsHtml = '';
    if (msg.role === 'assistant') {
        actionsHtml = `
            <div class="message-actions">
                <button onclick="regenerateReply()">🔄 重新生成</button>
                <button onclick="copyMessage(this)">📋 複製</button>
            </div>`;
    }

    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-body">
            <div class="message-header">
                <span class="message-role">${roleName}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content">${escapeHtml(msg.content)}</div>
            ${attachmentsHtml}
            ${actionsHtml}
        </div>`;
    chatMessages.appendChild(div);
}

// === 發送訊息 ===

async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content || !currentSessionId || isGenerating) return;

    messageInput.value = '';
    messageInput.style.height = 'auto';
    btnSend.disabled = true;

    // 顯示使用者訊息（即時）
    const tempUserMsg = {
        id: 'temp-user',
        role: 'user',
        content: content,
        timestamp: new Date().toISOString(),
        attachments: []
    };
    appendMessage(tempUserMsg);
    scrollToBottom();

    // 顯示載入動畫
    showTypingIndicator();
    setGenerating(true);

    try {
        const res = await fetch(`/api/sessions/${currentSessionId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const data = await res.json();

        // 移除暫時訊息與載入動畫
        removeTypingIndicator();
        const tempEl = chatMessages.querySelector('[data-id="temp-user"]');
        if (tempEl) tempEl.remove();

        // 顯示正式訊息
        appendMessage(data.user_message);
        appendMessage(data.ai_message);
        scrollToBottom();

        // 更新側邊欄
        await loadSessions();
    } catch (err) {
        console.error('發送訊息失敗：', err);
        removeTypingIndicator();
        alert('發送訊息失敗，請重試。');
    } finally {
        setGenerating(false);
    }
}

// === 回答控制 ===

async function regenerateReply() {
    if (!currentSessionId || isGenerating) return;

    // 移除最後一則 AI 訊息 DOM
    const aiMessages = chatMessages.querySelectorAll('.message.assistant');
    const lastAiMsg = aiMessages[aiMessages.length - 1];
    if (lastAiMsg) lastAiMsg.remove();

    showTypingIndicator();
    setGenerating(true);

    try {
        const res = await fetch(`/api/sessions/${currentSessionId}/regenerate`, { method: 'POST' });
        const data = await res.json();
        removeTypingIndicator();
        appendMessage(data);
        scrollToBottom();
    } catch (err) {
        console.error('重新生成失敗：', err);
        removeTypingIndicator();
        alert('重新生成失敗，請重試。');
    } finally {
        setGenerating(false);
    }
}

function stopGeneration() {
    // Mock 模式下模擬中止
    setGenerating(false);
    removeTypingIndicator();
}

function setGenerating(val) {
    isGenerating = val;
    btnSend.style.display = val ? 'none' : 'flex';
    btnStop.style.display = val ? 'flex' : 'none';
}

// === 檔案上傳 ===

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file || !currentSessionId) return;

    // 驗證大小
    if (file.size > 10 * 1024 * 1024) {
        alert('檔案大小超過 10MB 限制');
        fileInput.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', currentSessionId);

    showTypingIndicator();
    setGenerating(true);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (!res.ok) {
            alert(data.detail || '上傳失敗');
            return;
        }

        removeTypingIndicator();
        appendMessage(data.user_message);
        appendMessage(data.ai_message);
        scrollToBottom();
        await loadSessions();
    } catch (err) {
        console.error('檔案上傳失敗：', err);
        removeTypingIndicator();
        alert('檔案上傳失敗，請重試。');
    } finally {
        setGenerating(false);
        fileInput.value = '';
    }
}

// === 設定（記憶機制） ===

async function openSettings() {
    try {
        const res = await fetch('/api/memory');
        const memories = await res.json();
        const memMap = {};
        memories.forEach(m => { memMap[m.key] = m.value; });

        document.getElementById('settingName').value = memMap['display_name'] || '';
        document.getElementById('settingLanguage').value = memMap['language'] || '繁體中文';
        document.getElementById('settingStyle').value = memMap['reply_style'] || '友善';
        settingsModal.style.display = 'flex';
    } catch (err) {
        console.error('載入設定失敗：', err);
    }
}

function closeSettings() { settingsModal.style.display = 'none'; }

async function saveSettings() {
    const settings = [
        { key: 'display_name', value: document.getElementById('settingName').value || '使用者' },
        { key: 'language', value: document.getElementById('settingLanguage').value },
        { key: 'reply_style', value: document.getElementById('settingStyle').value }
    ];

    try {
        for (const s of settings) {
            await fetch('/api/memory', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(s)
            });
        }
        closeSettings();
        alert('設定已儲存！');
    } catch (err) {
        console.error('儲存設定失敗：', err);
        alert('儲存失敗，請重試。');
    }
}

// === 輔助函式 ===

function handleInputChange() {
    btnSend.disabled = !messageInput.value.trim();
    // 自動調整高度
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function showTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-body">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>`;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function removeTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function copyMessage(btn) {
    const content = btn.closest('.message-body').querySelector('.message-content').textContent;
    navigator.clipboard.writeText(content).then(() => {
        const orig = btn.textContent;
        btn.textContent = '✅ 已複製';
        setTimeout(() => { btn.textContent = orig; }, 1500);
    });
}
