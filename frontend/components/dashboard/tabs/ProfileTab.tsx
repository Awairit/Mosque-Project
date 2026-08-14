"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";
import { FACILITIES_LIST } from "@/lib/constants/facilities";

type ProfileState = {
  mosque_name: string;
  city: string;
  city_id?: number | null;
  address: string;
  description: string;
  contact_phone: string;
  contact_email: string;
  website: string;
  imam_name: string;
  imam_contact_number: string;
  women_prayer_available: boolean;
  parking_available: boolean;
  wudu_facility_available: boolean;
  wheelchair_accessible: boolean;
  drinking_water_available: boolean;
  washrooms_available: boolean;
  library_available: boolean;
  quran_classes_available: boolean;
  hifz_program_available: boolean;
  nikah_service_available: boolean;
  muslim_burial_ground_available: boolean;
  community_hall_available: boolean;
  ramadan_iftar_available: boolean;
  eid_prayer_ground_available: boolean;
  zakat_collection_available: boolean;
  funeral_prayer_facility_available: boolean;
  mosque_type: string;
  separate_women_entrance: boolean;
  mosque_status?: string;
};

export default function ProfileTab() {
  const [profile, setProfile] = useState<ProfileState>({
    mosque_name: "",
    city: "",
    city_id: null,
    address: "",
    description: "",
    contact_phone: "",
    contact_email: "",
    website: "",
    imam_name: "",
    imam_contact_number: "",
    women_prayer_available: false,
    parking_available: false,
    wudu_facility_available: false,
    wheelchair_accessible: false,
    drinking_water_available: false,
    washrooms_available: false,
    library_available: false,
    quran_classes_available: false,
    hifz_program_available: false,
    nikah_service_available: false,
    muslim_burial_ground_available: false,
    community_hall_available: false,
    ramadan_iftar_available: false,
    eid_prayer_ground_available: false,
    zakat_collection_available: false,
    funeral_prayer_facility_available: false,
    mosque_type: "jama_masjid",
    separate_women_entrance: false,
    mosque_status: "inactive",
  });
  const [cities, setCities] = useState<{ id: number; name: string }[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [successProfile, setSuccessProfile] = useState("");
  const [errorsProfile, setErrorsProfile] = useState<
    Partial<Record<keyof ProfileState | "non_field_errors", string>>
  >({});

  useEffect(() => {
    async function fetchProfileData() {
      try {
        const [profileRes, citiesRes] = await Promise.all([
          apiRequest<any>({ path: "/mosques/my-mosque/" }),
          apiRequest<{ id: number; name: string }[]>({ path: "/locations/cities/" }),
        ]);
        if (profileRes) {
          setProfile({
            mosque_name: profileRes.mosque_name || "",
            city: profileRes.city || "",
            city_id: profileRes.city_id || profileRes.city_relation || null,
            address: profileRes.address || "",
            description: profileRes.description || "",
            contact_phone: profileRes.contact_phone || "",
            contact_email: profileRes.contact_email || "",
            website: profileRes.website || "",
            imam_name: profileRes.imam_name || "",
            imam_contact_number: profileRes.imam_contact_number || "",
            women_prayer_available: !!profileRes.women_prayer_available,
            parking_available: !!profileRes.parking_available,
            wudu_facility_available: !!profileRes.wudu_facility_available,
            wheelchair_accessible: !!profileRes.wheelchair_accessible,
            drinking_water_available: !!profileRes.drinking_water_available,
            washrooms_available: !!profileRes.washrooms_available,
            library_available: !!profileRes.library_available,
            quran_classes_available: !!profileRes.quran_classes_available,
            hifz_program_available: !!profileRes.hifz_program_available,
            nikah_service_available: !!profileRes.nikah_service_available,
            muslim_burial_ground_available: !!profileRes.muslim_burial_ground_available,
            community_hall_available: !!profileRes.community_hall_available,
            ramadan_iftar_available: !!profileRes.ramadan_iftar_available,
            eid_prayer_ground_available: !!profileRes.eid_prayer_ground_available,
            zakat_collection_available: !!profileRes.zakat_collection_available,
            funeral_prayer_facility_available: !!profileRes.funeral_prayer_facility_available,
            mosque_type: profileRes.mosque_type || "jama_masjid",
            separate_women_entrance: !!profileRes.separate_women_entrance,
            mosque_status: profileRes.mosque_status || "inactive",
          });
        }
        if (citiesRes) {
          const citiesList = Array.isArray(citiesRes) ? citiesRes : (citiesRes as any)?.results || [];
          setCities(citiesList);
        }
      } catch (err) {
        console.error("Failed to load profile", err);
      } finally {
        setLoadingProfile(false);
      }
    }
    fetchProfileData();
  }, []);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setSuccessProfile("");
    setErrorsProfile({});

    try {
      await apiRequest({
        path: "/mosques/my-mosque/",
        method: "PATCH",
        body: JSON.stringify(profile),
      });
      setSuccessProfile("Mosque profile updated successfully!");
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const fieldErrors: Record<string, string> = {};
        Object.entries(err.details as Record<string, any>).forEach(([k, v]) => {
          fieldErrors[k] = Array.isArray(v) ? v[0] : String(v);
        });
        setErrorsProfile(fieldErrors);
      }
    } finally {
      setSavingProfile(false);
    }
  };

  if (loadingProfile) {
    return <div className="p-8 text-center text-slate-500">Loading mosque profile...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Mosque Profile & Details</h2>

      {successProfile && (
        <div className="mb-6 p-4 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 text-sm font-medium">
          {successProfile}
        </div>
      )}

      {errorsProfile.non_field_errors && (
        <div className="mb-6 p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-sm font-medium">
          {errorsProfile.non_field_errors}
        </div>
      )}

      <form onSubmit={handleProfileSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Mosque Name *</label>
            <input
              type="text"
              value={profile.mosque_name}
              onChange={(e) => setProfile({ ...profile, mosque_name: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              required
            />
            {errorsProfile.mosque_name && <p className="mt-1 text-xs text-rose-600">{errorsProfile.mosque_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">City *</label>
            <select
              value={profile.city_id || ""}
              onChange={(e) => {
                const selectedId = Number(e.target.value);
                const matchedCity = cities.find((c) => c.id === selectedId);
                setProfile({
                  ...profile,
                  city_id: selectedId || null,
                  city: matchedCity ? matchedCity.name : profile.city,
                });
              }}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white"
            >
              <option value="">Select City</option>
              {cities.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            {errorsProfile.city && <p className="mt-1 text-xs text-rose-600">{errorsProfile.city}</p>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Address *</label>
          <textarea
            rows={3}
            value={profile.address}
            onChange={(e) => setProfile({ ...profile, address: e.target.value })}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
            required
          />
          {errorsProfile.address && <p className="mt-1 text-xs text-rose-600">{errorsProfile.address}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea
            rows={4}
            value={profile.description}
            onChange={(e) => setProfile({ ...profile, description: e.target.value })}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
          />
        </div>

        <div className="border-t border-slate-200 pt-6">
          <h3 className="text-md font-semibold text-slate-800 mb-4">Facilities & Services</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {FACILITIES_LIST.map((fac) => {
              const key = fac.key as keyof ProfileState;
              const isChecked = !!profile[key];
              return (
                <label
                  key={fac.key}
                  className={`flex items-start space-x-3 p-3.5 rounded-xl border transition cursor-pointer ${
                    isChecked
                      ? "border-emerald-500 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={(e) => setProfile({ ...profile, [key]: e.target.checked })}
                    className="mt-1 h-4 w-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg leading-none">{fac.icon}</span>
                      <span className="text-sm font-semibold text-slate-900">{fac.label}</span>
                    </div>
                    {fac.desc && (
                      <p className="mt-0.5 text-xs text-slate-500 leading-snug">{fac.desc}</p>
                    )}
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={savingProfile}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {savingProfile ? "Saving Profile..." : "Save Profile Changes"}
          </button>
        </div>
      </form>
    </div>
  );
}
