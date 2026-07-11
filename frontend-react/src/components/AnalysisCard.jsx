import { motion } from "framer-motion";
import { AlertTriangle, Cpu, Brain } from "lucide-react";
import {
  MOOD_EMOJI,
  ENERGY_LABELS_FA,
  ACTIVITY_LABELS_FA,
  TIME_LABELS_FA,
  moodColor,
  moodLabel,
} from "../lib/constants";

const ANALYZER_BADGE = {
  gemini: { label: "Gemini AI", icon: <Brain size={10} />, cls: "text-mood-calm border-mood-calm/30 bg-mood-calm/10" },
  rule_based: { label: "Rule-Based", icon: <Cpu size={10} />, cls: "text-white/40 border-white/15 bg-white/[0.04]" },
  fallback: { label: "Fallback", icon: <Cpu size={10} />, cls: "text-mood-bored border-mood-bored/30 bg-mood-bored/10" },
};

export default function AnalysisCard({ analysis }) {
  const color = moodColor(analysis.mood);
  const badge = ANALYZER_BADGE[analysis.analyzer] || ANALYZER_BADGE.rule_based;

  const pills = [
    { label: "احساس غالب", value: moodLabel(analysis.mood), emoji: MOOD_EMOJI[analysis.mood], highlight: true },
    { label: "سطح انرژی", value: ENERGY_LABELS_FA[analysis.energy] || analysis.energy },
    { label: "فعالیت", value: ACTIVITY_LABELS_FA[analysis.activity] || analysis.activity },
    { label: "زمان", value: TIME_LABELS_FA[analysis.time_period] || analysis.time_period },
    { label: "اطمینان", value: `${Math.round(analysis.confidence * 100)}٪`, mono: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass rounded-2xl p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <h3 className="text-[12.5px] font-semibold text-white/60">تحلیل وضعیت شما</h3>
        {/* Analyzer badge */}
        <span className={`flex items-center gap-1 text-[10px] font-mono border rounded-full px-2 py-0.5 ${badge.cls}`}>
          {badge.icon}
          {badge.label}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {pills.map((pill) => (
          <div
            key={pill.label}
            className={`rounded-xl px-3 py-2.5 text-center border transition-colors ${
              pill.highlight ? "border-white/15" : "border-white/[0.06] bg-white/[0.03]"
            }`}
            style={pill.highlight ? { background: `${color}14`, borderColor: `${color}40` } : undefined}
          >
            <span className="block text-[10px] text-white/35 mb-1">{pill.label}</span>
            <span className={`block text-[13px] font-semibold ${pill.mono ? "font-mono" : ""}`}>
              {pill.emoji && <span className="ml-1">{pill.emoji}</span>}
              {pill.value}
            </span>
          </div>
        ))}
      </div>

      {analysis.safety_layer_active && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.3, delay: 0.15 }}
          className="mt-3.5 flex items-start gap-2.5 rounded-xl px-4 py-3 text-[12.5px] leading-6"
          style={{ background: "rgba(242, 90, 122, 0.1)", border: "1px solid rgba(242, 90, 122, 0.22)", color: "#fbd0da" }}
        >
          <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />
          <span>به نظر می‌رسه حالت خیلی سخته. پیشنهادهای آرام‌بخش و امیدوارکننده برات آوردیم.</span>
        </motion.div>
      )}
    </motion.div>
  );
}
