import { motion } from "framer-motion";
interface Feature {
  icon: React.ReactNode;
  title: string;
  desc: string;
}
import { FileText, Users, GitBranch, Zap, Sparkles,Brain } from "lucide-react";
export function FeaturesSection() {
    const FEATURES: Feature[] = [
      {
        icon: <Brain className="h-8 w-8" />,
        title: 'AI Knowledge Graph',
        desc: 'Automatically extract concepts and visualize relationships across documents with advanced AI algorithms.'
      },
      {
        icon: <FileText className="h-8 w-8" />,
        title: 'Smart Document Parsing',
        desc: 'Upload PDF, Word, or text files — get structured nodes and searchable content instantly.'
      },
      {
        icon: <Users className="h-8 w-8" />,
        title: 'Collaborative Workspaces',
        desc: 'Share, annotate and build knowledge together with your team in real-time.'
      },
      {
        icon: <GitBranch className="h-8 w-8" />,
        title: 'Connection Discovery',
        desc: 'Uncover hidden relationships between concepts automatically as you add more content.'
      },
      {
        icon: <Zap className="h-8 w-8" />,
        title: 'Lightning Fast Search',
        desc: 'Find anything across all your documents with semantic search powered by AI.'
      },
      {
        icon: <Sparkles className="h-8 w-8" />,
        title: 'Smart Insights',
        desc: 'Get AI-generated summaries and insights from your knowledge base automatically.'
      }
    ];
  return (
    <section id="features" className="mt-32">
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-center"
      >
        <h2 className="text-3xl font-bold text-white">
          Everything You Need to Build Your
          <span className="bg-gradient-to-r from-[#03C75A] to-[#00E08A] bg-clip-text text-transparent"> Knowledge Graph</span>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-[#bdbdbd]">
          Powerful features designed to help you organize, analyze, and collaborate on your knowledge base.
        </p>
      </motion.div>

      <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature, idx) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: idx * 0.1, duration: 0.5 }}
            whileHover={{ y: -8, scale: 1.02 }}
            className="group relative overflow-hidden rounded-2xl border border-[#1f1f1f] bg-gradient-to-br from-[#0b0b0b] to-[#050505] p-8 shadow-lg transition-all hover:border-[#03C75A]/50 hover:shadow-2xl hover:shadow-[#03C75A]/10"
          >
            {/* Glow effect */}
            <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#03C75A]/10 blur-2xl transition-all group-hover:bg-[#03C75A]/20" />
            
            <div className="relative">
              <div className="inline-flex rounded-xl bg-gradient-to-br from-[#03C75A]/20 to-[#00A84D]/10 p-3 text-[#03C75A]">
                {feature.icon}
              </div>
              
              <h3 className="mt-4 text-xl font-bold text-white">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#bdbdbd]">{feature.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}