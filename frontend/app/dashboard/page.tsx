"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, apiRequest } from "@/lib/api/client";

type AdminInfo = {
  mobile: string;
  mosqueName: string;
  mosqueId: string;
};

type ProfileState = {
  mosque_name: string;
  city: string;
  city_id?: number | null;
  address: string;
  description: string;
  contact_phone: string;
  website: string;
  women_prayer_available: boolean;
  parking_available: boolean;
  wudu_facility_available: boolean;
  wheelchair_accessible: boolean;
  mosque_type: string;
  separate_women_entrance: boolean;
};

type ScheduleState = {
  open_24_hours: boolean;
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
  updated_at: string;
};

type TimingsState = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  jumuah_time: string;
  effective_from: string;
  updated_at: string;
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
  id?: number;
  title: string;
  content: string;
  priority: string;
  status: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
};

type EventState = {
  id?: number;
  title: string;
  description: string;
  event_type: string;
  status: string;
  event_date: string;
  event_time: string;
  event_location: string;
  speaker_name: string;
  is_active: boolean;
};

type CommunityScheduleState = {
  id?: number;
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
  id?: number;
  deceased_name: string;
  gender: "male" | "female";
  age?: number | "" | null;
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
  version?: number;
};


const formatTimeForInput = (timeStr: string) => {
  if (!timeStr) return "";
  return timeStr.slice(0, 5);
};

const Tooltip = ({ content }: { content: string }) => {
  return (
    <span
      className="group relative ml-1 inline-block cursor-help text-slate-400 hover:text-slate-600 focus:outline-none"
      tabIndex={0}
    >
      ⓘ
      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-56 -translate-x-1/2 rounded-lg bg-slate-950 p-2 text-[10px] font-normal leading-normal text-white opacity-0 shadow-xl transition-opacity duration-150 group-hover:opacity-100 group-focus:opacity-100 group-active:opacity-100 select-none whitespace-normal">
        {content}
      </span>
    </span>
  );
};

