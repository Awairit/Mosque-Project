"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api/client";

type RequestDetail = {
  id: number;
  mosque_name: string;
  admin_name: string;
  mobile_number: string;
  email: string;
  city: string;
  city_raw: string;
  address: string;
  google_maps_link: string;
  google_maps_url: string;
  women_prayer_available: boolean;
  notes: string;
  status: "draft" | "whatsapp_verified" | "pending" | "under_verification" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
  mobile_verified: boolean;
  whatsapp_verified: boolean;
  whatsapp_verified_at?: string;
  verification_method?: string;
  verification_timestamp?: string;
  under_verification_at?: string;
  under_verification_by_username?: string;
  super_admin_notes?: string;
  approved_by_username?: string;
  approved_at?: string;
  rejected_by_username?: string;
  rejected_at?: string;
  rejection_reason?: string;
  duplicate_info?: {
    duplicate: boolean;
    reason: string;
    message: string;
    existing_admin: {
      name: string;
      mosque: string;
      city: string;
      status: string;
    };
  } | null;
};

type ApproveResponse = {
  detail: string;
  temp_password: string;
  username: string;
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function SuperAdminMosqueReviewPage({ params }: PageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const requestId = resolvedParams.id;

  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Rejection Modal state
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectError, setRejectError] = useState<string | null>(null);

  // Approval state
  const [isApproving, setIsApproving] = useState(false);
  const [approveSuccessData, setApproveSuccessData] = useState<ApproveResponse | null>(null);
  const [approveError, setApproveError] = useState<string | null>(null);

  // Reset Password state
  const [isResetting, setIsResetting] = useState(false);

  // Verification Notes and Status update states
  const [superAdminNotes, setSuperAdminNotes] = useState("");
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [notesSaveMessage, setNotesSaveMessage] = useState<string | null>(null);
  const [isMarkingUnderVerification, setIsMarkingUnderVerification] = useState(false);

  const fetchRequestDetail = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiRequest<RequestDetail>({
        path: `/platform/requests/${requestId}/`,
        method: "GET",
      });
      setRequest(data);
      setSuperAdminNotes(data.super_admin_notes || "");
    } catch (err: any) {
      console.error(err);
      setError("Failed to load registration request details.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequestDetail();
  }, [requestId]);

  const handleApprove = async () => {
    if (!confirm("Are you sure you want to approve this mosque registration request? This will create a live mosque record and its administrative account.")) {
      return;
    }

    setIsApproving(true);
    setApproveError(null);
    try {
      const data = await apiRequest<ApproveResponse>({
        path: `/platform/requests/${requestId}/approve/`,
        method: "POST",
      });
      setApproveSuccessData(data);
      // Refresh local model details
      fetchRequestDetail();
    } catch (err: any) {
      console.error(err);
      setApproveError(err?.message || "Failed to approve the registration request.");
    } finally {
      setIsApproving(false);
    }
  };

  const handleResetPassword = async () => {
    if (!confirm("Are you sure you want to reset the Mosque Admin password? The old temporary password will become invalid.")) {
      return;
    }

    setIsResetting(true);
    setApproveError(null);
    try {
      const data = await apiRequest<ApproveResponse>({
        path: `/platform/requests/${requestId}/reset-password/`,
        method: "POST",
      });
      setApproveSuccessData(data);
    } catch (err: any) {
      console.error(err);
      setApproveError(err?.message || "Failed to reset password.");
    } finally {
      setIsResetting(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectReason.trim()) {
      setRejectError("Rejection reason is required.");
      return;
    }

    setIsRejecting(true);
    setRejectError(null);
    try {
      await apiRequest({
        path: `/platform/requests/${requestId}/reject/`,
        method: "POST",
        body: JSON.stringify({ reason: rejectReason.trim() }),
      });
      setIsRejectModalOpen(false);
      fetchRequestDetail();
    } catch (err: any) {
      console.error(err);
      setRejectError(err?.message || "Failed to reject the registration request.");
    } finally {
      setIsRejecting(false);
    }
  };

  const handleSaveNotes = async () => {
    setIsSavingNotes(true);
    setNotesSaveMessage(null);
    try {
      await apiRequest({
        path: `/platform/requests/${requestId}/verification-notes/`,
        method: "PATCH",
        body: JSON.stringify({ super_admin_notes: superAdminNotes }),
      });
      setNotesSaveMessage("Internal verification notes saved successfully.");
      setTimeout(() => setNotesSaveMessage(null), 3000);
      fetchRequestDetail();
    } catch (err: any) {
      console.error(err);
      alert(err?.message || "Failed to save verification notes.");
    } finally {
      setIsSavingNotes(false);
    }
  };

  const handleMarkUnderVerification = async () => {
    if (!confirm("Mark this registration request as Under Verification to indicate that manual checking is in progress?")) {
      return;
    }
    setIsMarkingUnderVerification(true);
    try {
      await apiRequest({
        path: `/platform/requests/${requestId}/mark-under-verification/`,
        method: "POST",
      });
      fetchRequestDetail();
    } catch (err: any) {
      console.error(err);
      alert(err?.message || "Failed to mark request as under verification.");
    } finally {
      setIsMarkingUnderVerification(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "—";
    try {
      return new Date(dateString).toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="h-8 w-8 animate-spin text-emerald-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-xs text-slate-500 font-semibold">Loading registration form data...</span>
        </div>
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900/30 dark:bg-red-950/20">
        <h3 className="text-sm font-bold text-red-800 dark:text-red-400">Error Loading Details</h3>
        <p className="text-xs text-red-600 mt-1 dark:text-red-400/80">{error || "Request not found."}</p>
        <Link
          href="/super-admin/dashboard/mosques"
          className="mt-4 inline-flex rounded-xl bg-white px-4 py-2 text-xs font-bold text-slate-700 shadow-sm hover:bg-slate-50 border border-slate-200"
        >
          Back to Approvals
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top action bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/super-admin/dashboard/mosques"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to approvals
        </Link>

        {(request.status === "pending" || request.status === "whatsapp_verified" || request.status === "under_verification") && !approveSuccessData && (
          <div className="flex gap-2.5">
            {(request.status === "pending" || request.status === "whatsapp_verified") && (
              <button
                onClick={handleMarkUnderVerification}
                disabled={isMarkingUnderVerification}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-350 dark:hover:bg-slate-850 disabled:opacity-50"
              >
                {isMarkingUnderVerification ? "Updating..." : "Start Verification"}
              </button>
            )}
            <button
              onClick={() => setIsRejectModalOpen(true)}
              className="rounded-xl border border-rose-200 px-4 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 transition-colors dark:border-rose-900/30 dark:text-rose-400 dark:hover:bg-rose-950/20"
            >
              Reject Request
            </button>
            <button
              onClick={handleApprove}
              disabled={isApproving || !!request.duplicate_info}
              className="rounded-xl bg-emerald-700 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isApproving ? "Approving..." : "Approve Request"}
            </button>
          </div>
        )}

        {request.status === "approved" && !approveSuccessData && (
          <div className="flex gap-2.5">
            <button
              onClick={handleResetPassword}
              disabled={isResetting}
              className="rounded-xl border border-rose-200 px-4 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 transition-colors dark:border-rose-900/30 dark:text-rose-400 dark:hover:bg-rose-950/20 disabled:opacity-50"
            >
              {isResetting ? "Resetting..." : "Reset Password"}
            </button>
          </div>
        )}
      </div>

      {request.status === "pending" && request.duplicate_info && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-6 dark:border-rose-900/30 dark:bg-rose-950/10">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-rose-900 dark:text-rose-400">⚠ Duplicate Mosque Administrator Detected</h3>
              <p className="text-xs text-rose-700 mt-1 dark:text-rose-400/80">
                This registration cannot currently be approved.
              </p>
              
              <div className="mt-4 rounded-xl border border-rose-200 bg-white p-4 dark:border-rose-800 dark:bg-slate-900">
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-3">Reason:</p>
                <div className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <svg className="h-4 w-4 shrink-0 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{request.duplicate_info.message}</span>
                </div>

                <div className="mt-4 pt-4 border-t border-rose-100 dark:border-rose-900/30">
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">Existing Assignment</p>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 font-semibold block mb-1">Mosque:</span>
                      <strong className="text-slate-700 dark:text-slate-300">{request.duplicate_info.existing_admin.mosque}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block mb-1">City:</span>
                      <strong className="text-slate-700 dark:text-slate-300">{request.duplicate_info.existing_admin.city}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block mb-1">Status:</span>
                      <strong className="text-slate-700 dark:text-slate-300">{request.duplicate_info.existing_admin.status}</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal / Credentials card shown ONCE after approval */}
      {approveSuccessData && (
        <div className="rounded-2xl border border-emerald-250 bg-emerald-50/50 p-6 dark:border-emerald-900/30 dark:bg-emerald-950/10">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-400">
                {isResetting || (request.status === "approved" && !isApproving && approveSuccessData) ? "Password Reset Successful!" : "Mosque Approved & Account Registered!"}
              </h3>
              <p className="text-xs text-emerald-750 mt-1 dark:text-emerald-400/80">
                Below are the temporary admin login credentials. Make sure to share these securely with the mosque administrator. 
                <strong className="font-bold block mt-1 text-red-700 dark:text-red-400">IMPORTANT: This password is shown ONLY ONCE and will not be accessible again.</strong>
              </p>

              <div className="mt-4 max-w-sm rounded-xl border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-slate-900">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Login Username (Phone):</span>
                    <strong className="font-mono font-bold text-slate-800 dark:text-slate-200">{approveSuccessData.username}</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-semibold">Temporary Password:</span>
                    <strong className="font-mono font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded select-all dark:bg-emerald-950/40 dark:text-emerald-400">
                      {approveSuccessData.temp_password}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Errors displays */}
      {approveError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-800 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-400">
          {approveError}
        </div>
      )}

      {/* Grid panels */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main detail card */}
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              Mosque Details
            </h3>

            <div className="mt-4 grid gap-6 sm:grid-cols-2 text-xs">
              <div>
                <span className="text-slate-400 font-semibold block mb-1">Mosque Name</span>
                <p className="text-slate-800 font-bold dark:text-slate-200 text-sm">{request.mosque_name}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Status</span>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    request.status === "draft"
                      ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      : request.status === "whatsapp_verified"
                      ? "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-400"
                      : request.status === "pending"
                      ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                      : request.status === "under_verification"
                      ? "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400"
                      : request.status === "approved"
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
                      : "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400"
                  }`}
                >
                  {request.status.replace("_", " ")}
                </span>
              </div>

              <div className="sm:col-span-2">
                <span className="text-slate-400 font-semibold block mb-1">Street Address</span>
                <p className="text-slate-700 dark:text-slate-350 leading-relaxed font-semibold">{request.address || "No address provided."}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">City</span>
                <p className="text-slate-800 font-bold dark:text-slate-200">{request.city || request.city_raw || "—"}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Pincode</span>
                <p className="text-slate-700 dark:text-slate-400 font-medium">Not Provided</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Imam Name</span>
                <p className="text-slate-700 dark:text-slate-400 font-medium">Not Provided</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Google Maps Reference URL</span>
                {request.google_maps_link || request.google_maps_url ? (
                  <a
                    href={request.google_maps_link || request.google_maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-700 hover:underline font-bold dark:text-emerald-400 break-all"
                  >
                    {request.google_maps_link || request.google_maps_url}
                  </a>
                ) : (
                  <p className="text-slate-500 font-semibold">Not Provided</p>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              Registration Notes & Verification Files
            </h3>

            <div className="mt-4 space-y-4 text-xs">
              <div>
                <span className="text-slate-400 font-semibold block mb-1">User Notes / Details</span>
                <p className="bg-slate-50 rounded-xl p-4 text-slate-700 dark:bg-slate-950 dark:text-slate-350 leading-relaxed font-medium">
                  {request.notes || "No extra notes provided by submitter."}
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Mosque Images / Proof of Registry</span>
                <div className="border border-dashed border-slate-200 rounded-xl p-6 text-center text-slate-450 dark:border-slate-850">
                  <p className="text-xs">No media uploads attached to this registration request.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              Super Admin Internal Verification Notes
            </h3>
            <p className="text-xs text-slate-500 mt-1 mb-3">Internal only — never visible publicly. E.g. details of WhatsApp call or document verification.</p>
            <div className="space-y-3">
              <textarea
                rows={3}
                value={superAdminNotes}
                onChange={(e) => setSuperAdminNotes(e.target.value)}
                placeholder="E.g. Verified via WhatsApp call with Committee Secretary. Official registration certificate reviewed."
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-xs placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
              />
              <div className="flex justify-between items-center">
                {notesSaveMessage ? (
                  <span className="text-[11px] font-semibold text-emerald-600">{notesSaveMessage}</span>
                ) : <span />}
                <button
                  type="button"
                  onClick={handleSaveNotes}
                  disabled={isSavingNotes}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
                >
                  {isSavingNotes ? "Saving..." : "Save Notes"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right sidebar details */}
        <div className="space-y-6">
          {/* Submitter info */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              Submitter Profile
            </h3>

            <div className="mt-4 space-y-4 text-xs">
              <div>
                <span className="text-slate-400 font-semibold block">Contact Person</span>
                <p className="text-slate-800 font-bold mt-0.5 dark:text-slate-200">{request.admin_name || "—"}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block">Primary WhatsApp Contact</span>
                <p className="text-slate-800 font-bold mt-0.5 dark:text-slate-200 flex items-center gap-1.5 flex-wrap">
                  {request.mobile_number}
                  {request.whatsapp_verified && (
                    <span className="inline-flex items-center gap-0.5 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
                      ✓ WhatsApp Verified
                    </span>
                  )}
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block">Email Address</span>
                <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">{request.email || "Not Provided"}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block">Submission Timestamp</span>
                <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">{formatDate(request.created_at)}</p>
              </div>
            </div>
          </div>

          {/* Accommodation card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              Accommodations
            </h3>

            <div className="mt-4 space-y-3.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-semibold">Women's Prayer Area</span>
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    request.women_prayer_available
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
                      : "bg-slate-100 text-slate-500 dark:bg-slate-850 dark:text-slate-500"
                  }`}
                >
                  {request.women_prayer_available ? "Available" : "N/A"}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-semibold">Parking Lot</span>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full uppercase tracking-wider dark:bg-slate-850">
                  Pending Setup
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-semibold">Wudu Facility</span>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full uppercase tracking-wider dark:bg-slate-850">
                  Pending Setup
                </span>
              </div>
            </div>
          </div>

          {/* Approval log / Audit trail */}
          {(request.status !== "draft" || request.whatsapp_verified || request.under_verification_at) && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
                Action Log Audit
              </h3>

              <div className="mt-4 space-y-4 text-xs">
                {request.whatsapp_verified && (
                  <div>
                    <span className="text-slate-400 font-semibold block">WhatsApp Verified At</span>
                    <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">
                      {formatDate(request.whatsapp_verified_at || request.verification_timestamp)}
                    </p>
                  </div>
                )}
                {request.under_verification_at && (
                  <>
                    <div>
                      <span className="text-slate-400 font-semibold block">Verification Started By</span>
                      <p className="text-slate-800 font-bold mt-0.5 dark:text-slate-200">
                        @{request.under_verification_by_username || "system"}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block">Verification Started Date</span>
                      <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">{formatDate(request.under_verification_at)}</p>
                    </div>
                  </>
                )}
                {request.status === "approved" && (
                  <>
                    <div>
                      <span className="text-slate-400 font-semibold block">Approved By</span>
                      <p className="text-slate-800 font-bold mt-0.5 dark:text-slate-200">@{request.approved_by_username || "system"}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block">Approval Date</span>
                      <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">{formatDate(request.approved_at)}</p>
                    </div>
                  </>
                )}
                {request.status === "rejected" && (
                  <>
                    <div>
                      <span className="text-slate-400 font-semibold block">Rejected By</span>
                      <p className="text-slate-800 font-bold mt-0.5 dark:text-slate-200">@{request.rejected_by_username || "system"}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block">Rejection Date</span>
                      <p className="text-slate-700 mt-0.5 dark:text-slate-400 font-medium">{formatDate(request.rejected_at)}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block">Rejection Reason</span>
                      <p className="text-rose-800 bg-rose-50/50 border border-rose-100 rounded-xl p-3 font-semibold mt-1 dark:bg-rose-950/20 dark:text-rose-450 dark:border-rose-900/30">
                        {request.rejection_reason || "No reason specified."}
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Rejection Reasons Dialog Modal */}
      {isRejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900 animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Reject Registration Request</h3>
            <p className="text-xs text-slate-500 mt-1">Please provide a mandatory reason for rejecting this mosque registration request. Submitter will be notified.</p>

            <form onSubmit={handleRejectSubmit} className="mt-4 space-y-4">
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Reason for Rejection</label>
                <textarea
                  rows={4}
                  required
                  placeholder="e.g. Incomplete details, duplicate request, or invalid mobile contacts."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white p-3 text-xs placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              {rejectError && (
                <p className="text-xs font-semibold text-red-650">{rejectError}</p>
              )}

              <div className="flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsRejectModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-350 dark:hover:bg-slate-850"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRejecting}
                  className="rounded-xl bg-rose-700 px-4 py-2 text-xs font-bold text-white hover:bg-rose-600 transition-colors disabled:opacity-50"
                >
                  {isRejecting ? "Rejecting..." : "Confirm Rejection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
