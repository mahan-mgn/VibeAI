import { useEffect, useRef, useState, useCallback } from "react";
import { Menu, Sparkles, ChevronDown, WifiOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Sidebar from "./components/Sidebar";
import ChatMessage from "./components/ChatMessage";
import ResultBlock from "./components/ResultBlock";
import { LoadingState, ErrorState } from "./components/LoadingState";
import ChatInput from "./components/ChatInput";
import WelcomeScreen from "./components/WelcomeScreen";
import MoodOrb from "./components/MoodOrb";
import ToastContainer from "./components/Toast";
import MoodJournal from "./components/MoodJournal";
import ReminderSettings from "./components/ReminderSettings";
import useChat from "./hooks/useChat";
import useChatList from "./hooks/useChatList";
import useToast from "./hooks/useToast";
import { api } from "./lib/api";
import { moodColor } from "./lib/constants";

export default function App() {
  const [inputValue, setInputValue] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [view, setView] = useState("chat");
  const [reminderOpen, setReminderOpen] = useState(false);
  const chatLogRef = useRef(null);

  const { chatId, title, messages, isSending, sendMessage, retryLastMessage, loadChat, startNewChat } = useChat();
  const { chats, search, setSearch, isLoading: chatsLoading, upsertChatLocally } = useChatList();
  const { toasts, addToast, removeToast } = useToast();

  // بررسی وضعیت اتصال backend هنگام بارگذاری
  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  // اسکرول خودکار به پایین
  useEffect(() => {
    const el = chatLogRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 200;
    if (isNearBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  // نمایش دکمه scroll-to-bottom وقتی کاربر بالا رفته
  const handleScroll = useCallback(() => {
    const el = chatLogRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 300);
  }, []);

  const scrollToBottom = () => {
    chatLogRef.current?.scrollTo({ top: chatLogRef.current.scrollHeight, behavior: "smooth" });
  };

  // رنگ mood فعلی
  const lastResult = [...messages].reverse().find((m) => m.type === "result");
  const currentColor = lastResult ? moodColor(lastResult.analysis.mood) : "#a78bfa";

  const handleSubmit = async () => {
    const text = inputValue.trim();
    if (!text) return;
    setInputValue("");
    const result = await sendMessage(text);
    if (result) {
      upsertChatLocally(result.chatId, result.isNewChat ? text : undefined);
    }
  };

  const handleSelectChat = async (id) => {
    setSidebarOpen(false);
    setView("chat");
    try {
      await loadChat(id);
    } catch {
      addToast("خطا در بارگذاری چت. دوباره تلاش کنید.", "error");
    }
  };

  const handleNewChat = () => {
    startNewChat();
    setSidebarOpen(false);
    setView("chat");
  };

  const handleOpenJournal = () => {
    setView("journal");
    setSidebarOpen(false);
  };

  const handleOpenReminders = () => {
    setReminderOpen(true);
    setSidebarOpen(false);
  };

  const handleFeedback = async (historyId, itemType, itemName, reaction) => {
    try {
      await api.sendFeedback(historyId, itemType, itemName, reaction);
      addToast(reaction === "like" ? "ممنون از بازخوردت! 👍" : "فهمیدم، بهتر می‌شم! 👎", "success");
    } catch {
      addToast("خطا در ثبت بازخورد.", "error");
    }
  };

  return (
    <div className="h-screen flex bg-base-0 text-white overflow-hidden relative">
      {/* Ambient lights */}
      <div className="fixed top-0 left-1/4 w-[500px] h-[500px] bg-mood-neutral/[0.06] rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[400px] h-[400px] bg-mood-calm/[0.04] rounded-full blur-[120px] pointer-events-none" />

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chats={chats}
        activeChatId={chatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onOpenJournal={handleOpenJournal}
        onOpenReminders={handleOpenReminders}
        searchValue={search}
        onSearchChange={setSearch}
        isLoadingChats={chatsLoading}
      />

      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        {/* Topbar */}
        <header className="flex items-center gap-3 h-14 px-5 border-b border-white/[0.07] flex-shrink-0 backdrop-blur-md">
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden flex items-center justify-center w-8 h-8 rounded-lg glass text-white/60 hover:text-white transition-colors"
            aria-label="باز کردن منو"
          >
            <Menu size={15} />
          </button>

          {messages.length > 0 && (
            <motion.span
              key={currentColor}
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex-shrink-0 w-2 h-2 rounded-full transition-colors duration-700 animate-pulse-slow"
              style={{ backgroundColor: currentColor, boxShadow: `0 0 8px ${currentColor}88` }}
            />
          )}

          <h1 className="text-[13px] font-medium truncate text-white/65 flex-1">{title}</h1>

          <div className="hidden md:flex items-center gap-1.5 text-white/18 text-[11px] font-mono">
            <Sparkles size={11} className="text-mood-neutral/35" />
            VibeAI
          </div>
        </header>

        {/* Backend offline banner */}
        <AnimatePresence>
          {!backendOnline && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="flex items-center gap-2 px-5 py-2.5 bg-mood-stressed/15 border-b border-mood-stressed/25 text-[12px] text-rose-200/90"
            >
              <WifiOff size={13} className="flex-shrink-0 text-mood-stressed" />
              <span>Backend آفلاین است. لطفاً سرور را راه‌اندازی کنید.</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mood Journal or Chat Main */}
        {view === "journal" ? (
          <MoodJournal onBack={() => setView("chat")} />
        ) : (
        <main className="flex-1 flex flex-col min-w-0 max-w-3xl w-full mx-auto px-5 overflow-hidden">
          {messages.length === 0 ? (
            <WelcomeScreen onPick={(s) => setInputValue(s)} />
          ) : (
            <div
              ref={chatLogRef}
              onScroll={handleScroll}
              className="flex-1 overflow-y-auto py-6 flex flex-col gap-4 relative"
            >
              <MoodOrb color={currentColor} size={260} className="top-0 right-1/2 translate-x-1/2 -z-10" />

              {messages.map((m, i) => {
                if (m.type === "user" || m.type === "bot") {
                  return <ChatMessage key={i} role={m.type} text={m.text} />;
                }
                if (m.type === "loading") return <LoadingState key={i} />;
                if (m.type === "error") return (
                  <ErrorState key={i} message={m.message} onRetry={retryLastMessage} />
                );
                if (m.type === "result") {
                  return (
                    <ResultBlock
                      key={i}
                      analysis={m.analysis}
                      movies={m.movies}
                      music={m.music}
                      historyId={m.historyId}
                      onFeedback={handleFeedback}
                      existingFeedback={m.existingFeedback || []}
                    />
                  );
                }
                return null;
              })}
            </div>
          )}

          {/* Scroll-to-bottom button */}
          <AnimatePresence>
            {showScrollBtn && messages.length > 0 && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={scrollToBottom}
                className="absolute left-1/2 -translate-x-1/2 bottom-24 z-20
                  flex items-center gap-1.5 px-3.5 py-2 rounded-full glass-strong
                  border border-white/15 text-[11.5px] text-white/70
                  hover:text-white hover:border-white/25 transition-all shadow-glow shadow-black/40"
                aria-label="رفتن به پایین"
              >
                <ChevronDown size={14} />
                پیام جدید
              </motion.button>
            )}
          </AnimatePresence>

          <ChatInput value={inputValue} onChange={setInputValue} onSubmit={handleSubmit} disabled={isSending} />
        </main>
        )}
      </div>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Reminder settings modal */}
      <ReminderSettings isOpen={reminderOpen} onClose={() => setReminderOpen(false)} />
    </div>
  );
}
