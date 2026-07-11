import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star, ChevronDown, ThumbsUp, ThumbsDown, Film } from "lucide-react";
import { moodColor } from "../lib/constants";

export default function MovieCard({
  movie,
  historyId,
  onFeedback,
  index = 0,
  initialReaction = null,
  mood = "neutral",
}) {
  const [reasoningOpen, setReasoningOpen] = useState(false);
  const [reaction, setReaction] = useState(initialReaction);
  const accent = moodColor(mood);

  const handleReaction = async (type) => {
    const next = reaction === type ? null : type;
    setReaction(next);
    if (next) {
      try {
        await onFeedback(historyId, "movie", movie.title, type);
      } catch {
        setReaction(reaction);
      }
    }
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.38, delay: index * 0.07, ease: [0.25, 0.1, 0.25, 1] }}
      whileHover={{
        y: -7,
        boxShadow: `0 0 0 1.5px ${accent}35, 0 28px 56px -10px ${accent}20`,
      }}
      className="group flex flex-col rounded-2xl overflow-hidden cursor-default"
      style={{
        background: "rgba(255,255,255,0.038)",
        border: "1px solid rgba(255,255,255,0.075)",
      }}
    >
      {/* ── Poster ── */}
      <div className="relative w-full aspect-[2/3] overflow-hidden bg-base-3 flex-shrink-0">
        {movie.poster_path ? (
          <img
            src={movie.poster_path}
            alt={movie.title}
            loading="lazy"
            decoding="async"
            className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
          />
        ) : (
          <NoPoster title={movie.title} accent={accent} />
        )}

        {/* Cinematic gradient overlay — bottom heavy */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/96 via-black/25 to-transparent" />

        {/* Top row: genres left, rating right */}
        <div className="absolute top-0 inset-x-0 p-2 flex items-start justify-between gap-1">
          <div className="flex flex-wrap gap-1">
            {(movie.genres || []).slice(0, 2).map((g) => (
              <span
                key={g}
                className="text-[9px] leading-none font-medium text-white/80
                  bg-black/55 backdrop-blur-sm border border-white/10 rounded-full px-1.5 py-[3px]"
              >
                {g}
              </span>
            ))}
          </div>

          {movie.rating > 0 && (
            <span className="flex items-center gap-[3px] flex-shrink-0
              text-[10px] font-bold text-amber-300
              bg-black/60 backdrop-blur-sm border border-amber-400/20 rounded-full px-1.5 py-[3px]">
              <Star size={8} fill="currentColor" />
              {movie.rating.toFixed(1)}
            </span>
          )}
        </div>

        {/* Title on image */}
        <div className="absolute bottom-0 inset-x-0 px-3 pb-3 pt-6">
          <h4 className="font-bold text-[12.5px] text-white leading-snug line-clamp-2 drop-shadow-sm">
            {movie.title}
          </h4>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex flex-col gap-2 p-3 flex-1">
        {/* Overview */}
        {movie.overview && (
          <p className="text-[11px] text-white/38 leading-relaxed line-clamp-2">
            {movie.overview}
          </p>
        )}

        {/* Reasoning accordion */}
        {movie.reasoning?.length > 0 && (
          <div className="mt-0.5">
            <button
              onClick={() => setReasoningOpen((o) => !o)}
              className="flex items-center gap-1 text-[10.5px] font-medium transition-colors duration-150 cursor-pointer"
              style={{ color: reasoningOpen ? accent : `${accent}99` }}
            >
              <motion.span animate={{ rotate: reasoningOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={11} />
              </motion.span>
              چرا پیشنهاد شد؟
            </button>

            <AnimatePresence>
              {reasoningOpen && (
                <motion.ul
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.22 }}
                  className="overflow-hidden mt-1.5 space-y-1 text-[10.5px] text-white/38
                    leading-relaxed list-disc pr-4"
                >
                  {movie.reasoning.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* ── Feedback ── */}
        <div className="mt-auto pt-2 flex items-center gap-1.5 border-t border-white/[0.055]">
          <FeedBtn
            active={reaction === "like"}
            kind="like"
            onClick={() => handleReaction("like")}
            label="پسندیدم"
          >
            <ThumbsUp size={11} />
            <span>خوبه</span>
          </FeedBtn>

          <FeedBtn
            active={reaction === "dislike"}
            kind="dislike"
            onClick={() => handleReaction("dislike")}
            label="نپسندیدم"
          >
            <ThumbsDown size={11} />
            <span>نه</span>
          </FeedBtn>

          {movie.source === "tmdb" && (
            <span className="mr-auto text-[8.5px] font-mono text-white/18
              border border-white/10 rounded px-1.5 py-0.5">
              TMDB
            </span>
          )}
        </div>
      </div>
    </motion.article>
  );
}

/* ── Subcomponents ─────────────────────────────── */

function NoPoster({ title, accent }) {
  return (
    <div
      className="w-full h-full flex flex-col items-center justify-center gap-3"
      style={{
        background: `linear-gradient(160deg, ${accent}18 0%, ${accent}06 60%, transparent 100%)`,
      }}
    >
      <Film size={30} strokeWidth={1} style={{ color: `${accent}55` }} />
      <span
        className="text-[10.5px] text-center px-3 leading-snug line-clamp-3"
        style={{ color: `${accent}70` }}
      >
        {title}
      </span>
    </div>
  );
}

function FeedBtn({ active, kind, onClick, label, children }) {
  const activeStyle =
    kind === "like"
      ? { background: "rgba(52,217,188,0.14)", borderColor: "rgba(52,217,188,0.38)", color: "#34d9bc" }
      : { background: "rgba(242,90,122,0.14)", borderColor: "rgba(242,90,122,0.38)", color: "#f25a7a" };

  const idleStyle = {
    background: "rgba(255,255,255,0.03)",
    borderColor: "rgba(255,255,255,0.07)",
    color: "rgba(255,255,255,0.38)",
  };

  return (
    <motion.button
      whileTap={{ scale: 0.88 }}
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      className="flex items-center gap-1 h-7 px-2 rounded-lg border text-[10.5px]
        font-medium transition-all duration-150 cursor-pointer"
      style={active ? activeStyle : idleStyle}
    >
      {children}
    </motion.button>
  );
}
