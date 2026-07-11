import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Download, Share2 } from "lucide-react";
import { moodColor, moodLabel, truncateTitle, MOOD_EMOJI } from "../lib/constants";

// اندازه‌ی قابل‌اشتراک برای استوری/پست (نسبت 4:5)
const CARD_W = 1080;
const CARD_H = 1350;

function hexToRgba(hex, alpha) {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export default function ShareMoodCard({ analysis, movie, music, onClose }) {
  const canvasRef = useRef(null);
  const [blobUrl, setBlobUrl] = useState(null);
  const canShareFiles = typeof navigator !== "undefined" && !!navigator.canShare && typeof File !== "undefined";

  useEffect(() => {
    let cancelled = false;

    async function draw() {
      const canvas = canvasRef.current;
      if (!canvas) return;
      canvas.width = CARD_W;
      canvas.height = CARD_H;
      const ctx = canvas.getContext("2d");
      const color = moodColor(analysis.mood);

      // صبر برای لود شدن فونت فارسی تا گلیف‌ها درست رندر شوند
      try {
        await document.fonts.load("700 64px Vazirmatn");
        await document.fonts.load("600 36px Vazirmatn");
        await document.fonts.ready;
      } catch {
        // فونت لود نشد؛ با فونت پیش‌فرض مرورگر ادامه می‌دهیم
      }
      if (cancelled) return;

      // پس‌زمینه گرادیانی بر اساس رنگ mood
      const bg = ctx.createLinearGradient(0, 0, 0, CARD_H);
      bg.addColorStop(0, hexToRgba(color, 0.35));
      bg.addColorStop(0.55, "#0f0d16");
      bg.addColorStop(1, "#08070c");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, CARD_W, CARD_H);

      const glow = ctx.createRadialGradient(CARD_W / 2, 380, 40, CARD_W / 2, 380, 420);
      glow.addColorStop(0, hexToRgba(color, 0.35));
      glow.addColorStop(1, hexToRgba(color, 0));
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, CARD_W, CARD_H);

      ctx.textAlign = "center";

      ctx.font = "160px 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif";
      ctx.fillText(MOOD_EMOJI[analysis.mood] || "🙂", CARD_W / 2, 430);

      ctx.fillStyle = "#f4f2f9";
      ctx.font = "700 60px Vazirmatn, Tahoma, sans-serif";
      ctx.fillText(`امروز حس می‌کنی: ${moodLabel(analysis.mood)}`, CARD_W / 2, 560);

      ctx.fillStyle = hexToRgba(color, 0.95);
      ctx.font = "600 32px Vazirmatn, Tahoma, sans-serif";
      ctx.fillText(`${Math.round(analysis.confidence * 100)}٪ اطمینان`, CARD_W / 2, 618);

      ctx.strokeStyle = "rgba(255,255,255,0.12)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(CARD_W / 2 - 120, 678);
      ctx.lineTo(CARD_W / 2 + 120, 678);
      ctx.stroke();

      let y = 780;
      const drawChip = (icon, text) => {
        ctx.font = "500 34px Vazirmatn, Tahoma, sans-serif";
        const textWidth = ctx.measureText(`${icon}  ${text}`).width;
        const boxWidth = Math.min(textWidth + 100, CARD_W - 120);
        const boxX = (CARD_W - boxWidth) / 2;
        ctx.fillStyle = "rgba(255,255,255,0.06)";
        roundRect(ctx, boxX, y, boxWidth, 96, 24);
        ctx.fill();
        ctx.fillStyle = "#f4f2f9";
        ctx.fillText(`${icon}  ${text}`, CARD_W / 2, y + 62);
        y += 128;
      };

      if (movie) drawChip("🎬", truncateTitle(movie.title, 32));
      if (music) drawChip("🎧", truncateTitle(`${music.title} — ${music.artist}`, 32));

      ctx.fillStyle = "rgba(255,255,255,0.35)";
      ctx.font = "600 30px 'Space Grotesk', sans-serif";
      ctx.fillText("VibeAI ✦", CARD_W / 2, CARD_H - 70);

      canvas.toBlob((blob) => {
        if (blob && !cancelled) setBlobUrl(URL.createObjectURL(blob));
      }, "image/png");
    }

    draw();
    return () => {
      cancelled = true;
    };
  }, [analysis, movie, music]);

  useEffect(() => {
    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [blobUrl]);

  const handleDownload = () => {
    if (!blobUrl) return;
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `vibeai-mood-${analysis.mood}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const handleShare = async () => {
    if (!blobUrl) return;
    try {
      const res = await fetch(blobUrl);
      const blob = await res.blob();
      const file = new File([blob], `vibeai-mood-${analysis.mood}.png`, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: "VibeAI", text: "حس امروزم رو ببین 👀" });
      }
    } catch {
      // کاربر اشتراک‌گذاری را لغو کرده؛ دکمه‌ی دانلود همچنان در دسترس است
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.94, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 10 }}
          transition={{ duration: 0.2 }}
          onClick={(e) => e.stopPropagation()}
          className="glass-strong rounded-3xl p-4 w-full max-w-[340px] flex flex-col items-center gap-4"
        >
          <div className="flex items-center justify-between w-full">
            <h3 className="text-[13px] font-semibold text-white/70">اشتراک‌گذاری حالت</h3>
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white transition-colors"
              aria-label="بستن"
            >
              <X size={16} />
            </button>
          </div>

          <div className="w-full rounded-2xl overflow-hidden border border-white/10 bg-base-1">
            <canvas ref={canvasRef} className="w-full h-auto block" />
          </div>

          <div className="flex gap-2.5 w-full">
            <button
              onClick={handleDownload}
              disabled={!blobUrl}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl py-2.5 text-[12.5px] font-semibold
                bg-white/[0.06] hover:bg-white/[0.1] text-white/80 border border-white/10 transition-colors disabled:opacity-40"
            >
              <Download size={14} />
              دانلود تصویر
            </button>
            {canShareFiles && (
              <button
                onClick={handleShare}
                disabled={!blobUrl}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl py-2.5 text-[12.5px] font-semibold
                  bg-gradient-to-l from-mood-neutral to-violet-600 text-base-0 transition-transform hover:scale-[1.02] disabled:opacity-40"
              >
                <Share2 size={14} />
                اشتراک‌گذاری
              </button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
