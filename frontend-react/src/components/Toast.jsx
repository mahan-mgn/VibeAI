import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, X, AlertCircle, Info } from "lucide-react";

const ICONS = {
  success: <CheckCircle2 size={15} className="text-mood-calm flex-shrink-0" />,
  error: <AlertCircle size={15} className="text-mood-stressed flex-shrink-0" />,
  info: <Info size={15} className="text-mood-neutral flex-shrink-0" />,
};

export default function ToastContainer({ toasts, onRemove }) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 items-center pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 16, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="pointer-events-auto flex items-center gap-2.5 glass-strong rounded-xl px-4 py-3
              shadow-glow shadow-black/30 border border-white/10 min-w-[220px] max-w-[340px]"
          >
            {ICONS[t.type] || ICONS.info}
            <span className="flex-1 text-[12.5px] text-white/85">{t.message}</span>
            <button
              onClick={() => onRemove(t.id)}
              className="text-white/30 hover:text-white/70 transition-colors flex-shrink-0"
              aria-label="بستن"
            >
              <X size={13} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
