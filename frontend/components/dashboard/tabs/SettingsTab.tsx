"use client";

import { useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";

export default function SettingsTab() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg("");
    setErrorMsg("");

    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await apiRequest({
        path: "/auth/change-password/",
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      setSuccessMsg("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const detailsObj = err.details as Record<string, any>;
        setErrorMsg(detailsObj.detail || detailsObj.non_field_errors?.[0] || "Failed to change password.");
      } else {
        setErrorMsg("Failed to change password.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 max-w-2xl">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Account & Security Settings</h2>

      {successMsg && (
        <div className="mb-6 p-4 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 text-sm font-medium">
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div className="mb-6 p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-sm font-medium">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleChangePassword} className="space-y-4">
        <h3 className="text-md font-semibold text-slate-800 border-b pb-2">Change Password</h3>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Current Password *</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">New Password *</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Confirm New Password *</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {submitting ? "Updating Password..." : "Update Password"}
          </button>
        </div>
      </form>
    </div>
  );
}
