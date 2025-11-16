
import { Link } from "react-router-dom";
import { LogIn, Plus } from "lucide-react";
import { motion } from "framer-motion";
import { UserMenu } from "../UserMenu";

export function Header({ isAuthenticated, onCreate }: { isAuthenticated: boolean; onCreate: () => void }) {
  return (
    <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
      <Link to="/" className="inline-flex items-center gap-3">
        <span className="inline-flex items-center gap-2 rounded-full border border-[#222] bg-[#0f0f0f] px-3 py-1 text-xs font-semibold tracking-wider text-[#bdbdbd]">
          NavNexus
        </span>
        <span className="text-sm text-[#8f8f8f]">Alpha</span>
      </Link>

      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-[#03C75A] to-[#00A84D] px-5 py-2 text-sm font-semibold text-black shadow-sm shadow-[#03C75A]/30 transition-shadow hover:shadow-md hover:shadow-[#03C75A]/40"
              onClick={onCreate}
            >
              <Plus className="h-4 w-4" /> Create Workspace
            </motion.button>
            <UserMenu />
          </>
        ) : (
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-full border border-[#222] bg-[#0f0f0f] px-4 py-2 text-sm font-semibold transition-colors hover:border-[#03C75A]"
          >
            <LogIn className="h-4 w-4" /> Login
          </Link>
        )}
      </div>
    </header>
  );
}
