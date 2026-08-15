"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";

type JanazahNotice = {
  id: number;
  deceased_name: string;
  age?: number;
  gender: string;
  salah_date: string;
  salah_time: string;
  burial_place: string;
  relatives_contact: string;
  status: string;
  created_at: string;
};

export default function JanazahTab() {
  const [notices, setNotices] = useState<JanazahNotice[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("male");
  const [salahDate, setSalahDate] = useState("");
  const [salahTime, setSalahTime] = useState("");
  const [burialPlace, setBurialPlace] = useState("");
  const [contact, setContact] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchNotices();
  }, []);

  async function fetchNotices() {
    try {
      const res = await apiRequest<any>({ path: "/mosques/my-mosque/janazah/" });
      const items = Array.isArray(res) ? res : res.results || [];
      setNotices(items);
    } catch (err) {
      console.error("Failed to load Janazah notices", err);
    } finally {
      setLoading(false);
    }
  }

  const handleOpenCreate = () => {
    setName("");
    setAge("");
    setGender("male");
    setSalahDate(new Date().toISOString().split("T")[0]);
    setSalahTime("14:00");
    setBurialPlace("");
    setContact("");
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const payload = {
      deceased_name: name,
      age: age ? Number(age) : null,
      gender,
      salah_date: salahDate,
      salah_time: salahTime,
      burial_place: burialPlace,
      relatives_contact: contact,
      status: "published",
    };

    try {
      await apiRequest({
        path: "/mosques/my-mosque/janazah/",
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowModal(false);
      fetchNotices();
    } catch (err) {
      console.error("Failed to post Janazah notice", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading Janazah notices...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Janazah Funeral Notices</h2>
          <p className="text-sm text-slate-500">Notify the community about Janazah prayers and burials</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition"
        >
          + Post Janazah Notice
        </button>
      </div>

      {notices.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
          <p className="text-slate-500 font-medium">No Janazah notices posted.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {notices.map((item) => (
            <div key={item.id} className="p-4 rounded-lg border border-slate-200 flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-slate-900 text-base">{item.deceased_name} {item.age ? `(${item.age} yrs)` : ""}</h3>
                <p className="text-sm text-slate-600 mt-1">Janazah Prayer: {item.salah_date} at {item.salah_time}</p>
                <p className="text-xs text-slate-500 mt-1">Burial: {item.burial_place || "Not specified"} • Contact: {item.relatives_contact || "N/A"}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Post Janazah Notice</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Deceased Name *</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Age</label>
                  <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Gender</label>
                  <select value={gender} onChange={(e) => setGender(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-slate-900 bg-white">
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Salah Date *</label>
                  <input type="date" value={salahDate} onChange={(e) => setSalahDate(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Salah Time *</label>
                  <input type="time" value={salahTime} onChange={(e) => setSalahTime(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-slate-900" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Burial Place</label>
                <input type="text" value={burialPlace} onChange={(e) => setBurialPlace(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Contact Phone</label>
                <input type="text" value={contact} onChange={(e) => setContact(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-slate-900" />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg text-slate-700">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 bg-emerald-600 text-white rounded-lg">{submitting ? "Posting..." : "Post Notice"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
