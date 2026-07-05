"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";

type City = {
  id: number;
  name: string;
  latitude: string;
  longitude: string;
  timezone: string;
  timetable_policy: string;
  created_at: string;
  updated_at: string;
};

export default function SuperAdminCityManagement() {
  const [cities, setCities] = useState<City[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCity, setEditingCity] = useState<City | null>(null);
  
  const [formData, setFormData] = useState({
    name: "",
    latitude: "",
    longitude: "",
    timezone: "Asia/Kolkata",
    timetable_policy: "ANNUAL_UPLOAD",
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [count, setCount] = useState(0);

  const fetchCities = async (pageNum = page) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiRequest<any>({
        path: `/platform/cities/?page=${pageNum}`,
        method: "GET",
      });
      const list = Array.isArray(data) ? data : data.results || [];
      setCities(list);
      if (data && typeof data === "object" && "count" in data) {
        setCount(data.count);
        setTotalPages(Math.ceil(data.count / 20));
      } else {
        setCount(list.length);
        setTotalPages(1);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to load cities.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCities(1);
  }, []);

  const handleOpenModal = (city?: City) => {
    if (city) {
      setEditingCity(city);
      setFormData({
        name: city.name,
        latitude: city.latitude,
        longitude: city.longitude,
        timezone: city.timezone,
        timetable_policy: city.timetable_policy || "ANNUAL_UPLOAD",
      });
    } else {
      setEditingCity(null);
      setFormData({
        name: "",
        latitude: "",
        longitude: "",
        timezone: "Asia/Kolkata",
        timetable_policy: "ANNUAL_UPLOAD",
      });
    }
    setSubmitError(null);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingCity(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      if (editingCity) {
        await apiRequest<City>({
          path: `/platform/cities/${editingCity.id}/`,
          method: "PUT",
          body: JSON.stringify(formData),
        });
      } else {
        await apiRequest<City>({
          path: "/platform/cities/",
          method: "POST",
          body: JSON.stringify(formData),
        });
      }
      handleCloseModal();
      fetchCities(page);
    } catch (err: any) {
      console.error(err);
      setSubmitError(err?.message || "Failed to save city.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this city? This may affect associated mosques.")) {
      return;
    }
    try {
      await apiRequest({
        path: `/platform/cities/${id}/`,
        method: "DELETE",
      });
      fetchCities(page);
    } catch (err: any) {
      alert(err?.message || "Failed to delete city.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">City Management</h1>
          <p className="text-sm text-slate-500 mt-1">Configure global cities, coordinate boundaries, and default city-wide prayer time zones.</p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-indigo-500 transition-colors"
        >
          + Add City
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
              <tr>
                <th className="px-6 py-4 font-semibold">City Name</th>
                <th className="px-6 py-4 font-semibold">Coordinates</th>
                <th className="px-6 py-4 font-semibold">Timezone</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                    Loading cities...
                  </td>
                </tr>
              ) : cities.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                    No cities configured yet.
                  </td>
                </tr>
              ) : (
                cities.map((city) => (
                  <tr key={city.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">
                      {city.name}
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                      {city.latitude}, {city.longitude}
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                      <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        {city.timezone}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-3">
                        <button
                          onClick={() => handleOpenModal(city)}
                          className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(city.id)}
                          className="text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4 dark:border-slate-800">
              <span className="text-xs text-slate-500">
                Showing page <strong className="font-bold text-slate-850 dark:text-slate-200">{page}</strong> of <strong className="font-bold text-slate-850 dark:text-slate-200">{totalPages}</strong> ({count} total records)
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const newPage = Math.max(page - 1, 1);
                    setPage(newPage);
                    fetchCities(newPage);
                  }}
                  disabled={page === 1}
                  className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-650 hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-850"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const newPage = Math.min(page + 1, totalPages);
                    setPage(newPage);
                    fetchCities(newPage);
                  }}
                  disabled={page === totalPages}
                  className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-650 hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-850"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
              {editingCity ? "Edit City" : "Add City"}
            </h2>
            
            {submitError && (
              <div className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
                {submitError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  City Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-400 dark:focus:ring-indigo-400"
                  placeholder="e.g. Nanded"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-400 dark:focus:ring-indigo-400"
                    placeholder="19.1692"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-400 dark:focus:ring-indigo-400"
                    placeholder="77.3023"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Timezone
                </label>
                <input
                  type="text"
                  required
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-400 dark:focus:ring-indigo-400"
                  placeholder="e.g. Asia/Kolkata"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Prayer Timetable Policy
                </label>
                <select
                  required
                  value={formData.timetable_policy}
                  onChange={(e) => setFormData({ ...formData, timetable_policy: e.target.value })}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-400 dark:focus:ring-indigo-400"
                >
                  <option value="ANNUAL_UPLOAD">Annual Upload Required</option>
                  <option value="CONTINUE_PREVIOUS">Continue Previous Timetable Until Replaced</option>
                  <option value="ASTRONOMICAL" disabled>Astronomical Calculation (Future)</option>
                  <option value="AUTHORITY" disabled>Official Authority Source (Future)</option>
                </select>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Save City"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
