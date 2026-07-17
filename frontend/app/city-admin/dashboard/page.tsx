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
  Send 
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
};

export default function CityAdminDashboard() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [cityName, setCityName] = useState<string>("");
  const [cityId, setCityId] = useState<string>("");

  const [activeTab, setActiveTab] = useState<"overview" | "announcements" | "events" | "notifications">("overview");

  // Loading States
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);

  // Stats Data
  const [stats, setStats] = useState<Stats | null>(null);

  // List Data
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [events, setEvents] = useState<Event[]>([]);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");

  // Selected Items for Bulk Actions
  const [selectedAnnouncements, setSelectedAnnouncements] = useState<number[]>([]);

  // Modal States
  const [isAnnouncementModalOpen, setIsAnnouncementModalOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null);
  const [announcementForm, setAnnouncementForm] = useState({
    title: "",
    short_summary: "",
    content: "",
    priority: "normal",
    announcement_type: "general",
    status: "draft",
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
    event_time: "18:00:00",
    end_time: "19:30:00",
    event_location: "",
    speaker_name: "",
    registration_required: false,
    max_capacity: 100,
    organizer: "",
    status: "published",
  });

  // Calendar/List View Toggle for Events
  const [eventsViewMode, setEventsViewMode] = useState<"list" | "calendar">("list");

  // Custom Notification Dispatch Form
  const [notifChannel, setNotifChannel] = useState("whatsapp");
  const [notifRecipient, setNotifRecipient] = useState("");
  const [notifMessage, setNotifMessage] = useState("");
  const [sendingNotif, setSendingNotif] = useState(false);

  // Toast notifications
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Auth Validation
  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const role = localStorage.getItem("user_role");
    const city = localStorage.getItem("city_admin_city_name");
    const cId = localStorage.getItem("city_admin_city_id");

    if (!savedToken || role !== "city_admin") {
      router.push("/city-admin/login");
      return;
    }

    setToken(savedToken);
    setCityName(city || "Assigned City");
    setCityId(cId || "");
  }, [router]);

  // Load Dashboard Stats
  const loadStats = async () => {
    try {
      setLoadingStats(true);
      const data = await apiRequest<Stats>({ path: "/city-admin/stats/" });
      setStats(data);
    } catch (err) {
      showToast("Failed to load dashboard statistics.", "error");
    } finally {
      setLoadingStats(false);
    }
  };

  // Load Announcements
  const loadAnnouncements = async () => {
    try {
      setLoadingAnnouncements(true);
      const data = await apiRequest<any>({ path: `/city-admin/announcements/` });
      setAnnouncements(data.results || data);
    } catch (err) {
      showToast("Failed to load announcements list.", "error");
    } finally {
      setLoadingAnnouncements(false);
    }
  };

  // Load Events
  const loadEvents = async () => {
    try {
      setLoadingEvents(true);
      const data = await apiRequest<any>({ path: `/city-admin/events/` });
      setEvents(data.results || data);
    } catch (err) {
      showToast("Failed to load events list.", "error");
    } finally {
      setLoadingEvents(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    loadStats();
    loadAnnouncements();
    loadEvents();
  }, [token]);

  // Bulk Actions
  const handleBulkAction = async (action: "publish" | "archive" | "delete") => {
    if (selectedAnnouncements.length === 0) return;
    if (!confirm(`Are you sure you want to ${action} selected items?`)) return;

    try {
      for (const id of selectedAnnouncements) {
        if (action === "delete") {
          await apiRequest({ path: `/city-admin/announcements/${id}/`, method: "DELETE" });
        } else {
          const ann = announcements.find((a) => a.id === id);
          if (ann) {
            await apiRequest({
              path: `/city-admin/announcements/${id}/`,
              method: "PUT",
              body: JSON.stringify({
                ...ann,
                status: action === "publish" ? "published" : "archived",
              }),
            });
          }
        }
      }
      showToast(`Bulk ${action} action executed successfully.`, "success");
      setSelectedAnnouncements([]);
      loadAnnouncements();
      loadStats();
    } catch {
      showToast("Failed to complete bulk operations.", "error");
    }
  };

  // Create or Update Announcement
  const handleSaveAnnouncement = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...announcementForm,
        city: parseInt(cityId),
        is_active: true,
      };

      if (editingAnnouncement) {
        await apiRequest({
          path: `/city-admin/announcements/${editingAnnouncement.id}/`,
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showToast("Announcement updated successfully!", "success");
      } else {
        await apiRequest({
          path: `/city-admin/announcements/`,
          method: "POST",
          body: JSON.stringify(payload),
        });
        showToast("Announcement published/created successfully!", "success");
      }

      setIsAnnouncementModalOpen(false);
      setEditingAnnouncement(null);
      loadAnnouncements();
      loadStats();
    } catch {
      showToast("Failed to save announcement. Verify inputs.", "error");
    }
  };

  // Duplicate Announcement
  const handleDuplicateAnnouncement = (ann: Announcement) => {
    setEditingAnnouncement(null);
    setAnnouncementForm({
      title: `${ann.title} (Copy)`,
      short_summary: ann.short_summary,
      content: ann.content,
      priority: ann.priority,
      announcement_type: ann.announcement_type,
      status: "draft",
      start_date: new Date().toISOString().split("T")[0],
      end_date: ann.end_date,
    });
    setIsAnnouncementModalOpen(true);
  };

  // Archive or Restore Announcement
  const handleToggleArchiveAnn = async (ann: Announcement) => {
    try {
      const nextStatus = ann.status === "archived" ? "published" : "archived";
      await apiRequest({
        path: `/city-admin/announcements/${ann.id}/`,
        method: "PUT",
        body: JSON.stringify({
          ...ann,
          status: nextStatus,
        }),
      });
      showToast(
        nextStatus === "archived" ? "Announcement archived." : "Announcement restored.",
        "success"
      );
      loadAnnouncements();
      loadStats();
    } catch {
      showToast("Failed to change announcement archive state.", "error");
    }
  };

  // Create or Update Event
  const handleSaveEvent = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...eventForm,
        city: parseInt(cityId),
      };

      if (editingEvent) {
        await apiRequest({
          path: `/city-admin/events/${editingEvent.id}/`,
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showToast("Event details updated successfully!", "success");
      } else {
        await apiRequest({
          path: `/city-admin/events/`,
          method: "POST",
          body: JSON.stringify(payload),
        });
        showToast("New event published/created successfully!", "success");
      }

      setIsEventModalOpen(false);
      setEditingEvent(null);
      loadEvents();
      loadStats();
    } catch {
      showToast("Failed to save event. Verify inputs.", "error");
    }
  };

  const handleDuplicateEvent = (event: Event) => {
    setEditingEvent(null);
    setEventForm({
      title: `${event.title} (Copy)`,
      description: event.description,
      event_type: event.event_type,
      event_date: event.event_date,
      event_time: event.event_time,
      end_time: event.end_time,
      event_location: event.event_location,
      speaker_name: event.speaker_name,
      registration_required: event.registration_required,
      max_capacity: event.max_capacity,
      organizer: event.organizer,
      status: "draft",
    });
    setIsEventModalOpen(true);
  };

  const handleToggleArchiveEvent = async (event: Event) => {
    try {
      const nextStatus = event.status === "archived" ? "published" : "archived";
      await apiRequest({
        path: `/city-admin/events/${event.id}/`,
        method: "PUT",
        body: JSON.stringify({
          ...event,
          status: nextStatus,
        }),
      });
      showToast(
        nextStatus === "archived" ? "Event archived." : "Event restored.",
        "success"
      );
      loadEvents();
      loadStats();
    } catch {
      showToast("Failed to change event archive state.", "error");
    }
  };

  // Send Direct Alert Notification
  const handleSendNotification = async (e: FormEvent) => {
    e.preventDefault();
    setSendingNotif(true);
    try {
      await apiRequest({
        path: "/city-admin/notifications/send/",
        method: "POST",
        body: JSON.stringify({
          channel: notifChannel,
          recipient: notifRecipient,
          message: notifMessage,
        }),
      });
      showToast("Notification dispatched successfully!", "success");
      setNotifMessage("");
      setNotifRecipient("");
    } catch {
      showToast("Failed to dispatch notification.", "error");
    } finally {
      setSendingNotif(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_role");
    router.push("/city-admin/login");
  };

  // Filter lists based on search parameters
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
            <span className="bg-emerald-600 text-white rounded-lg p-2 font-bold text-sm tracking-wide">
              MF
            </span>
            <div>
              <h1 className="text-lg font-bold">City Admin Console</h1>
              <p className="text-xs text-slate-500 font-medium">Managing: {cityName}</p>
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
      <div className="bg-white border-b border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {[
              { id: "overview", label: "Overview", icon: Grid },
              { id: "announcements", label: "Notice Board", icon: FileText },
              { id: "events", label: "Events", icon: Calendar },
              { id: "notifications", label: "Notifications", icon: Bell },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`border-b-2 py-4 px-1 flex items-center gap-2 text-sm font-semibold transition ${
                    active 
                      ? "border-emerald-600 text-emerald-600 dark:text-emerald-400 dark:border-emerald-500" 
                      : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Body */}
      <main className="flex-1 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          
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
                  {/* Alert panel for Emergency alerts */}
                  {stats && stats.emergency_alerts > 0 && (
                    <div className="bg-red-50 text-red-900 border border-red-200 rounded-2xl p-4 flex items-center gap-3 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900">
                      <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400 animate-bounce" />
                      <div>
                        <h4 className="font-bold text-sm">Critical: Active Emergency Alerts</h4>
                        <p className="text-xs">There are currently {stats.emergency_alerts} active emergency alerts published for {cityName}.</p>
                      </div>
                    </div>
                  )}

                  <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Announcements</p>
                      <h3 className="text-3xl font-bold mt-2 text-slate-900 dark:text-slate-50">{stats?.announcements.total || 0}</h3>
                      <div className="mt-2 text-xs flex gap-2 text-slate-400">
                        <span className="text-emerald-600 font-semibold">{stats?.announcements.published || 0} Active</span>
                        <span>•</span>
                        <span>{stats?.announcements.draft || 0} Drafts</span>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Upcoming Events</p>
                      <h3 className="text-3xl font-bold mt-2 text-slate-900 dark:text-slate-50">{stats?.events.upcoming || 0}</h3>
                      <div className="mt-2 text-xs flex gap-2 text-slate-400">
                        <span className="text-emerald-600 font-semibold">{stats?.events.ongoing || 0} Today</span>
                        <span>•</span>
                        <span>{stats?.events.completed || 0} Past</span>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Emergency Alerts</p>
                      <h3 className="text-3xl font-bold mt-2 text-red-600 dark:text-red-400">{stats?.emergency_alerts || 0}</h3>
                      <p className="text-xs text-slate-400 mt-2">Active broadcast system</p>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Notification Dispatch Status</p>
                      <h3 className="text-3xl font-bold mt-2 text-emerald-600 dark:text-emerald-400">Online</h3>
                      <p className="text-xs text-slate-400 mt-2">Dummy dispatch provider active</p>
                    </div>
                  </div>

                  {/* Recent Activity Feed */}
                  <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-soft dark:bg-slate-900 dark:border-slate-800">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50 mb-4">Recent Console Activity</h3>
                    {stats?.recent_activity.length === 0 ? (
                      <p className="text-sm text-slate-500">No actions recorded recently in this city.</p>
                    ) : (
                      <div className="flow-root">
                        <ul className="-mb-8">
                          {stats?.recent_activity.map((activity, idx) => (
                            <li key={activity.id}>
                              <div className="relative pb-8">
                                {idx !== stats.recent_activity.length - 1 && (
                                  <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200 dark:bg-slate-800" aria-hidden="true" />
                                )}
                                <div className="relative flex space-x-3">
                                  <div>
                                    <span className="h-8 w-8 rounded-full bg-emerald-50 dark:bg-emerald-950/30 flex items-center justify-center ring-8 ring-white dark:ring-slate-900 text-emerald-600">
                                      <CheckCircle className="h-4 w-4" />
                                    </span>
                                  </div>
                                  <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                                    <div>
                                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                                        {activity.action}: <span className="font-normal text-slate-600 dark:text-slate-400">{activity.description}</span>
                                      </p>
                                    </div>
                                    <div className="text-right text-xs whitespace-nowrap text-slate-400 font-medium">
                                      {activity.time}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Tab 2: Announcement Management */}
          {activeTab === "announcements" && (
            <div className="space-y-6">
              {/* Toolbar */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex flex-1 max-w-md items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 dark:bg-slate-900 dark:border-slate-700">
                  <Search className="h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search announcements..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full border-0 bg-transparent p-0 text-sm focus:ring-0 outline-none"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="rounded-lg border-slate-300 text-sm bg-white dark:bg-slate-900 dark:border-slate-700 py-2 px-3 focus:ring-emerald-500"
                  >
                    <option value="all">All Categories</option>
                    <option value="general">General</option>
                    <option value="emergency">Emergency</option>
                    <option value="prayer">Prayer Update</option>
                    <option value="ramadan">Ramadan</option>
                    <option value="eid">Eid</option>
                  </select>

                  <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="rounded-lg border-slate-300 text-sm bg-white dark:bg-slate-900 dark:border-slate-700 py-2 px-3 focus:ring-emerald-500"
                  >
                    <option value="all">All Priorities</option>
                    <option value="normal">Normal</option>
                    <option value="important">Important</option>
                    <option value="urgent">Urgent</option>
                  </select>

                  <button
                    onClick={() => {
                      setEditingAnnouncement(null);
                      setAnnouncementForm({
                        title: "",
                        short_summary: "",
                        content: "",
                        priority: "normal",
                        announcement_type: "general",
                        status: "draft",
                        start_date: new Date().toISOString().split("T")[0],
                        end_date: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().split("T")[0],
                      });
                      setIsAnnouncementModalOpen(true);
                    }}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-500 transition"
                  >
                    <Plus className="h-4 w-4" /> Create Announcement
                  </button>
                </div>
              </div>

              {/* Bulk operations panel */}
              {selectedAnnouncements.length > 0 && (
                <div className="bg-slate-100 dark:bg-slate-900 rounded-xl p-3 flex items-center justify-between border border-slate-200 dark:border-slate-800">
                  <span className="text-sm font-semibold">{selectedAnnouncements.length} items selected</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleBulkAction("publish")}
                      className="text-xs bg-white border px-3 py-1.5 rounded-lg font-semibold hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 transition"
                    >
                      Publish
                    </button>
                    <button
                      onClick={() => handleBulkAction("archive")}
                      className="text-xs bg-white border px-3 py-1.5 rounded-lg font-semibold hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 transition"
                    >
                      Archive
                    </button>
                    <button
                      onClick={() => handleBulkAction("delete")}
                      className="text-xs bg-red-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-red-500 transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}

              {/* Table / Grid list */}
              {loadingAnnouncements ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse bg-white p-6 rounded-2xl border border-slate-200 h-24 dark:bg-slate-900 dark:border-slate-800"></div>
                  ))}
                </div>
              ) : filteredAnnouncements.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 dark:bg-slate-900 dark:border-slate-800">
                  No announcements found matching search criteria.
                </div>
              ) : (
                <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden dark:bg-slate-900 dark:border-slate-800 shadow-soft">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                      <tr>
                        <th className="px-6 py-3 text-left">
                          <input
                            type="checkbox"
                            checked={selectedAnnouncements.length === filteredAnnouncements.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedAnnouncements(filteredAnnouncements.map((a) => a.id));
                              } else {
                                setSelectedAnnouncements([]);
                              }
                            }}
                            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Title</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Priority</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {filteredAnnouncements.map((ann) => (
                        <tr key={ann.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                          <td className="px-6 py-4">
                            <input
                              type="checkbox"
                              checked={selectedAnnouncements.includes(ann.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedAnnouncements((prev) => [...prev, ann.id]);
                                } else {
                                  setSelectedAnnouncements((prev) => prev.filter((id) => id !== ann.id));
                                }
                              }}
                              className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                            />
                          </td>
                          <td className="px-6 py-4">
                            <div className="font-semibold text-slate-900 dark:text-slate-50">{ann.title}</div>
                            <div className="text-xs text-slate-500 line-clamp-1">{ann.short_summary || ann.content}</div>
                          </td>
                          <td className="px-6 py-4 text-sm capitalize">{ann.announcement_type}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium uppercase tracking-wider ${
                              ann.priority === "urgent"
                                ? "bg-red-50 text-red-800 ring-1 ring-inset ring-red-600/10"
                                : ann.priority === "important"
                                ? "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-600/10"
                                : "bg-slate-100 text-slate-800"
                            }`}>
                              {ann.priority}
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
                            <button
                              onClick={() => handleDuplicateAnnouncement(ann)}
                              className="p-1 text-slate-500 hover:text-slate-900"
                              title="Duplicate"
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleToggleArchiveAnn(ann)}
                              className="p-1 text-slate-500 hover:text-slate-900"
                              title={ann.status === "archived" ? "Restore" : "Archive"}
                            >
                              <Archive className="h-4 w-4" />
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

          {/* Tab 3: Event Management */}
          {activeTab === "events" && (
            <div className="space-y-6">
              {/* Event view filters & toggles */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex border rounded-lg overflow-hidden border-slate-300 dark:border-slate-700 bg-white">
                    <button
                      onClick={() => setEventsViewMode("list")}
                      className={`p-2 transition ${eventsViewMode === "list" ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30" : "hover:bg-slate-50"}`}
                      title="List View"
                    >
                      <List className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setEventsViewMode("calendar")}
                      className={`p-2 transition ${eventsViewMode === "calendar" ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30" : "hover:bg-slate-50"}`}
                      title="Calendar Grid View"
                    >
                      <Grid className="h-4 w-4" />
                    </button>
                  </div>

                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="rounded-lg border-slate-300 text-sm bg-white dark:bg-slate-900 dark:border-slate-700 py-2 px-3 focus:ring-emerald-500"
                  >
                    <option value="all">All Types</option>
                    <option value="lecture">Lectures</option>
                    <option value="program">Programs</option>
                    <option value="class">Islamic Classes</option>
                    <option value="youth">Youth Activities</option>
                  </select>
                </div>

                <button
                  onClick={() => {
                    setEditingEvent(null);
                    setEventForm({
                      title: "",
                      description: "",
                      event_type: "lecture",
                      event_date: new Date().toISOString().split("T")[0],
                      event_time: "18:00:00",
                      end_time: "19:30:00",
                      event_location: "",
                      speaker_name: "",
                      registration_required: false,
                      max_capacity: 100,
                      organizer: "",
                      status: "published",
                    });
                    setIsEventModalOpen(true);
                  }}
                  className="flex items-center gap-2 rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-500 transition"
                >
                  <Plus className="h-4 w-4" /> Create Event
                </button>
              </div>

              {/* View Render */}
              {loadingEvents ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse bg-white p-6 rounded-2xl border border-slate-200 h-24 dark:bg-slate-900 dark:border-slate-800"></div>
                  ))}
                </div>
              ) : eventsViewMode === "list" ? (
                /* List View */
                filteredEvents.length === 0 ? (
                  <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 dark:bg-slate-900 dark:border-slate-800">
                    No upcoming events scheduled.
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {filteredEvents.map((evt) => (
                      <div
                        key={evt.id}
                        className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft hover:shadow-md transition relative flex flex-col dark:bg-slate-900 dark:border-slate-800"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-inset ring-emerald-600/10 uppercase tracking-wider">
                            {evt.event_type}
                          </span>
                          <span className="text-xs font-semibold uppercase text-slate-500">{evt.status}</span>
                        </div>
                        <h4 className="font-bold text-slate-900 dark:text-slate-50 text-base mb-1">{evt.title}</h4>
                        <p className="text-xs text-slate-500 line-clamp-2 mb-4">{evt.description}</p>
                        
                        <div className="mt-auto space-y-1 text-xs text-slate-600 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-3">
                          <div><span className="font-semibold text-slate-800 dark:text-slate-300">Speaker:</span> {evt.speaker_name}</div>
                          <div><span className="font-semibold text-slate-800 dark:text-slate-300">Date:</span> {evt.event_date}</div>
                          <div><span className="font-semibold text-slate-800 dark:text-slate-300">Time:</span> {evt.event_time} - {evt.end_time}</div>
                          {evt.event_location && <div><span className="font-semibold text-slate-800 dark:text-slate-300">Location:</span> {evt.event_location}</div>}
                        </div>

                        <div className="flex justify-end gap-2 border-t border-slate-100 dark:border-slate-800 pt-3 mt-4">
                          <button
                            onClick={() => {
                              setEditingEvent(evt);
                              setEventForm({
                                title: evt.title,
                                description: evt.description,
                                event_type: evt.event_type,
                                event_date: evt.event_date,
                                event_time: evt.event_time,
                                end_time: evt.end_time,
                                event_location: evt.event_location,
                                speaker_name: evt.speaker_name,
                                registration_required: evt.registration_required,
                                max_capacity: evt.max_capacity,
                                organizer: evt.organizer,
                                status: evt.status,
                              });
                              setIsEventModalOpen(true);
                            }}
                            className="p-1.5 text-slate-500 hover:text-slate-900"
                            title="Edit"
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDuplicateEvent(evt)}
                            className="p-1.5 text-slate-500 hover:text-slate-900"
                            title="Duplicate"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleToggleArchiveEvent(evt)}
                            className="p-1.5 text-slate-500 hover:text-slate-900"
                            title={evt.status === "archived" ? "Restore" : "Archive"}
                          >
                            <Archive className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                /* Calendar Grid Mock layout for dashboard consistency */
                <div className="bg-white rounded-2xl border border-slate-200 p-6 dark:bg-slate-900 dark:border-slate-800">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-bold text-slate-900 dark:text-slate-50">July 2026</h4>
                  </div>
                  <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold text-slate-500 border-b pb-2">
                    {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                      <div key={d}>{d}</div>
                    ))}
                  </div>
                  <div className="grid grid-cols-7 gap-2 mt-2 text-sm">
                    {Array.from({ length: 31 }, (_, i) => {
                      const dayNum = i + 1;
                      const dateStr = `2026-07-${String(dayNum).padStart(2, "0")}`;
                      const dayEvents = filteredEvents.filter((e) => e.event_date === dateStr);
                      return (
                        <div key={i} className="min-h-16 border rounded-lg p-1 bg-slate-50/50 flex flex-col justify-between hover:bg-slate-100/50">
                          <span className="font-semibold text-slate-400">{dayNum}</span>
                          {dayEvents.map((e) => (
                            <span key={e.id} className="text-[10px] font-bold bg-emerald-100 text-emerald-900 rounded px-1 truncate">
                              {e.title}
                            </span>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 4: Direct Notification Broadcasting */}
          {activeTab === "notifications" && (
            <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 p-6 shadow-soft dark:bg-slate-900 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50 mb-2">Direct Notification Broadcast</h3>
              <p className="text-xs text-slate-500 mb-6">Dispatch priority notifications via WhatsApp, SMS, or In-App alerts directly to community members.</p>

              <form onSubmit={handleSendNotification} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold mb-1.5">Notification Channel</label>
                  <select
                    value={notifChannel}
                    onChange={(e) => setNotifChannel(e.target.value)}
                    className="w-full rounded-lg border-slate-300 bg-white dark:bg-slate-800 dark:border-slate-700 py-2 px-3"
                  >
                    <option value="whatsapp">Primary WhatsApp</option>
                    <option value="sms">SMS</option>
                    <option value="email">Email</option>
                    <option value="push">Push Notification</option>
                    <option value="in_app">In-App Notification</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1.5">Recipient Identity Contact</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. +919876543210 or user@email.com"
                    value={notifRecipient}
                    onChange={(e) => setNotifRecipient(e.target.value)}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 dark:border-slate-700 py-2 px-3 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1.5">Broadcast Message Content</label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Type details of notification..."
                    value={notifMessage}
                    onChange={(e) => setNotifMessage(e.target.value)}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 dark:border-slate-700 py-2 px-3 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <button
                  type="submit"
                  disabled={sendingNotif}
                  className="flex w-full justify-center rounded-lg bg-emerald-600 py-2.5 px-3.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {sendingNotif ? "Dispatching..." : "Send Notification"}
                </button>
              </form>
            </div>
          )}
        </div>
      </main>

      {/* Modal: Announcement Form */}
      {isAnnouncementModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-bold mb-4">{editingAnnouncement ? "Edit Announcement" : "Create Announcement"}</h3>
            <form onSubmit={handleSaveAnnouncement} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={announcementForm.title}
                  onChange={(e) => setAnnouncementForm({...announcementForm, title: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 dark:border-slate-750 py-2 px-3"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Short Summary (optional)</label>
                <input
                  type="text"
                  value={announcementForm.short_summary}
                  onChange={(e) => setAnnouncementForm({...announcementForm, short_summary: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 dark:border-slate-750 py-2 px-3"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Message Content</label>
                <textarea
                  required
                  rows={4}
                  value={announcementForm.content}
                  onChange={(e) => setAnnouncementForm({...announcementForm, content: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 dark:border-slate-750 py-2 px-3"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold mb-1">Category</label>
                  <select
                    value={announcementForm.announcement_type}
                    onChange={(e) => setAnnouncementForm({...announcementForm, announcement_type: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  >
                    <option value="general">General</option>
                    <option value="emergency">Emergency</option>
                    <option value="prayer">Prayer Update</option>
                    <option value="ramadan">Ramadan</option>
                    <option value="eid">Eid</option>
                    <option value="community">Community</option>
                    <option value="education">Education</option>
                    <option value="charity">Charity</option>
                    <option value="lost_found">Lost & Found</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Priority</label>
                  <select
                    value={announcementForm.priority}
                    onChange={(e) => setAnnouncementForm({...announcementForm, priority: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  >
                    <option value="normal">Normal</option>
                    <option value="important">Important</option>
                    <option value="urgent">Urgent</option>
                  </select>
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
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Expiry Date</label>
                  <input
                    type="date"
                    required
                    value={announcementForm.end_date}
                    onChange={(e) => setAnnouncementForm({...announcementForm, end_date: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Publish State</label>
                <select
                  value={announcementForm.status}
                  onChange={(e) => setAnnouncementForm({...announcementForm, status: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                >
                  <option value="draft">Draft (Private)</option>
                  <option value="published">Published (Public)</option>
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
                  className="rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-500 transition"
                >
                  Save Announcement
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
            <h3 className="text-lg font-bold mb-4">{editingEvent ? "Edit Event" : "Create Event"}</h3>
            <form onSubmit={handleSaveEvent} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Event Title</label>
                <input
                  type="text"
                  required
                  value={eventForm.title}
                  onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Description</label>
                <textarea
                  required
                  rows={3}
                  value={eventForm.description}
                  onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold mb-1">Speaker Name</label>
                  <input
                    type="text"
                    required
                    value={eventForm.speaker_name}
                    onChange={(e) => setEventForm({...eventForm, speaker_name: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Organizer</label>
                  <input
                    type="text"
                    required
                    value={eventForm.organizer}
                    onChange={(e) => setEventForm({...eventForm, organizer: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
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
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Start Time</label>
                  <input
                    type="text"
                    required
                    placeholder="18:00:00"
                    value={eventForm.event_time}
                    onChange={(e) => setEventForm({...eventForm, event_time: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">End Time</label>
                  <input
                    type="text"
                    required
                    placeholder="19:30:00"
                    value={eventForm.end_time}
                    onChange={(e) => setEventForm({...eventForm, end_time: e.target.value})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Venue Address / Location</label>
                <input
                  type="text"
                  required
                  placeholder="Mosque Hall, Nanded"
                  value={eventForm.event_location}
                  onChange={(e) => setEventForm({...eventForm, event_location: e.target.value})}
                  className="w-full rounded-lg border-slate-300 dark:bg-slate-800 py-2 px-3"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <input
                    id="registration_required"
                    type="checkbox"
                    checked={eventForm.registration_required}
                    onChange={(e) => setEventForm({...eventForm, registration_required: e.target.checked})}
                    className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <label htmlFor="registration_required" className="text-xs font-semibold">Registration Required</label>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Max Capacity</label>
                  <input
                    type="number"
                    disabled={!eventForm.registration_required}
                    value={eventForm.max_capacity}
                    onChange={(e) => setEventForm({...eventForm, max_capacity: parseInt(e.target.value)})}
                    className="w-full rounded-lg border-slate-300 dark:bg-slate-800 disabled:opacity-50 py-2 px-3"
                  />
                </div>
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
                  className="rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-500 transition"
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
