// ============================================================================
// VibeAI — API Client
// لایه‌ی ارتباط با Backend (FastAPI). دقیقاً منطبق با endpoint های تست‌شده.
// ============================================================================

const API_BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    let detail = `خطای سرور (کد ${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      // پاسخ JSON نبود؛ از پیام پیش‌فرض استفاده می‌شود
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export const api = {
  analyze(text) {
    return request("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  },

  recommend(text, chatId) {
    const payload = { text };
    if (chatId !== null && chatId !== undefined) payload.chat_id = chatId;
    return request("/api/recommend", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  createChat(title) {
    return request("/api/chats", {
      method: "POST",
      body: JSON.stringify({ title: title || "" }),
    });
  },

  listChats({ search, limit = 50 } = {}) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (search) params.set("search", search);
    return request(`/api/chats?${params.toString()}`);
  },

  getChat(chatId) {
    return request(`/api/chats/${chatId}`);
  },

  sendFeedback(historyId, itemType, itemName, reaction) {
    return request("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        history_id: historyId,
        item_type: itemType,
        item_name: itemName,
        reaction,
      }),
    });
  },

  getHistory({ limit = 50 } = {}) {
    return request(`/api/history?limit=${limit}`);
  },

  getTasteProfile() {
    return request("/api/taste-profile");
  },
};
