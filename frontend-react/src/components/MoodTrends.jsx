import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { ENERGY_LABELS_FA, MOOD_EMOJI, moodColor, moodLabel } from "../lib/constants";

const ENERGY_SCORE = { low: 1, medium: 2, high: 3 };
const TREND_DAYS = 30;

// رنگ اصلی نمودار خط انرژی — هماهنگ با accent برند (mood-neutral)
const ACCENT = "#a78bfa";
const SURFACE = "#12121a"; // تقریب رنگ پس‌زمینه‌ی glass برای حلقه‌ی دور نقطه‌ها

const CHART_W = 640;
const CHART_H = 150;
const PAD_X = 8;
const PAD_TOP = 14;
const PAD_BOTTOM = 22;

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function startOfDay(d) {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function useEnergyTrend(entries) {
  return useMemo(() => {
    const byDay = {};
    entries.forEach((e) => {
      const key = dateKey(new Date(e.timestamp));
      if (!byDay[key]) byDay[key] = [];
      byDay[key].push(e);
    });

    const today = startOfDay(new Date());
    const days = [];
    for (let i = TREND_DAYS - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = dateKey(d);
      const dayEntries = byDay[key] || [];
      let avgEnergy = null;
      let dominantMood = null;
      if (dayEntries.length > 0) {
        const scores = dayEntries.map((e) => ENERGY_SCORE[e.detected_energy] ?? 2);
        avgEnergy = scores.reduce((a, b) => a + b, 0) / scores.length;
        const counts = {};
        dayEntries.forEach((e) => (counts[e.detected_mood] = (counts[e.detected_mood] || 0) + 1));
        dominantMood = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
      }
      days.push({ key, date: d, avgEnergy, dominantMood, count: dayEntries.length });
    }
    return days;
  }, [entries]);
}

function weeklyDelta(days) {
  const thisWeek = days.slice(-7).filter((d) => d.avgEnergy !== null);
  const lastWeek = days.slice(-14, -7).filter((d) => d.avgEnergy !== null);
  if (thisWeek.length === 0 || lastWeek.length === 0) return null;

  const avg = (arr) => arr.reduce((a, b) => a + b.avgEnergy, 0) / arr.length;
  const diff = avg(thisWeek) - avg(lastWeek);
  return diff;
}

function EnergyTrendChart({ days }) {
  const [hoverIdx, setHoverIdx] = useState(null);

  const plotW = CHART_W - PAD_X * 2;
  const plotH = CHART_H - PAD_TOP - PAD_BOTTOM;

  const xAt = (i) => PAD_X + (i / (days.length - 1)) * plotW;
  const yAt = (score) => PAD_TOP + (1 - (score - 1) / 2) * plotH;

  // ساخت segmentهای پیوسته (شکاف در روزهایی که داده نداریم)
  const segments = useMemo(() => {
    const segs = [];
    let current = [];
    days.forEach((d, i) => {
      if (d.avgEnergy === null) {
        if (current.length > 1) segs.push(current);
        current = [];
      } else {
        current.push({ i, score: d.avgEnergy });
      }
    });
    if (current.length > 1) segs.push(current);
    return segs;
  }, [days]);

  const linePath = (seg) =>
    seg.map((p, idx) => `${idx === 0 ? "M" : "L"} ${xAt(p.i).toFixed(1)} ${yAt(p.score).toFixed(1)}`).join(" ");

  const areaPath = (seg) => {
    const line = linePath(seg);
    const first = seg[0];
    const last = seg[seg.length - 1];
    return `${line} L ${xAt(last.i).toFixed(1)} ${PAD_TOP + plotH} L ${xAt(first.i).toFixed(1)} ${PAD_TOP + plotH} Z`;
  };

  const handleMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * CHART_W;
    const idx = Math.round(((relX - PAD_X) / plotW) * (days.length - 1));
    const clamped = Math.max(0, Math.min(days.length - 1, idx));
    setHoverIdx(days[clamped].avgEnergy !== null ? clamped : null);
  };

  const hovered = hoverIdx !== null ? days[hoverIdx] : null;
  const tooltipLeftPct = hoverIdx !== null ? (xAt(hoverIdx) / CHART_W) * 100 : 0;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full h-[130px] overflow-visible"
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverIdx(null)}
      >
        {/* Gridlines — یک‌سطح روشن‌تر از پس‌زمینه، نازک، بی‌جلوه */}
        {[1, 2, 3].map((score) => (
          <line
            key={score}
            x1={PAD_X}
            x2={CHART_W - PAD_X}
            y1={yAt(score)}
            y2={yAt(score)}
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={1}
          />
        ))}

        {/* Area + Line per segment پیوسته */}
        {segments.map((seg, si) => (
          <g key={si}>
            <path d={areaPath(seg)} fill={ACCENT} opacity={0.1} stroke="none" />
            <motion.path
              d={linePath(seg)}
              fill="none"
              stroke={ACCENT}
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 0.7, ease: "easeOut" }}
            />
          </g>
        ))}

        {/* Crosshair + نقطه‌ی هاور */}
        {hovered && (
          <g>
            <line
              x1={xAt(hoverIdx)}
              x2={xAt(hoverIdx)}
              y1={PAD_TOP}
              y2={PAD_TOP + plotH}
              stroke="rgba(255,255,255,0.18)"
              strokeWidth={1}
            />
            <circle
              cx={xAt(hoverIdx)}
              cy={yAt(hovered.avgEnergy)}
              r={5}
              fill={ACCENT}
              stroke={SURFACE}
              strokeWidth={2}
            />
          </g>
        )}

        {/* برچسب محور Y */}
        <text x={PAD_X} y={yAt(3) - 4} className="fill-white/25" fontSize="9">زیاد</text>
        <text x={PAD_X} y={yAt(2) - 4} className="fill-white/25" fontSize="9">متوسط</text>
        <text x={PAD_X} y={yAt(1) - 4} className="fill-white/25" fontSize="9">کم</text>
      </svg>

      {/* Tooltip */}
      {hovered && (
        <div
          className="absolute -top-1 -translate-y-full -translate-x-1/2 pointer-events-none
            glass-strong rounded-lg px-2.5 py-1.5 text-[10.5px] whitespace-nowrap border border-white/10 z-10"
          style={{ left: `${tooltipLeftPct}%` }}
        >
          <div className="text-white/80 font-medium">
            {hovered.date.toLocaleDateString("fa-IR", { month: "short", day: "numeric" })}
          </div>
          <div className="text-white/45 flex items-center gap-1">
            <span>انرژی: {ENERGY_LABELS_FA[Object.keys(ENERGY_SCORE).find((k) => ENERGY_SCORE[k] === Math.round(hovered.avgEnergy))] || "متوسط"}</span>
            {hovered.dominantMood && <span>· {MOOD_EMOJI[hovered.dominantMood]}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

function MoodFrequencyBars({ entries }) {
  const counts = useMemo(() => {
    const c = {};
    entries.forEach((e) => (c[e.detected_mood] = (c[e.detected_mood] || 0) + 1));
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  }, [entries]);

  const maxCount = counts.length > 0 ? counts[0][1] : 1;

  if (counts.length === 0) {
    return <p className="text-center text-[12px] text-white/30 py-4">هنوز داده‌ای برای این نمودار نیست.</p>;
  }

  return (
    <div className="flex flex-col gap-2.5">
      {counts.map(([mood, count]) => {
        const pct = Math.max(4, (count / maxCount) * 100);
        const color = moodColor(mood);
        return (
          <div key={mood} className="flex items-center gap-2.5">
            <span className="w-24 flex-shrink-0 text-[11px] text-white/55 truncate flex items-center gap-1">
              <span>{MOOD_EMOJI[mood]}</span>
              <span>{moodLabel(mood)}</span>
            </span>
            <div className="flex-1 h-3 rounded-full bg-white/[0.05] overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: color }}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="w-6 flex-shrink-0 text-[10.5px] font-mono text-white/40 text-left">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

function DeltaBadge({ diff }) {
  if (diff === null) return null;
  const rounded = Math.round(diff * 100) / 100;
  if (Math.abs(rounded) < 0.05) {
    return (
      <span className="flex items-center gap-1 text-[10.5px] text-white/35">
        <Minus size={11} />
        بدون تغییر نسبت به هفته‌ی قبل
      </span>
    );
  }
  const isUp = rounded > 0;
  return (
    <span className="flex items-center gap-1 text-[10.5px] text-white/45">
      {isUp ? <TrendingUp size={11} className="text-mood-neutral" /> : <TrendingDown size={11} className="text-white/35" />}
      انرژی {isUp ? "بالاتر" : "پایین‌تر"} از هفته‌ی قبل
    </span>
  );
}

export default function MoodTrends({ entries }) {
  const days = useEnergyTrend(entries);
  const diff = useMemo(() => weeklyDelta(days), [days]);
  const hasAnyData = days.some((d) => d.avgEnergy !== null);

  return (
    <div className="flex flex-col gap-4">
      <div className="glass rounded-2xl p-4">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-1.5">
          <h3 className="text-[12.5px] font-semibold text-white/60">روند انرژی (۳۰ روز اخیر)</h3>
          <DeltaBadge diff={diff} />
        </div>
        {hasAnyData ? (
          <EnergyTrendChart days={days} />
        ) : (
          <p className="text-center text-[12px] text-white/30 py-8">
            هنوز داده‌ای برای رسم نمودار روند نیست.
          </p>
        )}
      </div>

      <div className="glass rounded-2xl p-4">
        <h3 className="text-[12.5px] font-semibold text-white/60 mb-3">فراوانی احساسات</h3>
        <MoodFrequencyBars entries={entries} />
      </div>
    </div>
  );
}
