import { motion } from 'framer-motion';

interface LoadingSkeletonProps {
  count?: number;
  variant?: 'node' | 'card' | 'text';
  className?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 1,
  variant = 'card',
  className = '',
}) => {
  const renderSkeleton = (index: number) => {
    switch (variant) {
      case 'node':
        return (
          <motion.div
            key={index}
            className={`w-64 h-24 rounded-xl bg-gradient-to-br from-gray-800/50 to-black/70 border border-white/10 overflow-hidden relative ${className}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
              initial={{ x: '-100%' }}
              animate={{ x: '100%' }}
              transition={{
                repeat: Infinity,
                duration: 1.5,
                ease: 'linear',
              }}
            />
            <div className="p-3 flex items-center gap-3">
              <div className="w-5 h-5 rounded bg-white/10" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-white/10 rounded w-3/4" />
                <div className="h-3 bg-white/5 rounded w-1/2" />
              </div>
            </div>
          </motion.div>
        );

      case 'text':
        return (
          <motion.div
            key={index}
            className={`h-4 bg-white/10 rounded overflow-hidden relative ${className}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.05 }}
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
              initial={{ x: '-100%' }}
              animate={{ x: '100%' }}
              transition={{
                repeat: Infinity,
                duration: 1.5,
                ease: 'linear',
              }}
            />
          </motion.div>
        );

      case 'card':
      default:
        return (
          <motion.div
            key={index}
            className={`rounded-xl bg-white/5 border border-white/10 p-4 overflow-hidden relative ${className}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
              initial={{ x: '-100%' }}
              animate={{ x: '100%' }}
              transition={{
                repeat: Infinity,
                duration: 1.5,
                ease: 'linear',
              }}
            />
            <div className="space-y-3 relative">
              <div className="h-5 bg-white/10 rounded w-3/4" />
              <div className="h-4 bg-white/5 rounded w-full" />
              <div className="h-4 bg-white/5 rounded w-5/6" />
            </div>
          </motion.div>
        );
    }
  };

  return (
    <div className="space-y-3">
      {Array.from({ length: count }, (_, i) => renderSkeleton(i))}
    </div>
  );
};
