import { motion } from "framer-motion";
import { AlertCircle, Sparkles, RotateCcw } from "lucide-react";

export function LoadingState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex gap-2.5 justify-start"
    >
      <div className="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-mood-neutral to-mood-calm mt-0.5 shadow-glow shadow-mood-neutral/30">
        <Sparkles size={13} className="text-base-0" />
      </div>
      <div className="glass rounded-2xl px-4 py-3.5 flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="block w-1.5 h-1.5 rounded-full bg-mood-neutral"
            animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
          />
        ))}
      </div>
    </motion.div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="self-start flex flex-col gap-2 max-w-[82%]"
    >
      <div
        className="flex items-start gap-3 rounded-2xl px-4 py-3"
        style={{
          background: "rgba(242, 90, 122, 0.1)",
          border: "1px solid rgba(242, 90, 122, 0.25)",
        }}
      >
        <AlertCircle size={15} className="text-mood-stressed flex-shrink-0 mt-0.5" />
        <span className="text-[13px] text-rose-100/90 leading-relaxed">{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="self-start flex items-center gap-1.5 text-[12px] text-mood-neutral/80
            hover:text-mood-neutral transition-colors px-1"
        >
          <RotateCcw size={12} />
          تلاش مجدد
        </button>
      )}
    </motion.div>
  );
}
