import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ThumbsUp, ThumbsDown, Music2, Play, Pause } from "lucide-react";

// آیکون رسمی Spotify — در lucide-react موجود نیست
function SpotifyIcon({ size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141 4.32-1.32 9.6-.66 13.32 1.621.42.18.6.719.42 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.18-1.2-.181-1.38-.72-.18-.6.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.3.421-1.02.599-1.559.3z"/>
    </svg>
  );
}

// آیکون رسمی YouTube — در lucide-react موجود نیست
function YoutubeIcon({ size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M23.5 6.2a3.02 3.02 0 0 0-2.12-2.14C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.38.56A3.02 3.02 0 0 0 .5 6.2 31.6 31.6 0 0 0 0 12a31.6 31.6 0 0 0 .5 5.8 3.02 3.02 0 0 0 2.12 2.14C4.5 20.5 12 20.5 12 20.5s7.5 0 9.38-.56a3.02 3.02 0 0 0 2.12-2.14A31.6 31.6 0 0 0 24 12a31.6 31.6 0 0 0-.5-5.8ZM9.6 15.6V8.4l6.3 3.6-6.3 3.6Z"/>
    </svg>
  );
}

// Unique gradient palette — یک رنگ متفاوت به هر آهنگ
const PALETTES = [
  ["#6D28D9", "#2563EB"],   // violet → blue
  ["#059669", "#0891B2"],   // emerald → cyan
  ["#C2410C", "#CA8A04"],   // orange → yellow
  ["#2563EB", "#7C3AED"],   // blue → violet
  ["#0891B2", "#10B981"],   // cyan → teal
  ["#9333EA", "#EC4899"],   // purple → pink
  ["#B45309", "#DC2626"],   // amber → red
  ["#0E7490", "#6D28D9"],   // teal → violet
  ["#7C3AED", "#DB2777"],   // violet → fuchsia
  ["#065F46", "#0F766E"],   // dark-emerald → teal
];

// Equalizer bar heights — 4 bars با phase‌های مختلف
const EQ_BARS = [
  { anim: "animate-eq-1", h: "h-4" },
  { anim: "animate-eq-2", h: "h-5" },
  { anim: "animate-eq-3", h: "h-3" },
  { anim: "animate-eq-4", h: "h-4" },
];

