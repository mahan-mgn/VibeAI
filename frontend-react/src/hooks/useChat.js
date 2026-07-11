import { useState, useCallback, useRef } from "react";
import { api } from "../lib/api";
import { buildBotSummary, isSafetyMood, truncateTitle } from "../lib/constants";

export default function useChat() {
  const [chatId, setChatId] = useState(null);
  const [title, setTitle] = useState("چت جدید");
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  // آخرین متن ارسال‌شده برای قابلیت retry
  const lastTextRef = useRef("");

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isSending) return;
      lastTextRef.current = text;

      setMessages((prev) => [...prev, { type: "user", text }]);
      setIsSending(true);
      setMessages((prev) => [...prev, { type: "loading" }]);

      try {
        const data = await api.recommend(text, chatId);

        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.type !== "loading");
          return [
            ...withoutLoading,
            { type: "bot", text: buildBotSummary(data.analysis) },
            {
              type: "result",
              analysis: data.analysis,
              movies: data.movies,
              music: data.music,
              historyId: data.history_id,
              existingFeedback: [],
            },
          ];
        });

        if (chatId === null) {
          setChatId(data.chat_id);
          setTitle(truncateTitle(text));
        }

        return { chatId: data.chat_id, isNewChat: chatId === null };
      } catch (err) {
        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.type !== "loading");
          return [
            ...withoutLoading,
            {
              type: "error",
              message:
                err.message?.includes("fetch") || err.name === "TypeError"
                  ? "اتصال به سرور برقرار نشد. لطفاً از روشن بودن backend مطمئن شوید."
                  : err.message || "خطایی پیش آمد. لطفاً دوباره تلاش کنید.",
            },
          ];
        });
        return null;
      } finally {
        setIsSending(false);
      }
    },
    [chatId, isSending]
  );

  // ارسال مجدد آخرین پیام (بعد از خطا)
  const retryLastMessage = useCallback(async () => {
    if (!lastTextRef.current || isSending) return;
    // حذف پیام خطا از لیست
    setMessages((prev) => prev.filter((m) => m.type !== "error"));
    return sendMessage(lastTextRef.current);
  }, [isSending, sendMessage]);

  const loadChat = useCallback(async (id) => {
    const chat = await api.getChat(id);
    setChatId(chat.id);
    setTitle(chat.title);

    const rebuilt = [];
    chat.messages.forEach((msg) => {
      const analysis = {
        mood: msg.detected_mood,
        energy: msg.detected_energy,
        activity: msg.detected_activity,
        time_period: msg.detected_time_period,
        confidence: msg.confidence,
        safety_layer_active: isSafetyMood(msg.detected_mood),
      };
      rebuilt.push({ type: "user", text: msg.user_input });
      rebuilt.push({ type: "bot", text: buildBotSummary(analysis) });
      rebuilt.push({
        type: "result",
        analysis,
        movies: msg.recommendations?.movies || [],
        music: msg.recommendations?.music || [],
        historyId: msg.id,
        existingFeedback: msg.feedback || [],
      });
    });

    setMessages(rebuilt);
  }, []);

  const startNewChat = useCallback(() => {
    setChatId(null);
    setTitle("چت جدید");
    setMessages([]);
    lastTextRef.current = "";
  }, []);

  return {
    chatId,
    title,
    messages,
    isSending,
    sendMessage,
    retryLastMessage,
    loadChat,
    startNewChat,
  };
}
