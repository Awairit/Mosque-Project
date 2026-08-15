"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";

type Announcement = {
  id: number;
  title: string;
  content: string;
  announcement_type: string;
  priority: string;
  status: string;
  start_date: string;
  end_date: string;
  created_at: string;
};

export default function AnnouncementsTab() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<Announcement | null>(null);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [announcementType, setAnnouncementType] = useState("general");
  const [priority, setPriority] = useState("normal");
  const [status, setStatus] = useState("published");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  async function fetchAnnouncements() {
    try {
      const res = await apiRequest<any>({ path: "/mosques/my-mosque/announcements/" });
      const items = Array.isArray(res) ? res : res.results || [];
      setAnnouncements(items);
    } catch (err) {
      console.error("Failed to load announcements", err);
    } finally {
      setLoading(false);
    }
  }

  const handleOpenCreate = () => {
    setEditingItem(null);
    setTitle("");
    setContent("");
    setAnnouncementType("general");
    setPriority("normal");
    setStatus("published");
    setStartDate(new Date().toISOString().split("T")[0]);
    setEndDate(new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0]);
    setShowModal(true);
  };

  const handleOpenEdit = (item: Announcement) => {
    setEditingItem(item);
    setTitle(item.title);
    setContent(item.content);
    setAnnouncementType(item.announcement_type);
    setPriority(item.priority);
    setStatus(item.status);
    setStartDate(item.start_date);
    setEndDate(item.end_date);
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const payload = {
      title,
      content,
      announcement_type: announcementType,
      priority,
      status,
      start_date: startDate,
      end_date: endDate,
    };

    try {
      if (editingItem) {
        await apiRequest({
          path: `/mosques/my-mosque/announcements/${editingItem.id}/`,
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest({
          path: "/mosques/my-mosque/announcements/",
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      setShowModal(false);
      fetchAnnouncements();
    } catch (err) {
      console.error("Failed to save announcement", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this announcement?")) return;
    try {
      await apiRequest({
        path: `/mosques/my-mosque/announcements/${id}/`,
        method: "DELETE",
      });
      fetchAnnouncements();
    } catch (err) {
      console.error("Failed to delete announcement", err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading announcements...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Announcements</h2>
          <p className="text-sm text-slate-500">Broadcast important notices to worshippers</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition"
        >
          + New Announcement
        </button>
      </div>

      {announcements.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
          <p className="text-slate-500 font-medium">No announcements published yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map((item) => (
            <div key={item.id} className="p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded ${item.status === "published" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>
                    {item.status}
                  </span>
                  <span className="text-xs text-slate-500">{item.start_date} to {item.end_date}</span>
                </div>
                <h3 className="font-semibold text-slate-900 text-base">{item.title}</h3>
                <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{item.content}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleOpenEdit(item)} className="px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded">
                  Edit
                </button>
                <button onClick={() => handleDelete(item.id)} className="px-3 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50 rounded">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">{editingItem ? "Edit Announcement" : "Create Announcement"}</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Content *</label>
                <textarea rows={4} value={content} onChange={(e) => setContent(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Start Date</label>
                  <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">End Date</label>
                  <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg text-slate-700">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 bg-emerald-600 text-white rounded-lg">{submitting ? "Saving..." : "Save Announcement"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
