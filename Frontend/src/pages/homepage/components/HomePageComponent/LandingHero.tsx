import { motion } from "framer-motion";

import { Link } from "react-router-dom";
import { Sparkles, ArrowRight, BookOpen } from "lucide-react";

export function LandingHero() {
  return (
    <section className="relative mt-16 text-center">
      {/* Animated gradient blobs */}
      <motion.div
        className="pointer-events-none absolute left-1/2 top-[-100px] h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-gradient-to-r from-[#03C75A] to-[#00A84D] opacity-20 blur-[120px]"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.2, 0.3, 0.2],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#03C75A]/30 bg-[#03C75A]/5 px-4 py-2"
        >
          <Sparkles className="h-4 w-4 text-[#03C75A]" />
          <span className="text-sm font-semibold text-[#03C75A]">AI-Powered Knowledge Management</span>
        </motion.div>

        <h1 className="mx-auto max-w-4xl text-[clamp(2rem,5vw,4rem)] font-black leading-[1.1] text-white">
          Transform Your Research Into
          <br />
          <span className="bg-gradient-to-r from-[#03C75A] via-[#00E08A] to-[#03C75A] bg-clip-text text-transparent">
            Structured Knowledge
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-[#bdbdbd]">
          NavNexus uses advanced AI to automatically extract concepts, discover connections, and visualize your knowledge in interactive graphs. Perfect for researchers, teams, and knowledge workers.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            to="/login"
            className="group inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-[#03C75A] to-[#00A84D] px-8 py-3 text-base font-bold text-black shadow-lg shadow-[#03C75A]/30 transition-all hover:shadow-xl hover:shadow-[#03C75A]/40"
          >
            Get Started Free
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>

          <a
            href="#features"
            className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#0a0a0a] px-8 py-3 text-base font-semibold transition-all hover:border-[#03C75A] hover:bg-[#0f0f0f]"
          >
            <BookOpen className="h-5 w-5" />
            Learn More
          </a>
        </div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="mx-auto mt-16 grid max-w-3xl grid-cols-3 gap-8 rounded-2xl border border-[#1f1f1f] bg-[#0a0a0a]/50 p-8 backdrop-blur-sm"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-[#03C75A]">10K+</div>
            <div className="mt-1 text-sm text-[#bdbdbd]">Documents Processed</div>
          </div>
          <div className="border-x border-[#1f1f1f] text-center">
            <div className="text-3xl font-bold text-[#03C75A]">500+</div>
            <div className="mt-1 text-sm text-[#bdbdbd]">Active Users</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-[#03C75A]">99.9%</div>
            <div className="mt-1 text-sm text-[#bdbdbd]">Uptime</div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}