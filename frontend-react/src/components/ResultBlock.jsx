import { useState } from "react";
import { motion } from "framer-motion";
import { Film, Music2, Clapperboard, Headphones, Share2 } from "lucide-react";
import AnalysisCard from "./AnalysisCard";
import MovieCard from "./MovieCard";
import MusicCard from "./MusicCard";
import ShareMoodCard from "./ShareMoodCard";

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

export default function ResultBlock({
  analysis,
  movies,
  music,
  historyId,
  onFeedback,
  existingFeedback = [],
}) {
  const [shareOpen, setShareOpen] = useState(false);

  const reactionFor = (itemType, itemName) => {
    const fb = existingFeedback.find(
      (f) => f.item_type === itemType && f.item_name === itemName
    );
    return fb ? fb.reaction : null;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6"
    >
      <div className="flex justify-start">
        <button
          onClick={() => setShareOpen(true)}
          className="flex items-center gap-1.5 text-[11.5px] text-white/40 hover:text-white/80
            transition-colors px-2.5 py-1.5 rounded-lg hover:bg-white/[0.05]"
        >
          <Share2 size={13} />
          اشتراک‌گذاری
        </button>
      </div>

      <AnalysisCard analysis={analysis} />

      {movies?.length > 0 && (
        <section>
          <SectionHeader
            icon={<Clapperboard size={15} />}
            label="فیلم"
            count={movies.length}
            gradient="from-mood-excited/80 to-mood-neutral/80"
          />
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3"
          >
            {movies.map((movie, i) => (
              <MovieCard
                key={`${movie.title}-${i}`}
                movie={movie}
                historyId={historyId}
                onFeedback={onFeedback}
                index={i}
                mood={analysis.mood}
                initialReaction={reactionFor("movie", movie.title)}
              />
            ))}
          </motion.div>
        </section>
      )}

      {music?.length > 0 && (
        <section>
          <SectionHeader
            icon={<Headphones size={15} />}
            label="موزیک"
            count={music.length}
            gradient="from-mood-calm/80 to-mood-neutral/80"
          />
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3"
          >
            {music.map((song, i) => (
              <MusicCard
                key={`${song.title}-${i}`}
                song={song}
                historyId={historyId}
                onFeedback={onFeedback}
                index={i}
                initialReaction={reactionFor("music", song.title)}
              />
            ))}
          </motion.div>
        </section>
      )}

      {shareOpen && (
        <ShareMoodCard
          analysis={analysis}
          movie={movies?.[0]}
          music={music?.[0]}
          onClose={() => setShareOpen(false)}
        />
      )}
    </motion.div>
  );
}

function SectionHeader({ icon, label, count, gradient }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      {/* Icon pill */}
      <div className={`flex items-center gap-1.5 bg-gradient-to-r ${gradient} bg-clip-text`}>
        <span className="text-mood-neutral">{icon}</span>
        <span className="text-[13px] font-bold text-white">{label}</span>
      </div>

      {/* Count badge */}
      <span className="text-[10.5px] font-mono text-white/30 bg-white/[0.04] border border-white/[0.06] rounded-full px-2 py-0.5">
        {count}
      </span>

      {/* Divider line */}
      <div className="flex-1 h-px bg-gradient-to-l from-transparent via-white/[0.06] to-transparent" />
    </div>
  );
}
