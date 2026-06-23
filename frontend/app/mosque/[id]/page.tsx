"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";

type PrayerTiming = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  jumuah_time: string;
  effective_from: string;
};

type OperatingStatus = {
  is_open: boolean;
  status_label: string;
  current_window?: string | null;
  closes_at?: string | null;
  opens_at?: string | null;
  next_prayer_name?: string | null;
  next_prayer_time?: string | null;
};

type PhotoState = {
  id: number;
  image: string;
  title: string;
  caption: string;
  display_order: number;
  is_active: boolean;
};

type AnnouncementState = {
  id: number;
  title: string;
  content: string;
  priority: "normal" | "important" | "urgent";
  status: "draft" | "published" | "archived";
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at?: string;
};

type EventState = {
  id: number;
  title: string;
  description: string;
  event_type: "lecture" | "dars" | "youth_program" | "community_meeting" | "fundraiser" | "ramadan" | "eid" | "other";
  status: "draft" | "published" | "archived";
  event_date: string;
  event_time: string;
  event_location: string;
  speaker_name: string;
  is_active: boolean;
};

type CommunityScheduleState = {
  id: number;
  schedule_type: "khutbah" | "weekly_dars";
  event_date: string;
  start_time: string;
  speaker: string;
  topic: string;
  extended_data?: {
    shift_number?: number;
    language?: string;
    day_of_week?: number;
  } | null;
};

type JanazahNoticeState = {
  id: number;
  deceased_name: string;
  gender: "male" | "female";
  age?: number | null;
  date_of_death: string;
  salah_date: string;
  salah_time: string;
  salah_details?: string;
  burial_date?: string;
  burial_time?: string;
  cemetery_name?: string;
  cemetery_address?: string;
  cemetery_gps_url?: string;
  family_contact_name?: string;
  family_contact_phone?: string;
  publish_contact_info: boolean;
  status: "draft" | "published" | "completed" | "cancelled" | "archived";
  timezone: string;
};

type MosqueDetail = {
  id: number;
  mosque_name: string;
  city: string;
  address: string;
  latitude: string;
  longitude: string;
  google_maps_url?: string | null;
  women_prayer_available: boolean;
  parking_available: boolean;
  wudu_facility_available: boolean;
  wheelchair_accessible: boolean;
  separate_women_entrance: boolean;
  mosque_status: string;
  description: string;
  contact_phone: string;
  website: string;
  mosque_type: string;
  prayer_timing?: PrayerTiming | null;
  operating_status?: OperatingStatus | null;
  distance?: number | null;
  photos?: PhotoState[] | null;
  announcements?: AnnouncementState[] | null;
  events?: EventState[] | null;
  schedules?: CommunityScheduleState[] | null;
  janazah_notices?: JanazahNoticeState[] | null;
};

const formatTimeTo12Hour = (timeStr?: string | null) => {
  if (!timeStr) return "Not set";
  const parts = timeStr.split(":");
  if (parts.length < 2) return timeStr;
  let hour = parseInt(parts[0], 10);
  const minute = parts[1];
  const ampm = hour >= 12 ? "PM" : "AM";
  hour = hour % 12;
  hour = hour ? hour : 12;
  return `${hour}:${minute} ${ampm}`;
};

const formatClassification = (typeStr?: string) => {
  if (!typeStr) return "Mosque";
  switch (typeStr) {
    case "jama_masjid":
      return "Jama Masjid (Juma Mosque)";
    case "daily_prayer":
      return "Daily Prayer Hall";
    case "musallah":
      return "Musallah (Prayer Room)";
    default:
      return "Mosque";
  }
};

const formatJanazahDate = (dateStr: string) => {
  if (!dateStr) return "";
  try {
    const dateObj = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    const isToday = dateObj.toDateString() === today.toDateString();
    const isTomorrow = dateObj.toDateString() === tomorrow.toDateString();

    const dayName = dateObj.toLocaleDateString(undefined, { weekday: "long" });
    const formattedDate = dateObj.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric"
    });

    if (isToday) return `Today (${dayName}), ${formattedDate}`;
    if (isTomorrow) return `Tomorrow (${dayName}), ${formattedDate}`;
    return `${dayName}, ${formattedDate}`;
  } catch (e) {
    return dateStr;
  }
};

