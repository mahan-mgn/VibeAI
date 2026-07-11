import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, List, LayoutGrid, Sparkles, RotateCcw } from "lucide-react";
import { api } from "../lib/api";
import MoodTrends from "./MoodTrends";
import {
  MOOD_LABELS_FA,
  MOOD_EMOJI,
  moodColor,
  moodLabel,
  truncateTitle,
} from "../lib/constants";

const WEEKS = 12;
const TOTAL_DAYS = WEEKS * 7;
const MOOD_ORDER = Object.keys(MOOD_LABELS_FA);

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function startOfDay(d) {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function dominantMood(dayEntries) {
  const counts = {};
  dayEntries.forEach((e) => {
    counts[e.detected_mood] = (counts[e.detected_mood] || 0) + 1;
  });
  const maxCount = Math.max(...Object.values(counts));
  const topMoods = Object.keys(counts).filter((m) => counts[m] === maxCount);
  if (topMoods.length === 1) return topMoods[0];
  // در صورت تساوی، mood جدیدترین رکورد آن روز انتخاب می‌شود (entries جدید->قدیم مرتب است)
  return dayEntries.find((e) => topMoods.includes(e.detected_mood)).detected_mood;
}

function GenreBar({ label, score, maxScore }) {
  const pct = maxScore > 0 ? Math.max(6, (score / maxScore) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 flex-shrink-0 text-[11.5px] text-white/55 truncate">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-white/[0.05] overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-mood-neutral/70"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      <span className="w-8 flex-shrink-0 text-[10.5px] font-mono text-white/35 text-left">
        {score.toFixed(1)}
      </span>
    </div>
  );
}

export default function MoodJournal({ onBack }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("calendar");
  const [selectedDay, setSelectedDay] = useState(null);
  const [taste, setTaste] = useState(null);

  const loadHistory = () => {
    setLoading(true);
    setError(null);
    api
      .getHistory({ limit: 200 })
      .then((data) => setEntries(data))
      .catch(() => setError("خطا در دریافت تاریخچه‌ی احساسات."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadHistory();
    api.getTasteProfile().then(setTaste).catch(() => setTaste(null));
  }, []);

  const dayMap = useMemo(() => {
    const map = {};
    entries.forEach((e) => {
      const key = dateKey(new Date(e.timestamp));
      if (!map[key]) map[key] = [];
      map[key].push(e);
    });
    return map;
  }, [entries]);

  const calendarDays = useMemo(() => {
    const today = startOfDay(new Date());
    // برگشت به شروع هفته‌ی ایرانی (شنبه) برای شبکه‌ی مرتب
    const endDow = (today.getDay() + 1) % 7; // JS: یکشنبه=0..شنبه=6 → تبدیل به شنبه=0..جمعه=6
    const end = new Date(today);
    end.setDate(end.getDate() + (6 - endDow));
    const start = new Date(end);
    start.setDate(start.getDate() - (TOTAL_DAYS - 1));

    const days = [];
    for (let i = 0; i < TOTAL_DAYS; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      const key = dateKey(d);
      const dayEntries = dayMap[key] || [];
      days.push({
        key,
        date: d,
        mood: dayEntries.length > 0 ? dominantMood(dayEntries) : null,
        entries: dayEntries,
        isFuture: d > today,
      });
    }
    return days;
  }, [dayMap]);

  const stats = useMemo(() => {
    if (entries.length === 0) return { total: 0, topMood: null, streak: 0 };

    const counts = {};
    entries.forEach((e) => {
      counts[e.detected_mood] = (counts[e.detected_mood] || 0) + 1;
    });
    const topMood = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];

    let streak = 0;
    const cursor = startOfDay(new Date());
    while (dayMap[dateKey(cursor)]) {
      streak += 1;
      cursor.setDate(cursor.getDate() - 1);
    }

    return { total: entries.length, topMood, streak };
  }, [entries, dayMap]);

  const maxMovieScore = taste ? Math.max(1, ...taste.movie_genres.map((g) => g.score)) : 1;
  const maxMusicScore = taste ? Math.max(1, ...taste.music_genres.map((g) => g.score)) : 1;

  return (
    <div className="flex-1 flex flex-col min-w-0 max-w-3xl w-full mx-auto px-5 overflow-y-auto py-6 gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex items-center justify-center w-8 h-8 rounded-lg glass text-white/60 hover:text-white transition-colors"
          aria-label="بازگشت به چت"
        >
          <ArrowRight size={15} />
        </button>
        <h2 className="text-[14px] font-semibold text-white/85">دفترچه احساسات</h2>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-white/40 text-[12.5px] py-10 justify-center">
          <Sparkles size={14} className="animate-pulse-slow" />
          در حال بارگذاری...
        </div>
      )}

      {error && !loading && (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <span className="text-[12.5px] text-rose-200/80">{error}</span>
          <button
            onClick={loadHistory}
            className="flex items-center gap-1.5 text-[12px] text-mood-neutral/80 hover:text-mood-neutral transition-colors"
          >
            <RotateCcw size={12} />
            تلاش مجدد
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-3 gap-3">
            <div className="glass rounded-2xl p-4 text-center">
              <span className="block text-[10.5px] text-white/35 mb-1.5">تحلیل‌های ثبت‌شده</span>
              <span className="block text-[18px] font-semibold text-white/90">{stats.total}</span>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <span className="block text-[10.5px] text-white/35 mb-1.5">پرتکرارترین حس</span>
              <span className="block text-[18px] font-semibold text-white/90">
                {stats.topMood ? `${MOOD_EMOJI[stats.topMood]} ${moodLabel(stats.topMood)}` : "—"}
              </span>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <span className="block text-[10.5px] text-white/35 mb-1.5">روزهای متوالی</span>
              <span className="block text-[18px] font-semibold text-white/90">{stats.streak}</span>
            </div>
          </div>

          {/* View toggle */}
          <div className="flex items-center justify-between">
            <h3 className="text-[12.5px] font-semibold text-white/60">تقویم احساسات (۱۲ هفته‌ی اخیر)</h3>
            <button
              onClick={() => setViewMode(viewMode === "calendar" ? "table" : "calendar")}
              className="flex items-center gap-1.5 text-[11.5px] text-white/40 hover:text-white/80 transition-colors px-2.5 py-1.5 rounded-lg hover:bg-white/[0.05]"
            >
              {viewMode === "calendar" ? <List size={13} /> : <LayoutGrid size={13} />}
              {viewMode === "calendar" ? "نمایش جدولی" : "نمایش تقویمی"}
            </button>
          </div>

          {viewMode === "calendar" ? (
            <div className="glass rounded-2xl p-4">
              <div
                dir="ltr"
                className="grid gap-[3px] overflow-x-auto"
                style={{ gridTemplateRows: "repeat(7, 13px)", gridAutoFlow: "column", gridAutoColumns: "13px" }}
              >
                {calendarDays.map((day) => (
                  <button
                    key={day.key}
                    disabled={day.isFuture}
                    onClick={() => setSelectedDay(day.key === selectedDay ? null : day.key)}
                    title={`${day.date.toLocaleDateString("fa-IR")}${day.mood ? " — " + moodLabel(day.mood) : ""}`}
                    className="rounded-[3px] transition-transform hover:scale-125 disabled:opacity-0 disabled:pointer-events-none"
                    style={{
                      backgroundColor: day.mood ? moodColor(day.mood) : "rgba(255,255,255,0.05)",
                      outline: day.key === selectedDay ? "2px solid rgba(255,255,255,0.6)" : "none",
                      outlineOffset: 1,
                    }}
                  />
                ))}
              </div>

              {/* Legend — رنگ به‌تنهایی معنا را منتقل نمی‌کند، همیشه با ایموجی/برچسب همراه است */}
              <div className="flex flex-wrap gap-x-3 gap-y-1.5 mt-4 pt-3 border-t border-white/[0.06]">
                {MOOD_ORDER.map((mood) => (
                  <div key={mood} className="flex items-center gap-1.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: moodColor(mood) }}
                    />
                    <span className="text-[10.5px] text-white/45">
                      {MOOD_EMOJI[mood]} {moodLabel(mood)}
                    </span>
                  </div>
                ))}
              </div>

              {entries.length === 0 && (
                <p className="text-center text-[12px] text-white/30 mt-4">
                  هنوز داده‌ای برای نمایش نیست — یه پیام بفرست تا این تقویم پر بشه!
                </p>
              )}

              {selectedDay && dayMap[selectedDay] && (
                <div className="mt-4 pt-3 border-t border-white/[0.06] flex flex-col gap-2">
                  <span className="text-[11px] text-white/40">
                    {new Date(selectedDay).toLocaleDateString("fa-IR")}
                  </span>
                  {dayMap[selectedDay].map((e) => (
                    <div key={e.id} className="flex items-start gap-2 text-[12px]">
                      <span className="flex-shrink-0">{MOOD_EMOJI[e.detected_mood]}</span>
                      <span className="text-white/70">{moodLabel(e.detected_mood)}</span>
                      <span className="text-white/35 truncate">— {truncateTitle(e.user_input, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="glass rounded-2xl p-2 max-h-[420px] overflow-y-auto flex flex-col divide-y divide-white/[0.05]">
              {entries.length === 0 && (
                <p className="text-center text-[12px] text-white/30 py-8">هنوز رکوردی ثبت نشده.</p>
              )}
              {entries.map((e) => (
                <div key={e.id} className="flex items-center gap-3 px-3 py-2.5 text-[12px]">
                  <span className="flex-shrink-0">{MOOD_EMOJI[e.detected_mood]}</span>
                  <span className="w-16 flex-shrink-0 text-white/70">{moodLabel(e.detected_mood)}</span>
                  <span className="flex-1 text-white/40 truncate">{truncateTitle(e.user_input, 50)}</span>
                  <span className="flex-shrink-0 text-[10.5px] font-mono text-white/25">
                    {new Date(e.timestamp).toLocaleDateString("fa-IR")}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Mood Trend Dashboard */}
          <div>
            <h3 className="text-[12.5px] font-semibold text-white/60 mb-3">روند حس و انرژی</h3>
            <MoodTrends entries={entries} />
          </div>

          {/* Taste profile */}
          <div>
            <h3 className="text-[12.5px] font-semibold text-white/60 mb-3">چیزی که VibeAI درباره‌ی سلیقه‌ت یاد گرفته</h3>
            {!taste || taste.total_feedback === 0 ? (
              <div className="glass rounded-2xl p-4 text-center text-[12px] text-white/35">
                هنوز داده‌ی کافی نداریم — چند تا لایک/دیسلایک بزن تا این بخش پر بشه!
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="glass rounded-2xl p-4 flex flex-col gap-3">
                  <span className="text-[11px] text-white/40">ژانرهای محبوب فیلم</span>
                  {taste.movie_genres.length === 0 ? (
                    <span className="text-[11.5px] text-white/25">هنوز داده‌ای نیست.</span>
                  ) : (
                    taste.movie_genres.map((g) => (
                      <GenreBar key={g.genre} label={g.genre} score={g.score} maxScore={maxMovieScore} />
                    ))
                  )}
                </div>
                <div className="glass rounded-2xl p-4 flex flex-col gap-3">
                  <span className="text-[11px] text-white/40">ژانرهای محبوب موزیک</span>
                  {taste.music_genres.length === 0 ? (
                    <span className="text-[11.5px] text-white/25">هنوز داده‌ای نیست.</span>
                  ) : (
                    taste.music_genres.map((g) => (
                      <GenreBar key={g.genre} label={g.genre} score={g.score} maxScore={maxMusicScore} />
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
