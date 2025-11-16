import { motion } from "framer-motion";

import { ArrowRight, Check } from "lucide-react";

import { Link } from "react-router-dom";

export function BenefitsSection() {
    const BENEFITS = [
  'Unlimited document uploads',
  'Real-time collaboration',
  'Advanced AI analysis',
  'Secure cloud storage',
  'Export in multiple formats',
  'Priority support'
];
  return (
    <section className="mt-32">
      <div className="overflow-hidden rounded-3xl border border-[#1f1f1f] bg-gradient-to-br from-[#0f0f0f] to-[#050505]">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left side - Benefits */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="p-12"
          >
            <h2 className="text-3xl font-bold text-white">
              Why Choose
              <span className="bg-gradient-to-r from-[#03C75A] to-[#00E08A] bg-clip-text text-transparent"> NavNexus?</span>
            </h2>
            <p className="mt-4 text-[#bdbdbd]">
              Join hundreds of teams already building their knowledge graphs with our platform.
            </p>

            <div className="mt-8 space-y-4">
              {BENEFITS.map((benefit, idx) => (
                <motion.div
                  key={benefit}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1, duration: 0.4 }}
                  className="flex items-center gap-3"
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#03C75A]/20">
                    <Check className="h-4 w-4 text-[#03C75A]" />
                  </div>
                  <span className="text-white">{benefit}</span>
                </motion.div>
              ))}
            </div>

            <Link
              to="/login"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-[#03C75A] to-[#00A84D] px-6 py-3 font-semibold text-black transition-all hover:shadow-lg hover:shadow-[#03C75A]/30"
            >
              Start Building Today <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>

          {/* Right side - Visual */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative flex items-center justify-center bg-gradient-to-br from-[#03C75A]/5 to-transparent p-12"
          >
            {/* Animated circles representing knowledge nodes */}
            <div className="relative h-64 w-64">
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute h-16 w-16 rounded-full border-2 border-[#03C75A]/30 bg-[#03C75A]/10"
                  style={{
                    top: `${Math.sin((i * Math.PI) / 3) * 100 + 100}px`,
                    left: `${Math.cos((i * Math.PI) / 3) * 100 + 100}px`,
                  }}
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    delay: i * 0.5,
                  }}
                />
              ))}
              <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-[#03C75A] bg-gradient-to-br from-[#03C75A]/20 to-[#00A84D]/20" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}