export default function MusicCard({
  song,
  historyId,
  onFeedback,
  index = 0,
  initialReaction = null,
}) {
  const [reasoningOpen, setReasoningOpen] = useState(false);
  const [reaction, setReaction] = useState(initialReaction);
  const [artHovered, setArtHovered] = useState(false);
  const [embedOpen, setEmbedOpen] = useState(false);

  const [fromColor, toColor] = PALETTES[index % PALETTES.length];
  const isLiked = reaction === "like";
  const showEq = isLiked || artHovered;

  // شناسه‌ی ترک از روی spotify_url استخراج می‌شود تا نیازی به فیلد جدا از بک‌اند نباشد
  const spotifyTrackId = useMemo(() => {
    if (!song.spotify_url) return null;
    const match = song.spotify_url.match(/track\/([a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }, [song.spotify_url]);

  const handleReaction = async (type) => {
    const next = reaction === type ? null : type;
    setReaction(next);
    if (next) {
      try {
        await onFeedback(historyId, "music", song.title, type);
      } catch {
        setReaction(reaction);
      }
    }
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 18, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.36, delay: index * 0.055, ease: [0.25, 0.1, 0.25, 1] }}
      whileHover={{ y: -5, boxShadow: `0 0 0 1.5px ${fromColor}35, 0 20px 48px -10px ${fromColor}18` }}
      className="group flex flex-col rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.038)",
        border: "1px solid rgba(255,255,255,0.075)",
      }}
    >
      {/* ── Album Art ── */}
      <div
        className="relative w-full aspect-square overflow-hidden cursor-pointer flex-shrink-0"
        onMouseEnter={() => setArtHovered(true)}
        onMouseLeave={() => setArtHovered(false)}
        onClick={() => window.open(song.youtube_link, "_blank", "noopener noreferrer")}
        role="link"
        aria-label={`پخش ${song.title} در یوتیوب`}
      >
        {song.album_image ? (
          /* کاور واقعی آلبوم (از Spotify) */
          <img
            src={song.album_image}
            alt={`کاور آلبوم ${song.title}`}
            loading="lazy"
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <>
            {/* Gradient background */}
            <div
              className="absolute inset-0 transition-opacity duration-500"
              style={{
                background: `linear-gradient(145deg, ${fromColor} 0%, ${toColor} 100%)`,
              }}
            />

            {/* Noise texture overlay */}
            <div
              className="absolute inset-0 opacity-20 mix-blend-overlay"
              style={{
                backgroundImage:
                  "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E\")",
                backgroundSize: "150px 150px",
              }}
            />

            {/* Radial light */}
            <div
              className="absolute inset-0"
              style={{
                background: `radial-gradient(circle at 30% 30%, rgba(255,255,255,0.18) 0%, transparent 60%)`,
              }}
            />
          </>
        )}

        {/* Scrim پایین تصویر — خوانایی نشان "یوتیوب" و اکولایزر روی کاورهای روشن */}
        {song.album_image && (
          <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-transparent to-transparent pointer-events-none" />
        )}

        {/* Center content: icon or equalizer (روی کاور واقعی فقط اکولایزر نشان داده می‌شود) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <AnimatePresence mode="wait">
            {showEq ? (
              <motion.div
                key="eq"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.18 }}
                className={`flex items-end gap-1 h-10 px-1 ${song.album_image ? "bg-black/35 backdrop-blur-sm rounded-xl px-3 py-2" : ""}`}
                aria-hidden="true"
              >
                {EQ_BARS.map((bar, i) => (
                  <div
                    key={i}
                    className={`w-[5px] ${bar.h} ${bar.anim} rounded-full origin-bottom`}
                    style={{ background: "rgba(255,255,255,0.85)" }}
                  />
                ))}
              </motion.div>
            ) : !song.album_image ? (
              <motion.div
                key="icon"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.18 }}
              >
                <Music2
                  size={36}
                  strokeWidth={1.2}
                  className="text-white/70 drop-shadow-sm"
                />
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Play hint on hover */}
        <AnimatePresence>
          {artHovered && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-2.5 left-2.5 flex items-center gap-1.5
                bg-black/50 backdrop-blur-sm rounded-full px-2.5 py-1.5
                border border-white/15 text-[10px] text-white/80"
            >
              <Play size={9} fill="currentColor" />
              یوتیوب
            </motion.div>
          )}
        </AnimatePresence>

        {/* Liked glow ring */}
        <AnimatePresence>
          {isLiked && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 rounded-2xl"
              style={{ boxShadow: `inset 0 0 0 2px rgba(52,217,188,0.5)` }}
            />
          )}
        </AnimatePresence>
      </div>

      {/* ── Body ── */}
      <div className="flex flex-col gap-2 p-3.5 flex-1">
        {/* Title + Artist */}
        <div className="min-w-0">
          <h4 className="font-bold text-[13px] leading-snug truncate text-white">{song.title}</h4>
          <p className="text-[11.5px] text-white/45 truncate mt-0.5">{song.artist}</p>
        </div>

        {/* Genre */}
        <span
          className="self-start text-[10px] font-medium rounded-full px-2.5 py-1 border"
          style={{
            background: `${fromColor}18`,
            borderColor: `${fromColor}35`,
            color: `${fromColor}ee`,
          }}
        >
          {song.genre}
        </span>

        {/* Listen on — یوتیوب و اسپاتیفای */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <a
              href={song.youtube_link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 h-6 px-2 rounded-full text-[10px] font-medium
                text-[#ff3b3b] bg-[#ff3b3b]/12 border border-[#ff3b3b]/30
                hover:bg-[#ff3b3b]/20 transition-colors"
            >
              <YoutubeIcon size={11} />
              یوتیوب
            </a>

            {spotifyTrackId && (
              <button
                onClick={() => setEmbedOpen((o) => !o)}
                aria-expanded={embedOpen}
                aria-label={embedOpen ? "بستن پخش‌کننده" : "پخش پیش‌نمایش در اسپاتیفای"}
                className="flex items-center gap-1 h-6 px-2 rounded-full border text-[10px] font-medium
                  text-white/55 border-white/10 bg-white/[0.03] hover:text-white/85 hover:bg-white/[0.06]
                  transition-colors cursor-pointer"
              >
                {embedOpen ? <Pause size={9} /> : <Play size={9} />}
                پیش‌نمایش
              </button>
            )}

            {song.spotify_url && (
              <a
                href={song.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 h-6 px-2 rounded-full text-[10px] font-medium
                  text-[#1ed760] bg-[#1ed760]/12 border border-[#1ed760]/30
                  hover:bg-[#1ed760]/20 transition-colors"
              >
                <SpotifyIcon size={10} />
                Spotify
              </a>
            )}
          </div>

          <AnimatePresence>
            {embedOpen && spotifyTrackId && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 152, opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden rounded-xl"
              >
                <iframe
                  src={`https://open.spotify.com/embed/track/${spotifyTrackId}?utm_source=generator&theme=0`}
                  width="100%"
                  height="152"
                  style={{ borderRadius: "12px", border: "none" }}
                  allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                  loading="lazy"
                  title={`پخش‌کننده‌ی اسپاتیفای — ${song.title}`}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Reasoning */}
        {song.reasoning?.length > 0 && (
          <div>
            <button
              onClick={() => setReasoningOpen((o) => !o)}
              className="flex items-center gap-1 text-[10.5px] font-medium text-white/35 hover:text-white/65 transition-colors cursor-pointer"
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
                  {song.reasoning.map((r, i) => (
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
        </div>
      </div>
    </motion.article>
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