export default function DashboardPage() {
  const router = useRouter();
  const [admin, setAdmin] = useState<AdminInfo | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    const mobile = localStorage.getItem("admin_mobile");
    const mosqueId = localStorage.getItem("admin_mosque_id");
    const mosqueName = localStorage.getItem("admin_mosque_name");
    if (token && mobile && mosqueId && mosqueName) {
      setAdmin({ mobile, mosqueId, mosqueName });
    }
    setLoadingAuth(false);
  }, []);

  // Profile Form States
  const [profile, setProfile] = useState<ProfileState>({
    mosque_name: "",
    city: "",
    city_id: null,
    address: "",
    description: "",
    contact_phone: "",
    website: "",
    women_prayer_available: false,
    parking_available: false,
    wudu_facility_available: false,
    wheelchair_accessible: false,
    mosque_type: "jama_masjid",
    separate_women_entrance: false,
  });
  const [cities, setCities] = useState<{ id: number; name: string }[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [successProfile, setSuccessProfile] = useState("");
  const [errorsProfile, setErrorsProfile] = useState<
    Partial<Record<keyof ProfileState | "non_field_errors", string>>
  >({});

  // Operating Schedule States
  const [schedule, setSchedule] = useState<ScheduleState>({
    open_24_hours: false,
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
    updated_at: "",
  });
  const [loadingSchedule, setLoadingSchedule] = useState(true);
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [successSchedule, setSuccessSchedule] = useState("");
  const [errorsSchedule, setErrorsSchedule] = useState<
    Partial<Record<keyof ScheduleState | "non_field_errors", string>>
  >({});

  // Timings States
  const [timings, setTimings] = useState<TimingsState>({
    fajr_time: "",
    dhuhr_time: "",
    asr_time: "",
    maghrib_time: "",
    isha_time: "",
    jumuah_time: "",
    effective_from: "",
    updated_at: "",
  });
  const [loadingTimings, setLoadingTimings] = useState(true);
  const [savingTimings, setSavingTimings] = useState(false);
  const [successTimings, setSuccessTimings] = useState("");
  const [errorsTimings, setErrorsTimings] = useState<
    Partial<Record<keyof TimingsState | "non_field_errors", string>>
  >({});

  // Photo states
  const [photos, setPhotos] = useState<PhotoState[]>([]);
  const [loadingPhotos, setLoadingPhotos] = useState(true);
  const [savingPhoto, setSavingPhoto] = useState(false);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [newPhotoTitle, setNewPhotoTitle] = useState("");
  const [newPhotoCaption, setNewPhotoCaption] = useState("");
  const [newPhotoOrder, setNewPhotoOrder] = useState(0);
  const [editingPhotoId, setEditingPhotoId] = useState<number | null>(null);
  const [editingPhotoTitle, setEditingPhotoTitle] = useState("");
  const [editingPhotoCaption, setEditingPhotoCaption] = useState("");
  const [editingPhotoOrder, setEditingPhotoOrder] = useState(0);
  const [editingPhotoActive, setEditingPhotoActive] = useState(true);
  const [errorPhoto, setErrorPhoto] = useState("");

  // Announcement states
  const [announcements, setAnnouncements] = useState<AnnouncementState[]>([]);
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(true);
  const [savingAnnouncement, setSavingAnnouncement] = useState(false);
  const [successAnnouncement, setSuccessAnnouncement] = useState("");
  const [errorAnnouncement, setErrorAnnouncement] = useState("");
  const [editingAnnouncementId, setEditingAnnouncementId] = useState<number | null>(null);
  const [announcementForm, setAnnouncementForm] = useState<AnnouncementState>({
    title: "",
    content: "",
    priority: "normal",
    status: "draft",
    start_date: "",
    end_date: "",
    is_active: true,
  });

  // Event states
  const [events, setEvents] = useState<EventState[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [savingEvent, setSavingEvent] = useState(false);
  const [successEvent, setSuccessEvent] = useState("");
  const [errorEvent, setErrorEvent] = useState("");
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [eventForm, setEventForm] = useState<EventState>({
    title: "",
    description: "",
    event_type: "other",
    status: "draft",
    event_date: "",
    event_time: "",
    event_location: "",
    speaker_name: "",
    is_active: true,
  });

  // Community Schedule states
  const [communitySchedules, setCommunitySchedules] = useState<CommunityScheduleState[]>([]);
  const [loadingCommunitySchedules, setLoadingCommunitySchedules] = useState(true);
  const [savingCommunitySchedule, setSavingCommunitySchedule] = useState(false);
  const [successCommunitySchedule, setSuccessCommunitySchedule] = useState("");
  const [errorCommunitySchedule, setErrorCommunitySchedule] = useState("");
  const [editingCommunityScheduleId, setEditingCommunityScheduleId] = useState<number | null>(null);
  const [errorsCommunitySchedule, setErrorsCommunitySchedule] = useState<
    Partial<Record<keyof CommunityScheduleState | "non_field_errors" | "extended_data", string>>
  >({});
  const [communityScheduleForm, setCommunityScheduleForm] = useState<CommunityScheduleState>({
    schedule_type: "khutbah",
    event_date: "",
    start_time: "",
    speaker: "",
    topic: "",
    extended_data: {
      shift_number: 1,
      language: "",
      day_of_week: 1,
    },
  });

  // Janazah states
  const [janazahs, setJanazahs] = useState<JanazahNoticeState[]>([]);
  const [loadingJanazahs, setLoadingJanazahs] = useState(true);
  const [savingJanazah, setSavingJanazah] = useState(false);
  const [successJanazah, setSuccessJanazah] = useState("");
  const [errorJanazah, setErrorJanazah] = useState("");
  const [editingJanazahId, setEditingJanazahId] = useState<number | null>(null);
  const [errorsJanazah, setErrorsJanazah] = useState<
    Partial<Record<keyof JanazahNoticeState | "non_field_errors", string>>
  >({});
  const [janazahForm, setJanazahForm] = useState<JanazahNoticeState>({
    deceased_name: "",
    gender: "male",
    age: "",
    date_of_death: "",
    salah_date: "",
    salah_time: "",
    salah_details: "",
    burial_date: "",
    burial_time: "",
    cemetery_name: "",
    cemetery_address: "",
    cemetery_gps_url: "",
    family_contact_name: "",
    family_contact_phone: "",
    publish_contact_info: false,
    status: "draft",
  });

  useEffect(() => {
    if (loadingAuth) return;

    if (!admin) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("admin_mobile");
        localStorage.removeItem("admin_mosque_id");
        localStorage.removeItem("admin_mosque_name");
      }
      router.push("/login");
      return;
    }

    let isMounted = true;

    // Load Mosque Profile & Facilities
    async function loadProfile() {
      try {
        const data = await apiRequest<ProfileState>({
          path: "/dashboard/mosque-profile/",
          method: "GET",
        });
        if (isMounted) {
          setProfile(data);
          setLoadingProfile(false);
        }
      } catch {
        if (isMounted) {
          setLoadingProfile(false);
          setErrorsProfile({
            non_field_errors: "Failed to load profile. Please try again.",
          });
        }
      }
    }

    // Load Cities List
    async function loadCities() {
      try {
        const data = await apiRequest<any>({
          path: "/locations/cities/",
          method: "GET",
        });
        if (isMounted) {
          setCities(
            Array.isArray(data)
              ? data
              : data.results || []
          );
        }
      } catch (err) {
        console.error("Failed to load cities", err);
      }
    }

    // Load Operating Schedule
    async function loadSchedule() {
      try {
        const data = await apiRequest<ScheduleState>({
          path: "/dashboard/operating-schedule/",
          method: "GET",
        });
        if (isMounted) {
          setSchedule({
            open_24_hours: data.open_24_hours,
            fajr_open: formatTimeForInput(data.fajr_open),
            fajr_close: formatTimeForInput(data.fajr_close),
            dhuhr_open: formatTimeForInput(data.dhuhr_open),
            dhuhr_close: formatTimeForInput(data.dhuhr_close),
            asr_open: formatTimeForInput(data.asr_open),
            asr_close: formatTimeForInput(data.asr_close),
            maghrib_open: formatTimeForInput(data.maghrib_open),
            maghrib_close: formatTimeForInput(data.maghrib_close),
            isha_open: formatTimeForInput(data.isha_open),
            isha_close: formatTimeForInput(data.isha_close),
            updated_at: data.updated_at,
          });
          setLoadingSchedule(false);
        }
      } catch {
        if (isMounted) {
          setLoadingSchedule(false);
          setErrorsSchedule({
            non_field_errors: "Failed to load operating schedule.",
          });
        }
      }
    }

    // Load Timings
    async function loadTimings() {
      try {
        const data = await apiRequest<TimingsState>({
          path: "/dashboard/prayer-timings/",
          method: "GET",
        });
        if (isMounted) {
          setTimings({
            fajr_time: formatTimeForInput(data.fajr_time),
            dhuhr_time: formatTimeForInput(data.dhuhr_time),
            asr_time: formatTimeForInput(data.asr_time),
            maghrib_time: formatTimeForInput(data.maghrib_time),
            isha_time: formatTimeForInput(data.isha_time),
            jumuah_time: formatTimeForInput(data.jumuah_time),
            effective_from: data.effective_from || "",
            updated_at: data.updated_at,
          });
          setLoadingTimings(false);
        }
      } catch {
        if (isMounted) {
          setLoadingTimings(false);
          setErrorsTimings({
            non_field_errors: "Failed to load timings.",
          });
        }
      }
    }

    // Load Photos
    async function loadPhotos() {
      try {
        const data = await apiRequest<PhotoState[]>({
          path: "/dashboard/photos/",
          method: "GET",
        });
        if (isMounted) {
          setPhotos(data);
          setLoadingPhotos(false);
        }
      } catch {
        if (isMounted) {
          setLoadingPhotos(false);
        }
      }
    }

    // Load Announcements
    async function loadAnnouncements() {
      try {
        const data = await apiRequest<AnnouncementState[]>({
          path: "/dashboard/announcements/",
          method: "GET",
        });
        if (isMounted) {
          setAnnouncements(data);
          setLoadingAnnouncements(false);
        }
      } catch {
        if (isMounted) {
          setLoadingAnnouncements(false);
        }
      }
    }

    // Load Events
    async function loadEvents() {
      try {
        const data = await apiRequest<EventState[]>({
          path: "/dashboard/events/",
          method: "GET",
        });
        if (isMounted) {
          setEvents(data);
          setLoadingEvents(false);
        }
      } catch {
        if (isMounted) {
          setLoadingEvents(false);
        }
      }
    }

    async function loadCommunitySchedules() {
      try {
        const data = await apiRequest<CommunityScheduleState[]>({
          path: "/dashboard/schedules/",
          method: "GET",
        });
        if (isMounted) {
          setCommunitySchedules(data);
          setLoadingCommunitySchedules(false);
        }
      } catch {
        if (isMounted) {
          setLoadingCommunitySchedules(false);
        }
      }
    }

    async function loadJanazahs() {
      try {
        const data = await apiRequest<JanazahNoticeState[]>({
          path: "/dashboard/janazah/",
          method: "GET",
        });
        if (isMounted) {
          setJanazahs(data);
          setLoadingJanazahs(false);
        }
      } catch {
        if (isMounted) {
          setLoadingJanazahs(false);
        }
      }
    }

    loadProfile();
    loadCities();
    loadSchedule();
    loadTimings();
    loadPhotos();
    loadAnnouncements();
    loadEvents();
    loadCommunitySchedules();
    loadJanazahs();

    return () => {
      isMounted = false;
    };
  }, [admin, loadingAuth, router]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("admin_mobile");
    localStorage.removeItem("admin_mosque_id");
    localStorage.removeItem("admin_mosque_name");
    router.push("/login");
  };

  // Submit profile settings
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setErrorsProfile({});
    setSuccessProfile("");

    try {
      const data = await apiRequest<ProfileState>({
        path: "/dashboard/mosque-profile/",
        method: "PUT",
        body: JSON.stringify(profile),
      });
      setProfile(data);
      setSuccessProfile("Profile updated successfully!");

      // Update name in local state if name has changed
      if (admin && data.mosque_name !== admin.mosqueName) {
        localStorage.setItem("admin_mosque_name", data.mosque_name);
        setAdmin((prev) => prev ? { ...prev, mosqueName: data.mosque_name } : null);
      }
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.details &&
        typeof err.details === "object"
      ) {
        const details = err.details as Record<string, unknown>;
        const fieldErrors: typeof errorsProfile = {};
        Object.entries(details).forEach(([k, v]) => {
          fieldErrors[k as keyof typeof errorsProfile] = Array.isArray(v)
            ? v.join(" ")
            : String(v);
        });
        setErrorsProfile(fieldErrors);
      } else {
        setErrorsProfile({
          non_field_errors: "Failed to save profile. Please try again.",
        });
      }
    } finally {
      setSavingProfile(false);
    }
  };

  // Submit operating schedule settings
  const handleSaveSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSchedule(true);
    setErrorsSchedule({});
    setSuccessSchedule("");

    // Prepare payload. Empty strings must be sent as null to django timefields
    const payload = {
      open_24_hours: schedule.open_24_hours,
      fajr_open: schedule.fajr_open || null,
      fajr_close: schedule.fajr_close || null,
      dhuhr_open: schedule.dhuhr_open || null,
      dhuhr_close: schedule.dhuhr_close || null,
      asr_open: schedule.asr_open || null,
      asr_close: schedule.asr_close || null,
      maghrib_open: schedule.maghrib_open || null,
      maghrib_close: schedule.maghrib_close || null,
      isha_open: schedule.isha_open || null,
      isha_close: schedule.isha_close || null,
    };

    try {
      const data = await apiRequest<ScheduleState>({
        path: "/dashboard/operating-schedule/",
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setSchedule({
        open_24_hours: data.open_24_hours,
        fajr_open: formatTimeForInput(data.fajr_open),
        fajr_close: formatTimeForInput(data.fajr_close),
        dhuhr_open: formatTimeForInput(data.dhuhr_open),
        dhuhr_close: formatTimeForInput(data.dhuhr_close),
        asr_open: formatTimeForInput(data.asr_open),
        asr_close: formatTimeForInput(data.asr_close),
        maghrib_open: formatTimeForInput(data.maghrib_open),
        maghrib_close: formatTimeForInput(data.maghrib_close),
        isha_open: formatTimeForInput(data.isha_open),
        isha_close: formatTimeForInput(data.isha_close),
        updated_at: data.updated_at,
      });
      setSuccessSchedule("Operating schedule updated successfully!");
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.details &&
        typeof err.details === "object"
      ) {
        const details = err.details as Record<string, unknown>;
        const fieldErrors: typeof errorsSchedule = {};
        Object.entries(details).forEach(([k, v]) => {
          fieldErrors[k as keyof typeof errorsSchedule] = Array.isArray(v)
            ? v.join(" ")
            : String(v);
        });
        setErrorsSchedule(fieldErrors);
      } else {
        setErrorsSchedule({
          non_field_errors: "Failed to save schedule. Please try again.",
        });
      }
    } finally {
      setSavingSchedule(false);
    }
  };

  // Submit timings settings
  const handleSaveTimings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingTimings(true);
    setErrorsTimings({});
    setSuccessTimings("");

    try {
      const data = await apiRequest<TimingsState>({
        path: "/dashboard/prayer-timings/",
        method: "PUT",
        body: JSON.stringify(timings),
      });
      setTimings({
        fajr_time: formatTimeForInput(data.fajr_time),
        dhuhr_time: formatTimeForInput(data.dhuhr_time),
        asr_time: formatTimeForInput(data.asr_time),
        maghrib_time: formatTimeForInput(data.maghrib_time),
        isha_time: formatTimeForInput(data.isha_time),
        jumuah_time: formatTimeForInput(data.jumuah_time),
        effective_from: data.effective_from || "",
        updated_at: data.updated_at,
      });
      setSuccessTimings("Prayer timings updated successfully!");
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.details &&
        typeof err.details === "object"
      ) {
        const details = err.details as Record<string, unknown>;
        const fieldErrors: typeof errorsTimings = {};
        Object.entries(details).forEach(([k, v]) => {
          fieldErrors[k as keyof typeof errorsTimings] = Array.isArray(v)
            ? v.join(" ")
            : String(v);
        });
        setErrorsTimings(fieldErrors);
      } else {
        setErrorsTimings({
          non_field_errors: "Failed to save timings. Please try again.",
        });
      }
    } finally {
      setSavingTimings(false);
    }
  };

  // ==========================================
  // PHOTO GALLERY HANDLERS
  // ==========================================
  const handleUploadPhoto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!photoFile) {
      setErrorPhoto("Please select an image file to upload.");
      return;
    }
    setSavingPhoto(true);
    setErrorPhoto("");

    const formData = new FormData();
    formData.append("image", photoFile);
    formData.append("title", newPhotoTitle);
    formData.append("caption", newPhotoCaption);
    formData.append("display_order", String(newPhotoOrder));
    formData.append("is_active", "true");

    try {
      await apiRequest({
        path: "/dashboard/photos/",
        method: "POST",
        body: formData,
      });
      setPhotoFile(null);
      setNewPhotoTitle("");
      setNewPhotoCaption("");
      setNewPhotoOrder(0);
      
      const updated = await apiRequest<PhotoState[]>({
        path: "/dashboard/photos/",
        method: "GET",
      });
      setPhotos(updated);
    } catch {
      setErrorPhoto("Failed to upload photo. Please verify it is a valid image.");
    } finally {
      setSavingPhoto(false);
    }
  };

  const handleStartEditPhoto = (photo: PhotoState) => {
    setEditingPhotoId(photo.id);
    setEditingPhotoTitle(photo.title);
    setEditingPhotoCaption(photo.caption);
    setEditingPhotoOrder(photo.display_order);
    setEditingPhotoActive(photo.is_active);
  };

  const handleSaveEditPhoto = async (id: number) => {
    try {
      await apiRequest({
        path: `/dashboard/photos/${id}/`,
        method: "PATCH",
        body: JSON.stringify({
          title: editingPhotoTitle,
          caption: editingPhotoCaption,
          display_order: editingPhotoOrder,
          is_active: editingPhotoActive,
        }),
      });
      setEditingPhotoId(null);
      const updated = await apiRequest<PhotoState[]>({
        path: "/dashboard/photos/",
        method: "GET",
      });
      setPhotos(updated);
    } catch {
      setErrorPhoto("Failed to update photo details.");
    }
  };

  const handleDeletePhoto = async (id: number) => {
    if (!confirm("Are you sure you want to delete this photo?")) return;
    try {
      await apiRequest({
        path: `/dashboard/photos/${id}/`,
        method: "DELETE",
      });
      const updated = await apiRequest<PhotoState[]>({
        path: "/dashboard/photos/",
        method: "GET",
      });
      setPhotos(updated);
    } catch {
      setErrorPhoto("Failed to delete photo.");
    }
  };


  // ==========================================
  // ANNOUNCEMENT HANDLERS
  // ==========================================
  const handleSaveAnnouncement = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingAnnouncement(true);
    setErrorAnnouncement("");
    setSuccessAnnouncement("");

    try {
      if (editingAnnouncementId) {
        await apiRequest({
          path: `/dashboard/announcements/${editingAnnouncementId}/`,
          method: "PUT",
          body: JSON.stringify(announcementForm),
        });
        setSuccessAnnouncement("Announcement updated successfully!");
        setEditingAnnouncementId(null);
      } else {
        await apiRequest({
          path: "/dashboard/announcements/",
          method: "POST",
          body: JSON.stringify(announcementForm),
        });
        setSuccessAnnouncement("Announcement created successfully!");
      }
      setAnnouncementForm({
        title: "",
        content: "",
        priority: "normal",
        status: "draft",
        start_date: "",
        end_date: "",
        is_active: true,
      });
      const updated = await apiRequest<AnnouncementState[]>({
        path: "/dashboard/announcements/",
        method: "GET",
      });
      setAnnouncements(updated);
    } catch {
      setErrorAnnouncement("Failed to save announcement. Verify all fields.");
    } finally {
      setSavingAnnouncement(false);
    }
  };

  const handleStartEditAnnouncement = (a: AnnouncementState) => {
    setEditingAnnouncementId(a.id || null);
    setAnnouncementForm({
      title: a.title,
      content: a.content,
      priority: a.priority,
      status: a.status,
      start_date: a.start_date,
      end_date: a.end_date,
      is_active: a.is_active,
    });
  };

  const handleDeleteAnnouncement = async (id: number) => {
    if (!confirm("Are you sure you want to delete this announcement?")) return;
    try {
      await apiRequest({
        path: `/dashboard/announcements/${id}/`,
        method: "DELETE",
      });
      const updated = await apiRequest<AnnouncementState[]>({
        path: "/dashboard/announcements/",
        method: "GET",
      });
      setAnnouncements(updated);
    } catch {
      setErrorAnnouncement("Failed to delete announcement.");
    }
  };


  // ==========================================
  // EVENT HANDLERS
  // ==========================================
  const handleSaveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingEvent(true);
    setErrorEvent("");
    setSuccessEvent("");

    let formattedTime = eventForm.event_time;
    if (formattedTime && formattedTime.length === 5) {
      formattedTime = formattedTime + ":00";
    }

    const payload = {
      ...eventForm,
      event_time: formattedTime,
    };

    try {
      if (editingEventId) {
        await apiRequest({
          path: `/dashboard/events/${editingEventId}/`,
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setSuccessEvent("Event updated successfully!");
        setEditingEventId(null);
      } else {
        await apiRequest({
          path: "/dashboard/events/",
          method: "POST",
          body: JSON.stringify(payload),
        });
        setSuccessEvent("Event created successfully!");
      }
      setEventForm({
        title: "",
        description: "",
        event_type: "other",
        status: "draft",
        event_date: "",
        event_time: "",
        event_location: "",
        speaker_name: "",
        is_active: true,
      });
      const updated = await apiRequest<EventState[]>({
        path: "/dashboard/events/",
        method: "GET",
      });
      setEvents(updated);
    } catch {
      setErrorEvent("Failed to save event. Verify all fields.");
    } finally {
      setSavingEvent(false);
    }
  };

  const handleStartEditEvent = (evt: EventState) => {
    setEditingEventId(evt.id || null);
    setEventForm({
      title: evt.title,
      description: evt.description,
      event_type: evt.event_type,
      status: evt.status,
      event_date: evt.event_date,
      event_time: formatTimeForInput(evt.event_time),
      event_location: evt.event_location,
      speaker_name: evt.speaker_name,
      is_active: evt.is_active,
    });
  };

  const handleDeleteEvent = async (id: number) => {
    if (!confirm("Are you sure you want to delete this event?")) return;
    try {
      await apiRequest({
        path: `/dashboard/events/${id}/`,
        method: "DELETE",
      });
      const updated = await apiRequest<EventState[]>({
        path: "/dashboard/events/",
        method: "GET",
      });
      setEvents(updated);
    } catch {
      setErrorEvent("Failed to delete event.");
    }
  };

  // ==========================================
  // COMMUNITY SCHEDULE HANDLERS
  // ==========================================
  const handleSaveCommunitySchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCommunitySchedule(true);
    setErrorCommunitySchedule("");
    setSuccessCommunitySchedule("");
    setErrorsCommunitySchedule({});

    let formattedTime = communityScheduleForm.start_time;
    if (formattedTime && formattedTime.length === 5) {
      formattedTime = formattedTime + ":00";
    }

    const extData: any = {};
    if (communityScheduleForm.schedule_type === "khutbah") {
      if (communityScheduleForm.extended_data?.shift_number) {
        extData.shift_number = Number(communityScheduleForm.extended_data.shift_number);
      }
      if (communityScheduleForm.extended_data?.language) {
        extData.language = communityScheduleForm.extended_data.language;
      }
    } else if (communityScheduleForm.schedule_type === "weekly_dars") {
      if (communityScheduleForm.extended_data?.day_of_week !== undefined) {
        extData.day_of_week = Number(communityScheduleForm.extended_data.day_of_week);
      }
      if (communityScheduleForm.extended_data?.language) {
        extData.language = communityScheduleForm.extended_data.language;
      }
    }

    const payload = {
      schedule_type: communityScheduleForm.schedule_type,
      event_date: communityScheduleForm.event_date,
      start_time: formattedTime,
      speaker: communityScheduleForm.speaker,
      topic: communityScheduleForm.topic,
      extended_data: extData,
    };

    try {
      if (editingCommunityScheduleId) {
        await apiRequest({
          path: `/dashboard/schedules/${editingCommunityScheduleId}/`,
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setSuccessCommunitySchedule("Schedule updated successfully!");
        setEditingCommunityScheduleId(null);
      } else {
        await apiRequest({
          path: "/dashboard/schedules/",
          method: "POST",
          body: JSON.stringify(payload),
        });
        setSuccessCommunitySchedule("Schedule created successfully!");
      }
      setCommunityScheduleForm({
        schedule_type: "khutbah",
        event_date: "",
        start_time: "",
        speaker: "",
        topic: "",
        extended_data: {
          shift_number: 1,
          language: "",
          day_of_week: 1,
        },
      });
      const updated = await apiRequest<CommunityScheduleState[]>({
        path: "/dashboard/schedules/",
        method: "GET",
      });
      setCommunitySchedules(updated);
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const details = err.details as Record<string, unknown>;
        const fieldErrors: any = {};
        Object.entries(details).forEach(([k, v]) => {
          fieldErrors[k] = Array.isArray(v) ? v.join(" ") : String(v);
        });
        setErrorsCommunitySchedule(fieldErrors);
        if (fieldErrors.non_field_errors) {
          setErrorCommunitySchedule(fieldErrors.non_field_errors);
        } else {
          setErrorCommunitySchedule("Failed to save schedule. Verify all fields.");
        }
      } else {
        setErrorCommunitySchedule("Failed to save schedule. Verify all fields.");
      }
    } finally {
      setSavingCommunitySchedule(false);
    }
  };

  const handleStartEditCommunitySchedule = (sched: CommunityScheduleState) => {
    setEditingCommunityScheduleId(sched.id || null);
    setCommunityScheduleForm({
      schedule_type: sched.schedule_type,
      event_date: sched.event_date,
      start_time: formatTimeForInput(sched.start_time),
      speaker: sched.speaker,
      topic: sched.topic,
      extended_data: {
        shift_number: sched.extended_data?.shift_number || 1,
        language: sched.extended_data?.language || "",
        day_of_week: sched.extended_data?.day_of_week !== undefined ? sched.extended_data.day_of_week : 1,
      },
    });
    setErrorsCommunitySchedule({});
    setErrorCommunitySchedule("");
    setSuccessCommunitySchedule("");
  };

  const handleDeleteCommunitySchedule = async (id: number) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return;
    try {
      await apiRequest({
        path: `/dashboard/schedules/${id}/`,
        method: "DELETE",
      });
      const updated = await apiRequest<CommunityScheduleState[]>({
        path: "/dashboard/schedules/",
        method: "GET",
      });
      setCommunitySchedules(updated);
    } catch {
      setErrorCommunitySchedule("Failed to delete schedule.");
    }
  };

  // ==========================================
  // JANAZAH NOTICES HANDLERS
  // ==========================================
  const handleSaveJanazah = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingJanazah(true);
    setErrorsJanazah({});
    setErrorJanazah("");
    setSuccessJanazah("");

    // Prepare payload. Age must be null if empty string.
    const payload = {
      ...janazahForm,
      age: janazahForm.age === "" ? null : Number(janazahForm.age),
      salah_time: janazahForm.salah_time ? (janazahForm.salah_time.length === 5 ? janazahForm.salah_time + ":00" : janazahForm.salah_time) : "",
      burial_time: janazahForm.burial_time ? (janazahForm.burial_time.length === 5 ? janazahForm.burial_time + ":00" : janazahForm.burial_time) : null,
      burial_date: janazahForm.burial_date || null,
      cemetery_gps_url: janazahForm.cemetery_gps_url || null,
    };

    try {
      if (editingJanazahId) {
        // Find if Salah or Burial times changed to trigger correction alert
        const original = janazahs.find(j => j.id === editingJanazahId);
        const timingChanged = original && (
          original.salah_date !== payload.salah_date ||
          original.salah_time.slice(0, 5) !== payload.salah_time.slice(0, 5) ||
          (original.burial_date || "") !== (payload.burial_date || "") ||
          (original.burial_time || "").slice(0, 5) !== (payload.burial_time || "").slice(0, 5)
        );

        const res = await apiRequest<JanazahNoticeState>({
          path: `/dashboard/janazah/${editingJanazahId}/`,
          method: "PUT",
          body: JSON.stringify(payload),
        });

        setSuccessJanazah("Janazah notice updated successfully!");
        setEditingJanazahId(null);

        // Correction alert dispatch prompt
        if (timingChanged && res.status === "published") {
          if (confirm("Burial or Salah timings have changed. Would you like to dispatch an alert update to subscribers?")) {
            try {
              await apiRequest({
                path: `/dashboard/janazah/${res.id}/send-correction/`,
                method: "POST"
              });
              setSuccessJanazah("Janazah notice updated and subscribers notified!");
            } catch {
              setErrorJanazah("Timing updated, but failed to notify subscribers.");
            }
          }
        }
      } else {
        await apiRequest({
          path: "/dashboard/janazah/",
          method: "POST",
          body: JSON.stringify(payload),
        });
        setSuccessJanazah("Janazah notice created successfully!");
      }

      setJanazahForm({
        deceased_name: "",
        gender: "male",
        age: "",
        date_of_death: "",
        salah_date: "",
        salah_time: "",
        salah_details: "",
        burial_date: "",
        burial_time: "",
        cemetery_name: "",
        cemetery_address: "",
        cemetery_gps_url: "",
        family_contact_name: "",
        family_contact_phone: "",
        publish_contact_info: false,
        status: "draft",
      });

      const updated = await apiRequest<JanazahNoticeState[]>({
        path: "/dashboard/janazah/",
        method: "GET",
      });
      setJanazahs(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setErrorJanazah("This notice has been updated by another user. Please refresh and try again.");
        } else if (err.details && typeof err.details === "object") {
          const details = err.details as Record<string, unknown>;
          const fieldErrors: any = {};
          Object.entries(details).forEach(([k, v]) => {
            fieldErrors[k] = Array.isArray(v) ? v.join(" ") : String(v);
          });
          setErrorsJanazah(fieldErrors);
          if (fieldErrors.non_field_errors) {
            setErrorJanazah(fieldErrors.non_field_errors);
          } else {
            setErrorJanazah("Failed to save notice. Verify all fields.");
          }
        } else {
          setErrorJanazah("Failed to save notice. Verify all fields.");
        }
      } else {
        setErrorJanazah("Failed to save notice. Verify all fields.");
      }
    } finally {
      setSavingJanazah(false);
    }
  };

  const handleStartEditJanazah = (j: JanazahNoticeState) => {
    setEditingJanazahId(j.id || null);
    setJanazahForm({
      deceased_name: j.deceased_name,
      gender: j.gender,
      age: j.age === null ? "" : j.age,
      date_of_death: j.date_of_death,
      salah_date: j.salah_date,
      salah_time: formatTimeForInput(j.salah_time),
      salah_details: j.salah_details || "",
      burial_date: j.burial_date || "",
      burial_time: formatTimeForInput(j.burial_time || ""),
      cemetery_name: j.cemetery_name || "",
      cemetery_address: j.cemetery_address || "",
      cemetery_gps_url: j.cemetery_gps_url || "",
      family_contact_name: j.family_contact_name || "",
      family_contact_phone: j.family_contact_phone || "",
      publish_contact_info: j.publish_contact_info,
      status: j.status,
      version: j.version,
    });
    setErrorsJanazah({});
    setErrorJanazah("");
    setSuccessJanazah("");
  };

  const handleDeleteJanazah = async (id: number) => {
    if (!confirm("Are you sure you want to delete this notice?")) return;
    try {
      await apiRequest({
        path: `/dashboard/janazah/${id}/`,
        method: "DELETE",
      });
      const updated = await apiRequest<JanazahNoticeState[]>({
        path: "/dashboard/janazah/",
        method: "GET",
      });
      setJanazahs(updated);
    } catch {
      setErrorJanazah("Failed to delete notice.");
    }
  };

  if (loadingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F7F5]">
        <p className="text-slate-600">Checking authentication...</p>
      </div>
    );
  }

  const formatLastUpdated = (dateStr: string) => {
    if (!dateStr) return "Never";
    try {
      return new Date(dateStr).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return "Unknown";
    }
  };

  const isScheduleEmpty = (s: ScheduleState) => {
    return (
      !s.fajr_open &&
      !s.fajr_close &&
      !s.dhuhr_open &&
      !s.dhuhr_close &&
      !s.asr_open &&
      !s.asr_close &&
      !s.maghrib_open &&
      !s.maghrib_close &&
      !s.isha_open &&
      !s.isha_close
    );
  };

  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <p className="inline-flex rounded-full border border-emerald-900/10 bg-white/70 px-4 py-2 text-sm font-medium text-emerald-800 shadow-sm">
              Mosque Management Portal
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              Dashboard
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="inline-flex min-h-11 items-center justify-center rounded-full border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-950/10"
          >
            Sign out
          </button>
        </header>

        <div className="grid gap-6 md:grid-cols-[280px_1fr]">
          {/* Mosque Info Sidebar */}
          <section className="h-fit space-y-4 rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Session Profile
            </h2>
            <div className="space-y-4 pt-1">
              <div>
                <p className="text-xs font-medium text-slate-400">Mosque Name</p>
                <p className="mt-0.5 text-sm font-semibold text-slate-900 font-sans">
                  {admin?.mosqueName}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400">
                  Administrator Phone
                </p>
                <p className="mt-0.5 text-sm font-semibold text-slate-900">
                  {admin?.mobile}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400">
                  Account Status
                </p>
                <span className="mt-1 inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                  Active
                </span>
              </div>
            </div>
          </section>

          {/* Right Panels Stack */}
          <div className="space-y-6">
            {/* Panel 1: Mosque Profile */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Mosque Profile
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Update basic identity details for your mosque.
              </p>

              {loadingProfile ? (
                <div className="py-6 text-sm text-slate-400">
                  Loading profile...
                </div>
              ) : (
                <form onSubmit={handleSaveProfile} className="mt-6 space-y-4">
                  {errorsProfile.non_field_errors && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorsProfile.non_field_errors}
                    </div>
                  )}

                  {successProfile && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successProfile}
                    </div>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label
                        htmlFor="mosque_name"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Mosque Name
                      </label>
                      <input
                        id="mosque_name"
                        type="text"
                        value={profile.mosque_name}
                        onChange={(e) =>
                          setProfile({ ...profile, mosque_name: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingProfile}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="mosque_type"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Mosque Classification <Tooltip content="Choose Jama Masjid if this mosque hosts Friday prayers; Daily Prayer Hall for standard 5-time prayers; or Musallah for smaller prayer rooms." />
                      </label>
                      <select
                        id="mosque_type"
                        value={profile.mosque_type}
                        onChange={(e) =>
                          setProfile({ ...profile, mosque_type: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingProfile}
                      >
                        <option value="jama_masjid">Jama Masjid (Juma Mosque)</option>
                        <option value="daily_prayer">Daily Prayer Hall</option>
                        <option value="musallah">Musallah (Prayer Room)</option>
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor="city"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        City
                      </label>
                      <select
                        id="city"
                        value={profile.city_id || ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          const selectedId = val ? parseInt(val) : null;
                          const selectedCityObj = Array.isArray(cities) ? cities.find((c) => c.id === selectedId) : undefined;
                          setProfile({
                            ...profile,
                            city_id: selectedId,
                            city: selectedCityObj ? selectedCityObj.name : "",
                          });
                        }}
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 bg-white outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingProfile}
                      >
                        <option value="">Select a city</option>
                        {Array.isArray(cities) && cities.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor="contact_phone"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Contact Phone
                      </label>
                      <input
                        id="contact_phone"
                        type="text"
                        value={profile.contact_phone}
                        onChange={(e) =>
                          setProfile({ ...profile, contact_phone: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingProfile}
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="website"
                      className="block text-sm font-semibold text-slate-700"
                    >
                      Website URL
                    </label>
                    <input
                      id="website"
                      type="url"
                      value={profile.website}
                      onChange={(e) =>
                        setProfile({ ...profile, website: e.target.value })
                      }
                      className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                      disabled={savingProfile}
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="address"
                      className="block text-sm font-semibold text-slate-700"
                    >
                      Address Details
                    </label>
                    <textarea
                      id="address"
                      value={profile.address}
                      onChange={(e) =>
                        setProfile({ ...profile, address: e.target.value })
                      }
                      rows={2}
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                      disabled={savingProfile}
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="description"
                      className="block text-sm font-semibold text-slate-700"
                    >
                      About the Mosque (Description)
                    </label>
                    <textarea
                      id="description"
                      value={profile.description}
                      onChange={(e) =>
                        setProfile({ ...profile, description: e.target.value })
                      }
                      rows={3}
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                      disabled={savingProfile}
                      placeholder="Describe timings special notices or history..."
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="min-h-11 rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white transition hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-800/20 disabled:opacity-60"
                  >
                    {savingProfile ? "Saving Profile..." : "Save Profile Details"}
                  </button>
                </form>
              )}
            </section>

            {/* Panel 2: Facilities Checklist */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Facilities & Accommodation
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Select facilities currently active at your mosque.
              </p>

              {loadingProfile ? (
                <div className="py-6 text-sm text-slate-400">
                  Loading facilities...
                </div>
              ) : (
                <form onSubmit={handleSaveProfile} className="mt-6 space-y-5">
                  {successProfile && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successProfile}
                    </div>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3.5">
                      <input
                        type="checkbox"
                        checked={profile.women_prayer_available}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            women_prayer_available: e.target.checked,
                          })
                        }
                        className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                        disabled={savingProfile}
                      />
                      <span>
                        <span className="block text-sm font-semibold text-slate-900">
                          Women&apos;s Prayer Space
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          Separate area for ladies to pray.
                        </span>
                      </span>
                    </label>

                    <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3.5">
                      <input
                        type="checkbox"
                        checked={profile.separate_women_entrance}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            separate_women_entrance: e.target.checked,
                          })
                        }
                        className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                        disabled={savingProfile}
                      />
                      <span>
                        <span className="block text-sm font-semibold text-slate-900">
                          Separate Women Entrance
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          Has a private entrance for ladies.
                        </span>
                      </span>
                    </label>

                    <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3.5">
                      <input
                        type="checkbox"
                        checked={profile.parking_available}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            parking_available: e.target.checked,
                          })
                        }
                        className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                        disabled={savingProfile}
                      />
                      <span>
                        <span className="block text-sm font-semibold text-slate-900">
                          Parking Available
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          Dedicated parking area for cars/bikes.
                        </span>
                      </span>
                    </label>

                    <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3.5">
                      <input
                        type="checkbox"
                        checked={profile.wudu_facility_available}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            wudu_facility_available: e.target.checked,
                          })
                        }
                        className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                        disabled={savingProfile}
                      />
                      <span>
                        <span className="block text-sm font-semibold text-slate-900">
                          Wudu Facility Available
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          Ablution spaces configured on site.
                        </span>
                      </span>
                    </label>

                    <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3.5 sm:col-span-2">
                      <input
                        type="checkbox"
                        checked={profile.wheelchair_accessible}
                        onChange={(e) =>
                          setProfile({
                            ...profile,
                            wheelchair_accessible: e.target.checked,
                          })
                        }
                        className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                        disabled={savingProfile}
                      />
                      <span>
                        <span className="block text-sm font-semibold text-slate-900">
                          Wheelchair Accessible
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          Ramps or elevators supporting wheelchair entry.
                        </span>
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="min-h-11 rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white transition hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-800/20 disabled:opacity-60"
                  >
                    {savingProfile ? "Saving..." : "Save Facilities Configurations"}
                  </button>
                </form>
              )}
            </section>

            {/* Panel 3: Operating Schedule */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Operating Schedule
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Configure opening times. Helps visitors check if the building is
                open.
              </p>

              {loadingSchedule ? (
                <div className="py-6 text-sm text-slate-400">
                  Loading schedule...
                </div>
              ) : (
                <form onSubmit={handleSaveSchedule} className="mt-6 space-y-6">
                  {errorsSchedule.non_field_errors && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorsSchedule.non_field_errors}
                    </div>
                  )}

                  {successSchedule && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successSchedule}
                    </div>
                  )}

                  <label className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <input
                      type="checkbox"
                      checked={schedule.open_24_hours}
                      onChange={(e) =>
                        setSchedule({
                          ...schedule,
                          open_24_hours: e.target.checked,
                        })
                      }
                      className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
                      disabled={savingSchedule}
                    />
                    <span>
                      <span className="block text-sm font-semibold text-slate-900">
                        Open 24 Hours
                      </span>
                      <span className="mt-1 block text-sm text-slate-600 font-normal">
                        Select if the mosque remains open continuously at all hours.
                      </span>
                    </span>
                  </label>

                  {/* Empty Warning notice if not 24 hours and empty */}
                  {!schedule.open_24_hours && isScheduleEmpty(schedule) && (
                    <div className="rounded-xl bg-slate-50 border border-slate-100 p-4 text-sm text-slate-600">
                      <span className="font-semibold text-slate-900 block mb-1">
                        Schedule status:
                      </span>
                      No operating schedule configured yet. Please configure the open
                      and close timings for the prayer windows below.
                    </div>
                  )}

                  {!schedule.open_24_hours && (
                    <div className="space-y-4 border-t border-slate-100 pt-5">
                      <h3 className="text-sm font-semibold text-slate-900">
                        Prayer Window Timings
                      </h3>
                      <p className="text-xs text-slate-500 leading-normal">
                        Enter times for when the mosque opens and closes for each
                        individual prayer service window.
                      </p>

                      <div className="grid gap-4 sm:grid-cols-2">
                        {/* Fajr Window */}
                        <div className="rounded-xl border border-slate-100 p-3">
                          <h4 className="text-sm font-semibold text-emerald-800">
                            Fajr Window
                          </h4>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Open
                              </label>
                              <input
                                type="time"
                                value={schedule.fajr_open}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    fajr_open: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Close
                              </label>
                              <input
                                type="time"
                                value={schedule.fajr_close}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    fajr_close: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Dhuhr Window */}
                        <div className="rounded-xl border border-slate-100 p-3">
                          <h4 className="text-sm font-semibold text-emerald-800">
                            Dhuhr Window
                          </h4>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Open
                              </label>
                              <input
                                type="time"
                                value={schedule.dhuhr_open}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    dhuhr_open: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Close
                              </label>
                              <input
                                type="time"
                                value={schedule.dhuhr_close}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    dhuhr_close: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Asr Window */}
                        <div className="rounded-xl border border-slate-100 p-3">
                          <h4 className="text-sm font-semibold text-emerald-800">
                            Asr Window
                          </h4>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Open
                              </label>
                              <input
                                type="time"
                                value={schedule.asr_open}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    asr_open: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Close
                              </label>
                              <input
                                type="time"
                                value={schedule.asr_close}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    asr_close: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Maghrib Window */}
                        <div className="rounded-xl border border-slate-100 p-3">
                          <h4 className="text-sm font-semibold text-emerald-800">
                            Maghrib Window
                          </h4>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Open
                              </label>
                              <input
                                type="time"
                                value={schedule.maghrib_open}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    maghrib_open: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Close
                              </label>
                              <input
                                type="time"
                                value={schedule.maghrib_close}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    maghrib_close: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Isha Window */}
                        <div className="rounded-xl border border-slate-100 p-3 sm:col-span-2">
                          <h4 className="text-sm font-semibold text-emerald-800">
                            Isha Window
                          </h4>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Open
                              </label>
                              <input
                                type="time"
                                value={schedule.isha_open}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    isha_open: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-semibold text-slate-500">
                                Close
                              </label>
                              <input
                                type="time"
                                value={schedule.isha_close}
                                onChange={(e) =>
                                  setSchedule({
                                    ...schedule,
                                    isha_close: e.target.value,
                                  })
                                }
                                className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-sm text-slate-950 outline-none transition focus:border-emerald-900"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={savingSchedule}
                    className="min-h-11 rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white transition hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-800/20 disabled:opacity-60"
                  >
                    {savingSchedule ? "Saving..." : "Save Operating Schedule"}
                  </button>
                </form>
              )}
            </section>

            {/* Panel 4: Congregation Timings */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                <h2 className="text-lg font-semibold text-slate-950">
                  Congregation (Jamaat) Timings
                </h2>
                {timings.updated_at && (
                  <p className="text-xs text-slate-500">
                    Last updated: {formatLastUpdated(timings.updated_at)}
                  </p>
                )}
              </div>
              <p className="mt-1 text-sm text-slate-500">
                Configure daily congregation prayer times for public displays.
              </p>

              {loadingTimings ? (
                <div className="py-6 text-sm text-slate-400">
                  Loading timings...
                </div>
              ) : (
                <form onSubmit={handleSaveTimings} className="mt-6 space-y-6">
                  {errorsTimings.non_field_errors && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorsTimings.non_field_errors}
                    </div>
                  )}

                  {successTimings && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successTimings}
                    </div>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label
                        htmlFor="fajr_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Fajr
                      </label>
                      <input
                        id="fajr_time"
                        type="time"
                        value={timings.fajr_time}
                        onChange={(e) =>
                          setTimings({ ...timings, fajr_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="dhuhr_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Dhuhr
                      </label>
                      <input
                        id="dhuhr_time"
                        type="time"
                        value={timings.dhuhr_time}
                        onChange={(e) =>
                          setTimings({ ...timings, dhuhr_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="asr_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Asr
                      </label>
                      <input
                        id="asr_time"
                        type="time"
                        value={timings.asr_time}
                        onChange={(e) =>
                          setTimings({ ...timings, asr_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="maghrib_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Maghrib
                      </label>
                      <input
                        id="maghrib_time"
                        type="time"
                        value={timings.maghrib_time}
                        onChange={(e) =>
                          setTimings({ ...timings, maghrib_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="isha_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Isha
                      </label>
                      <input
                        id="isha_time"
                        type="time"
                        value={timings.isha_time}
                        onChange={(e) =>
                          setTimings({ ...timings, isha_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="jumuah_time"
                        className="block text-sm font-semibold text-slate-700"
                      >
                        Jumuah
                      </label>
                      <input
                        id="jumuah_time"
                        type="time"
                        value={timings.jumuah_time}
                        onChange={(e) =>
                          setTimings({ ...timings, jumuah_time: e.target.value })
                        }
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                        disabled={savingTimings}
                        required
                      />
                    </div>
                  </div>

                  <div className="border-t border-slate-100 pt-5">
                    <label
                      htmlFor="effective_from"
                      className="block text-sm font-semibold text-slate-700"
                    >
                      Effective From <Tooltip content="The date these timings start. Timings will remain active from this day onward until a new schedule is created." />
                    </label>
                    <input
                      id="effective_from"
                      type="date"
                      value={timings.effective_from}
                      onChange={(e) =>
                        setTimings({ ...timings, effective_from: e.target.value })
                      }
                      className="mt-1 min-h-11 w-full max-w-sm rounded-xl border border-slate-200 px-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                      disabled={savingTimings}
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={savingTimings}
                    className="min-h-11 rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white transition hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-800/20 disabled:opacity-60"
                  >
                    {savingTimings ? "Saving..." : "Save Timings"}
                  </button>
                </form>
              )}
            </section>

            {/* Panel 5: Mosque Gallery */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Mosque Gallery
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Upload photos of your entrance, prayer halls, and facilities for visitors.
              </p>

              {loadingPhotos ? (
                <div className="py-6 text-sm text-slate-400">Loading gallery...</div>
              ) : (
                <div className="mt-6 space-y-6">
                  {errorPhoto && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorPhoto}
                    </div>
                  )}

                  {/* Upload Form */}
                  <form onSubmit={handleUploadPhoto} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-4">
                    <h3 className="text-sm font-semibold text-slate-800">Upload New Photo</h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label className="block text-xs font-semibold text-slate-600">Select Image File</label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setPhotoFile(e.target.files?.[0] || null)}
                          className="mt-1 w-full text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-800 file:hover:bg-emerald-100 cursor-pointer"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-600">Title</label>
                        <input
                          type="text"
                          value={newPhotoTitle}
                          onChange={(e) => setNewPhotoTitle(e.target.value)}
                          placeholder="e.g. Main Entrance"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label className="block text-xs font-semibold text-slate-600">Caption / Description</label>
                        <input
                          type="text"
                          value={newPhotoCaption}
                          onChange={(e) => setNewPhotoCaption(e.target.value)}
                          placeholder="A brief description of this area..."
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-600">Display Order <Tooltip content="Photos are sorted in ascending order (lowest number first, e.g. 1 appears before 2)." /></label>
                        <input
                          type="number"
                          value={newPhotoOrder}
                          onChange={(e) => setNewPhotoOrder(parseInt(e.target.value) || 0)}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      disabled={savingPhoto}
                      className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-800 px-4 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-60"
                    >
                      {savingPhoto ? "Uploading..." : "Upload Photo"}
                    </button>
                  </form>

                  {/* Gallery List */}
                  {photos.length === 0 ? (
                    <p className="text-xs text-slate-400">No photos uploaded yet.</p>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2">
                      {photos.map((photo) => (
                        <div key={photo.id} className="flex flex-col rounded-xl border border-slate-100 p-3 bg-white space-y-2">
                          <img
                            src={photo.image}
                            alt={photo.title}
                            className="h-32 w-full rounded-lg object-cover bg-slate-50 border border-slate-100 animate-fadeIn"
                          />
                          {editingPhotoId === photo.id ? (
                            <div className="space-y-2 pt-1">
                              <input
                                type="text"
                                value={editingPhotoTitle}
                                onChange={(e) => setEditingPhotoTitle(e.target.value)}
                                className="w-full rounded border border-slate-200 px-2 py-1 text-xs outline-none"
                                placeholder="Title"
                              />
                              <input
                                type="text"
                                value={editingPhotoCaption}
                                onChange={(e) => setEditingPhotoCaption(e.target.value)}
                                className="w-full rounded border border-slate-200 px-2 py-1 text-xs outline-none"
                                placeholder="Caption"
                              />
                              <div className="flex gap-2">
                                <input
                                  type="number"
                                  value={editingPhotoOrder}
                                  onChange={(e) => setEditingPhotoOrder(parseInt(e.target.value) || 0)}
                                  className="w-16 rounded border border-slate-200 px-2 py-1 text-xs outline-none"
                                  placeholder="Order"
                                />
                                <label className="flex items-center gap-1 text-[11px] text-slate-600 font-semibold cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={editingPhotoActive}
                                    onChange={(e) => setEditingPhotoActive(e.target.checked)}
                                  />
                                  Active
                                </label>
                              </div>
                              <div className="flex gap-1.5 pt-1">
                                <button
                                  onClick={() => handleSaveEditPhoto(photo.id)}
                                  className="rounded bg-emerald-800 px-2 py-1 text-[10px] font-bold text-white hover:bg-emerald-900"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => setEditingPhotoId(null)}
                                  className="rounded bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-700 hover:bg-slate-200"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="space-y-1">
                              <div className="flex items-start justify-between font-sans">
                                <h4 className="text-xs font-bold text-slate-800 leading-tight">{photo.title || "(Untitled)"}</h4>
                                <span className={`text-[9px] font-bold rounded-full px-1.5 py-0.5 ${photo.is_active ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                                  {photo.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 line-clamp-2 leading-snug">{photo.caption || "No caption added."}</p>
                              <p className="text-[10px] text-slate-400">Order: {photo.display_order}</p>
                              <div className="flex gap-2 pt-1.5">
                                <button
                                  onClick={() => handleStartEditPhoto(photo)}
                                  className="text-[11px] font-bold text-emerald-800 hover:text-emerald-950"
                                >
                                  Edit details
                                </button>
                                <button
                                  onClick={() => handleDeletePhoto(photo.id)}
                                  className="text-[11px] font-bold text-red-600 hover:text-red-800"
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Panel 6: Announcements */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Announcements
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Publish operational notices, community updates, or holiday schedules.
              </p>

              {loadingAnnouncements ? (
                <div className="py-6 text-sm text-slate-400">Loading announcements...</div>
              ) : (
                <div className="mt-6 space-y-6">
                  {errorAnnouncement && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorAnnouncement}
                    </div>
                  )}
                  {successAnnouncement && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successAnnouncement}
                    </div>
                  )}

                  {/* Announcement Form */}
                  <form onSubmit={handleSaveAnnouncement} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-4">
                    <h3 className="text-sm font-semibold text-slate-800">
                      {editingAnnouncementId ? "Edit Announcement" : "Create New Announcement"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <label htmlFor="ann_title" className="block text-xs font-semibold text-slate-600">Title</label>
                        <input
                          id="ann_title"
                          type="text"
                          value={announcementForm.title}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, title: e.target.value })}
                          placeholder="e.g. Water Maintenance Notice"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingAnnouncement}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="ann_content" className="block text-xs font-semibold text-slate-600">Content / Message</label>
                        <textarea
                          id="ann_content"
                          value={announcementForm.content}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, content: e.target.value })}
                          placeholder="Provide the detail description here..."
                          rows={3}
                          className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900 resize-y"
                          required
                          disabled={savingAnnouncement}
                        />
                      </div>
                      <div>
                        <label htmlFor="ann_priority" className="block text-xs font-semibold text-slate-600">Priority Level <Tooltip content="Changes the visual style of the badge on the public feed. It does not send SMS or push notifications." /></label>
                        <select
                          id="ann_priority"
                          value={announcementForm.priority}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, priority: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingAnnouncement}
                        >
                          <option value="normal">Normal</option>
                          <option value="important">Important</option>
                          <option value="urgent">Urgent</option>
                        </select>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Normal → Regular update. Important → Highlighted banner. Urgent → High-priority badge.
                        </p>
                      </div>
                      <div>
                        <label htmlFor="ann_status" className="block text-xs font-semibold text-slate-600">Workflow Status <Tooltip content="Controls who can see this entry." /></label>
                        <select
                          id="ann_status"
                          value={announcementForm.status}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, status: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingAnnouncement}
                        >
                          <option value="draft">Draft (Admin Only)</option>
                          <option value="published">Published (Public)</option>
                          <option value="archived">Archived (Hidden)</option>
                        </select>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Draft → Hidden from public. Published → Visible to everyone. Archived → Kept for records.
                        </p>
                      </div>
                      <div>
                        <label htmlFor="ann_start_date" className="block text-xs font-semibold text-slate-600">Start Date <Tooltip content="The date this announcement will automatically become visible to the public." /></label>
                        <input
                          id="ann_start_date"
                          type="date"
                          value={announcementForm.start_date}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, start_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingAnnouncement}
                        />
                      </div>
                      <div>
                        <label htmlFor="ann_end_date" className="block text-xs font-semibold text-slate-600">End Date <Tooltip content="The date this announcement will automatically be hidden from the public." /></label>
                        <input
                          id="ann_end_date"
                          type="date"
                          value={announcementForm.end_date}
                          onChange={(e) => setAnnouncementForm({ ...announcementForm, end_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingAnnouncement}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={announcementForm.is_active}
                            onChange={(e) => setAnnouncementForm({ ...announcementForm, is_active: e.target.checked })}
                            disabled={savingAnnouncement}
                          />
                          Active (Visible to users)
                        </label>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Uncheck to temporarily hide this announcement from public views, overriding other settings.
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <button
                        type="submit"
                        disabled={savingAnnouncement}
                        className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-800 px-5 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-60"
                      >
                        {savingAnnouncement ? "Saving..." : (editingAnnouncementId ? "Save Changes" : "Create Announcement")}
                      </button>
                      {editingAnnouncementId && (
                        <button
                          type="button"
                          onClick={() => {
                            setEditingAnnouncementId(null);
                            setAnnouncementForm({
                              title: "",
                              content: "",
                              priority: "normal",
                              status: "draft",
                              start_date: "",
                              end_date: "",
                              is_active: true,
                            });
                          }}
                          className="inline-flex min-h-9 items-center justify-center rounded-full bg-slate-100 px-5 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Announcement List */}
                  {announcements.length === 0 ? (
                    <p className="text-xs text-slate-400">No announcements added yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {announcements.map((ann) => (
                        <div key={ann.id} className="rounded-xl border border-slate-100 p-4 bg-white space-y-2 animate-fadeIn">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <h4 className="text-xs font-bold text-slate-900 font-sans">{ann.title}</h4>
                              <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 ${
                                ann.priority === 'urgent' ? 'bg-red-50 text-red-700 border border-red-100 animate-pulse' :
                                ann.priority === 'important' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                                'bg-slate-50 text-slate-700 border border-slate-100'
                              }`}>
                                {ann.priority.toUpperCase()}
                              </span>
                              <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 ${
                                ann.status === 'published' ? 'bg-emerald-50 text-emerald-800' :
                                ann.status === 'archived' ? 'bg-slate-100 text-slate-500' :
                                'bg-blue-50 text-blue-800'
                              }`}>
                                {ann.status.toUpperCase()}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400">
                              Active: {ann.start_date} to {ann.end_date}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 whitespace-pre-line leading-relaxed font-normal">{ann.content}</p>
                          <div className="flex gap-3 pt-1 border-t border-slate-50">
                            <button
                              onClick={() => handleStartEditAnnouncement(ann)}
                              className="text-xs font-bold text-emerald-800 hover:text-emerald-950"
                            >
                              Edit Notice
                            </button>
                            <button
                              onClick={() => handleDeleteAnnouncement(ann.id!)}
                              className="text-xs font-bold text-red-600 hover:text-red-800"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Panel 7: Events */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6">
              <h2 className="text-lg font-semibold text-slate-950">
                Events & Programs
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Organize and schedule lectures, circles, youth programs, and community gatherings.
              </p>

              {loadingEvents ? (
                <div className="py-6 text-sm text-slate-400">Loading events...</div>
              ) : (
                <div className="mt-6 space-y-6">
                  {errorEvent && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorEvent}
                    </div>
                  )}
                  {successEvent && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successEvent}
                    </div>
                  )}

                  {/* Event Form */}
                  <form onSubmit={handleSaveEvent} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-4">
                    <h3 className="text-sm font-semibold text-slate-800">
                      {editingEventId ? "Edit Event" : "Schedule New Event"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <label htmlFor="evt_title" className="block text-xs font-semibold text-slate-600">Event Title</label>
                        <input
                          id="evt_title"
                          type="text"
                          value={eventForm.title}
                          onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                          placeholder="e.g. Weekly Dars (Study Circle)"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingEvent}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="evt_desc" className="block text-xs font-semibold text-slate-600">Description</label>
                        <textarea
                          id="evt_desc"
                          value={eventForm.description}
                          onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                          placeholder="Describe the topics, details, or target audience..."
                          rows={3}
                          className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900 resize-y"
                          disabled={savingEvent}
                        />
                      </div>
                      <div>
                        <label htmlFor="evt_type" className="block text-xs font-semibold text-slate-600">Event Classification</label>
                        <select
                          id="evt_type"
                          value={eventForm.event_type}
                          onChange={(e) => setEventForm({ ...eventForm, event_type: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingEvent}
                        >
                          <option value="lecture">Lecture</option>
                          <option value="dars">Dars (Study Circle)</option>
                          <option value="youth_program">Youth Program</option>
                          <option value="community_meeting">Community Meeting</option>
                          <option value="fundraiser">Fundraiser</option>
                          <option value="ramadan">Ramadan Program</option>
                          <option value="eid">Eid Event</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="evt_status" className="block text-xs font-semibold text-slate-600">Workflow Status <Tooltip content="Controls who can see this entry." /></label>
                        <select
                          id="evt_status"
                          value={eventForm.status}
                          onChange={(e) => setEventForm({ ...eventForm, status: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingEvent}
                        >
                          <option value="draft">Draft (Admin Only)</option>
                          <option value="published">Published (Public)</option>
                          <option value="archived">Archived (Hidden)</option>
                        </select>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Draft → Hidden from public. Published → Visible to everyone. Archived → Kept for records.
                        </p>
                      </div>
                      <div>
                        <label htmlFor="evt_date" className="block text-xs font-semibold text-slate-600">Event Date</label>
                        <input
                          id="evt_date"
                          type="date"
                          value={eventForm.event_date}
                          onChange={(e) => setEventForm({ ...eventForm, event_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingEvent}
                        />
                      </div>
                      <div>
                        <label htmlFor="evt_time" className="block text-xs font-semibold text-slate-600">Event Time</label>
                        <input
                          id="evt_time"
                          type="time"
                          value={eventForm.event_time}
                          onChange={(e) => setEventForm({ ...eventForm, event_time: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingEvent}
                        />
                      </div>
                      <div>
                        <label htmlFor="evt_location" className="block text-xs font-semibold text-slate-600">Event Location (Room / Hall)</label>
                        <input
                          id="evt_location"
                          type="text"
                          value={eventForm.event_location}
                          onChange={(e) => setEventForm({ ...eventForm, event_location: e.target.value })}
                          placeholder="e.g. Main Prayer Hall"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingEvent}
                        />
                      </div>
                      <div>
                        <label htmlFor="evt_speaker" className="block text-xs font-semibold text-slate-600">Speaker Name</label>
                        <input
                          id="evt_speaker"
                          type="text"
                          value={eventForm.speaker_name}
                          onChange={(e) => setEventForm({ ...eventForm, speaker_name: e.target.value })}
                          placeholder="e.g. Mufti Muhammad"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingEvent}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={eventForm.is_active}
                            onChange={(e) => setEventForm({ ...eventForm, is_active: e.target.checked })}
                            disabled={savingEvent}
                          />
                          Active (Visible to users)
                        </label>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Uncheck to temporarily hide this event from public views, overriding other settings.
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <button
                        type="submit"
                        disabled={savingEvent}
                        className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-800 px-5 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-60"
                      >
                        {savingEvent ? "Saving..." : (editingEventId ? "Save Changes" : "Schedule Event")}
                      </button>
                      {editingEventId && (
                        <button
                          type="button"
                          onClick={() => {
                            setEditingEventId(null);
                            setEventForm({
                              title: "",
                              description: "",
                              event_type: "other",
                              status: "draft",
                              event_date: "",
                              event_time: "",
                              event_location: "",
                              speaker_name: "",
                              is_active: true,
                            });
                          }}
                          className="inline-flex min-h-9 items-center justify-center rounded-full bg-slate-100 px-5 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Event List */}
                  {events.length === 0 ? (
                    <p className="text-xs text-slate-400">No scheduled events yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {events.map((evt) => (
                        <div key={evt.id} className="rounded-xl border border-slate-100 p-4 bg-white space-y-2 animate-fadeIn">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <h4 className="text-xs font-bold text-slate-900 font-sans">{evt.title}</h4>
                              <span className="text-[9px] font-bold rounded-full px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-100">
                                {evt.event_type.replace('_', ' ').toUpperCase()}
                              </span>
                              <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 ${
                                evt.status === 'published' ? 'bg-emerald-50 text-emerald-800' :
                                evt.status === 'archived' ? 'bg-slate-100 text-slate-500' :
                                'bg-blue-50 text-blue-800'
                              }`}>
                                {evt.status.toUpperCase()}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ⏰ {evt.event_date} @ {evt.event_time.slice(0, 5)}
                            </span>
                          </div>
                          {evt.description && <p className="text-xs text-slate-600 font-normal leading-relaxed">{evt.description}</p>}
                          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-0.5">
                            {evt.speaker_name && <span>🎤 Speaker: {evt.speaker_name}</span>}
                            {evt.event_location && <span>📍 Location: {evt.event_location}</span>}
                          </div>
                          <div className="flex gap-3 pt-1 border-t border-slate-50">
                            <button
                              onClick={() => handleStartEditEvent(evt)}
                              className="text-xs font-bold text-emerald-800 hover:text-emerald-950"
                            >
                              Edit Program
                            </button>
                            <button
                              onClick={() => handleDeleteEvent(evt.id!)}
                              className="text-xs font-bold text-red-600 hover:text-red-800"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Panel 8: Weekly Lectures & Friday Sermons */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6 animate-fadeIn">
              <h2 className="text-lg font-semibold text-slate-950 font-sans">
                Weekly Lectures & Friday Sermons
              </h2>
              <p className="mt-1 text-sm text-slate-500 font-normal">
                Configure Friday Khutbah shifts and Weekly Dars topics.
              </p>

              {loadingCommunitySchedules ? (
                <div className="py-6 text-sm text-slate-400 font-semibold">Loading schedules...</div>
              ) : (
                <div className="mt-6 space-y-6">
                  {errorCommunitySchedule && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800 font-semibold border border-red-100">
                      {errorCommunitySchedule}
                    </div>
                  )}
                  {successCommunitySchedule && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800 font-semibold border border-emerald-100">
                      {successCommunitySchedule}
                    </div>
                  )}

                  {/* Schedule Form */}
                  <form onSubmit={handleSaveCommunitySchedule} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-4 shadow-inner">
                    <h3 className="text-sm font-semibold text-slate-800">
                      {editingCommunityScheduleId ? "Edit Schedule Entry" : "Create New Schedule Entry"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label htmlFor="sched_type" className="block text-xs font-semibold text-slate-600">Schedule Type <Tooltip content="Configure Friday Khutbah shifts or recurring Weekly Dars lectures." /></label>
                        <select
                          id="sched_type"
                          value={communityScheduleForm.schedule_type}
                          onChange={(e) => setCommunityScheduleForm({
                            ...communityScheduleForm,
                            schedule_type: e.target.value as "khutbah" | "weekly_dars"
                          })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingCommunitySchedule}
                        >
                          <option value="khutbah">Friday Khutbah Shift</option>
                          <option value="weekly_dars">Weekly Dars (Lecture)</option>
                        </select>
                      </div>

                      <div>
                        <label htmlFor="sched_date" className="block text-xs font-semibold text-slate-600">Date</label>
                        <input
                          id="sched_date"
                          type="date"
                          value={communityScheduleForm.event_date}
                          onChange={(e) => setCommunityScheduleForm({ ...communityScheduleForm, event_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingCommunitySchedule}
                        />
                      </div>

                      <div>
                        <label htmlFor="sched_time" className="block text-xs font-semibold text-slate-600">Start Time</label>
                        <input
                          id="sched_time"
                          type="time"
                          value={communityScheduleForm.start_time}
                          onChange={(e) => setCommunityScheduleForm({ ...communityScheduleForm, start_time: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingCommunitySchedule}
                        />
                      </div>

                      <div>
                        <label htmlFor="sched_speaker" className="block text-xs font-semibold text-slate-600">Speaker / Imam</label>
                        <input
                          id="sched_speaker"
                          type="text"
                          value={communityScheduleForm.speaker}
                          onChange={(e) => setCommunityScheduleForm({ ...communityScheduleForm, speaker: e.target.value })}
                          placeholder="e.g. Imam Ahmed"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingCommunitySchedule}
                        />
                      </div>

                      <div className="sm:col-span-2">
                        <label htmlFor="sched_topic" className="block text-xs font-semibold text-slate-600">Topic / Title (Optional)</label>
                        <input
                          id="sched_topic"
                          type="text"
                          value={communityScheduleForm.topic}
                          onChange={(e) => setCommunityScheduleForm({ ...communityScheduleForm, topic: e.target.value })}
                          placeholder="e.g. Tafseer of Surah Al-Kahf"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingCommunitySchedule}
                        />
                      </div>

                      {/* Extended Data - Conditional Fields */}
                      {communityScheduleForm.schedule_type === "khutbah" && (
                        <>
                          <div>
                            <label htmlFor="sched_shift" className="block text-xs font-semibold text-slate-600">Khutbah Shift Number <Tooltip content="If your mosque hosts multiple Friday Jumuah prayer shifts, specify which shift this entry represents (e.g. Shift 1 or Shift 2)." /></label>
                            <input
                              id="sched_shift"
                              type="number"
                              min="1"
                              value={communityScheduleForm.extended_data?.shift_number || 1}
                              onChange={(e) => setCommunityScheduleForm({
                                ...communityScheduleForm,
                                extended_data: {
                                  ...communityScheduleForm.extended_data,
                                  shift_number: parseInt(e.target.value) || 1
                                }
                              })}
                              className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                              required
                              disabled={savingCommunitySchedule}
                            />
                            {errorsCommunitySchedule.extended_data && (
                              <p className="mt-1 text-[10px] text-red-600 font-semibold">{errorsCommunitySchedule.extended_data}</p>
                            )}
                          </div>
                          <div>
                            <label htmlFor="sched_lang_khutbah" className="block text-xs font-semibold text-slate-600">Language</label>
                            <input
                              id="sched_lang_khutbah"
                              type="text"
                              value={communityScheduleForm.extended_data?.language || ""}
                              onChange={(e) => setCommunityScheduleForm({
                                ...communityScheduleForm,
                                extended_data: {
                                  ...communityScheduleForm.extended_data,
                                  language: e.target.value
                                }
                              })}
                              placeholder="e.g. Arabic & English"
                              className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                              disabled={savingCommunitySchedule}
                            />
                          </div>
                        </>
                      )}

                      {communityScheduleForm.schedule_type === "weekly_dars" && (
                        <>
                          <div>
                            <label htmlFor="sched_day_of_week" className="block text-xs font-semibold text-slate-600">Day of the Week (Optional) <Tooltip content="The day of the week this lecture typically recurs on (helps users searching for regular classes)." /></label>
                            <select
                              id="sched_day_of_week"
                              value={communityScheduleForm.extended_data?.day_of_week ?? 1}
                              onChange={(e) => setCommunityScheduleForm({
                                ...communityScheduleForm,
                                extended_data: {
                                  ...communityScheduleForm.extended_data,
                                  day_of_week: parseInt(e.target.value)
                                }
                              })}
                              className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                              disabled={savingCommunitySchedule}
                            >
                              <option value="1">Monday</option>
                              <option value="2">Tuesday</option>
                              <option value="3">Wednesday</option>
                              <option value="4">Thursday</option>
                              <option value="5">Friday</option>
                              <option value="6">Saturday</option>
                              <option value="0">Sunday</option>
                            </select>
                            <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                              Select the recurring day of the week this lecture typically takes place on.
                            </p>
                          </div>
                          <div>
                            <label htmlFor="sched_lang_dars" className="block text-xs font-semibold text-slate-600">Language</label>
                            <input
                              id="sched_lang_dars"
                              type="text"
                              value={communityScheduleForm.extended_data?.language || ""}
                              onChange={(e) => setCommunityScheduleForm({
                                ...communityScheduleForm,
                                extended_data: {
                                  ...communityScheduleForm.extended_data,
                                  language: e.target.value
                                }
                              })}
                              placeholder="e.g. English"
                              className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                              disabled={savingCommunitySchedule}
                            />
                          </div>
                        </>
                      )}
                    </div>

                    <div className="flex gap-2 pt-2">
                      <button
                        type="submit"
                        disabled={savingCommunitySchedule}
                        className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-800 px-5 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-60 shadow-sm"
                      >
                        {savingCommunitySchedule ? "Saving..." : (editingCommunityScheduleId ? "Save Changes" : "Create Schedule")}
                      </button>
                      {editingCommunityScheduleId && (
                        <button
                          type="button"
                          onClick={() => {
                            setEditingCommunityScheduleId(null);
                            setCommunityScheduleForm({
                              schedule_type: "khutbah",
                              event_date: "",
                              start_time: "",
                              speaker: "",
                              topic: "",
                              extended_data: {
                                shift_number: 1,
                                language: "",
                                day_of_week: 1,
                              },
                            });
                            setErrorsCommunitySchedule({});
                            setErrorCommunitySchedule("");
                            setSuccessCommunitySchedule("");
                          }}
                          className="inline-flex min-h-9 items-center justify-center rounded-full bg-slate-100 px-5 text-xs font-semibold text-slate-700 hover:bg-slate-200 shadow-sm"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Schedules List */}
                  {communitySchedules.length === 0 ? (
                    <p className="text-xs text-slate-400 font-medium">No schedules configured yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {communitySchedules.map((sched) => {
                        const isKhutbah = sched.schedule_type === "khutbah";
                        const displayDay = (day: number) => {
                          const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
                          return days[day] || "Unknown";
                        };

                        return (
                          <div key={sched.id} className="rounded-xl border border-slate-100 p-4 bg-white space-y-2 hover:border-emerald-800/10 hover:shadow-md transition duration-200">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-2">
                                <h4 className="text-xs font-bold text-slate-900 font-sans">
                                  {sched.topic || (isKhutbah ? "Friday Khutbah Sermon" : "Weekly Lecture")}
                                </h4>
                                <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 border ${
                                  isKhutbah ? 'bg-emerald-50 text-emerald-800 border-emerald-100' :
                                  'bg-blue-50 text-blue-800 border-blue-100'
                                }`}>
                                  {isKhutbah ? "FRIDAY KHUTBAH" : "WEEKLY DARS"}
                                </span>
                              </div>
                              <span className="text-[10px] text-slate-400 font-mono font-bold">
                                📅 {sched.event_date} @ {sched.start_time.slice(0, 5)}
                              </span>
                            </div>
                            
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-0.5 font-medium border-t border-slate-100/50 pt-2">
                              <span>👤 <strong className="text-slate-700">Speaker:</strong> {sched.speaker}</span>
                              {isKhutbah && sched.extended_data?.shift_number && (
                                <span>🔄 <strong className="text-slate-700">Shift:</strong> {sched.extended_data.shift_number}</span>
                              )}
                              {!isKhutbah && sched.extended_data?.day_of_week !== undefined && (
                                <span>📅 <strong className="text-slate-700">Day:</strong> {displayDay(sched.extended_data.day_of_week)}</span>
                              )}
                              {sched.extended_data?.language && (
                                <span>🌐 <strong className="text-slate-700">Language:</strong> {sched.extended_data.language}</span>
                              )}
                            </div>

                            <div className="flex gap-3 pt-1 border-t border-slate-50">
                              <button
                                onClick={() => handleStartEditCommunitySchedule(sched)}
                                className="text-xs font-bold text-emerald-800 hover:text-emerald-950 transition"
                              >
                                Edit Entry
                              </button>
                              <button
                                onClick={() => handleDeleteCommunitySchedule(sched.id!)}
                                className="text-xs font-bold text-red-600 hover:text-red-800 transition"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Panel 8: Janazah Notices */}
            <section className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm sm:p-6 animate-fadeIn">
              <h2 className="text-lg font-semibold text-slate-950">
                Janazah Announcements
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Manage local funeral prayer timings, burial schedules, and family coordinates.
              </p>

              {loadingJanazahs ? (
                <div className="py-6 text-sm text-slate-400">Loading Janazah notices...</div>
              ) : (
                <div className="mt-6 space-y-6">
                  {errorJanazah && (
                    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                      {errorJanazah}
                    </div>
                  )}
                  {successJanazah && (
                    <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                      {successJanazah}
                    </div>
                  )}

                  {/* Janazah Notice Form */}
                  <form onSubmit={handleSaveJanazah} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-4">
                    <h3 className="text-sm font-semibold text-slate-800">
                      {editingJanazahId ? "Edit Janazah Notice" : "Create Janazah Notice"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <label htmlFor="jn_deceased_name" className="block text-xs font-semibold text-slate-600">Deceased Name</label>
                        <input
                          id="jn_deceased_name"
                          type="text"
                          value={janazahForm.deceased_name}
                          onChange={(e) => setJanazahForm({ ...janazahForm, deceased_name: e.target.value })}
                          placeholder="e.g. Ahmad bin Muhammad"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_gender" className="block text-xs font-semibold text-slate-600">Gender</label>
                        <select
                          id="jn_gender"
                          value={janazahForm.gender}
                          onChange={(e) => setJanazahForm({ ...janazahForm, gender: e.target.value as any })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        >
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="jn_age" className="block text-xs font-semibold text-slate-600">Age (Optional)</label>
                        <input
                          id="jn_age"
                          type="number"
                          value={janazahForm.age ?? ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, age: e.target.value === "" ? "" : Number(e.target.value) })}
                          placeholder="e.g. 68"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_date_of_death" className="block text-xs font-semibold text-slate-600">Date of Death</label>
                        <input
                          id="jn_date_of_death"
                          type="date"
                          value={janazahForm.date_of_death}
                          onChange={(e) => setJanazahForm({ ...janazahForm, date_of_death: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_status" className="block text-xs font-semibold text-slate-600">Workflow Status <Tooltip content="Controls public visibility." /></label>
                        <select
                          id="jn_status"
                          value={janazahForm.status}
                          onChange={(e) => setJanazahForm({ ...janazahForm, status: e.target.value as any })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        >
                          <option value="draft">Draft (Admin Only)</option>
                          <option value="published">Published (Publicly Visible)</option>
                          <option value="completed">Completed (Burial Done)</option>
                          <option value="cancelled">Cancelled</option>
                          <option value="archived">Archived</option>
                        </select>
                      </div>

                      <div className="sm:col-span-2 border-t border-slate-200/50 pt-2">
                        <h4 className="text-xs font-bold text-slate-700">FUNERAL PRAYER (SALAH) DETAILS</h4>
                      </div>

                      <div>
                        <label htmlFor="jn_salah_date" className="block text-xs font-semibold text-slate-600">Salah Date</label>
                        <input
                          id="jn_salah_date"
                          type="date"
                          value={janazahForm.salah_date}
                          onChange={(e) => setJanazahForm({ ...janazahForm, salah_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_salah_time" className="block text-xs font-semibold text-slate-600">Salah Time</label>
                        <input
                          id="jn_salah_time"
                          type="time"
                          value={janazahForm.salah_time}
                          onChange={(e) => setJanazahForm({ ...janazahForm, salah_time: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          required
                          disabled={savingJanazah}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="jn_salah_details" className="block text-xs font-semibold text-slate-600">Salah Details (Instructions) <Tooltip content="Parking, venue or specific Friday shifts details." /></label>
                        <input
                          id="jn_salah_details"
                          type="text"
                          value={janazahForm.salah_details || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, salah_details: e.target.value })}
                          placeholder="e.g. Prayer will be held directly after Dhuhr / Jumuah Salah."
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>

                      <div className="sm:col-span-2 border-t border-slate-200/50 pt-2">
                        <h4 className="text-xs font-bold text-slate-700">BURIAL DETAILS (OPTIONAL)</h4>
                      </div>

                      <div>
                        <label htmlFor="jn_burial_date" className="block text-xs font-semibold text-slate-600">Burial Date</label>
                        <input
                          id="jn_burial_date"
                          type="date"
                          value={janazahForm.burial_date || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, burial_date: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_burial_time" className="block text-xs font-semibold text-slate-600">Burial Time</label>
                        <input
                          id="jn_burial_time"
                          type="time"
                          value={janazahForm.burial_time || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, burial_time: e.target.value })}
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="jn_cemetery_name" className="block text-xs font-semibold text-slate-600">Cemetery Name</label>
                        <input
                          id="jn_cemetery_name"
                          type="text"
                          value={janazahForm.cemetery_name || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, cemetery_name: e.target.value })}
                          placeholder="e.g. Central City Cemetery"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="jn_cemetery_address" className="block text-xs font-semibold text-slate-600">Cemetery Address</label>
                        <textarea
                          id="jn_cemetery_address"
                          value={janazahForm.cemetery_address || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, cemetery_address: e.target.value })}
                          placeholder="Full address of the cemetery plot..."
                          rows={2}
                          className="mt-1 w-full rounded-lg border border-slate-200 p-2 text-xs text-slate-950 outline-none focus:border-emerald-900 resize-y"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="jn_cemetery_gps" className="block text-xs font-semibold text-slate-600">Cemetery GPS URL</label>
                        <input
                          id="jn_cemetery_gps"
                          type="url"
                          value={janazahForm.cemetery_gps_url || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, cemetery_gps_url: e.target.value })}
                          placeholder="e.g. https://maps.google.com/?q=..."
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>

                      <div className="sm:col-span-2 border-t border-slate-200/50 pt-2">
                        <h4 className="text-xs font-bold text-slate-700">FAMILY CONTACT & CONSENT</h4>
                      </div>

                      <div>
                        <label htmlFor="jn_family_name" className="block text-xs font-semibold text-slate-600">Family Representative Name</label>
                        <input
                          id="jn_family_name"
                          type="text"
                          value={janazahForm.family_contact_name || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, family_contact_name: e.target.value })}
                          placeholder="e.g. Ahmad Doe"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div>
                        <label htmlFor="jn_family_phone" className="block text-xs font-semibold text-slate-600">Family Phone Number</label>
                        <input
                          id="jn_family_phone"
                          type="text"
                          value={janazahForm.family_contact_phone || ""}
                          onChange={(e) => setJanazahForm({ ...janazahForm, family_contact_phone: e.target.value })}
                          placeholder="e.g. +91 98765 43210"
                          className="mt-1 min-h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-950 outline-none focus:border-emerald-900"
                          disabled={savingJanazah}
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={janazahForm.publish_contact_info}
                            onChange={(e) => setJanazahForm({ ...janazahForm, publish_contact_info: e.target.checked })}
                            disabled={savingJanazah}
                          />
                          Show contact number publicly (Requires family consent)
                        </label>
                        <p className="mt-1 text-[10px] text-slate-500 font-normal leading-tight">
                          Grave privacy protection: unchecking this hides the phone number and contact name from public cards by default.
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <button
                        type="submit"
                        disabled={savingJanazah}
                        className="inline-flex min-h-9 items-center justify-center rounded-full bg-emerald-800 px-5 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-60 shadow-sm"
                      >
                        {savingJanazah ? "Saving..." : (editingJanazahId ? "Save Changes" : "Create Notice")}
                      </button>
                      {editingJanazahId && (
                        <button
                          type="button"
                          onClick={() => {
                            setEditingJanazahId(null);
                            setJanazahForm({
                              deceased_name: "",
                              gender: "male",
                              age: "",
                              date_of_death: "",
                              salah_date: "",
                              salah_time: "",
                              salah_details: "",
                              burial_date: "",
                              burial_time: "",
                              cemetery_name: "",
                              cemetery_address: "",
                              cemetery_gps_url: "",
                              family_contact_name: "",
                              family_contact_phone: "",
                              publish_contact_info: false,
                              status: "draft",
                            });
                            setErrorsJanazah({});
                            setErrorJanazah("");
                            setSuccessJanazah("");
                          }}
                          className="inline-flex min-h-9 items-center justify-center rounded-full bg-slate-100 px-5 text-xs font-semibold text-slate-700 hover:bg-slate-200 shadow-sm"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Janazahs List */}
                  {janazahs.length === 0 ? (
                    <p className="text-xs text-slate-400 font-medium">No Janazah notices added yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {janazahs.map((jn) => (
                        <div key={jn.id} className="rounded-xl border border-slate-100 p-4 bg-white space-y-2 hover:border-emerald-800/10 hover:shadow-md transition duration-200">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <h4 className="text-xs font-bold text-slate-900 font-sans">
                                {jn.deceased_name}
                              </h4>
                              <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 border ${
                                jn.gender === 'male' ? 'bg-blue-50 text-blue-800 border-blue-100' : 'bg-pink-50 text-pink-800 border-pink-100'
                              }`}>
                                {jn.gender.toUpperCase()}
                              </span>
                              <span className={`text-[9px] font-bold rounded-full px-2 py-0.5 border ${
                                jn.status === 'published' ? 'bg-emerald-50 text-emerald-800 border-emerald-100' :
                                jn.status === 'cancelled' ? 'bg-red-50 text-red-800 border-red-100' :
                                jn.status === 'completed' ? 'bg-indigo-50 text-indigo-800 border-indigo-100' :
                                jn.status === 'archived' ? 'bg-slate-50 text-slate-500 border-slate-100' :
                                'bg-slate-50 text-slate-800 border-slate-100'
                              }`}>
                                {jn.status.toUpperCase()}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono font-bold">
                              Salah: 📅 {jn.salah_date} @ {jn.salah_time.slice(0, 5)}
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-0.5 font-medium border-t border-slate-100/50 pt-2">
                            {jn.age && <span>🎂 <strong>Age:</strong> {jn.age}</span>}
                            <span>💀 <strong>Deceased Date:</strong> {jn.date_of_death}</span>
                            {jn.cemetery_name && <span>🪦 <strong>Cemetery:</strong> {jn.cemetery_name}</span>}
                          </div>

                          <div className="flex gap-3 pt-1 border-t border-slate-50">
                            <button
                              onClick={() => handleStartEditJanazah(jn)}
                              className="text-xs font-bold text-emerald-800 hover:text-emerald-950 transition"
                            >
                              Edit Notice
                            </button>
                            <button
                              onClick={() => handleDeleteJanazah(jn.id!)}
                              className="text-xs font-bold text-red-600 hover:text-red-800 transition"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
