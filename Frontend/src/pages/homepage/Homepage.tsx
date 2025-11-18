import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import AddWorkSpaceForm from "./components/AddWorkSpaceForm";

import { Header } from "./components/HomePageComponent/Header";
import { LandingHero } from "./components/HomePageComponent/LandingHero";
import { FeaturesSection } from "./components/HomePageComponent/FeaturesSection";
import { BenefitsSection } from "./components/HomePageComponent/BenefitsSection";

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-20 flex flex-col gap-3 border-t border-[#1c1c1c] pt-8 text-xs text-[#9a9a9a] sm:flex-row sm:items-center sm:justify-between">
      <p>© {currentYear} NavNexus. All rights reserved.</p>
      <nav className="flex gap-4" aria-label="Footer navigation">
        <a href="/privacy" className="transition-colors hover:text-[#03C75A]">
          Privacy
        </a>
        <a href="/terms" className="transition-colors hover:text-[#03C75A]">
          Terms
        </a>
        <a href="/support" className="transition-colors hover:text-[#03C75A]">
          Support
        </a>
      </nav>
    </footer>
  );
}

// Main component
export default function Homepage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [openWorkSpace, setOpenWorkSpace] = useState(false);

  // Redirect authenticated users to /workspaces
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/workspaces");
    }
  }, [isAuthenticated, navigate]);

  const handleCreateWorkspace = (data: any) => {
    console.log("Create workspace:", data);
    setOpenWorkSpace(false);
  };

  const handleCancelWorkspace = () => {
    setOpenWorkSpace(false);
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#f5f5f5]">
      {/* Modal */}
      {openWorkSpace && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md"
          role="dialog"
          aria-modal="true"
          aria-labelledby="workspace-modal-title"
        >
          <AddWorkSpaceForm
            onCreate={handleCreateWorkspace}
            onCancel={handleCancelWorkspace}
          />
        </div>
      )}

      <div className="mx-auto max-w-7xl px-6 py-12">
        <Header
          isAuthenticated={isAuthenticated}
          onCreate={() => setOpenWorkSpace(true)}
        />

        {/* Show landing page for unauthenticated users */}
        <LandingHero />
        <FeaturesSection />
        <BenefitsSection />
        <Footer />
      </div>
    </div>
  );
}
