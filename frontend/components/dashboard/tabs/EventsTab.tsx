"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";

type EventItem = {
  id: number;
  title: string;
  description: string;
  event_date: string;
  event_time: string;
  status: string;
  location_name?: string;
  created_at: string;
};

export default function EventsTab() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<EventItem | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [eventTime, setEventTime] = useState("");
  const [status, setStatus] = useState("published");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, []);

  async function fetchEvents() {
    try {
      const res = await apiRequest<any>({ path: "/mosques/my-mosque/events/" });
      const items = Array.isArray(res) ? res : res.results || [];
      setEvents(items);
    } catch (err) {
      console.error("Failed to load events", err);
    } finally {
      setLoading(false);
    }
  }

  const handleOpenCreate = () => {
    setEditingItem(null);
    setTitle("");
    setDescription("");
    setEventDate(new Date().toISOString().split("T")[0]);
    setEventTime("18:00");
    setStatus("published");
    setShowModal(true);
  };

  const handleOpenEdit = (item: EventItem) => {
    setEditingItem(item);
    setTitle(item.title);
    setDescription(item.description);
    setEventDate(item.event_date);
    setEventTime(item.event_time);
    setStatus(item.status);
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const payload = {
      title,
      description,
      event_date: eventDate,
      event_time: eventTime,
      status,
    };

    try {
      if (editingItem) {
        await apiRequest({
          path: `/mosques/my-mosque/events/${editingItem.id}/`,
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest({
          path: "/mosques/my-mosque/events/",
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      setShowModal(false);
      fetchEvents();
    } catch (err) {
      console.error("Failed to save event", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this event?")) return;
    try {
      await apiRequest({
        path: `/mosques/my-mosque/events/${id}/`,
        method: "DELETE",
      });
      fetchEvents();
    } catch (err) {
      console.error("Failed to delete event", err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading events...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Events & Programs</h2>
          <p className="text-sm text-slate-500">Manage lectures, gatherings, and special programs</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition"
        >
          + New Event
        </button>
      </div>

      {events.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
          <p className="text-slate-500 font-medium">No events scheduled yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((item) => (
            <div key={item.id} className="p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800">
                    {item.event_date} at {item.event_time}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900 text-base">{item.title}</h3>
                <p className="text-sm text-slate-600 mt-1">{item.description}</p>
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
            <h3 className="text-lg font-bold text-slate-900">{editingItem ? "Edit Event" : "Create Event"}</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Event Date *</label>
                  <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Event Time *</label>
                  <input type="time" value={eventTime} onChange={(e) => setEventTime(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg text-slate-700">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 bg-emerald-600 text-white rounded-lg">{submitting ? "Saving..." : "Save Event"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
