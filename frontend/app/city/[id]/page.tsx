"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";
import { getPreviewFacilities } from "@/lib/constants/facilities";

type TimingRow = {
  date: string;
  fajr: string;
  sunrise: string;
  dhuhr: string;
  asr: string;
  maghrib: string;
  isha: string;
};

type CityDetails = {
  id: number;
  name: string;
  state: string;
  country: string;
  latitude: string;
  longitude: string;
};

type CityTimings = {
  city_details: CityDetails;
  today: {
    fajr: string;
    sunrise: string;
    dhuhr: string;
    asr: string;
    maghrib: string;
    isha: string;
    date: string;
  };
};

type Announcement = {
  id: number;
  title: string;
  short_summary: string;
  content: string;
  priority: string;
  announcement_type: string;
  publish_date?: string;
};

type Event = {
  id: number;
  title: string;
  description: string;
  event_type: string;
  event_date: string;
  event_time: string;
  end_time?: string;
  event_location?: string;
  speaker_name?: string;
};

type MosquePreview = {
  id: number;
  mosque_name: string;
  address: string;
  mosque_status: string;
  women_prayer_available?: boolean;
  separate_women_entrance?: boolean;
  parking_available?: boolean;
  wudu_facility_available?: boolean;
  wheelchair_accessible?: boolean;
  drinking_water_available?: boolean;
  washrooms_available?: boolean;
  library_available?: boolean;
  quran_classes_available?: boolean;
  hifz_program_available?: boolean;
  nikah_service_available?: boolean;
  muslim_burial_ground_available?: boolean;
  community_hall_available?: boolean;
  ramadan_iftar_available?: boolean;
  eid_prayer_ground_available?: boolean;
  zakat_collection_available?: boolean;
  funeral_prayer_facility_available?: boolean;
};

