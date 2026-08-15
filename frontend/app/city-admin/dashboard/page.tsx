"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, FormEvent } from "react";
import { 
  Bell, 
  Calendar, 
  FileText, 
  Plus, 
  Search, 
  Trash2, 
  Edit3, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  LogOut, 
  Grid, 
  List, 
  Copy, 
  Archive, 
  Send,
  Building2,
  Shield,
  User,
  Phone,
  KeyRound,
  Lock
} from "lucide-react";

import { apiRequest } from "@/lib/api/client";

type Stats = {
  announcements: {
    total: number;
    published: number;
    draft: number;
    scheduled: number;
    expired: number;
  };
  events: {
    total: number;
    upcoming: number;
    ongoing: number;
    completed: number;
  };
  emergency_alerts: number;
  recent_activity: Array<{
    id: string;
    type: string;
    title: string;
    action: string;
    description: string;
    time: string;
  }>;
};

type Announcement = {
  id: number;
  title: string;
  short_summary: string;
  content: string;
  priority: string;
  announcement_type: string;
  status: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
};

type PublisherAttribution = {
  name: string;
  role: string;
  city: string;
};

type Event = {
  id: number;
  title: string;
  description: string;
  event_type: string;
  event_date: string;
  event_time: string;
  end_time: string;
  event_location: string;
  speaker_name: string;
  registration_required: boolean;
  max_capacity: number;
  organizer: string;
  status: string;
  temporal_status?: "upcoming" | "completed";
  organizer_name?: string;
  published_by?: PublisherAttribution | null;
};

type ProfileData = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  mobile_number: string;
  city_id: number;
  city_name: string;
  is_active: boolean;
  must_change_password: boolean;
};

function formatTimeTo12Hour(timeStr: string): string {
  if (!timeStr) return "";
  const parts = timeStr.split(":");
  if (parts.length < 2) return timeStr;
  let hours = parseInt(parts[0], 10);
  const minutes = parts[1];
  if (isNaN(hours)) return timeStr;
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  if (hours === 0) hours = 12;
  const formattedHours = hours < 10 ? `0${hours}` : `${hours}`;
  return `${formattedHours}:${minutes} ${ampm}`;
}

