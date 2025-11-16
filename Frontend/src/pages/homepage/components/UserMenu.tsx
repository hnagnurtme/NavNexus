import { useState, useRef, useEffect } from "react";
import {
  LogOut,
  ChevronDown,
  Mail,
  Phone,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export const UserMenu = () => {
  const { user, signOutUser } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  // Generate simple avatar letter
  const initial = user?.name?.charAt(0)?.toUpperCase() || "U";

  return (
    <div className="relative" ref={menuRef}>
      {/* Profile button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 rounded-full bg-[#0f0f0f] border border-[#2b2b2b] px-4 py-2 transition-all hover:border-[#03C75A] hover:bg-[#151515]"
      >
        {/* Avatar */}
        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[#03C75A] to-[#027a3a] text-black font-bold flex items-center justify-center shadow-md">
          {initial}
        </div>

        <span className="text-sm text-[#f5f5f5] font-medium">
          {user?.name || "User"}
        </span>

        <ChevronDown
          className={`w-4 h-4 text-[#b3b3b3] transition ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Popup */}
      {open && (
        <div className="absolute right-0 mt-3 w-72 rounded-2xl border border-[#2a2a2a] bg-[#0f0f0f] shadow-xl shadow-black/40 p-5 z-50 animate-fadeIn">
          {/* Header */}
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#03C75A] to-[#027a3a] text-black font-bold flex items-center justify-center text-lg shadow-lg">
              {initial}
            </div>
            <div>
              <p className="text-base font-semibold text-[#ffffff]">
                {user?.name || "Unknown User"}
              </p>
              <span className="text-xs px-2 py-1 rounded-full bg-[#03C75A]/15 text-[#03C75A] font-semibold">
                Verified User
              </span>
            </div>
          </div>

          {/* Info list */}
          <div className="mt-4 space-y-3">
            {/* Email */}
            <div className="flex items-center gap-3 text-[#b3b3b3]">
              <Mail className="w-4 h-4 text-[#03C75A]" />
              <span className="text-sm">{user?.email || "No email"}</span>
            </div>

            {/* Phone */}
            <div className="flex items-center gap-3 text-[#b3b3b3]">
              <Phone className="w-4 h-4 text-[#03C75A]" />
              <span className="text-sm">{user?.phoneNumber || "No phone"}</span>
            </div>
          </div>

          <div className="my-4 h-px w-full bg-[#2a2a2a]" />

          {/* Logout Button */}
          <button
            onClick={signOutUser}
            className="flex items-center gap-2 w-full px-4 py-2 rounded-xl bg-[#1a1a1a] text-[#ff6b6b] font-semibold text-sm hover:bg-[#251616] transition"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      )}
    </div>
  );
};





