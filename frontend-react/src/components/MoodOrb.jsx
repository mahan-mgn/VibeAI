import { motion, AnimatePresence } from "framer-motion";

/**
 * MoodOrb — سیگنیچر بصری VibeAI.
 * یک کره‌ی نورانی blur-شده که رنگ و شدت تپش آن با mood فعلی تغییر می‌کند.
 * در پس‌زمینه‌ی هدر شناور است و حس "زنده بودن" دستیار را منتقل می‌کند.
 */
export default function MoodOrb({ color = "#a78bfa", size = 320, className = "" }) {
  return (
    <div
      className={`pointer-events-none absolute ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <AnimatePresence>
        <motion.div
          key={color}
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle at 50% 50%, ${color}55 0%, ${color}22 35%, transparent 70%)`,
            filter: "blur(30px)",
          }}
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        />
      </AnimatePresence>
      <motion.div
        className="absolute inset-0 rounded-full animate-pulse-slow"
        style={{
          background: `radial-gradient(circle at 40% 35%, ${color}40 0%, transparent 60%)`,
          filter: "blur(20px)",
        }}
      />
    </div>
  );
}
