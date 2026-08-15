"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import ProfileTab from "@/components/dashboard/tabs/ProfileTab";
import TimetablesTab from "@/components/dashboard/tabs/TimetablesTab";
import AnnouncementsTab from "@/components/dashboard/tabs/AnnouncementsTab";
import EventsTab from "@/components/dashboard/tabs/EventsTab";
import JanazahTab from "@/components/dashboard/tabs/JanazahTab";
import SettingsTab from "@/components/dashboard/tabs/SettingsTab";
import { ScheduleTab } from "@/components/dashboard/tabs/ScheduleTab";
import { GalleryTab } from "@/components/dashboard/tabs/GalleryTab";

type AdminInfo = {
  mobile: string;
  mosqueName: string;
  mosqueId: string;
};

type TabType = "timetables" | "announcements" | "events" | "janazah" | "schedule" | "gallery" | "profile" | "settings";

export default function MosqueAdminDashboardPage() {
  const router = useRouter();
  const [admin, setAdmin] = useState<AdminInfo | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("timetables");

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    const mobile = localStorage.getItem("admin_mobile");
    const mosqueId = localStorage.getItem("admin_mosque_id");
    const mosqueName = localStorage.getItem("admin_mosque_name");
    if (token && mosqueId && mosqueId !== "undefined" && mosqueName && mosqueName !== "undefined") {
      setAdmin({ mobile: mobile || "", mosqueId, mosqueName });
    }
    setLoadingAuth(false);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("admin_mobile");
    localStorage.removeItem("admin_mosque_id");
    localStorage.removeItem("admin_mosque_name");
    router.replace("/login");
  };

  if (loadingAuth) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="text-slate-500 font-medium">Verifying authentication...</div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: "timetables", label: "Prayer Timings", icon: "🕒" },
    { id: "announcements", label: "Announcements", icon: "📢" },
    { id: "events", label: "Events & Programs", icon: "📅" },
    { id: "janazah", label: "Janazah Notices", icon: "🤲" },
    { id: "schedule", label: "Operating Hours", icon: "⏰" },
    { id: "gallery", label: "Photo Gallery", icon: "🖼️" },
    { id: "profile", label: "Mosque Profile", icon: "🕌" },
    { id: "settings", label: "Account Settings", icon: "⚙️" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🕌</span>
              <div>
                <h1 className="font-bold text-slate-900 text-lg leading-tight">
                  {admin?.mosqueName || "Mosque Dashboard"}
                </h1>
                <p className="text-xs text-slate-500">Mosque Administrator Portal</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-xs font-medium text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full">
                {admin?.mobile}
              </span>
              <button
                onClick={handleLogout}
                className="text-xs font-medium text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 px-3 py-1.5 rounded-lg transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation Bar */}
        <div className="flex overflow-x-auto space-x-2 border-b border-slate-200 mb-8 pb-1 no-scrollbar">
          {tabs.map((t) => {
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center space-x-2 px-4 py-2.5 font-medium text-sm rounded-lg whitespace-nowrap transition ${
                  isActive
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <span>{t.icon}</span>
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panel */}
        <main>
          {activeTab === "timetables" && <TimetablesTab />}
          {activeTab === "announcements" && <AnnouncementsTab />}
          {activeTab === "events" && <EventsTab />}
          {activeTab === "janazah" && <JanazahTab />}
          {activeTab === "schedule" && <ScheduleTab />}
          {activeTab === "gallery" && <GalleryTab />}
          {activeTab === "profile" && <ProfileTab />}
          {activeTab === "settings" && <SettingsTab />}
        </main>
      </div>
    </div>
  );
}