export default function CityAdminDashboard() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [cityName, setCityName] = useState<string>("");
  const [cityId, setCityId] = useState<string>("");

  const [activeTab, setActiveTab] = useState<"overview" | "mosques" | "announcements" | "events" | "my_mosque" | "account">("overview");
  const [hasMosqueAdmin, setHasMosqueAdmin] = useState(false);
  const [mosqueName, setMosqueName] = useState("");
  const [mosqueId, setMosqueId] = useState("");

  // Loading States
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [loadingMosques, setLoadingMosques] = useState(false);

  // Stats Data
  const [stats, setStats] = useState<Stats | null>(null);
  const [cityAnalytics, setCityAnalytics] = useState<{
    total_visits: number;
    unique_identified_visitors: number;
    period_metrics: { today: number; this_week: number; this_month: number };
    top_mosques: Array<{ mosque_id: number; mosque_name: string; views: number }>;
  } | null>(null);

  // List Data
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [cityMosques, setCityMosques] = useState<any[]>([]);

  // Profile State
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [profileForm, setProfileForm] = useState({ first_name: "", last_name: "", email: "" });
  const [savingProfile, setSavingProfile] = useState(false);

  // Password Change State
  const [passwordForm, setPasswordForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [savingPassword, setSavingPassword] = useState(false);

  // Mobile Change State
  const [mobileStep, setMobileStep] = useState<"request" | "verify">("request");
  const [mobileForm, setMobileForm] = useState({ current_password: "", new_mobile_number: "", otp_code: "" });
  const [savingMobile, setSavingMobile] = useState(false);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");

  // Modal States
  const [isAnnouncementModalOpen, setIsAnnouncementModalOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null);
  const [announcementForm, setAnnouncementForm] = useState({
    title: "",
    short_summary: "",
    content: "",
    priority: "normal",
    announcement_type: "general",
    status: "published",
    start_date: new Date().toISOString().split("T")[0],
    end_date: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().split("T")[0],
  });

  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [eventForm, setEventForm] = useState({
    title: "",
    description: "",
    event_type: "lecture",
    event_date: new Date().toISOString().split("T")[0],
    event_time: "18:00",
    end_time: "19:30",
    event_location: "",
    speaker_name: "",
    registration_required: false,
    max_capacity: 100,
    organizer: "",
    status: "published",
  });

  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const role = localStorage.getItem("user_role");
    const city = localStorage.getItem("city_admin_city_name");
    const cId = localStorage.getItem("city_admin_city_id");
    const rolesStr = localStorage.getItem("user_roles");
    const roles: string[] = rolesStr ? JSON.parse(rolesStr) : [];
    const mId = localStorage.getItem("admin_mosque_id");
    const mName = localStorage.getItem("admin_mosque_name");

    if (!savedToken) {
      router.push("/login");
      return;
    }
    if (role === "mosque_admin" && !roles.includes("city_admin")) {
      router.push("/dashboard");
      return;
    }
    if (role === "super_admin") {
      router.push("/super-admin/dashboard");
      return;
    }

    setToken(savedToken);
    setCityName(city || "Assigned City");
    setCityId(cId || "");

    const isDual = roles.includes("mosque_admin") || (!!mId && mId !== "undefined");
    setHasMosqueAdmin(isDual);
    if (mId && mId !== "undefined") setMosqueId(mId);
    if (mName && mName !== "undefined") setMosqueName(mName);
  }, [router]);


  const loadStats = async () => {
    try {
      setLoadingStats(true);
      const data = await apiRequest<Stats>({ path: "/city-admin/stats/" });
      setStats(data);
    } catch {
      showToast("Failed to load dashboard statistics.", "error");
    } finally {
      setLoadingStats(false);
    }
  };

  const loadAnnouncements = async () => {
    try {
      setLoadingAnnouncements(true);
      const data = await apiRequest<any>({ path: `/city-admin/announcements/` });
      setAnnouncements(data.results || data);
    } catch {
      showToast("Failed to load city notices list.", "error");
    } finally {
      setLoadingAnnouncements(false);
    }
  };

  const loadEvents = async () => {
    try {
      setLoadingEvents(true);
      const data = await apiRequest<any>({ path: `/city-admin/events/` });
      setEvents(data.results || data);
    } catch {
      showToast("Failed to load events list.", "error");
    } finally {
      setLoadingEvents(false);
    }
  };

  const loadCityMosques = async () => {
    try {
      setLoadingMosques(true);
      const data = await apiRequest<any>({ path: "/city-admin/mosques/" });
      setCityMosques(data.results || data);
    } catch {
      showToast("Failed to load city mosques.", "error");
    } finally {
      setLoadingMosques(false);
    }
  };

  const loadCityAnalytics = async () => {
    try {
      const data = await apiRequest<any>({ path: "/analytics/city-admin/" });
      setCityAnalytics(data);
    } catch {
      // analytics fallback silently
    }
  };

  const loadProfile = async () => {
    try {
      const data = await apiRequest<any>({ path: "/city-admin/profile/" });
      setProfile(data);
      setProfileForm({
        first_name: data.first_name || "",
        last_name: data.last_name || "",
        email: data.email || "",
      });
      if (data.has_mosque_admin) {
        setHasMosqueAdmin(true);
        if (data.mosque_id) {
          setMosqueId(String(data.mosque_id));
          localStorage.setItem("admin_mosque_id", String(data.mosque_id));
        }
        if (data.mosque_name) {
          setMosqueName(data.mosque_name);
          localStorage.setItem("admin_mosque_name", data.mosque_name);
        }
        if (data.roles) {
          localStorage.setItem("user_roles", JSON.stringify(data.roles));
        }
      } else {
        setHasMosqueAdmin(false);
        setMosqueId("");
        setMosqueName("");
        localStorage.removeItem("admin_mosque_id");
        localStorage.removeItem("admin_mosque_name");
        if (data.roles) {
          localStorage.setItem("user_roles", JSON.stringify(data.roles));
        }
      }
    } catch {
      showToast("Failed to load profile details.", "error");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadStats();
    loadAnnouncements();
    loadEvents();
    loadCityMosques();
    loadCityAnalytics();
    loadProfile();
  }, [token]);

  const handleUpdateProfile = async (e: FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const updated = await apiRequest<ProfileData>({
        path: "/city-admin/profile/",
        method: "PATCH",
        body: JSON.stringify(profileForm),
      });
      setProfile(updated);
      showToast("Profile details updated successfully!", "success");
    } catch {
      showToast("Failed to update profile.", "error");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      showToast("New passwords do not match.", "error");
      return;
    }
    setSavingPassword(true);
    try {
      const res = await apiRequest<{ token: string; detail: string }>({
        path: "/city-admin/change-password/",
        method: "POST",
        body: JSON.stringify(passwordForm),
      });
      if (res.token) {
        localStorage.setItem("auth_token", res.token);
        setToken(res.token);
      }
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      showToast("Password updated successfully!", "success");
    } catch {
      showToast("Failed to update password. Check current password.", "error");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleMobileRequestOTP = async (e: FormEvent) => {
    e.preventDefault();
    setSavingMobile(true);
    try {
      await apiRequest({
        path: "/city-admin/change-mobile/request/",
        method: "POST",
        body: JSON.stringify({
          current_password: mobileForm.current_password,
          new_mobile_number: mobileForm.new_mobile_number,
        }),
      });
      setMobileStep("verify");
      showToast("OTP sent to your new mobile number.", "success");
    } catch {
      showToast("Failed to send OTP. Verify current password.", "error");
    } finally {
      setSavingMobile(false);
    }
  };

  const handleMobileVerifyOTP = async (e: FormEvent) => {
    e.preventDefault();
    setSavingMobile(true);
    try {
      const res = await apiRequest<{ token: string; detail: string }>({
        path: "/city-admin/change-mobile/verify/",
        method: "POST",
        body: JSON.stringify({
          new_mobile_number: mobileForm.new_mobile_number,
          otp_code: mobileForm.otp_code,
        }),
      });
      if (res.token) {
        localStorage.setItem("auth_token", res.token);
        setToken(res.token);
      }
      setMobileForm({ current_password: "", new_mobile_number: "", otp_code: "" });
      setMobileStep("request");
      loadProfile();
      showToast("Mobile number updated successfully!", "success");
    } catch {
      showToast("Failed to verify OTP.", "error");
    } finally {
      setSavingMobile(false);
    }
  };

  const handleToggleMosqueStatus = async (mosqueId: number, currentStatus: string) => {
    const nextStatus = currentStatus === "active" ? "inactive" : "active";
    try {
      await apiRequest({
        path: `/city-admin/mosques/${mosqueId}/status/`,
        method: "PATCH",
        body: JSON.stringify({ mosque_status: nextStatus }),
      });
      showToast(`Mosque status changed to ${nextStatus}`, "success");
      loadCityMosques();
    } catch {
      showToast("Failed to update mosque status.", "error");
    }
  };

  const handleSaveAnnouncement = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (editingAnnouncement) {
        await apiRequest({
          path: `/city-admin/announcements/${editingAnnouncement.id}/`,
          method: "PATCH",
          body: JSON.stringify(announcementForm),
        });
        showToast("City notice updated successfully!", "success");
      } else {
        await apiRequest({
          path: `/city-admin/announcements/`,
          method: "POST",
          body: JSON.stringify(announcementForm),
        });
        showToast("City notice created successfully!", "success");
      }
      setIsAnnouncementModalOpen(false);
      loadAnnouncements();
      loadStats();
    } catch {
      showToast("Failed to save city notice. Verify inputs.", "error");
    }
  };

  const handleSaveEvent = async (e: FormEvent) => {
    e.preventDefault();
    try {
      // Ensure backend HH:MM:SS format
      const formattedEventTime = eventForm.event_time.includes(":") && eventForm.event_time.split(":").length === 2
        ? `${eventForm.event_time}:00`
        : eventForm.event_time;
      const formattedEndTime = eventForm.end_time.includes(":") && eventForm.end_time.split(":").length === 2
        ? `${eventForm.end_time}:00`
        : eventForm.end_time;

      const payload = {
        ...eventForm,
        event_time: formattedEventTime,
        end_time: formattedEndTime,
      };

      if (editingEvent) {
        await apiRequest({
          path: `/city-admin/events/${editingEvent.id}/`,
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        showToast("City event updated successfully!", "success");
      } else {
        await apiRequest({
          path: `/city-admin/events/`,
          method: "POST",
          body: JSON.stringify(payload),
        });
        showToast("City event created successfully!", "success");
      }
      setIsEventModalOpen(false);
      loadEvents();
      loadStats();
    } catch {
      showToast("Failed to save event. Verify inputs.", "error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_role");
    router.push("/city-admin/login");
  };

  const filteredAnnouncements = announcements.filter((ann) => {
    const matchesSearch =
      ann.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ann.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === "all" || ann.announcement_type === filterType;
    const matchesPriority = filterPriority === "all" || ann.priority === filterPriority;
    return matchesSearch && matchesType && matchesPriority;
  });

  const filteredEvents = events.filter((evt) => {
    const matchesSearch =
      evt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      evt.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      evt.speaker_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === "all" || evt.event_type === filterType;
    return matchesSearch && matchesType;
  });

  const getEventDate = (evt: Event) => {
    if (!evt.event_date) return new Date(0);
    const timeStr = evt.event_time || "00:00:00";
    return new Date(`${evt.event_date}T${timeStr}`);
  };

  const isEventCompleted = (evt: Event) => {
    if (evt.temporal_status) {
      return evt.temporal_status === "completed";
    }
    if (!evt.event_date) return false;
    const timeStr = evt.end_time || evt.event_time || "23:59:59";
    const evtDate = new Date(`${evt.event_date}T${timeStr}`);
    return evtDate < new Date();
  };

  const upcomingEvents = filteredEvents
    .filter((evt) => !isEventCompleted(evt))
    .sort((a, b) => getEventDate(a).getTime() - getEventDate(b).getTime());

  const completedEvents = filteredEvents
    .filter((evt) => isEventCompleted(evt))
    .sort((a, b) => getEventDate(b).getTime() - getEventDate(a).getTime());

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 flex flex-col font-sans">
      {/* Toast Alert */}
      {toast && (
        <div className={`fixed bottom-5 right-5 z-50 rounded-xl px-4 py-3 shadow-lg flex items-center gap-3 border ${
          toast.type === "success" 
            ? "bg-emerald-50 text-emerald-900 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900"
            : "bg-red-50 text-red-900 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900"
        }`}>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header bar */}
      <header className="bg-white border-b border-slate-200 dark:bg-slate-900 dark:border-slate-800 sticky top-0 z-30">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="bg-indigo-600 text-white rounded-lg p-2 font-bold text-sm tracking-wide">
              CA
            </span>
            <div>
              <h1 className="text-lg font-bold">City Administrator Console</h1>
              <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold uppercase tracking-wider">
                Jurisdiction: {cityName}
              </p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800 transition"
          >
            <LogOut className="h-4 w-4" /> Sign Out
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-slate-200 dark:bg-slate-900 dark:border-slate-800 w-full overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-4 sm:space-x-8 overflow-x-auto no-scrollbar py-1" aria-label="Tabs">
            {[
              { id: "overview", label: "City Overview", icon: Grid },
              { id: "mosques", label: "City Mosques", icon: Building2 },
              { id: "announcements", label: "City Notices", icon: FileText },
              { id: "events", label: "City Events", icon: Calendar },
              ...(hasMosqueAdmin ? [{ id: "my_mosque", label: "My Mosque", icon: Building2 }] : []),
              { id: "account", label: "Account & Security", icon: Shield },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`border-b-2 py-3 sm:py-4 px-1 flex items-center gap-2 text-xs sm:text-sm font-semibold whitespace-nowrap flex-shrink-0 transition ${
                    active 
                      ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-500" 
                      : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300"
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Body */}
      <main className="flex-1 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          
          {/* Tab: My Mosque (Dual Role) */}
          {activeTab === "my_mosque" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-6 dark:border-emerald-900/30 dark:bg-emerald-950/20 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 mb-2">
                      Dual Role Assignment
                    </span>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                      {mosqueName || "Assigned Mosque"} Management
                    </h2>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      You are assigned as Mosque Administrator for this mosque in addition to your City Administrator responsibilities.
                    </p>
                  </div>
                  <button
                    onClick={() => router.push("/dashboard")}
                    className="inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-700 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 dark:bg-emerald-600 dark:hover:bg-emerald-700"
                  >
                    Open Mosque Management Dashboard →
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Tab 1: Overview Dashboard Stats */}
          {activeTab === "overview" && (
            <div className="space-y-8">
              {loadingStats ? (
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="animate-pulse bg-white p-6 rounded-2xl border border-slate-200 h-28 dark:bg-slate-900 dark:border-slate-800"></div>
                  ))}
                </div>
              ) : (
                <>
                  {stats && stats.emergency_alerts > 0 && (
                    <div className="bg-red-50 text-red-900 border border-red-200 rounded-2xl p-4 flex items-center gap-3 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900">
                      <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400 animate-bounce" />
                      <div>
                        <h4 className="font-bold text-sm">Active Urgent City Notices</h4>
                        <p className="text-xs">There are currently {stats.emergency_alerts} active urgent notices for {cityName}.</p>
                      </div>
                    </div>
                  )}

                  <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">City Mosques</p>
                      <h3 className="text-3xl font-bold mt-2 text-slate-900 dark:text-slate-50">{cityMosques.length}</h3>
                      <div className="mt-2 text-xs flex gap-2 text-slate-400">
                        <span className="text-emerald-600 font-semibold">{cityMosques.filter(m => m.mosque_status === 'active').length} Active</span>
                        <span>•</span>
                        <span>{cityMosques.filter(m => m.mosque_status !== 'active').length} Inactive/Archived</span>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">City Notices</p>
                      <h3 className="text-3xl font-bold mt-2 text-slate-900 dark:text-slate-50">{stats?.announcements.total || 0}</h3>
                      <div className="mt-2 text-xs flex gap-2 text-slate-400">
                        <span className="text-emerald-600 font-semibold">{stats?.announcements.published || 0} Published</span>
                        <span>•</span>
                        <span>{stats?.announcements.draft || 0} Drafts</span>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">City Events</p>
                      <h3 className="text-3xl font-bold mt-2 text-slate-900 dark:text-slate-50">{stats?.events.upcoming || 0}</h3>
                      <p className="text-xs text-slate-400 mt-2">Upcoming scheduled programs</p>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">City Visits</p>
                      <h3 className="text-3xl font-bold mt-2 text-indigo-600 dark:text-indigo-400">{cityAnalytics?.total_visits || 0}</h3>
                      <p className="text-xs text-slate-400 mt-2">{cityAnalytics?.unique_identified_visitors || 0} unique visitors</p>
                    </div>
                  </div>

                  {cityAnalytics && (
                    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                        <div>
                          <h3 className="text-base font-bold text-slate-900 dark:text-slate-50 flex items-center gap-2">
                            <Building2 className="h-5 w-5 text-indigo-600" /> Visitor Analytics ({cityName})
                          </h3>
                          <p className="text-xs text-slate-400 mt-0.5">Privacy-conscious visitor metrics for your city.</p>
                        </div>
                        <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 dark:text-indigo-400 px-3 py-1 rounded-full">
                          City Scoped
                        </span>
                      </div>

                      <div className="mt-6 grid gap-5 sm:grid-cols-3">
                        <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                          <p className="text-xs font-semibold text-slate-500">Total City Visits</p>
                          <h4 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{cityAnalytics.total_visits}</h4>
                          <div className="mt-2 text-[11px] text-slate-400 flex justify-between">
                            <span>Today: {cityAnalytics.period_metrics.today}</span>
                            <span>This Week: {cityAnalytics.period_metrics.this_week}</span>
                          </div>
                        </div>

                        <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                          <p className="text-xs font-semibold text-slate-500">Unique Identified Visitors</p>
                          <h4 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{cityAnalytics.unique_identified_visitors}</h4>
                          <p className="mt-2 text-[11px] text-slate-400">Anonymous device session tokens</p>
                        </div>

                        <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                          <p className="text-xs font-semibold text-slate-500">Top Viewed Mosques</p>
                          {cityAnalytics.top_mosques.length === 0 ? (
                            <p className="text-xs text-slate-400 mt-2">No mosque views recorded yet.</p>
                          ) : (
                            <ul className="mt-2 space-y-1 text-xs text-slate-600 dark:text-slate-300">
                              {cityAnalytics.top_mosques.slice(0, 3).map((m) => (
                                <li key={m.mosque_id} className="flex justify-between truncate">
                                  <span className="truncate">{m.mosque_name}</span>
                                  <span className="font-bold text-indigo-600 ml-2">{m.views}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Tab 2: City Mosques Directory */}
          {activeTab === "mosques" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-indigo-600" /> Mosques Directory — {cityName}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Review and manage mosque status across your city jurisdiction.
                  </p>
                </div>
                <button
                  onClick={loadCityMosques}
                  className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                >
                  <RefreshCw className="h-4 w-4" /> Refresh
                </button>
              </div>

              {loadingMosques ? (
                <div className="p-8 text-center text-slate-500">Loading mosques in {cityName}...</div>
              ) : cityMosques.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 dark:bg-slate-900 dark:border-slate-800">
                  No mosques registered in {cityName} yet.
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {cityMosques.map((m) => (
                    <div key={m.id} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h4 className="font-bold text-slate-900 dark:text-slate-50 text-base">{m.mosque_name}</h4>
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                            m.mosque_status === "active"
                              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400"
                              : "bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400"
                          }`}>
                            {m.mosque_status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mb-3">{m.address || "No street address provided"}</p>
                      </div>

                      <div className="border-t pt-3 flex items-center justify-between">
                        <span className="text-xs text-slate-400">ID: #{m.id}</span>
                        <button
                          onClick={() => handleToggleMosqueStatus(m.id, m.mosque_status)}
                          className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
                            m.mosque_status === "active"
                              ? "border border-red-200 text-red-700 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-950/30"
                              : "bg-emerald-600 text-white hover:bg-emerald-500"
                          }`}
                        >
                          {m.mosque_status === "active" ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 3: City Notices */}
          {activeTab === "announcements" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex flex-1 max-w-md items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 dark:bg-slate-900 dark:border-slate-700">
                  <Search className="h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search city notices..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full border-0 bg-transparent p-0 text-sm focus:ring-0 outline-none"
                  />
                </div>

                <button
                  onClick={() => {
                    setEditingAnnouncement(null);
                    setAnnouncementForm({
                      title: "",
                      short_summary: "",
                      content: "",
                      priority: "normal",
                      announcement_type: "general",
                      status: "published",
                      start_date: new Date().toISOString().split("T")[0],
                      end_date: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().split("T")[0],
                    });
                    setIsAnnouncementModalOpen(true);
                  }}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-500 transition"
                >
                  <Plus className="h-4 w-4" /> Create City Notice
                </button>
              </div>

              {loadingAnnouncements ? (
                <div className="space-y-4">
                  {[1, 2].map((i) => (
                    <div key={i} className="animate-pulse bg-white p-6 rounded-2xl border border-slate-200 h-24 dark:bg-slate-900 dark:border-slate-800"></div>
                  ))}
                </div>
              ) : filteredAnnouncements.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 dark:bg-slate-900 dark:border-slate-800">
                  No city notices published yet. Click &quot;Create City Notice&quot; to publish announcements for {cityName}.
                </div>
              ) : (
                <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden dark:bg-slate-900 dark:border-slate-800 shadow-soft">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Notice Title</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Importance</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {filteredAnnouncements.map((ann) => (
                        <tr key={ann.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                          <td className="px-6 py-4">
                            <div className="font-semibold text-slate-900 dark:text-slate-50">{ann.title}</div>
                            <div className="text-xs text-slate-500 line-clamp-1">{ann.short_summary || ann.content}</div>
                          </td>
                          <td className="px-6 py-4 text-sm capitalize">{ann.announcement_type}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                              ann.priority === "urgent"
                                ? "bg-red-50 text-red-800 ring-1 ring-inset ring-red-600/10"
                                : ann.priority === "important"
                                ? "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-600/10"
                                : "bg-slate-100 text-slate-800"
                            }`}>
                              {ann.priority === "urgent" ? "Urgent" : ann.priority === "important" ? "Important" : "Normal"}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm capitalize">{ann.status}</td>
                          <td className="px-6 py-4 text-right flex justify-end gap-2">
                            <button
                              onClick={() => {
                                setEditingAnnouncement(ann);
                                setAnnouncementForm({
                                  title: ann.title,
                                  short_summary: ann.short_summary,
                                  content: ann.content,
                                  priority: ann.priority,
                                  announcement_type: ann.announcement_type,
                                  status: ann.status,
                                  start_date: ann.start_date,
                                  end_date: ann.end_date,
                                });
                                setIsAnnouncementModalOpen(true);
                              }}
                              className="p-1 text-slate-500 hover:text-slate-900"
                              title="Edit"
                            >
                              <Edit3 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Tab 4: City Events */}
          {activeTab === "events" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">City Events & Programs</h3>
                  <p className="text-xs text-slate-500">Public events scheduled across {cityName}.</p>
                </div>
                <button
                  onClick={() => {
                    setEditingEvent(null);
                    setEventForm({
                      title: "",
                      description: "",
                      event_type: "lecture",
                      event_date: new Date().toISOString().split("T")[0],
                      event_time: "18:00",
                      end_time: "19:30",
                      event_location: "",
                      speaker_name: "",
                      registration_required: false,
                      max_capacity: 100,
                      organizer: "",
                      status: "published",
                    });
                    setIsEventModalOpen(true);
                  }}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-500 transition"
                >
                  <Plus className="h-4 w-4" /> Create City Event
                </button>
              </div>

              {loadingEvents ? (
                <div className="p-8 text-center text-slate-500">Loading city events...</div>
              ) : (
                <div className="space-y-10">
                  {/* Section 1: UPCOMING EVENTS */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                        <h4 className="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                          Upcoming Events ({upcomingEvents.length})
                        </h4>
                      </div>
                      <span className="text-xs text-slate-500">Sorted nearest upcoming first</span>
                    </div>

                    {upcomingEvents.length === 0 ? (
                      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 dark:bg-slate-900 dark:border-slate-800">
                        No upcoming events scheduled. Click &quot;Create City Event&quot; to publish a new event.
                      </div>
                    ) : (
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {upcomingEvents.map((evt) => (
                          <div key={evt.id} className="bg-white rounded-2xl border border-emerald-200/80 p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800 flex flex-col justify-between">
                            <div>
                              <div className="flex justify-between items-start mb-2 gap-2">
                                <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-800 uppercase tracking-wider">
                                  {evt.event_type}
                                </span>
                                <div className="flex items-center gap-1.5 flex-wrap justify-end">
                                  <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                                    Upcoming
                                  </span>
                                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 uppercase tracking-wider">
                                    {evt.status}
                                  </span>
                                </div>
                              </div>
                              <h4 className="font-bold text-slate-900 dark:text-slate-50 text-base mb-1">{evt.title}</h4>
                              {evt.description && <p className="text-xs text-slate-500 line-clamp-2 mb-3">{evt.description}</p>}
                            </div>
                            <div className="border-t border-slate-100 pt-3 space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                              <div><span className="font-semibold text-slate-700 dark:text-slate-300">Date:</span> {evt.event_date}</div>
                              <div><span className="font-semibold text-slate-700 dark:text-slate-300">Time:</span> {formatTimeTo12Hour(evt.event_time)}{evt.end_time ? ` - ${formatTimeTo12Hour(evt.end_time)}` : ""}</div>
                              {evt.speaker_name && <div><span className="font-semibold text-slate-700 dark:text-slate-300">Speaker:</span> {evt.speaker_name}</div>}
                              {evt.event_location && <div><span className="font-semibold text-slate-700 dark:text-slate-300">Venue:</span> {evt.event_location}</div>}
                              
                              <div className="border-t border-slate-100 pt-2 mt-2 space-y-0.5 text-[11px]">
                                <div>
                                  <span className="text-slate-400">Organized by:</span>{" "}
                                  <span className="font-medium text-slate-700 dark:text-slate-300">{evt.organizer_name || `${cityName} City Administration`}</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">Posted by:</span>{" "}
                                  <span className="font-medium text-slate-700 dark:text-slate-300">
                                    {evt.published_by?.name || "City Administrator"} · City Administrator, {evt.published_by?.city || cityName}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Section 2: COMPLETED EVENTS */}
                  <div className="space-y-4 pt-4 border-t border-slate-200/60 dark:border-slate-800">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-slate-400"></span>
                        <h4 className="text-base font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                          Completed Events ({completedEvents.length})
                        </h4>
                      </div>
                      <span className="text-xs text-slate-400">Sorted most-recent completed first</span>
                    </div>

                    {completedEvents.length === 0 ? (
                      <div className="bg-slate-50/50 rounded-2xl border border-slate-200 p-8 text-center text-slate-400 dark:bg-slate-900/50 dark:border-slate-800 text-xs">
                        No completed events yet.
                      </div>
                    ) : (
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {completedEvents.map((evt) => (
                          <div key={evt.id} className="bg-slate-50/60 rounded-2xl border border-slate-200/80 p-5 dark:bg-slate-900/40 dark:border-slate-800 flex flex-col justify-between opacity-85 hover:opacity-100 transition">
                            <div>
                              <div className="flex justify-between items-start mb-2 gap-2">
                                <span className="inline-flex items-center rounded-full bg-slate-200/70 px-2.5 py-0.5 text-xs font-semibold text-slate-700 uppercase tracking-wider">
                                  {evt.event_type}
                                </span>
                                <div className="flex items-center gap-1.5 flex-wrap justify-end">
                                  <span className="inline-flex items-center rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-700 uppercase tracking-wider">
                                    Completed
                                  </span>
                                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                                    {evt.status}
                                  </span>
                                </div>
                              </div>
                              <h4 className="font-bold text-slate-800 dark:text-slate-200 text-base mb-1">{evt.title}</h4>
                              {evt.description && <p className="text-xs text-slate-500 line-clamp-2 mb-3">{evt.description}</p>}
                            </div>
                            <div className="border-t border-slate-200/60 pt-3 space-y-1.5 text-xs text-slate-500 dark:text-slate-400">
                              <div><span className="font-semibold text-slate-600 dark:text-slate-400">Date:</span> {evt.event_date}</div>
                              <div><span className="font-semibold text-slate-600 dark:text-slate-400">Time:</span> {formatTimeTo12Hour(evt.event_time)}{evt.end_time ? ` - ${formatTimeTo12Hour(evt.end_time)}` : ""}</div>
                              {evt.speaker_name && <div><span className="font-semibold text-slate-600 dark:text-slate-400">Speaker:</span> {evt.speaker_name}</div>}
                              {evt.event_location && <div><span className="font-semibold text-slate-600 dark:text-slate-400">Venue:</span> {evt.event_location}</div>}
                              
                              <div className="border-t border-slate-200/60 pt-2 mt-2 space-y-0.5 text-[11px]">
                                <div>
                                  <span className="text-slate-400">Organized by:</span>{" "}
                                  <span className="font-medium text-slate-600 dark:text-slate-400">{evt.organizer_name || `${cityName} City Administration`}</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">Posted by:</span>{" "}
                                  <span className="font-medium text-slate-600 dark:text-slate-400">
                                    {evt.published_by?.name || "City Administrator"} · City Administrator, {evt.published_by?.city || cityName}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 5: Account & Security */}
          {activeTab === "account" && (
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Profile Details Card */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                <div className="flex items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <User className="h-6 w-6 text-indigo-600" />
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Personal Profile</h3>
                    <p className="text-xs text-slate-500">Manage your administrator contact details.</p>
                  </div>
                </div>

                <form onSubmit={handleUpdateProfile} className="mt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold mb-1">First Name</label>
                      <input
                        type="text"
                        required
                        value={profileForm.first_name}
                        onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold mb-1">Last Name</label>
                      <input
                        type="text"
                        required
                        value={profileForm.last_name}
                        onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={savingProfile}
                      className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
                    >
                      {savingProfile ? "Saving..." : "Save Profile Details"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Password Change Card */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                <div className="flex items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <KeyRound className="h-6 w-6 text-indigo-600" />
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Change Password</h3>
                    <p className="text-xs text-slate-500">Update your account password securely.</p>
                  </div>
                </div>

                <form onSubmit={handleChangePassword} className="mt-6 space-y-4">
                  <div>
                    <label className="block text-xs font-semibold mb-1">Current Password</label>
                    <input
                      type="password"
                      required
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold mb-1">New Password</label>
                      <input
                        type="password"
                        required
                        minLength={8}
                        value={passwordForm.new_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold mb-1">Confirm New Password</label>
                      <input
                        type="password"
                        required
                        minLength={8}
                        value={passwordForm.confirm_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:bg-slate-800 dark:border-slate-700"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={savingPassword}
                      className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
                    >
                      {savingPassword ? "Updating..." : "Update Password"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Mobile Number & Account Security Policy Banner */}
              <div className="bg-amber-50 rounded-2xl border border-amber-200 p-6 text-amber-900 dark:bg-amber-950/30 dark:border-amber-900 dark:text-amber-300">
                <div className="flex items-start gap-3">
                  <Lock className="h-6 w-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-sm">Registered Mobile Number & Security Policy</h4>
                    <p className="text-xs mt-1 leading-relaxed">
                      Your registered mobile number <strong>({profile?.mobile_number || "Verified"})</strong> is your primary security credential. If you ever lose access to this mobile line, self-service phone change is disabled to protect your city console from account takeover. Contact MosqueCom Super Admin for manual identity verification.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

      {/* Modal: Notice Form */}
      {isAnnouncementModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-bold mb-1">{editingAnnouncement ? "Edit City Notice" : "Create City Notice"}</h3>
            <p className="text-xs text-slate-500 mb-4">Publish a community notice or public announcement relevant to {cityName}.</p>

            <form onSubmit={handleSaveAnnouncement} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Eid Prayer Announcement"
                  value={announcementForm.title}
                  onChange={(e) => setAnnouncementForm({...announcementForm, title: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Give your notice a short, clear title.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Short Description</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Eid prayer will be held at Eidgah Ground at 8:00 AM."
                  value={announcementForm.short_summary}
                  onChange={(e) => setAnnouncementForm({...announcementForm, short_summary: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Write a short summary that people can understand quickly.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Notice Details</label>
                <textarea
                  required
                  rows={4}
                  placeholder={`Example:
Eid-ul-Adha prayer will be held at Eidgah Ground on Monday, 9 June at 8:00 AM.

Please arrive 20 minutes early and bring your prayer mat.`}
                  value={announcementForm.content}
                  onChange={(e) => setAnnouncementForm({...announcementForm, content: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Write the complete information you want people in your city to know.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold mb-1">Category</label>
                  <select
                    value={announcementForm.announcement_type}
                    onChange={(e) => setAnnouncementForm({...announcementForm, announcement_type: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  >
                    <option value="general">General</option>
                    <option value="emergency">Emergency</option>
                    <option value="prayer">Prayer Update</option>
                    <option value="ramadan">Ramadan</option>
                    <option value="eid">Eid</option>
                    <option value="community">Community</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Importance</label>
                  <select
                    value={announcementForm.priority}
                    onChange={(e) => setAnnouncementForm({...announcementForm, priority: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  >
                    <option value="normal">Normal</option>
                    <option value="important">Important</option>
                    <option value="urgent">Urgent</option>
                  </select>
                  <p className="text-[11px] text-slate-400 mt-1">Use Urgent only when immediate attention is required.</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={announcementForm.start_date}
                    onChange={(e) => setAnnouncementForm({...announcementForm, start_date: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Expiry Date</label>
                  <input
                    type="date"
                    required
                    value={announcementForm.end_date}
                    onChange={(e) => setAnnouncementForm({...announcementForm, end_date: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Status</label>
                <select
                  value={announcementForm.status}
                  onChange={(e) => setAnnouncementForm({...announcementForm, status: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                >
                  <option value="published">Published (Public)</option>
                  <option value="draft">Draft (Private)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setIsAnnouncementModalOpen(false)}
                  className="rounded-lg border px-4 py-2 text-sm font-semibold hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-500 transition"
                >
                  {announcementForm.status === "published" ? "Publish Notice" : "Save Notice"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Event Form */}
      {isEventModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-bold mb-1">{editingEvent ? "Edit City Event" : "Create City Event"}</h3>
            <p className="text-xs text-slate-500 mb-4">Schedule a public community event or lecture in {cityName}.</p>

            <form onSubmit={handleSaveEvent} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Event Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Annual Seerah Conference"
                  value={eventForm.title}
                  onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Description</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Write event details, agenda, and guidelines for attendees..."
                  value={eventForm.description}
                  onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold mb-1">Speaker Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Maulana Abdul Rahman"
                    value={eventForm.speaker_name}
                    onChange={(e) => setEventForm({...eventForm, speaker_name: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Organizer</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Nanded Islamic Council"
                    value={eventForm.organizer}
                    onChange={(e) => setEventForm({...eventForm, organizer: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Event Date</label>
                  <input
                    type="date"
                    required
                    value={eventForm.event_date}
                    onChange={(e) => setEventForm({...eventForm, event_date: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Start Time</label>
                  <input
                    type="time"
                    required
                    value={eventForm.event_time}
                    onChange={(e) => setEventForm({...eventForm, event_time: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                  <p className="text-[10px] text-slate-400 mt-0.5">{formatTimeTo12Hour(eventForm.event_time)}</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">End Time</label>
                  <input
                    type="time"
                    required
                    value={eventForm.end_time}
                    onChange={(e) => setEventForm({...eventForm, end_time: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                  />
                  <p className="text-[10px] text-slate-400 mt-0.5">{formatTimeTo12Hour(eventForm.end_time)}</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Venue Location</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Eidgah Ground / Central Community Hall"
                  value={eventForm.event_location}
                  onChange={(e) => setEventForm({...eventForm, event_location: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3 text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setIsEventModalOpen(false)}
                  className="rounded-lg border px-4 py-2 text-sm font-semibold hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-500 transition"
                >
                  Save Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
