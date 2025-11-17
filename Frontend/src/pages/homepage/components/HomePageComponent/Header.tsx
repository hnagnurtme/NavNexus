import { Link } from "react-router-dom";
import { LogIn, Plus } from "lucide-react";
import { motion } from "framer-motion";
import { UserMenu } from "../UserMenu";

export function Header({
  isAuthenticated,
  onCreate,
}: {
  isAuthenticated: boolean;
  onCreate: () => void;
}) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"
    >
      {/* Brand Name Only */}
      <Link to="/" className="flex items-center gap-2 group">
        <span
          className="
            text-2xl font-bold tracking-wide
            bg-gradient-to-r from-[#03C75A] to-[#02ad50]
            bg-clip-text text-transparent
            transition-opacity group-hover:opacity-90
          "
        >
          NavNexus
        </span>

        <span
          className="
            text-[11px] px-2 py-[2px] rounded-full font-medium
            border border-[#1e1e1e] bg-[#0d0d0d]/70 text-[#888]
            transition-colors group-hover:text-[#03C75A] group-hover:border-[#03C75A]
          "
        >
          Alpha
        </span>
      </Link>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            {/* Create Button */}
            <motion.button
              whileHover={{ scale: 1.04, y: -1 }}
              whileTap={{ scale: 0.97 }}
              className="
                inline-flex items-center gap-2 rounded-full
                bg-gradient-to-r from-[#03C75A] via-[#02b450] to-[#009c45]
                px-5 py-2 text-sm font-semibold text-black
                shadow-[0_4px_14px_rgba(3,199,90,0.4)]
                transition-shadow hover:shadow-[0_4px_20px_rgba(3,199,90,0.55)]
              "
              onClick={onCreate}
            >
              <Plus className="h-4 w-4" />
              Create Workspace
            </motion.button>

            <UserMenu />
          </>
        ) : (
          <motion.div whileHover={{ scale: 1.03 }}>
            <Link
              to="/login"
              className="
                inline-flex items-center gap-2 rounded-full
                border border-[#2a2a2a] bg-[#0f0f0f]
                px-4 py-2 text-sm font-semibold text-[#dcdcdc]
                transition-colors hover:border-[#03C75A] hover:text-[#03C75A]
              "
            >
              <LogIn className="h-4 w-4" />
              Login
            </Link>
          </motion.div>
        )}
      </div>
    </motion.header>
  );
}