export default function MosqueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [mosque, setMosque] = useState<MosqueDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"announcements" | "events" | "janazah">("announcements");
  const [showFuneralGuide, setShowFuneralGuide] = useState(false);

  // Retrieve user location on mount if granted
  useEffect(() => {
    if (typeof window !== "undefined" && "geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCoords({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
        },
        () => {},
        { timeout: 5000 }
      );
    }
  }, []);

  // Keyboard navigation for Lightbox
  useEffect(() => {
    if (selectedPhotoIndex === null || !mosque?.photos) return;
    
    const photos = mosque.photos;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedPhotoIndex(null);
      } else if (e.key === "ArrowLeft" && selectedPhotoIndex > 0) {
        setSelectedPhotoIndex(selectedPhotoIndex - 1);
      } else if (e.key === "ArrowRight" && selectedPhotoIndex < photos.length - 1) {
        setSelectedPhotoIndex(selectedPhotoIndex + 1);
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [selectedPhotoIndex, mosque?.photos]);

  // Fetch Mosque details
  useEffect(() => {
    if (!id) return;
    let isMounted = true;

    async function fetchDetail() {
      setLoading(true);
      try {
        let path = `/mosques/${id}/`;
        if (coords) {
          path += `?lat=${coords.lat}&lon=${coords.lon}`;
        }
        const data = await apiRequest<MosqueDetail>({ path, cache: "no-store" });
        if (isMounted) {
          setMosque(data);
          setError("");
        }
      } catch (err) {
        if (isMounted) {
          setError("Failed to load mosque details. Please verify the URL or try again later.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchDetail();

    return () => {
      isMounted = false;
    };
  }, [id, coords]);

  const formatDistance = (meters?: number | null) => {
    if (meters === undefined || meters === null) return "";
    if (meters < 1000) {
      return `${Math.round(meters)} meters away`;
    }
    return `${(meters / 1000).toFixed(1)} km away`;
  };

  const getStatusBadge = (status?: OperatingStatus | null) => {
    if (!status) return null;
    switch (status.status_label) {
      case "Open 24 Hours":
        return <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 border border-emerald-200">🟢 Open 24 Hours</span>;
      case "Open Now":
        return <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 border border-emerald-200">🟢 Open Now</span>;
      case "Closing Soon":
        return <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800 border border-amber-200">⚠️ Closing Soon</span>;
      case "Schedule Not Verified":
        return <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600 border border-slate-200">⚪ Schedule Unverified</span>;
      case "Closed":
      default:
        return <span className="inline-flex rounded-full bg-red-100 px-3 py-1 text-xs font-bold text-red-800 border border-red-200">🔴 Closed</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F7F5]">
        <p className="text-slate-500 font-semibold">Loading mosque profile...</p>
      </div>
    );
  }

  if (error || !mosque) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#F4F7F5] px-4 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Mosque Not Found</h1>
        <p className="mt-2 text-slate-600 max-w-md">{error || "The requested mosque could not be resolved."}</p>
        <Link
          href="/"
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white hover:bg-emerald-900"
        >
          Return to home page
        </Link>
      </div>
    );
  }

  const directionUrl = mosque.google_maps_url
    ? mosque.google_maps_url
    : (mosque.latitude && mosque.longitude
        ? `https://www.google.com/maps/dir/?api=1&destination=${mosque.latitude},${mosque.longitude}`
        : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mosque.mosque_name + " " + mosque.city)}`);

  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Back navigation */}
        <Link href="/" className="inline-flex items-center text-sm font-bold text-emerald-800 hover:text-emerald-950 transition-colors">
          ← Back to discovery
        </Link>

        {/* 1. Header Card */}
        <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
            <div className="space-y-2">
              <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {formatClassification(mosque.mosque_type)}
              </span>
              <h1 className="text-3xl font-bold tracking-tight text-slate-950">
                {mosque.mosque_name}
              </h1>
              <p className="text-sm text-slate-600 leading-relaxed font-normal">
                {mosque.address ? `${mosque.address}, ` : ""}{mosque.city}
              </p>
              {mosque.distance !== undefined && mosque.distance !== null && (
                <p className="text-sm font-semibold text-emerald-800">
                  📍 Distance: {formatDistance(mosque.distance)}
                </p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2.5 md:flex-col md:items-end">
              {getStatusBadge(mosque.operating_status)}
              {mosque.operating_status?.is_open ? (
                mosque.operating_status.closes_at && (
                  <p className="text-xs text-slate-500 font-medium">Closes at {mosque.operating_status.closes_at}</p>
                )
              ) : (
                mosque.operating_status?.opens_at && (
                  <p className="text-xs text-slate-500 font-medium">Opens at {mosque.operating_status.opens_at}</p>
                )
              )}
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3 border-t border-slate-100 pt-6">
            <a
              href={directionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-11 items-center justify-center rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white hover:bg-emerald-900 transition focus:outline-none focus:ring-4 focus:ring-emerald-800/20"
            >
              Get Directions
            </a>
            {mosque.contact_phone && (
              <a
                href={`tel:${mosque.contact_phone}`}
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-slate-200 bg-white px-6 text-sm font-semibold text-slate-800 hover:bg-slate-50 transition"
              >
                Call Mosque
              </a>
            )}
            {mosque.website && (
              <a
                href={mosque.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-slate-200 bg-white px-6 text-sm font-semibold text-slate-800 hover:bg-slate-50 transition"
              >
                Visit Website
              </a>
            )}
          </div>
        </section>

        {/* 2. Photo Gallery */}
        <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-950">Photo Gallery</h2>
          {mosque.photos && mosque.photos.length > 0 ? (
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              {mosque.photos.map((photo, index) => (
                <button
                  key={photo.id}
                  onClick={() => setSelectedPhotoIndex(index)}
                  className="group relative aspect-video block w-full text-left overflow-hidden rounded-xl border border-slate-100 bg-slate-50 transition duration-300 hover:scale-[1.02] hover:shadow-md focus:outline-none focus:ring-2 focus:ring-emerald-800/20"
                  aria-label={photo.title ? `View ${photo.title}` : "View gallery image"}
                >
                  <img
                    src={photo.image}
                    alt={photo.title || "Mosque Photo"}
                    className="h-full w-full object-cover"
                  />
                  {(photo.title || photo.caption) && (
                    <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/80 via-black/20 to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                      {photo.title && <p className="text-xs font-bold text-white line-clamp-1">{photo.title}</p>}
                      {photo.caption && <p className="text-[10px] text-slate-200 line-clamp-2 mt-0.5">{photo.caption}</p>}
                    </div>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="mt-4 flex min-h-[140px] items-center justify-center rounded-xl bg-slate-50/50 border border-dashed border-slate-200 text-center p-6 text-slate-400">
              <div>
                <span className="block text-2xl mb-1">📸</span>
                <p className="text-sm font-medium">No photos have been uploaded for this mosque yet.</p>
              </div>
            </div>
          )}
        </section>

        <div className="grid gap-6 md:grid-cols-[1fr_320px]">
          {/* Main Info Columns */}
          <div className="space-y-6">
            {/* Active Announcements */}
            {/* Active Janazah Notices (Red-Bordered Box) */}
            {mosque.janazah_notices && mosque.janazah_notices.filter(n => n.status === "published").length > 0 && (
              <section className="rounded-2xl border-2 border-red-500 bg-red-50/10 p-6 shadow-md space-y-4">
                <div className="flex items-center gap-2 border-b border-red-100 pb-3">
                  <span className="text-2xl animate-pulse">🚨</span>
                  <div>
                    <h2 className="text-lg font-bold text-red-950">Active Janazah Announcements</h2>
                    <p className="text-xs text-red-700/80">Please keep the deceased and their families in your prayers.</p>
                  </div>
                </div>
                <div className="space-y-6">
                  {mosque.janazah_notices
                    .filter(n => n.status === "published")
                    .map((notice) => {
                      const shareText = `*Janazah Announcement*\n*Deceased:* ${notice.deceased_name} (${notice.gender === "male" ? "Male" : "Female"}${notice.age ? `, Age: ${notice.age}` : ""})\n*Inna lillahi wa inna ilayhi raji'un*\n\n*Janazah Salah:*\nDate: ${formatJanazahDate(notice.salah_date)}\nTime: ${formatTimeTo12Hour(notice.salah_time)}\nLocation: ${notice.salah_details || mosque.mosque_name}\n\n*Burial Details:*\nDate: ${notice.burial_date ? formatJanazahDate(notice.burial_date) : "N/A"}\nTime: ${notice.burial_time ? formatTimeTo12Hour(notice.burial_time) : "N/A"}\nCemetery: ${notice.cemetery_name || "N/A"}\n${notice.cemetery_address ? `Address: ${notice.cemetery_address}` : ""}\n\nDetails: ${typeof window !== "undefined" ? window.location.origin + "/mosque/" + mosque.id : ""}`;
                      const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`;

                      return (
                        <div key={notice.id} className="rounded-xl border border-red-200 bg-white p-5 shadow-sm space-y-3.5">
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-50 pb-2.5">
                            <span className="font-serif italic text-sm text-slate-500 font-medium">Inna lillahi wa inna ilayhi raji'un</span>
                            <span className="text-xs font-bold bg-red-100 text-red-800 px-2 py-0.5 rounded-full">
                              Janazah Prayer
                            </span>
                          </div>
                          
                          <div className="grid gap-3 sm:grid-cols-2 text-sm">
                            <div className="space-y-1">
                              <span className="text-slate-500 text-xs block font-medium">Deceased Details</span>
                              <span className="font-bold text-slate-900 text-base">{notice.deceased_name}</span>
                              <span className="text-slate-600 block font-normal">
                                {notice.gender === "male" ? "Male" : "Female"}
                                {notice.age ? `, Age: ${notice.age}` : ""}
                              </span>
                              <span className="text-slate-500 text-xs block mt-1">Passed away: {formatJanazahDate(notice.date_of_death)}</span>
                            </div>

                            <div className="space-y-1">
                              <span className="text-slate-500 text-xs block font-medium">Janazah Salah</span>
                              <span className="font-semibold text-slate-800 block">
                                📅 {formatJanazahDate(notice.salah_date)}
                              </span>
                              <span className="font-bold text-slate-900 block font-mono">
                                🕒 {formatTimeTo12Hour(notice.salah_time)}
                              </span>
                              {notice.salah_details && (
                                <span className="text-slate-600 block text-xs bg-slate-50 p-1.5 rounded font-normal leading-snug">
                                  📍 {notice.salah_details}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="border-t border-slate-100 pt-3 text-sm grid gap-3 sm:grid-cols-2">
                            <div className="space-y-1">
                              <span className="text-slate-500 text-xs block font-medium">Burial Details</span>
                              {notice.cemetery_name ? (
                                <>
                                  <span className="font-semibold text-slate-800 block">
                                    {notice.cemetery_name}
                                  </span>
                                  {notice.cemetery_address && (
                                    <span className="text-slate-600 text-xs block font-normal leading-tight">
                                      {notice.cemetery_address}
                                    </span>
                                  )}
                                  <span className="text-slate-600 text-xs block font-mono font-medium">
                                    Time: {notice.burial_date ? formatJanazahDate(notice.burial_date) : ""} @ {notice.burial_time ? formatTimeTo12Hour(notice.burial_time) : "Not set"}
                                  </span>
                                </>
                              ) : (
                                <span className="text-slate-400 italic text-xs">Cemetery details pending</span>
                              )}
                            </div>

                            <div className="flex flex-col justify-end gap-2">
                              {notice.cemetery_gps_url && (
                                <a
                                  href={notice.cemetery_gps_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center justify-center rounded-xl bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition"
                                >
                                  📍 View Cemetery Location on Map
                                </a>
                              )}
                            </div>
                          </div>

                          {/* Family contacts */}
                          {notice.publish_contact_info && (notice.family_contact_name || notice.family_contact_phone) && (
                            <div className="border-t border-slate-100 pt-3 text-xs text-slate-600 leading-normal font-medium flex flex-wrap gap-2">
                              <span className="text-slate-600">Family Contact:</span>
                              <span className="text-slate-800 font-bold">{notice.family_contact_name || "Family Representative"}</span>
                              {notice.family_contact_phone && (
                                <a href={`tel:${notice.family_contact_phone}`} className="text-emerald-800 hover:underline font-bold">
                                  ({notice.family_contact_phone})
                                </a>
                              )}
                            </div>
                          )}

                          <div className="mt-3.5 flex flex-wrap gap-2 pt-2 border-t border-slate-100">
                            <a
                              href={whatsappUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-600 hover:bg-emerald-700 px-4 py-1.5 text-xs font-bold text-white transition focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                            >
                              Share to WhatsApp
                            </a>
                            <button
                              onClick={() => setShowFuneralGuide(true)}
                              className="inline-flex min-h-9 items-center justify-center rounded-full border border-slate-200 bg-white hover:bg-slate-50 px-4 py-1.5 text-xs font-bold text-slate-700 transition"
                            >
                              View Funeral Guide
                            </button>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </section>
            )}

            {/* 3. Congregation Timings */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-950">Congregation (Jamaat) Timings</h2>
              <p className="mt-1 text-xs text-slate-500">Public verified timings for congregational prayer times.</p>
              
              {mosque.prayer_timing ? (
                <div className="mt-5 space-y-3.5">
                  {[
                    { name: "Fajr", time: mosque.prayer_timing.fajr_time },
                    { name: "Dhuhr", time: mosque.prayer_timing.dhuhr_time },
                    { name: "Asr", time: mosque.prayer_timing.asr_time },
                    { name: "Maghrib", time: mosque.prayer_timing.maghrib_time },
                    { name: "Isha", time: mosque.prayer_timing.isha_time },
                    { name: "Jumuah", time: mosque.prayer_timing.jumuah_time },
                  ].map((p) => (
                    <div key={p.name} className="flex items-center justify-between border-b border-slate-50 pb-2.5 last:border-0 last:pb-0">
                      <span className="text-sm font-semibold text-slate-700">{p.name}</span>
                      <span className="font-mono text-sm font-bold text-slate-950">{formatTimeTo12Hour(p.time)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-5 rounded-xl bg-slate-50 py-8 text-center text-sm text-slate-500 font-medium">
                  No congregation timings configured yet.
                </div>
              )}
            </section>

            {/* Community Section (Unified Tabs: Announcements, Events, Janazah Notices) */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm space-y-5">
              <div className="border-b border-slate-100 pb-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-slate-950">Community Hub</h2>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    onClick={() => setActiveTab("announcements")}
                    className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                      activeTab === "announcements"
                        ? "bg-emerald-800 text-white"
                        : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    Announcements ({mosque.announcements?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("events")}
                    className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                      activeTab === "events"
                        ? "bg-emerald-800 text-white"
                        : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    Upcoming Events ({mosque.events?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("janazah")}
                    className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                      activeTab === "janazah"
                        ? "bg-emerald-800 text-white"
                        : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    Janazah Notices ({mosque.janazah_notices?.filter(n => n.status === "published").length || 0})
                  </button>
                </div>
              </div>

              {/* Tab Contents */}
              <div className="space-y-4">
                {activeTab === "announcements" && (
                  <>
                    {mosque.announcements && mosque.announcements.length > 0 ? (
                      <div className="space-y-4">
                        {mosque.announcements.map((announcement) => {
                          let priorityStyle = "";
                          let badgeText = "";
                          switch (announcement.priority) {
                            case "urgent":
                              priorityStyle = "border-red-500 bg-red-50/40 text-red-950";
                              badgeText = "🔴 Urgent";
                              break;
                            case "important":
                              priorityStyle = "border-amber-500 bg-amber-50/40 text-amber-950";
                              badgeText = "⚠️ Important";
                              break;
                            default:
                              priorityStyle = "border-slate-200 bg-slate-50/50 text-slate-900";
                              badgeText = "📋 Notice";
                              break;
                          }
                          return (
                            <div
                              key={announcement.id}
                              className={`rounded-xl border-l-4 border p-4 shadow-sm transition hover:shadow-md ${priorityStyle}`}
                            >
                              <div className="flex items-start justify-between gap-4">
                                <h3 className="font-bold text-md">{announcement.title}</h3>
                                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-white/80 border border-slate-900/5">
                                  {badgeText}
                                </span>
                              </div>
                              <p className="mt-2 text-sm leading-relaxed whitespace-pre-line text-slate-700 font-normal">
                                {announcement.content}
                              </p>
                              {announcement.created_at && (
                                <div className="mt-3 text-[10px] text-slate-500 font-medium">
                                  Posted on {new Date(announcement.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex min-h-[140px] items-center justify-center rounded-xl bg-slate-50/50 border border-dashed border-slate-200 text-center p-6 text-slate-400">
                        <div>
                          <span className="block text-2xl mb-1">📢</span>
                          <p className="text-sm font-medium">No active announcements at the moment.</p>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {activeTab === "events" && (
                  <>
                    {mosque.events && mosque.events.length > 0 ? (
                      <div className="space-y-4">
                        {mosque.events.map((event) => {
                          let eventBadgeColor = "bg-emerald-50 text-emerald-800 border-emerald-100";
                          let eventTypeLabel = "Event";
                          switch (event.event_type) {
                            case "lecture":
                              eventBadgeColor = "bg-blue-50 text-blue-800 border-blue-100";
                              eventTypeLabel = "Lecture";
                              break;
                            case "dars":
                              eventBadgeColor = "bg-indigo-50 text-indigo-800 border-indigo-100";
                              eventTypeLabel = "Dars";
                              break;
                            case "youth_program":
                              eventBadgeColor = "bg-purple-50 text-purple-800 border-purple-100";
                              eventTypeLabel = "Youth Program";
                              break;
                            case "community_meeting":
                              eventBadgeColor = "bg-sky-50 text-sky-800 border-sky-100";
                              eventTypeLabel = "Community Meeting";
                              break;
                            case "fundraiser":
                              eventBadgeColor = "bg-pink-50 text-pink-800 border-pink-100";
                              eventTypeLabel = "Fundraiser";
                              break;
                            case "ramadan":
                              eventBadgeColor = "bg-amber-50 text-amber-800 border-amber-100";
                              eventTypeLabel = "Ramadan Program";
                              break;
                            case "eid":
                              eventBadgeColor = "bg-orange-50 text-orange-800 border-orange-100";
                              eventTypeLabel = "Eid Event";
                              break;
                            default:
                              eventBadgeColor = "bg-slate-50 text-slate-800 border-slate-100";
                              eventTypeLabel = "Other Activity";
                              break;
                          }

                          const eventDateObj = new Date(event.event_date);
                          const formattedDate = eventDateObj.toLocaleDateString(undefined, {
                            weekday: 'long',
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          });

                          return (
                            <div
                              key={event.id}
                              className="rounded-xl border border-slate-100 bg-slate-50/30 p-4 transition duration-200 hover:border-emerald-800/10 hover:bg-slate-50/70"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2.5">
                                <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${eventBadgeColor}`}>
                                  {eventTypeLabel}
                                </span>
                                <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
                                  📅 {formattedDate} @ {formatTimeTo12Hour(event.event_time)}
                                </span>
                              </div>
                              <h3 className="mt-2 text-md font-bold text-slate-900">{event.title}</h3>
                              {event.description && (
                                <p className="mt-1.5 text-sm text-slate-600 leading-relaxed font-normal whitespace-pre-line">
                                  {event.description}
                                </p>
                              )}
                              
                              {(event.speaker_name || event.event_location) && (
                                <div className="mt-3.5 flex flex-wrap items-center gap-4 text-xs text-slate-500 font-medium border-t border-slate-100/80 pt-3">
                                  {event.speaker_name && (
                                    <span className="flex items-center gap-1">
                                      👤 <strong className="text-slate-700">Speaker:</strong> {event.speaker_name}
                                    </span>
                                  )}
                                  {event.event_location && (
                                    <span className="flex items-center gap-1">
                                      📍 <strong className="text-slate-700">Location:</strong> {event.event_location}
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex min-h-[140px] items-center justify-center rounded-xl bg-slate-50/50 border border-dashed border-slate-200 text-center p-6 text-slate-400">
                        <div>
                          <span className="block text-2xl mb-1">📅</span>
                          <p className="text-sm font-medium">No upcoming events scheduled at the moment.</p>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {activeTab === "janazah" && (
                  <>
                    {mosque.janazah_notices && mosque.janazah_notices.filter(n => n.status === "published").length > 0 ? (
                      <div className="space-y-4">
                        {mosque.janazah_notices
                          .filter(n => n.status === "published")
                          .map((notice) => {
                            const shareText = `*Janazah Announcement*\n*Deceased:* ${notice.deceased_name} (${notice.gender === "male" ? "Male" : "Female"}${notice.age ? `, Age: ${notice.age}` : ""})\n*Inna lillahi wa inna ilayhi raji'un*\n\n*Janazah Salah:*\nDate: ${formatJanazahDate(notice.salah_date)}\nTime: ${formatTimeTo12Hour(notice.salah_time)}\nLocation: ${notice.salah_details || mosque.mosque_name}\n\n*Burial Details:*\nDate: ${notice.burial_date ? formatJanazahDate(notice.burial_date) : "N/A"}\nTime: ${notice.burial_time ? formatTimeTo12Hour(notice.burial_time) : "N/A"}\nCemetery: ${notice.cemetery_name || "N/A"}\n${notice.cemetery_address ? `Address: ${notice.cemetery_address}` : ""}\n\nDetails: ${typeof window !== "undefined" ? window.location.origin + "/mosque/" + mosque.id : ""}`;
                            const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`;

                            return (
                              <div key={notice.id} className="rounded-xl border border-slate-100 bg-slate-50/30 p-4 transition duration-200 hover:border-emerald-800/10 hover:bg-slate-50/70 space-y-3">
                                <div className="flex flex-wrap items-center justify-between gap-2.5">
                                  <span className="inline-flex items-center rounded-full border border-red-100 bg-red-50 px-2.5 py-0.5 text-[10px] font-bold text-red-800">
                                    Janazah Notice
                                  </span>
                                  <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                                    📅 Passed away: {formatJanazahDate(notice.date_of_death)}
                                  </span>
                                </div>
                                
                                <h3 className="mt-2 text-md font-bold text-slate-900">
                                  {notice.deceased_name} ({notice.gender === "male" ? "Male" : "Female"}{notice.age ? `, Age: ${notice.age}` : ""})
                                </h3>

                                <div className="grid gap-3 sm:grid-cols-2 text-xs text-slate-600">
                                  <div className="space-y-1 bg-white/50 p-2.5 rounded-lg border border-slate-100/50">
                                    <strong className="text-slate-800 block text-xs">🕌 Janazah Salah:</strong>
                                    <span>Date: {formatJanazahDate(notice.salah_date)}</span>
                                    <span className="block font-semibold">Time: {formatTimeTo12Hour(notice.salah_time)}</span>
                                    {notice.salah_details && <span className="block">Details: {notice.salah_details}</span>}
                                  </div>

                                  <div className="space-y-1 bg-white/50 p-2.5 rounded-lg border border-slate-100/50">
                                    <strong className="text-slate-800 block text-xs">🪦 Burial / Cemetery:</strong>
                                    {notice.cemetery_name ? (
                                      <>
                                        <span>Cemetery: {notice.cemetery_name}</span>
                                        {notice.cemetery_address && <span className="block">Address: {notice.cemetery_address}</span>}
                                        <span className="block font-semibold">Time: {notice.burial_date ? formatJanazahDate(notice.burial_date) : ""} @ {notice.burial_time ? formatTimeTo12Hour(notice.burial_time) : "Not set"}</span>
                                      </>
                                    ) : (
                                      <span className="text-slate-400 italic">Cemetery details pending</span>
                                    )}
                                  </div>
                                </div>

                                {notice.publish_contact_info && (notice.family_contact_name || notice.family_contact_phone) && (
                                  <div className="text-xs text-slate-600 pt-2 border-t border-slate-100/65 flex flex-wrap gap-2">
                                    <span>Family Contact:</span>
                                    <strong className="text-slate-700">{notice.family_contact_name || "Family Representative"}</strong>
                                    {notice.family_contact_phone && (
                                      <a href={`tel:${notice.family_contact_phone}`} className="text-emerald-800 hover:underline">
                                        ({notice.family_contact_phone})
                                      </a>
                                    )}
                                  </div>
                                )}

                                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100/50">
                                  <a
                                    href={whatsappUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex min-h-8 items-center justify-center rounded-full bg-emerald-600 hover:bg-emerald-700 px-3 text-[11px] font-bold text-white transition focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                                  >
                                    Share to WhatsApp
                                  </a>
                                  {notice.cemetery_gps_url && (
                                    <a
                                      href={notice.cemetery_gps_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex min-h-8 items-center justify-center rounded-full border border-slate-200 bg-white hover:bg-slate-50 px-3 text-[11px] font-bold text-slate-700 transition"
                                    >
                                      Map Location
                                    </a>
                                  )}
                                  <button
                                    onClick={() => setShowFuneralGuide(true)}
                                    className="inline-flex min-h-8 items-center justify-center rounded-full border border-slate-200 bg-white hover:bg-slate-50 px-3 text-[11px] font-bold text-slate-700 transition"
                                  >
                                    Funeral Guide
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    ) : (
                      <div className="flex min-h-[140px] items-center justify-center rounded-xl bg-slate-50/50 border border-dashed border-slate-200 text-center p-6 text-slate-400">
                        <div>
                          <span className="block text-2xl mb-1">🖤</span>
                          <p className="text-sm font-medium">No active Janazah notices at the moment.</p>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </section>

            {/* Weekly Lectures & Friday Sermons Schedules */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-950">Weekly Lectures & Friday Sermons</h2>
              <p className="mt-1 text-xs text-slate-500">Timetables for upcoming Friday sermons (Khutbah) and weekly lectures (Dars).</p>

              {mosque.schedules && mosque.schedules.length > 0 ? (
                <div className="mt-5 space-y-4">
                  {mosque.schedules.map((schedule) => {
                    const isKhutbah = schedule.schedule_type === "khutbah";
                    const badgeColor = isKhutbah
                      ? "bg-emerald-50 text-emerald-800 border-emerald-100"
                      : "bg-blue-50 text-blue-800 border-blue-100";
                    const label = isKhutbah ? "Friday Khutbah" : "Weekly Dars";
                    
                    const dateObj = new Date(schedule.event_date);
                    const formattedDate = dateObj.toLocaleDateString(undefined, {
                      weekday: 'long',
                      month: 'short',
                      day: 'numeric',
                    });

                    return (
                      <div
                        key={schedule.id}
                        className="rounded-xl border border-slate-100 bg-slate-50/30 p-4 transition duration-200 hover:border-emerald-800/10 hover:bg-slate-50/70"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2.5">
                          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${badgeColor}`}>
                            {label}
                          </span>
                          <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                            🕒 {formattedDate} @ {formatTimeTo12Hour(schedule.start_time)}
                          </span>
                        </div>
                        <h3 className="mt-2 text-md font-bold text-slate-900">
                          {schedule.topic || (isKhutbah ? "Friday Sermon" : "Lecture")}
                        </h3>
                        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500 font-medium">
                          <span className="flex items-center gap-1">
                            👤 <strong className="text-slate-700">Speaker:</strong> {schedule.speaker}
                          </span>
                          {isKhutbah && schedule.extended_data?.shift_number && (
                            <span className="flex items-center gap-1">
                              🔄 <strong className="text-slate-700">Shift:</strong> {schedule.extended_data.shift_number}
                            </span>
                          )}
                          {schedule.extended_data?.language && (
                            <span className="flex items-center gap-1">
                              🌐 <strong className="text-slate-700">Language:</strong> {schedule.extended_data.language}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="mt-5 rounded-xl bg-slate-50 py-8 text-center text-sm text-slate-500 font-medium">
                  No lectures or sermon details scheduled yet.
                </div>
              )}
            </section>

            {/* 4. Facilities Checklist */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-950">Facilities & Accommodation</h2>
              <p className="mt-1 text-xs text-slate-500">Accommodations supported by this mosque.</p>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {[
                  { name: "Women's Prayer Space", status: mosque.women_prayer_available, icon: "🚺" },
                  { name: "Separate Ladies Entrance", status: mosque.separate_women_entrance, icon: "🚪" },
                  { name: "Dedicated Parking Area", status: mosque.parking_available, icon: "🚗" },
                  { name: "Ablution (Wudu) Space", status: mosque.wudu_facility_available, icon: "💧" },
                  { name: "Wheelchair Accessibility", status: mosque.wheelchair_accessible, icon: "♿" },
                ].map((f) => (
                  <div key={f.name} className="flex items-center gap-2.5 rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-sm">
                    <span className="text-lg">{f.icon}</span>
                    <div className="flex-1">
                      <span className="block font-semibold text-slate-800 leading-tight">{f.name}</span>
                    </div>
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold ${f.status ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-400"}`}>
                      {f.status ? "Available" : "No"}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Sidebar Columns */}
          <div className="space-y-6">
            {/* 5. Operating Schedule Windows */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm">
              <h2 className="text-md font-bold text-slate-950">Operating Schedule</h2>
              <p className="mt-0.5 text-[11px] text-slate-500">Opening hours and public windows.</p>

              {mosque.operating_status?.status_label === "Open 24 Hours" ? (
                <div className="mt-4 rounded-xl bg-emerald-50/50 border border-emerald-100 p-4 text-center">
                  <p className="text-sm font-bold text-emerald-800">Open 24 Hours</p>
                  <p className="text-[11px] text-emerald-600 mt-0.5">The building is open continuously.</p>
                </div>
              ) : (
                <div className="mt-4 space-y-3.5">
                  {/* We resolve the operating hours if not 24 hours */}
                  {/* Let's show the windows if available */}
                  {mosque.operating_status?.status_label === "Schedule Not Verified" ? (
                    <div className="rounded-xl bg-slate-50 py-6 text-center text-xs text-slate-400">
                      No schedule configured yet.
                    </div>
                  ) : (
                    <div className="space-y-3 font-sans">
                      {/* For now, detail pages can show a message or list timing blocks */}
                      <p className="text-xs text-slate-600 leading-relaxed font-normal">
                        This mosque operates during specific prayer windows. Check active open hours.
                      </p>
                      {/* Quick lookup helper */}
                      {mosque.operating_status?.opens_at && (
                        <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100 flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-600">Next Opening:</span>
                          <span className="font-bold text-slate-950 font-mono">{mosque.operating_status.opens_at}</span>
                        </div>
                      )}
                      {mosque.operating_status?.closes_at && (
                        <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100 flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-600">Active Closing:</span>
                          <span className="font-bold text-slate-950 font-mono">{mosque.operating_status.closes_at}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* 6. About Mosque Panel */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm">
              <h2 className="text-md font-bold text-slate-950">About Mosque</h2>
              <p className="mt-2 text-xs text-slate-700 leading-relaxed font-normal whitespace-pre-line">
                {mosque.description || "No description has been posted by the administrator yet."}
              </p>
            </section>
          </div>
        </div>
      </div>

      {/* Lightbox Modal */}
      {selectedPhotoIndex !== null && mosque.photos && mosque.photos[selectedPhotoIndex] && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/90 p-4 backdrop-blur-sm transition-all duration-300 animate-in fade-in">
          {/* Close button */}
          <button
            onClick={() => setSelectedPhotoIndex(null)}
            className="absolute top-4 right-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition cursor-pointer"
            aria-label="Close Lightbox"
          >
            ✕
          </button>

          {/* Image Container */}
          <div className="relative flex max-h-[80vh] max-w-full items-center justify-center">
            {/* Prev button */}
            {selectedPhotoIndex > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPhotoIndex(selectedPhotoIndex - 1);
                }}
                className="absolute left-4 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition cursor-pointer"
                aria-label="Previous Photo"
              >
                ‹
              </button>
            )}

            <img
              src={mosque.photos[selectedPhotoIndex].image}
              alt={mosque.photos[selectedPhotoIndex].title || "Full Mosque Photo"}
              className="max-h-[75vh] max-w-[90vw] object-contain rounded-lg shadow-2xl"
            />

            {/* Next button */}
            {selectedPhotoIndex < mosque.photos.length - 1 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPhotoIndex(selectedPhotoIndex + 1);
                }}
                className="absolute right-4 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition cursor-pointer"
                aria-label="Next Photo"
              >
                ›
              </button>
            )}
          </div>

          {/* Info bar */}
          {(mosque.photos[selectedPhotoIndex].title || mosque.photos[selectedPhotoIndex].caption) && (
            <div className="mt-4 text-center text-white max-w-xl px-4">
              {mosque.photos[selectedPhotoIndex].title && (
                <h4 className="text-lg font-bold">{mosque.photos[selectedPhotoIndex].title}</h4>
              )}
              {mosque.photos[selectedPhotoIndex].caption && (
                <p className="mt-1 text-sm text-slate-300 leading-relaxed font-normal">
                  {mosque.photos[selectedPhotoIndex].caption}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Funeral Guide Modal */}
      {showFuneralGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
            <button
              onClick={() => setShowFuneralGuide(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition cursor-pointer"
              aria-label="Close Guide"
            >
              ✕
            </button>
            <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              📖 Janazah Salah Guide
            </h3>
            <p className="mt-2 text-xs text-slate-500 font-medium">
              A brief step-by-step guide on how to perform the funeral prayer (Salah al-Janazah).
            </p>
            
            <div className="mt-4 space-y-4 max-h-[60vh] overflow-y-auto pr-2 text-sm text-slate-700 leading-relaxed font-normal">
              <div>
                <strong className="text-emerald-800">1. Intention (Niyyah) & First Takbeer</strong>
                <p className="mt-1">
                  Stand facing the Qiblah and form the intention to pray Salah al-Janazah for the deceased. When the Imam says the first takbeer ("Allahu Akbar"), raise your hands to your ears (or shoulders), tie them over your chest, and silently recite <em>Sana</em>:
                </p>
                <p className="mt-1 bg-slate-50 p-2 rounded text-xs font-serif italic border-l-2 border-emerald-800">
                  Subhanaka Allahumma wa bihamdika, wa tabarakasmuka, wa ta'ala jadduka, wa jalla thana'uka, wa la ilaha ghayruk.
                </p>
              </div>

              <div>
                <strong className="text-emerald-800">2. Second Takbeer & Durood</strong>
                <p className="mt-1">
                  Upon the second takbeer, recite <em>Durood Ibrahim</em> (the salutation upon the Prophet, peace be upon him) silently, without raising your hands:
                </p>
                <p className="mt-1 bg-slate-50 p-2 rounded text-xs font-serif italic border-l-2 border-emerald-800">
                  Allahumma salli 'ala Muhammadin wa 'ala ali Muhammadin, kama sallayta 'ala Ibrahima wa 'ala ali Ibrahima, innaka Hamidun Majid...
                </p>
              </div>

              <div>
                <strong className="text-emerald-800">3. Third Takbeer & Dua for the Deceased</strong>
                <p className="mt-1">
                  Upon the third takbeer, recite the supplication (Dua) for the deceased:
                </p>
                <p className="mt-1 bg-slate-50 p-2 rounded text-xs font-serif italic border-l-2 border-emerald-800">
                  Allahummaghfir li-hayyina wa mayyitina, wa shahidina wa gha'ibina, wa saghirina wa kabirina, wa dhakarina wa unthana...
                  (O Allah, forgive our living and our dead, those present and those absent, our young and our old...)
                </p>
              </div>

              <div>
                <strong className="text-emerald-800">4. Fourth Takbeer & Taslim (Salam)</strong>
                <p className="mt-1">
                  Upon the final takbeer, the Imam will say "Allahu Akbar". Pause for a moment, then perform Taslim (Salam) to the right ("Assalamu alaykum wa rahmatullah") and then to the left to complete the prayer.
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowFuneralGuide(false)}
                className="rounded-full bg-emerald-800 px-6 py-2 text-sm font-semibold text-white hover:bg-emerald-950 transition cursor-pointer"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
