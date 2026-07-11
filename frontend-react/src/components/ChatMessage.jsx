import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, User, Copy, Check } from "lucide-react";

export default function ChatMessage({ role, text }) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className={`group flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* Bot avatar */}
      {!isUser && (
        <div className="relative flex-shrink-0 mt-0.5">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-mood-neutral to-mood-calm shadow-glow shadow-mood-neutral/30">
            <Sparkles size={13} className="text-base-0" strokeWidth={2.5} />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-mood-calm border-2 border-base-0" />
        </div>
      )}

      {/* Bubble + copy */}
      <div className={`flex flex-col gap-1 max-w-[78%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "user-bubble text-white rounded-tr-sm"
              : "bot-bubble text-white/90 rounded-tl-sm"
          }`}
        >
          {text}
        </div>

        {/* Copy button — ظاهر می‌شه با hover */}
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150
            text-[10.5px] text-white/30 hover:text-white/60 px-1"
          aria-label="کپی متن"
        >
          {copied
            ? <><Check size={11} className="text-mood-calm" /> کپی شد</>
            : <><Copy size={11} /> کپی</>
          }
        </button>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-lg bg-white/10 border border-white/15 mt-0.5">
          <User size={13} className="text-white/60" />
        </div>
      )}
    </motion.div>
  );
}
