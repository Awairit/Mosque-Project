"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";
import { formatTimeTo12Hour } from "@/lib/utils/formatters";

type TimingsState = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  jumuah_time: string;
  effective_from: string;
  updated_at: string;
  maghrib_congregation_mode?: string;
  maghrib_delay_minutes?: number;
  resolved_maghrib_time?: string;
};

export default function TimetablesTab() {
  const [timings, setTimings] = useState<TimingsState>({
    fajr_time: "",
    dhuhr_time: "",
    asr_time: "",
    maghrib_time: "",
    isha_time: "",
    jumuah_time: "",
    effective_from: "",
    updated_at: "",
    maghrib_congregation_mode: "manual",
    maghrib_delay_minutes: 15,
    resolved_maghrib_time: "",
  });
  const [loadingTimings, setLoadingTimings] = useState(true);
  const [savingTimings, setSavingTimings] = useState(false);
  const [successTimings, setSuccessTimings] = useState("");
  const [errorsTimings, setErrorsTimings] = useState<
    Partial<Record<keyof TimingsState | "non_field_errors", string>>
  >({});

  useEffect(() => {
    async function fetchTimings() {
      try {
        const res = await apiRequest<any>({ path: "/mosques/my-mosque/timings/" });
        if (res) {
          setTimings({
            fajr_time: res.fajr_time || "",
            dhuhr_time: res.dhuhr_time || "",
            asr_time: res.asr_time || "",
            maghrib_time: res.maghrib_time || "",
            isha_time: res.isha_time || "",
            jumuah_time: res.jumuah_time || "",
            effective_from: res.effective_from || "",
            updated_at: res.updated_at || "",
            maghrib_congregation_mode: res.maghrib_congregation_mode || "manual",
            maghrib_delay_minutes: res.maghrib_delay_minutes ?? 15,
            resolved_maghrib_time: res.resolved_maghrib_time || "",
          });
        }
      } catch (err) {
        console.error("Failed to load timings", err);
      } finally {
        setLoadingTimings(false);
      }
    }
    fetchTimings();
  }, []);

  const handleTimingsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingTimings(true);
    setSuccessTimings("");
    setErrorsTimings({});

    try {
      await apiRequest({
        path: "/mosques/my-mosque/timings/",
        method: "PUT",
        body: JSON.stringify(timings),
      });
      setSuccessTimings("Prayer timings updated successfully!");
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const fieldErrors: Record<string, string> = {};
        Object.entries(err.details as Record<string, any>).forEach(([k, v]) => {
          fieldErrors[k] = Array.isArray(v) ? v[0] : String(v);
        });
        setErrorsTimings(fieldErrors);
      }
    } finally {
      setSavingTimings(false);
    }
  };

  if (loadingTimings) {
    return <div className="p-8 text-center text-slate-500">Loading prayer timings...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Prayer Timings & Schedule</h2>

      {successTimings && (
        <div className="mb-6 p-4 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 text-sm font-medium">
          {successTimings}
        </div>
      )}

      {errorsTimings.non_field_errors && (
        <div className="mb-6 p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-sm font-medium">
          {errorsTimings.non_field_errors}
        </div>
      )}

      <form onSubmit={handleTimingsSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Fajr Time *</label>
            <input
              type="time"
              value={timings.fajr_time}
              onChange={(e) => setTimings({ ...timings, fajr_time: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {timings.fajr_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.fajr_time)}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Dhuhr Time *</label>
            <input
              type="time"
              value={timings.dhuhr_time}
              onChange={(e) => setTimings({ ...timings, dhuhr_time: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {timings.dhuhr_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.dhuhr_time)}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Asr Time *</label>
            <input
              type="time"
              value={timings.asr_time}
              onChange={(e) => setTimings({ ...timings, asr_time: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {timings.asr_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.asr_time)}</p>}
          </div>

          <div className="md:col-span-3 bg-slate-50 p-4 rounded-lg border border-slate-200">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Maghrib Congregation Mode</label>
                <select
                  value={timings.maghrib_congregation_mode || "manual"}
                  onChange={(e) => setTimings({ ...timings, maghrib_congregation_mode: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
                >
                  <option value="manual">Manual Fixed Time</option>
                  <option value="city_offset">Dynamic Sunset Delay (1-30 mins)</option>
                </select>
              </div>

              {timings.maghrib_congregation_mode === "city_offset" ? (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Maghrib Jamaat Delay (Minutes after Sunset) *</label>
                  <select
                    value={timings.maghrib_delay_minutes || 15}
                    onChange={(e) => setTimings({ ...timings, maghrib_delay_minutes: Number(e.target.value) })}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
                  >
                    {Array.from({ length: 30 }, (_, i) => i + 1).map((m) => (
                      <option key={m} value={m}>
                        +{m} {m === 1 ? "minute" : "minutes"} after sunset
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-emerald-600 font-medium">Maghrib Jamaat = Sunset + {timings.maghrib_delay_minutes || 15} mins</p>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Maghrib Fixed Time *</label>
                  <input
                    type="time"
                    value={timings.maghrib_time}
                    onChange={(e) => setTimings({ ...timings, maghrib_time: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
                    required
                  />
                  {timings.maghrib_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.maghrib_time)}</p>}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Isha Time *</label>
            <input
              type="time"
              value={timings.isha_time}
              onChange={(e) => setTimings({ ...timings, isha_time: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {timings.isha_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.isha_time)}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Jumuah (Friday) Time *</label>
            <input
              type="time"
              value={timings.jumuah_time}
              onChange={(e) => setTimings({ ...timings, jumuah_time: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {timings.jumuah_time && <p className="mt-1 text-xs text-slate-500">{formatTimeTo12Hour(timings.jumuah_time)}</p>}
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={savingTimings}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {savingTimings ? "Updating Timings..." : "Update Prayer Timings"}
          </button>
        </div>
      </form>
    </div>
  );
}