export default function CityPublicPage() {
  const params = useParams();
  const router = useRouter();
  const cityId = params?.id ? String(params.id) : "";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [timings, setTimings] = useState<CityTimings | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [mosques, setMosques] = useState<MosquePreview[]>([]);

  useEffect(() => {
    if (!cityId) return;

    const loadData = async () => {
      try {
        setLoading(true);
        setError(false);

        // Fetch timings & city details
        const timingRes = await apiRequest<CityTimings>({
          path: `/locations/cities/${cityId}/timings/`,
          cache: "no-store",
        });
        setTimings(timingRes);

        // Fetch public announcements
        const annRes = await apiRequest<any>({
          path: `/public/announcements/?city_id=${cityId}`,
          cache: "no-store",
        });
        setAnnouncements(annRes || []);

        // Fetch public events
        const evtRes = await apiRequest<any>({
          path: `/public/events/?city_id=${cityId}`,
          cache: "no-store",
        });
        setEvents(evtRes || []);

        // Fetch participating mosques in this city
        const mosquesRes = await apiRequest<any>({
          path: `/mosques/?city_id=${cityId}`,
          cache: "no-store",
        });
        setMosques(mosquesRes.results || mosquesRes || []);

      } catch (err) {
        console.error("Failed to load city public details", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [cityId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 dark:bg-slate-950">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="text-slate-500 text-sm">Loading city information...</p>
        </div>
      </div>
    );
  }

  if (error || !timings) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 dark:bg-slate-950">
        <div className="bg-white rounded-2xl border p-8 max-w-md w-full text-center shadow-soft dark:bg-slate-900">
          <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Page</h2>
          <p className="text-slate-500 text-sm mb-6">We could not retrieve the prayer timings or details for this city. Please try again later.</p>
          <button 
            onClick={() => router.push("/")}
            className="bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-semibold hover:bg-emerald-500"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const { city_details, today } = timings;
  const emergencyAlerts = announcements.filter((a) => a.priority === "urgent" || a.announcement_type === "emergency");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50 pb-16">
      {/* Banner / Header */}
      <section className="bg-emerald-800 text-white py-12 px-4 shadow-soft">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <span className="text-xs bg-emerald-700/60 rounded-full px-2.5 py-1 font-semibold uppercase tracking-wider">
              City Timetable & Info
            </span>
            <h1 className="text-4xl font-bold mt-2">{city_details.name}</h1>
            <p className="text-sm text-emerald-100 mt-1">{city_details.state}, {city_details.country}</p>
          </div>
          <Link
            href="/"
            className="text-sm bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg px-4 py-2 transition"
          >
            Change City
          </Link>
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4 mt-8 grid gap-8 lg:grid-cols-[1fr_360px]">
        {/* Left Column: Timings and Info */}
        <div className="space-y-8">
          
          {/* Emergency Alert Broadcast Panel */}
          {emergencyAlerts.length > 0 && (
            <div className="bg-red-50 text-red-900 border border-red-200 rounded-2xl p-5 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900">
              <h3 className="font-bold text-base flex items-center gap-2 mb-3">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-600 animate-ping"></span>
                Emergency Alerts
              </h3>
              <div className="space-y-4">
                {emergencyAlerts.map((alert) => (
                  <div key={alert.id} className="border-l-4 border-red-500 pl-3">
                    <h4 className="font-bold text-sm">{alert.title}</h4>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{alert.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Today's timings */}
          <div className="bg-white rounded-2xl border p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-lg font-bold mb-4 border-b pb-2">Today&apos;s Prayer Times ({today.date})</h3>
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-4 text-center">
              {[
                { name: "Fajr", time: today.fajr },
                { name: "Sunrise", time: today.sunrise },
                { name: "Dhuhr", time: today.dhuhr },
                { name: "Asr", time: today.asr },
                { name: "Maghrib", time: today.maghrib },
                { name: "Isha", time: today.isha },
              ].map((p) => (
                <div key={p.name} className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 border">
                  <div className="text-xs font-semibold text-slate-500 uppercase">{p.name}</div>
                  <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mt-1">{p.time}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Participating Mosques */}
          <div className="bg-white rounded-2xl border p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-lg font-bold mb-4 border-b pb-2">Participating Mosques</h3>
            {mosques.length === 0 ? (
              <p className="text-sm text-slate-500">No active mosques onboarded yet in {city_details.name}.</p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {mosques.map((mosque) => (
                  <Link
                    key={mosque.id}
                    href={`/mosque/${mosque.id}`}
                    className="group border rounded-xl p-4 hover:border-emerald-600 bg-slate-50/50 hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 transition flex flex-col justify-between min-h-[100px]"
                  >
                    <div>
                      <h4 className="font-bold text-slate-900 group-hover:text-emerald-800 dark:text-slate-100 transition">
                        {mosque.mosque_name}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">{mosque.address}</p>
                    </div>
                    {(() => {
                      const { preview, remainingCount } = getPreviewFacilities(mosque, 4);
                      if (preview.length === 0) return null;
                      return (
                        <div className="mt-3 flex flex-wrap gap-1">
                          {preview.map((f) => (
                            <span key={f.key} title={f.label} className="rounded bg-white dark:bg-slate-900 border dark:border-slate-850 px-1.5 py-0.5 text-[9px] text-slate-600 dark:text-slate-400">
                              {f.icon} {f.label}
                            </span>
                          ))}
                          {remainingCount > 0 && (
                            <span className="rounded bg-slate-100 dark:bg-slate-900 border dark:border-slate-850 px-1.5 py-0.5 text-[9px] text-slate-500 font-medium">
                              +{remainingCount}
                            </span>
                          )}
                        </div>
                      );
                    })()}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Community Notice Board and Events */}
        <div className="space-y-8">
          {/* Announcements */}
          <div className="bg-white rounded-2xl border p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-base font-bold mb-4 border-b pb-2">Community Notices</h3>
            {announcements.length === 0 ? (
              <p className="text-xs text-slate-500">No recent announcements in this city.</p>
            ) : (
              <div className="space-y-4">
                {announcements.map((ann) => (
                  <div key={ann.id} className="border-b pb-3 last:border-b-0 last:pb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold bg-slate-100 text-slate-700 rounded px-1.5 py-0.5 uppercase">
                        {ann.announcement_type}
                      </span>
                    </div>
                    <h4 className="font-bold text-xs">{ann.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{ann.short_summary || ann.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming Events */}
          <div className="bg-white rounded-2xl border p-5 shadow-soft dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-base font-bold mb-4 border-b pb-2">Upcoming Events</h3>
            {events.length === 0 ? (
              <p className="text-xs text-slate-500">No scheduled events found.</p>
            ) : (
              <div className="space-y-4">
                {events.map((evt) => (
                  <div key={evt.id} className="border-b pb-3 last:border-b-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold bg-emerald-50 text-emerald-800 rounded px-1.5 py-0.5 uppercase">
                        {evt.event_type}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">{evt.event_date}</span>
                    </div>
                    <h4 className="font-bold text-xs mt-1.5">{evt.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5">{evt.speaker_name && `Speaker: ${evt.speaker_name}`}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">{evt.event_location && `Location: ${evt.event_location}`}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
