// ============================================================================
// VibeAI — Constants
// ترجمه‌های فارسی و نگاشت رنگ/استایل برای mood, energy, activity, time
// ============================================================================

export const MOOD_LABELS_FA = {
  tired: "خستگی",
  stressed: "استرس",
  happy: "شادی",
  excited: "هیجان",
  calm: "آرامش",
  anxious: "نگرانی",
  sad: "ناراحتی",
  bored: "بی‌حوصلگی",
  neutral: "خنثی",
};

export const MOOD_EMOJI = {
  tired: "😴",
  stressed: "😣",
  happy: "😊",
  excited: "🤩",
  calm: "😌",
  anxious: "😟",
  sad: "😢",
  bored: "😐",
  neutral: "🙂",
};

// رنگ هر mood — باید با tailwind.config.js (theme.colors.mood) هماهنگ باشد
export const MOOD_HEX = {
  tired: "#7c93e8",
  stressed: "#f25a7a",
  happy: "#fbbf24",
  excited: "#fb7a3f",
  calm: "#34d9bc",
  anxious: "#d896f0",
  sad: "#8b9fd9",
  bored: "#a39d8f",
  neutral: "#a78bfa",
};

export const ENERGY_LABELS_FA = {
  low: "پایین",
  medium: "متوسط",
  high: "بالا",
};

export const ACTIVITY_LABELS_FA = {
  coding: "برنامه‌نویسی",
  studying: "مطالعه",
  resting: "استراحت",
  exercise: "ورزش",
  general: "عمومی",
};

export const TIME_LABELS_FA = {
  morning: "صبح",
  afternoon: "بعدازظهر",
  evening: "عصر",
  night: "شب",
  current: "اکنون",
};

export function moodColor(mood) {
  return MOOD_HEX[mood] || MOOD_HEX.neutral;
}

export function moodLabel(mood) {
  return MOOD_LABELS_FA[mood] || mood;
}

export function buildBotSummary(analysis) {
  const moodFa = moodLabel(analysis.mood);
  const moodEmoji = MOOD_EMOJI[analysis.mood] || "";
  const energyFa = ENERGY_LABELS_FA[analysis.energy] || analysis.energy;
  const activityFa = ACTIVITY_LABELS_FA[analysis.activity] || analysis.activity;
  const confidence = Math.round(analysis.confidence * 100);

  let text = `${moodEmoji} حالت رو فهمیدم — احساس «${moodFa}» با انرژی «${energyFa}»`;
  if (analysis.activity !== "general") {
    text += `، حین «${activityFa}»`;
  }
  text += ".";

  if (confidence < 65) {
    text += ` (اطمینان: ${confidence}٪ — سعی کردم بهترین انتخاب رو بیارم)`;
  }

  text += analysis.safety_layer_active
    ? " چند پیشنهاد آرام‌بخش و سبک برات آماده کردم 💜"
    : " این‌ها بهترین پیشنهادهامه:";

  return text;
}

export function isSafetyMood(mood) {
  return ["stressed", "sad", "tired", "anxious"].includes(mood);
}

export function truncateTitle(text, maxLen = 42) {
  const clean = text.trim();
  return clean.length <= maxLen ? clean : clean.slice(0, maxLen).trimEnd() + "…";
}
