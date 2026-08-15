"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import { ShieldAlert, CheckCircle2, XCircle, Clock, Search, RefreshCw, X } from "lucide-react";

interface AccountRecoveryRequestItem {
  id: number;
  mosque_name: string;
  applicant_name: string;
  previous_registered_contact: string;
  contact_email: string;
  contact_whatsapp: string;
  notes: string;
  status: "pending" | "under_review" | "approved" | "rejected";
  reviewed_by: number | null;
  reviewed_by_username: string | null;
  reviewed_at: string | null;
  review_notes: string;
  target_user: number | null;
  created_at: string;
  updated_at: string;
}

export default function AccountRecoveryManagementPage() {
  const [requests, setRequests] = useState<AccountRecoveryRequestItem[]>([]);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal State
  const [activeRequest, setActiveRequest] = useState<AccountRecoveryRequestItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string>("");
  const [customMobileNumber, setCustomMobileNumber] = useState<string>("");
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

  const fetchRequests = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const query = selectedStatusFilter !== "all" ? `?status=${selectedStatusFilter}` : "";
      const res = await apiRequest<{
        count: number;
        pending_count: number;
        results: AccountRecoveryRequestItem[];
      }>({
        path: `/platform/account-recovery/${query}`,
      });
      setRequests(res.results || []);
      setPendingCount(res.pending_count || 0);
    } catch (err: any) {
      setError(err?.message || "Failed to load account recovery requests.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [selectedStatusFilter]);

  const openReviewModal = (req: AccountRecoveryRequestItem) => {
    setActiveRequest(req);
    setReviewNotes(req.review_notes || "");
    setCustomMobileNumber(req.contact_whatsapp || "");
    setActionSuccessMessage(null);
    setActionErrorMessage(null);
  };

  const closeReviewModal = () => {
    setActiveRequest(null);
    setIsSubmittingAction(false);
    setActionSuccessMessage(null);
    setActionErrorMessage(null);
  };

  const handleApprove = async () => {
    if (!activeRequest) return;
    setIsSubmittingAction(true);
    setActionErrorMessage(null);
    setActionSuccessMessage(null);
    try {
      const res = await apiRequest<{ detail: string; request: AccountRecoveryRequestItem }>({
        path: `/platform/account-recovery/${activeRequest.id}/approve/`,
        method: "POST",
        body: JSON.stringify({
          review_notes: reviewNotes,
          new_mobile_number: customMobileNumber,
        }),
      });
      setActionSuccessMessage(res.detail || "Recovery request approved successfully.");
      setActiveRequest(res.request);
      fetchRequests();
    } catch (err: any) {
      const msg = err?.details?.detail || err?.message || "Failed to approve recovery request.";
      setActionErrorMessage(msg);
      fetchRequests();
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleReject = async () => {
    if (!activeRequest) return;
    setIsSubmittingAction(true);
    setActionErrorMessage(null);
    setActionSuccessMessage(null);
    try {
      const res = await apiRequest<{ detail: string; request: AccountRecoveryRequestItem }>({
        path: `/platform/account-recovery/${activeRequest.id}/reject/`,
        method: "POST",
        body: JSON.stringify({
          review_notes: reviewNotes,
        }),
      });
      setActionSuccessMessage(res.detail || "Recovery request rejected successfully.");
      setActiveRequest(res.request);
      fetchRequests();
    } catch (err: any) {
      const msg = err?.details?.detail || err?.message || "Failed to reject recovery request.";
      setActionErrorMessage(msg);
      fetchRequests();
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleReopen = async () => {
    if (!activeRequest) return;
    setIsSubmittingAction(true);
    setActionErrorMessage(null);
    setActionSuccessMessage(null);
    try {
      const res = await apiRequest<{ detail: string; request: AccountRecoveryRequestItem }>({
        path: `/platform/account-recovery/${activeRequest.id}/reopen/`,
        method: "POST",
      });
      setActionSuccessMessage(res.detail || "Recovery request reopened successfully.");
      setActiveRequest(res.request);
      fetchRequests();
    } catch (err: any) {
      const msg = err?.details?.detail || err?.message || "Failed to reopen recovery request.";
      setActionErrorMessage(msg);
      fetchRequests();
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.mosque_name.toLowerCase().includes(q) ||
      r.applicant_name.toLowerCase().includes(q) ||
      r.contact_whatsapp.toLowerCase().includes(q) ||
      r.contact_email.toLowerCase().includes(q)
    );
  });

  const countPending = requests.filter((r) => r.status === "pending").length;
  const countApproved = requests.filter((r) => r.status === "approved").length;
  const countRejected = requests.filter((r) => r.status === "rejected").length;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <ShieldAlert className="h-7 w-7 text-amber-600" />
            Account Recovery Requests
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Review identity proof and restore account access for trustees and administrators.
          </p>
        </div>
        <button
          onClick={fetchRequests}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stats overview */}
      <div className="grid gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-5 dark:border-amber-900/30 dark:bg-amber-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-800 dark:text-amber-400 uppercase tracking-wider">Pending Review</span>
            <Clock className="h-5 w-5 text-amber-600" />
          </div>
          <p className="mt-3 text-3xl font-bold text-amber-900 dark:text-amber-300">{pendingCount || countPending}</p>
        </div>

        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5 dark:border-emerald-900/30 dark:bg-emerald-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider">Approved</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="mt-3 text-3xl font-bold text-emerald-900 dark:text-emerald-300">{countApproved}</p>
        </div>

        <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-5 dark:border-rose-900/30 dark:bg-rose-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-800 dark:text-rose-400 uppercase tracking-wider">Rejected</span>
            <XCircle className="h-5 w-5 text-rose-600" />
          </div>
          <p className="mt-3 text-3xl font-bold text-rose-900 dark:text-rose-300">{countRejected}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Requests</span>
            <ShieldAlert className="h-5 w-5 text-slate-400" />
          </div>
          <p className="mt-3 text-3xl font-bold text-slate-900 dark:text-white">{requests.length}</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex gap-2 border-b sm:border-b-0 pb-2 sm:pb-0 border-slate-100 dark:border-slate-800 overflow-x-auto">
          {["all", "pending", "approved", "rejected"].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatusFilter(st)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold capitalize transition ${
                selectedStatusFilter === st
                  ? "bg-emerald-800 text-white dark:bg-emerald-700"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400"
              }`}
            >
              {st}
              {st === "pending" && pendingCount > 0 && (
                <span className="ml-2 rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-bold text-white">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search mosque, name or phone..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-4 py-2 text-xs text-slate-900 outline-none transition focus:border-emerald-800 focus:bg-white dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
        </div>
      </div>

      {/* Table Section */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-500">
            <RefreshCw className="h-6 w-6 animate-spin text-emerald-700 mr-3" />
            Loading recovery requests...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 text-sm font-medium">{error}</div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center text-slate-500 dark:text-slate-400">
            No recovery requests found matching your filter criteria.
          </div>
        ) : (
          <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-950 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-3.5">ID / Mosque</th>
                <th className="px-6 py-3.5">Requester Name</th>
                <th className="px-6 py-3.5">New WhatsApp</th>
                <th className="px-6 py-3.5">Email Contact</th>
                <th className="px-6 py-3.5">Submitted Date</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredRequests.map((req) => (
                <tr key={req.id} className="hover:bg-slate-50/80 transition dark:hover:bg-slate-800/40">
                  <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">
                    <div className="text-xs font-bold text-slate-400">#{req.id}</div>
                    <div>{req.mosque_name}</div>
                  </td>
                  <td className="px-6 py-4">{req.applicant_name}</td>
                  <td className="px-6 py-4 font-mono text-xs">{req.contact_whatsapp}</td>
                  <td className="px-6 py-4 text-xs">{req.contact_email || "—"}</td>
                  <td className="px-6 py-4 text-xs">
                    {new Date(req.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                        req.status === "pending"
                          ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                          : req.status === "approved"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                          : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                      }`}
                    >
                      {req.status === "pending" && <Clock className="h-3.5 w-3.5" />}
                      {req.status === "approved" && <CheckCircle2 className="h-3.5 w-3.5" />}
                      {req.status === "rejected" && <XCircle className="h-3.5 w-3.5" />}
                      {req.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => openReviewModal(req)}
                      className="rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Review Modal */}
      {activeRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-amber-600" />
                  Account Recovery Request #{activeRequest.id}
                </h2>
                <p className="text-xs text-slate-500">Submitted on {new Date(activeRequest.created_at).toLocaleString("en-IN")}</p>
              </div>
              <button onClick={closeReviewModal} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Request Information Details */}
            <div className="mt-4 space-y-3.5 text-sm">
              <div className="grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-3.5 dark:bg-slate-950">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">Mosque Name</span>
                  <p className="font-semibold text-slate-900 dark:text-white mt-0.5">{activeRequest.mosque_name}</p>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">Requester Name</span>
                  <p className="font-semibold text-slate-900 dark:text-white mt-0.5">{activeRequest.applicant_name}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-3.5 dark:bg-slate-950">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">Previous Registered Contact</span>
                  <p className="font-mono font-medium text-slate-900 dark:text-white mt-0.5">{activeRequest.previous_registered_contact || "Not provided"}</p>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">New WhatsApp Contact</span>
                  <p className="font-mono font-medium text-slate-900 dark:text-white mt-0.5">{activeRequest.contact_whatsapp}</p>
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-3.5 dark:bg-slate-950">
                <span className="text-xs font-semibold text-slate-500 uppercase">New Contact Email</span>
                <p className="font-medium text-slate-900 dark:text-white mt-0.5">{activeRequest.contact_email || "Not provided"}</p>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Reason / Proof of Authority</span>
                <p className="mt-1 rounded-xl border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
                  {activeRequest.notes || "No explanation provided."}
                </p>
              </div>

              {/* Status & Review Notes */}
              <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Current Status</span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-3 py-0.5 text-xs font-bold uppercase ${
                      activeRequest.status === "pending"
                        ? "bg-amber-100 text-amber-800"
                        : activeRequest.status === "approved"
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {activeRequest.status}
                  </span>
                </div>

                {activeRequest.reviewed_by_username && (
                  <p className="text-xs text-slate-500">
                    Reviewed by <strong>{activeRequest.reviewed_by_username}</strong> on{" "}
                    {activeRequest.reviewed_at ? new Date(activeRequest.reviewed_at).toLocaleString("en-IN") : ""}
                  </p>
                )}

                {activeRequest.status === "pending" && (
                  <>
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 text-xs text-emerald-900">
                      <p className="font-semibold">Approval Side Effects:</p>
                      <p className="mt-0.5 leading-relaxed text-emerald-800">
                        Approving this request will restore administrator access and update the registered mosque&apos;s official contact information.
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Mobile Number to Restore/Set (E.164)
                      </label>
                      <input
                        type="text"
                        value={customMobileNumber}
                        onChange={(e) => setCustomMobileNumber(e.target.value)}
                        placeholder="+919876543210"
                        className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-900 outline-none focus:border-emerald-800 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Super Admin Review Notes / Reason
                      </label>
                      <textarea
                        rows={2}
                        value={reviewNotes}
                        onChange={(e) => setReviewNotes(e.target.value)}
                        placeholder="Add review notes or justification..."
                        className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-900 outline-none focus:border-emerald-800 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                      />
                    </div>
                  </>
                )}

                {activeRequest.status !== "pending" && activeRequest.review_notes && (
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase">Super Admin Notes</span>
                    <p className="mt-1 text-xs text-slate-700 dark:text-slate-300 italic">{activeRequest.review_notes}</p>
                  </div>
                )}
              </div>

              {actionSuccessMessage && (
                <div className="rounded-xl bg-emerald-50 p-3 text-xs font-semibold text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  {actionSuccessMessage}
                </div>
              )}

              {actionErrorMessage && (
                <div className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-800 flex items-center gap-2">
                  <XCircle className="h-4 w-4" />
                  {actionErrorMessage}
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
              <button
                onClick={closeReviewModal}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300"
              >
                Close
              </button>

              {activeRequest.status === "pending" && (
                <>
                  <button
                    onClick={handleReject}
                    disabled={isSubmittingAction}
                    className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 disabled:opacity-50"
                  >
                    Reject Request
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={isSubmittingAction}
                    className="rounded-xl bg-emerald-800 px-5 py-2 text-xs font-semibold text-white transition hover:bg-emerald-900 disabled:opacity-50"
                  >
                    {isSubmittingAction ? "Processing..." : "Approve Recovery"}
                  </button>
                </>
              )}

              {activeRequest.status === "rejected" && (
                <button
                  onClick={handleReopen}
                  disabled={isSubmittingAction}
                  className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-2 text-xs font-semibold text-amber-800 hover:bg-amber-100 transition disabled:opacity-50"
                >
                  {isSubmittingAction ? "Reopening..." : "Reopen Request"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
