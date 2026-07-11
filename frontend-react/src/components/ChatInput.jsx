import { useRef, useEffect } from "react";
import { Send } from "lucide-react";

const MAX_LENGTH = 500;

export default function ChatInput({ value, onChange, onSubmit, disabled }) {
  const textareaRef = useRef(null);
  const filled = value.length / MAX_LENGTH;
  const nearLimit = value.length >= MAX_LENGTH * 0.85;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  };

  return (
    <div className="border-t border-white/[0.07] pt-4 pb-2">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (value.trim() && !disabled) onSubmit();
        }}
        className="flex items-end gap-3"
      >
        {/* Input wrapper with animated glow border */}
        <div className="relative flex-1 chat-input-wrapper">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            maxLength={MAX_LENGTH}
            rows={1}
            placeholder="مثلاً: امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام..."
            disabled={disabled}
            className="w-full resize-none glass rounded-2xl px-4 py-3.5 text-[13.5px] outline-none
              placeholder:text-white/25 min-h-[52px] max-h-[140px]
              focus:ring-1 focus:ring-mood-neutral/60 transition-all duration-200
              disabled:opacity-50"
          />

          {/* Progress ring hint when near limit */}
          {nearLimit && (
            <span className={`absolute bottom-3 left-3 font-mono text-[10px] ${value.length >= MAX_LENGTH ? "text-mood-stressed" : "text-mood-neutral/60"}`}>
              {MAX_LENGTH - value.length}
            </span>
          )}
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="send-btn relative flex items-center justify-center w-12 h-12 rounded-2xl flex-shrink-0
            bg-gradient-to-br from-mood-neutral to-violet-600
            shadow-glow shadow-mood-neutral/40
            transition-all duration-200
            hover:shadow-glow-lg hover:shadow-mood-neutral/50 hover:scale-105
            active:scale-95
            disabled:opacity-35 disabled:cursor-not-allowed disabled:shadow-none disabled:scale-100"
          aria-label="ارسال پیام"
        >
          <Send size={16} className="-scale-x-100 text-white" strokeWidth={2.5} />
        </button>
      </form>

      {/* Bottom hint */}
      <p className="mt-2 px-1 text-[11px] text-white/20 text-center">
        Enter برای ارسال &nbsp;·&nbsp; Shift+Enter برای خط جدید
      </p>
    </div>
  );
}
