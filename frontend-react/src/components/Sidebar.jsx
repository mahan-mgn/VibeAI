import { motion, AnimatePresence } from "framer-motion";
import { Plus, Search, X, MessageSquare, Sparkles, CalendarDays, Bell } from "lucide-react";

export default function Sidebar({
  isOpen,
  onClose,
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onOpenJournal,
  onOpenReminders,
  searchValue,
  onSearchChange,
  isLoadingChats,
}) {
  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      <aside
        className={`fixed md:static z-50 top-0 right-0 h-full w-[275px] flex-shrink-0
          flex flex-col gap-3.5 p-4
          border-l border-white/[0.08]
          transition-transform duration-300 ease-out
          sidebar-bg
          ${isOpen ? "translate-x-0" : "translate-x-full md:translate-x-0"}
        `}
      >
        {/* Brand */}
        <div className="flex items-center justify-between pt-1 pb-0.5">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-mood-neutral to-mood-calm shadow-glow shadow-mood-neutral/40">
              <Sparkles size={15} className="text-base-0" strokeWidth={2.5} />
              {/* shine dot */}
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-white/50" />
            </div>
            <div>
              <span className="font-display font-bold text-[15px] tracking-wide text-white">VibeAI</span>
              <span className="block text-[9.5px] text-white/30 leading-none mt-0.5 font-mono">v1.0</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="md:hidden flex items-center justify-center w-8 h-8 rounded-lg glass text-white/50 hover:text-white transition-colors"
            aria-label="بستن منو"
          >
            <X size={14} />
          </button>
        </div>

        {/* New chat button */}
        <button
          onClick={onNewChat}
          className="group flex items-center gap-2.5 rounded-xl px-4 py-3
            bg-gradient-to-l from-mood-neutral to-violet-600
            text-base-0 font-semibold text-[13.5px]
            shadow-glow shadow-mood-neutral/30
            transition-all duration-200
            hover:shadow-glow-lg hover:shadow-mood-neutral/45 hover:scale-[1.02]
            active:scale-[0.97]"
        >
          <Plus size={16} strokeWidth={2.5} className="transition-transform duration-200 group-hover:rotate-90" />
          <span>چت جدید</span>
        </button>

        {/* Mood journal */}
        <button
          onClick={onOpenJournal}
          className="flex items-center gap-2.5 rounded-xl px-4 py-2.5 text-[12.5px]
            text-white/55 border border-white/[0.07] hover:bg-white/[0.05] hover:text-white/85
            transition-colors"
        >
          <CalendarDays size={14} className="text-mood-calm/70" />
          <span>دفترچه احساسات</span>
        </button>

        {/* Daily reminder */}
        <button
          onClick={onOpenReminders}
          className="flex items-center gap-2.5 rounded-xl px-4 py-2.5 text-[12.5px]
            text-white/55 border border-white/[0.07] hover:bg-white/[0.05] hover:text-white/85
            transition-colors"
        >
          <Bell size={14} className="text-mood-neutral/70" />
          <span>یادآوری روزانه</span>
        </button>

        {/* Search */}
        <div className="relative flex items-center gap-2 rounded-xl glass px-3 py-2.5
          focus-within:ring-1 focus-within:ring-mood-neutral/50 transition-shadow">
          <Search size={13} className="text-white/30 flex-shrink-0" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="جستجوی چت..."
            className="flex-1 bg-transparent outline-none text-[12.5px] placeholder:text-white/25 min-w-0"
          />
          {searchValue && (
            <button
              onClick={() => onSearchChange("")}
              className="text-white/30 hover:text-white/70 transition-colors"
              aria-label="پاک کردن"
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Divider label */}
        {chats.length > 0 && !searchValue && (
          <p className="text-[10.5px] text-white/25 font-mono px-1">تاریخچه</p>
        )}

        {/* Chat list */}
        <nav className="flex-1 overflow-y-auto -mx-1.5 px-1.5 space-y-0.5">
          {isLoadingChats ? (
            <div className="space-y-2 pt-1">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-10 rounded-xl bg-white/[0.04] animate-pulse"
                  style={{ opacity: 1 - i * 0.15 }}
                />
              ))}
            </div>
          ) : chats.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 px-3">
              <MessageSquare size={22} className="text-white/15" />
              <p className="text-center text-[12px] text-white/30 leading-6">
                {searchValue
                  ? "چتی پیدا نشد."
                  : "هنوز چتی نداری.\nاولین پیامت رو بفرست!"}
              </p>
            </div>
          ) : (
            chats.map((chat) => {
              const isActive = chat.id === activeChatId;
              return (
                <button
                  key={chat.id}
                  onClick={() => onSelectChat(chat.id)}
                  className={`group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-right text-[12.5px]
                    transition-all duration-150 cursor-pointer
                    ${isActive
                      ? "bg-mood-neutral/15 text-white border border-mood-neutral/25"
                      : "text-white/55 hover:bg-white/[0.05] hover:text-white/85 border border-transparent"
                    }`}
                >
                  <MessageSquare
                    size={12}
                    className={`flex-shrink-0 transition-colors ${isActive ? "text-mood-neutral" : "text-white/25 group-hover:text-white/50"}`}
                  />
                  <span className="truncate flex-1 leading-snug">{chat.title}</span>
                  {isActive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-mood-neutral flex-shrink-0" />
                  )}
                </button>
              );
            })
          )}
        </nav>

        {/* Footer */}
        <div className="pt-2 border-t border-white/[0.06]">
          <p className="text-center text-[10.5px] text-white/15 font-mono">
            powered by VibeAI ✦
          </p>
        </div>
      </aside>
    </>
  );
}
