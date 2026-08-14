"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";

type ScheduleState = {
  schedule_mode: "24_HOURS" | "GENERAL" | "SALAH_BASED";
  open_24_hours: boolean;
  general_open_time: string;
  general_close_time: string;
  fajr_open: string;
  fajr_close: string;
  dhuhr_open: string;
  dhuhr_close: string;
  asr_open: string;
  asr_close: string;
  maghrib_open: string;
  maghrib_close: string;
  isha_open: string;
  isha_close: string;
};

const initialSchedule: ScheduleState = {
  schedule_mode: "SALAH_BASED",
  open_24_hours: false,
  general_open_time: "",
  general_close_time: "",
  fajr_open: "",
  fajr_close: "",
  dhuhr_open: "",
  dhuhr_close: "",
  asr_open: "",
  asr_close: "",
  maghrib_open: "",
  maghrib_close: "",
  isha_open: "",
  isha_close: "",
};

export function ScheduleTab() {
  const [schedule, setSchedule] = useState<ScheduleState>(initialSchedule);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    async function fetchSchedule() {
      try {
        const fmtTime = (t: string | null) => (t ? t.slice(0, 5) : "");
        const res = await apiRequest<any>({ path: "/mosques/my-mosque/schedule/" });
        if (res) {
          setSchedule({
            schedule_mode: res.schedule_mode || (res.open_24_hours ? "24_HOURS" : "SALAH_BASED"),
            open_24_hours: !!res.open_24_hours,
            general_open_time: fmtTime(res.general_open_time),
            general_close_time: fmtTime(res.general_close_time),
            fajr_open: fmtTime(res.fajr_open),
            fajr_close: fmtTime(res.fajr_close),
            dhuhr_open: fmtTime(res.dhuhr_open),
            dhuhr_close: fmtTime(res.dhuhr_close),
            asr_open: fmtTime(res.asr_open),
            asr_close: fmtTime(res.asr_close),
            maghrib_open: fmtTime(res.maghrib_open),
            maghrib_close: fmtTime(res.maghrib_close),
            isha_open: fmtTime(res.isha_open),
            isha_close: fmtTime(res.isha_close),
          });
        }
      } catch (err) {
        console.error("Failed to load operating schedule", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSchedule();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess("");
    setErrors({});

    const cleanTime = (val: string) => (val && val.trim() ? val.trim() : null);

    const payload = {
      schedule_mode: schedule.schedule_mode,
      open_24_hours: schedule.schedule_mode === "24_HOURS",
      general_open_time: cleanTime(schedule.general_open_time),
      general_close_time: cleanTime(schedule.general_close_time),
      fajr_open: cleanTime(schedule.fajr_open),
      fajr_close: cleanTime(schedule.fajr_close),
      dhuhr_open: cleanTime(schedule.dhuhr_open),
      dhuhr_close: cleanTime(schedule.dhuhr_close),
      asr_open: cleanTime(schedule.asr_open),
      asr_close: cleanTime(schedule.asr_close),
      maghrib_open: cleanTime(schedule.maghrib_open),
      maghrib_close: cleanTime(schedule.maghrib_close),
      isha_open: cleanTime(schedule.isha_open),
      isha_close: cleanTime(schedule.isha_close),
    };

    try {
      await apiRequest({
        path: "/mosques/my-mosque/schedule/",
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setSuccess("Operating schedule updated successfully!");
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const fieldErrors: Record<string, string> = {};
        Object.entries(err.details as Record<string, any>).forEach(([k, v]) => {
          fieldErrors[k] = Array.isArray(v) ? v[0] : String(v);
        });
        setErrors(fieldErrors);
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading operating schedule...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Mosque Hours of Operation & Doors Schedule</h2>

      {success && (
        <div className="mb-6 p-4 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 text-sm font-medium">
          {success}
        </div>
      )}

      {errors.non_field_errors && (
        <div className="mb-6 p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-sm font-medium">
          {errors.non_field_errors}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Operating Schedule Mode</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <label className={`flex items-center space-x-3 p-4 rounded-xl border cursor-pointer ${schedule.schedule_mode === "24_HOURS" ? "border-emerald-500 bg-emerald-50/50" : "border-slate-200 hover:bg-slate-50"}`}>
              <input
                type="radio"
                name="schedule_mode"
                value="24_HOURS"
                checked={schedule.schedule_mode === "24_HOURS"}
                onChange={() => setSchedule({ ...schedule, schedule_mode: "24_HOURS", open_24_hours: true })}
                className="h-4 w-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div>
                <span className="block text-sm font-semibold text-slate-900">Open 24 Hours</span>
                <span className="block text-xs text-slate-500">Mosque doors remain open continuously.</span>
              </div>
            </label>

            <label className={`flex items-center space-x-3 p-4 rounded-xl border cursor-pointer ${schedule.schedule_mode === "GENERAL" ? "border-emerald-500 bg-emerald-50/50" : "border-slate-200 hover:bg-slate-50"}`}>
              <input
                type="radio"
                name="schedule_mode"
                value="GENERAL"
                checked={schedule.schedule_mode === "GENERAL"}
                onChange={() => setSchedule({ ...schedule, schedule_mode: "GENERAL", open_24_hours: false })}
                className="h-4 w-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div>
                <span className="block text-sm font-semibold text-slate-900">General Daily Hours</span>
                <span className="block text-xs text-slate-500">Fixed daily opening and closing times.</span>
              </div>
            </label>

            <label className={`flex items-center space-x-3 p-4 rounded-xl border cursor-pointer ${schedule.schedule_mode === "SALAH_BASED" ? "border-emerald-500 bg-emerald-50/50" : "border-slate-200 hover:bg-slate-50"}`}>
              <input
                type="radio"
                name="schedule_mode"
                value="SALAH_BASED"
                checked={schedule.schedule_mode === "SALAH_BASED"}
                onChange={() => setSchedule({ ...schedule, schedule_mode: "SALAH_BASED", open_24_hours: false })}
                className="h-4 w-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div>
                <span className="block text-sm font-semibold text-slate-900">Salah Prayer Windows</span>
                <span className="block text-xs text-slate-500">Doors open & close around each prayer.</span>
              </div>
            </label>
          </div>
        </div>

        {schedule.schedule_mode === "GENERAL" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">General Daily Opening Time *</label>
              <input
                type="time"
                value={schedule.general_open_time}
                onChange={(e) => setSchedule({ ...schedule, general_open_time: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">General Daily Closing Time *</label>
              <input
                type="time"
                value={schedule.general_close_time}
                onChange={(e) => setSchedule({ ...schedule, general_close_time: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
                required
              />
            </div>
          </div>
        )}

        {schedule.schedule_mode === "SALAH_BASED" && (
          <div className="space-y-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h3 className="text-sm font-semibold text-slate-800">Per-Salah Opening & Closing Windows</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Fajr Open / Close</label>
                <div className="flex space-x-2">
                  <input type="time" value={schedule.fajr_open} onChange={(e) => setSchedule({ ...schedule, fajr_open: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                  <input type="time" value={schedule.fajr_close} onChange={(e) => setSchedule({ ...schedule, fajr_close: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Dhuhr Open / Close</label>
                <div className="flex space-x-2">
                  <input type="time" value={schedule.dhuhr_open} onChange={(e) => setSchedule({ ...schedule, dhuhr_open: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                  <input type="time" value={schedule.dhuhr_close} onChange={(e) => setSchedule({ ...schedule, dhuhr_close: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Asr Open / Close</label>
                <div className="flex space-x-2">
                  <input type="time" value={schedule.asr_open} onChange={(e) => setSchedule({ ...schedule, asr_open: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                  <input type="time" value={schedule.asr_close} onChange={(e) => setSchedule({ ...schedule, asr_close: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Maghrib Open / Close</label>
                <div className="flex space-x-2">
                  <input type="time" value={schedule.maghrib_open} onChange={(e) => setSchedule({ ...schedule, maghrib_open: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                  <input type="time" value={schedule.maghrib_close} onChange={(e) => setSchedule({ ...schedule, maghrib_close: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Isha Open / Close</label>
                <div className="flex space-x-2">
                  <input type="time" value={schedule.isha_open} onChange={(e) => setSchedule({ ...schedule, isha_open: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                  <input type="time" value={schedule.isha_close} onChange={(e) => setSchedule({ ...schedule, isha_close: e.target.value })} className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {saving ? "Saving Schedule..." : "Save Operating Schedule"}
          </button>
        </div>
      </form>
    </div>
  );
}
