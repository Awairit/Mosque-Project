"use client";

import { useEffect, useState } from "react";
import { Plus, Search, Shield, RefreshCw, Key, CheckCircle, XCircle, Building2 } from "lucide-react";
import { apiRequest } from "@/lib/api/client";

type City = {
  id: number;
  name: string;
};

type CityAdmin = {
  id: number;
  user_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  mobile_number: string;
  city_id: number;
  city_name: string;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
};

export default function CityAdminsPage() {
  const [cityAdmins, setCityAdmins] = useState<CityAdmin[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal States
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    mobile_number: "",
    city_id: "",
    email: "",
    first_name: "",
    last_name: "",
  });

  const [tempPasswordResult, setTempPasswordResult] = useState<{ username: string; temp_password: string } | null>(null);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [adminsData, citiesData] = await Promise.all([
        apiRequest<CityAdmin[]>({ path: "/platform/city-admins/" }),
        apiRequest<any>({ path: "/platform/cities/" }),
      ]);
      setCityAdmins(adminsData);
      setCities(citiesData.results || citiesData);
    } catch (err) {
      showToast("Failed to load City Administrators or Cities.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCityAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.mobile_number || !createForm.city_id) {
      showToast("Mobile number and City selection are required.", "error");
      return;
    }
    try {
      const data = await apiRequest<any>({
        path: "/platform/city-admins/",
        method: "POST",
        body: JSON.stringify({
          mobile_number: createForm.mobile_number,
          city_id: parseInt(createForm.city_id),
          email: createForm.email,
          first_name: createForm.first_name,
          last_name: createForm.last_name,
        }),
      });

      showToast("City Administrator created successfully!", "success");
      setIsCreateModalOpen(false);
      setTempPasswordResult({
        username: data.username,
        temp_password: data.temp_password,
      });
      setCreateForm({ mobile_number: "", city_id: "", email: "", first_name: "", last_name: "" });
      loadData();
    } catch (err: any) {
      showToast(err?.details?.mobile_number?.[0] || err?.message || "Failed to create City Administrator.", "error");
    }
  };

  const handleToggleActive = async (admin: CityAdmin) => {
    try {
      await apiRequest({
        path: `/platform/city-admins/${admin.id}/`,
        method: "PATCH",
        body: JSON.stringify({ is_active: !admin.is_active }),
      });
      showToast(`City Admin account ${admin.is_active ? "deactivated" : "activated"}.`, "success");
      loadData();
    } catch (err) {
      showToast("Failed to update status.", "error");
    }
  };

  const handleResetPassword = async (admin: CityAdmin) => {
    if (!confirm(`Are you sure you want to reset password for City Admin ${admin.mobile_number}?`)) return;
    try {
      const res = await apiRequest<any>({
        path: `/platform/city-admins/${admin.id}/reset-password/`,
        method: "POST",
      });
      setTempPasswordResult({
        username: res.username,
        temp_password: res.temp_password,
      });
      showToast("Password reset successfully.", "success");
      loadData();
    } catch (err) {
      showToast("Failed to reset password.", "error");
    }
  };

  const filteredAdmins = cityAdmins.filter(
    (a) =>
      a.city_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.mobile_number.includes(searchQuery) ||
      a.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (a.email && a.email.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 rounded-xl px-4 py-3 text-sm font-medium shadow-lg transition-all ${
            toast.type === "success" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Shield className="h-6 w-6 text-emerald-600" /> City Administrators
          </h1>
          <p className="text-sm text-slate-500">
            Assign and manage city-scoped administrative access across all registered cities.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add City Admin
          </button>
        </div>
      </div>

      {/* Temp Password Generated Alert Modal */}
      {tempPasswordResult && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-5 dark:border-emerald-900/50 dark:bg-emerald-950/30">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-base font-bold text-emerald-900 dark:text-emerald-300 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" /> Temporary Credentials Generated
              </h3>
              <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-400">
                Provide these login credentials to the City Administrator. They will be forced to change password on first login.
              </p>
              <div className="mt-3 flex flex-wrap gap-4 text-sm font-mono bg-white dark:bg-slate-900 p-3 rounded-xl border border-emerald-200 dark:border-emerald-800">
                <div>
                  <span className="text-xs text-slate-500 font-sans block">Mobile / Username:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{tempPasswordResult.username}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 font-sans block">Temporary Password:</span>
                  <span className="font-bold text-emerald-700 dark:text-emerald-400">{tempPasswordResult.temp_password}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setTempPasswordResult(null)}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 dark:text-emerald-400"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by city, mobile, email or name..."
          className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
        />
      </div>

      {/* City Admins Table */}
      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden dark:border-slate-800 dark:bg-slate-900 shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading City Administrators...</div>
        ) : filteredAdmins.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No City Administrators found. Click "Add City Admin" to create one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3.5">Assigned City</th>
                  <th className="px-5 py-3.5">Mobile Number</th>
                  <th className="px-5 py-3.5">Name / Email</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredAdmins.map((admin) => (
                  <tr key={admin.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-5 py-4 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-emerald-600" />
                      {admin.city_name}
                    </td>
                    <td className="px-5 py-4 font-mono text-slate-700 dark:text-slate-300">
                      {admin.mobile_number}
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-400">
                      <div>{admin.first_name || admin.last_name ? `${admin.first_name} ${admin.last_name}` : "City Administrator"}</div>
                      {admin.email && <div className="text-xs text-slate-400">{admin.email}</div>}
                    </td>
                    <td className="px-5 py-4">
                      {admin.is_active ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400">
                          <CheckCircle className="h-3.5 w-3.5" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                          <XCircle className="h-3.5 w-3.5" /> Deactivated
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleResetPassword(admin)}
                          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:text-amber-400 transition-colors"
                          title="Reset Password"
                        >
                          <Key className="h-3.5 w-3.5" /> Reset Pass
                        </button>
                        <button
                          onClick={() => handleToggleActive(admin)}
                          className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                            admin.is_active
                              ? "bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-950/40 dark:text-red-400"
                              : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-400"
                          }`}
                        >
                          {admin.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Add New City Administrator</h2>
            <form onSubmit={handleCreateCityAdmin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Assign City *
                </label>
                <select
                  value={createForm.city_id}
                  onChange={(e) => setCreateForm({ ...createForm, city_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  required
                >
                  <option value="">Select a city...</option>
                  {cities.map((city) => (
                    <option key={city.id} value={city.id}>
                      {city.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Mobile Number * (e.g. +919876543210)
                </label>
                <input
                  type="text"
                  value={createForm.mobile_number}
                  onChange={(e) => setCreateForm({ ...createForm, mobile_number: e.target.value })}
                  placeholder="+919876543210"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">First Name</label>
                  <input
                    type="text"
                    value={createForm.first_name}
                    onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={createForm.last_name}
                    onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Email Address</label>
                <input
                  type="email"
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  placeholder="admin@example.com"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700"
                >
                  Create & Generate Temp Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
