import { motion } from "framer-motion";
import { Sparkles, Film, Music2, Zap } from "lucide-react";
import MoodOrb from "./MoodOrb";

const SUGGESTIONS = [
  { icon: "😮‍💨", text: "امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام" },
  { icon: "💻", text: "دارم برنامه‌نویسی می‌کنم، یه پلی‌لیست تمرکزی می‌خوام" },
  { icon: "🌧️", text: "امروز استرس زیادی داشتم، یه موزیک آروم پیشنهاد بده" },
  { icon: "🎉", text: "حالم خوبه و دنبال یه فیلم هیجان‌انگیز می‌گردم" },
];

const FEATURES = [
  { icon: Film, label: "فیلم" },
  { icon: Music2, label: "موزیک" },
  { icon: Zap, label: "لحظه‌ای" },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.15 } },
};

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

export default function WelcomeScreen({ onPick }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-5 relative overflow-hidden">
      {/* Ambient orb */}
      <MoodOrb color="#a78bfa" size={440} className="-translate-y-16 -z-10" />

      {/* Decorative floating particles */}
      <div className="absolute inset-0 pointer-events-none -z-10" aria-hidden="true">
        {[
          { w: 2, h: 2, top: "18%", left: "15%", delay: "0s" },
          { w: 3, h: 3, top: "30%", right: "12%", delay: "1.2s" },
          { w: 1.5, h: 1.5, top: "65%", left: "20%", delay: "0.6s" },
          { w: 2.5, h: 2.5, top: "55%", right: "18%", delay: "1.8s" },
          { w: 2, h: 2, top: "80%", left: "40%", delay: "0.3s" },
        ].map((p, i) => (
          <span
            key={i}
            className="absolute rounded-full bg-mood-neutral/40 animate-float"
            style={{ width: p.w * 4, height: p.h * 4, top: p.top, left: p.left, right: p.right, animationDelay: p.delay }}
          />
        ))}
      </div>

      {/* Logo icon */}
      <motion.div
        initial={{ opacity: 0, scale: 0.7, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
        className="relative z-10 mb-6"
      >
        <div className="relative flex items-center justify-center w-18 h-18 w-[72px] h-[72px]">
          {/* outer glow ring */}
          <div className="absolute inset-0 rounded-2xl bg-mood-neutral/20 blur-xl animate-pulse-slow" />
          <div className="relative flex items-center justify-center w-full h-full rounded-2xl glass-strong border border-mood-neutral/30 animate-float">
            <Sparkles size={30} className="text-mood-neutral" strokeWidth={1.8} />
          </div>
        </div>
      </motion.div>

      {/* Headline */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12, duration: 0.38 }}
        className="relative z-10 mb-1.5"
      >
        <h2 className="font-display text-[26px] font-bold leading-tight">
          سلام! چه{" "}
          <span className="bg-gradient-to-l from-mood-neutral to-mood-calm bg-clip-text text-transparent">
            حسی
          </span>{" "}
          داری؟
        </h2>
      </motion.div>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.38 }}
        className="relative z-10 text-[13px] text-white/45 max-w-xs mb-2 leading-7"
      >
        حال‌وهوات رو بگو، بهت فیلم و موزیک مناسب پیشنهاد می‌دم.
      </motion.p>

      {/* Feature badges */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.28, duration: 0.4 }}
        className="relative z-10 flex items-center gap-2 mb-8"
      >
        {FEATURES.map(({ icon: Icon, label }) => (
          <span key={label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass border border-white/10 text-[11.5px] text-white/50">
            <Icon size={11} className="text-mood-neutral" />
            {label}
          </span>
        ))}
      </motion.div>

      {/* Suggestions */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col gap-2.5 w-full max-w-md"
      >
        {SUGGESTIONS.map((s, i) => (
          <motion.button
            key={i}
            variants={item}
            onClick={() => onPick(s.text)}
            className="suggestion-chip group flex items-center gap-3 text-right rounded-2xl glass
              px-4 py-3.5 text-[13px] text-white/60
              border border-white/[0.07]
              hover:text-white hover:border-mood-neutral/30 hover:bg-mood-neutral/[0.08]
              transition-all duration-200 cursor-pointer"
          >
            <span className="text-base leading-none flex-shrink-0">{s.icon}</span>
            <span className="flex-1">{s.text}</span>
            <span className="text-white/20 group-hover:text-mood-neutral/60 transition-colors text-[11px]">←</span>
          </motion.button>
        ))}
      </motion.div>
    </div>
  );
}
