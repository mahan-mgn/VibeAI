import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../lib/api";

/**
 * useChatList — مدیریت لیست چت‌ها برای سایدبار: بارگذاری، جستجو (debounced)،
 * و به‌روزرسانی محلی بعد از ساخت/تغییر یک چت (بدون نیاز به رفرش کامل از سرور).
 */
export default function useChatList() {
  const [chats, setChats] = useState([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const debounceRef = useRef(null);

  const fetchChats = useCallback(async (searchTerm) => {
    setIsLoading(true);
    try {
      const result = await api.listChats({ search: searchTerm || undefined, limit: 50 });
      setChats(result);
    } catch {
      setChats([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchChats(search.trim() || undefined);
    }, 250);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // وقتی چت جدید ساخته می‌شود یا پیامی به چت موجود اضافه می‌شود،
  // آن را بدون فراخوانی سرور به بالای لیست منتقل/اضافه می‌کنیم.
  const upsertChatLocally = useCallback((chatId, newTitle) => {
    setChats((prev) => {
      const existing = prev.find((c) => c.id === chatId);
      const rest = prev.filter((c) => c.id !== chatId);
      const updated = existing
        ? { ...existing, title: newTitle || existing.title }
        : { id: chatId, title: newTitle || "چت جدید" };
      return [updated, ...rest];
    });
  }, []);

  return { chats, search, setSearch, isLoading, upsertChatLocally };
}
