"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api/client";

type RequestItem = {
  id: number;
  mosque_name: string;
  admin_name: string;
  mobile_number: string;
  city: string;
  status: "draft" | "whatsapp_verified" | "pending" | "under_verification" | "approved" | "rejected";
  created_at: string;
};

type ListResponse = {
  results: RequestItem[];
  count: number;
  num_pages: number;
};

export default function SuperAdminMosqueApprovals() {
  const router = useRouter();
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchInput, setSearchInput] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [count, setCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRequests = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({
        page: page.toString(),
        page_size: "10",
      });

      if (statusFilter !== "all") {
        queryParams.append("status", statusFilter);
      }
      if (searchQuery) {
        queryParams.append("search", searchQuery);
      }

      const res = await apiRequest<ListResponse>({
        path: `/platform/requests/?${queryParams.toString()}`,
        method: "GET",
      });
      setRequests(res.results);
      setCount(res.count);
      setTotalPages(res.num_pages || 1);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load registration requests. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [statusFilter, searchQuery, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearchQuery(searchInput);
  };

  const handleTabChange = (status: string) => {
    setStatusFilter(status);
    setPage(1);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Mosque Approvals</h1>
          <p className="text-sm text-slate-500 mt-1">Review, approve, or reject incoming registration requests from new mosques.</p>
        </div>
      </div>

      {/* Tabs and Search Bar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Status Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-800">
          {[
            { id: "pending", label: "Pending Reviews" },
            { id: "under_verification", label: "Under Verification" },
            { id: "approved", label: "Approved" },
            { id: "rejected", label: "Rejected" },
            { id: "all", label: "All Requests" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`px-4 py-2 text-xs font-semibold border-b-2 -mb-[2px] transition-colors ${
                statusFilter === tab.id
                  ? "border-emerald-600 text-emerald-600 dark:border-emerald-500 dark:text-emerald-500"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full max-w-md">
          <div className="relative flex-grow">
            <input
              type="text"
              placeholder="Search mosque name, admin, city, phone..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 pl-9 text-xs placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
            />
            <div className="absolute left-3 top-2.5 text-slate-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            {searchInput && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput("");
                  setSearchQuery("");
                  setPage(1);
                }}
                className="absolute right-3 top-2 text-slate-400 hover:text-slate-600"
              >
                Clear
              </button>
            )}
          </div>
          <button
            type="submit"
            className="rounded-xl bg-emerald-700 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-600 transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Main Table Card */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {isLoading ? (
          /* Loading Skeletons */
          <div className="p-6 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between py-2.5 animate-pulse border-b border-slate-100 last:border-0 dark:border-slate-800">
                <div className="space-y-2 w-1/3">
                  <div className="h-4 bg-slate-100 rounded dark:bg-slate-800 w-3/4"></div>
                  <div className="h-3 bg-slate-50 rounded dark:bg-slate-800 w-1/2"></div>
                </div>
                <div className="h-4 bg-slate-100 rounded dark:bg-slate-800 w-1/6"></div>
                <div className="h-6 bg-slate-100 rounded-full dark:bg-slate-800 w-16"></div>
              </div>
            ))}
          </div>
        ) : error ? (
          /* Error State */
          <div className="p-8 text-center text-red-500 dark:text-red-400">
            <p className="text-sm font-semibold">{error}</p>
            <button
              onClick={fetchRequests}
              className="mt-4 rounded-xl bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Retry
            </button>
          </div>
        ) : requests.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-50 text-slate-400 dark:bg-slate-800 dark:text-slate-500">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h3 className="mt-4 text-sm font-bold text-slate-900 dark:text-white">No registration requests found</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">There are no registration requests matching your current filters.</p>
          </div>
        ) : (
          /* Table Layout */
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-300">
                  <th className="px-6 py-3.5">Request ID</th>
                  <th className="px-6 py-3.5">Mosque Name</th>
                  <th className="px-6 py-3.5">City</th>
                  <th className="px-6 py-3.5">Contact Person</th>
                  <th className="px-6 py-3.5">Primary WhatsApp Contact</th>
                  <th className="px-6 py-3.5">Submitted Date</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {requests.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => router.push(`/super-admin/dashboard/mosques/${item.id}`)}
                    className="group cursor-pointer hover:bg-slate-50/70 transition-colors dark:hover:bg-slate-800/40"
                  >
                    <td className="px-6 py-4 font-semibold text-slate-500">#{item.id}</td>
                    <td className="px-6 py-4 font-bold text-slate-900 group-hover:text-emerald-700 dark:text-white dark:group-hover:text-emerald-400">
                      {item.mosque_name}
                    </td>
                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{item.city}</td>
                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{item.admin_name || "—"}</td>
                    <td className="px-6 py-4 font-medium text-slate-600 dark:text-slate-400">{item.mobile_number}</td>
                    <td className="px-6 py-4 text-slate-500">{formatDate(item.created_at)}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          item.status === "draft"
                            ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-350"
                            : item.status === "whatsapp_verified"
                            ? "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-400"
                            : item.status === "pending"
                            ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                            : item.status === "under_verification"
                            ? "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400"
                            : item.status === "approved"
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
                            : "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400"
                        }`}
                      >
                        {item.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Link
                        href={`/super-admin/dashboard/mosques/${item.id}`}
                        className="inline-flex rounded-xl bg-slate-50 px-3 py-1.5 text-[11px] font-bold text-slate-700 hover:bg-slate-100 transition-colors dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                      >
                        Review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls Footer */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4 dark:border-slate-800">
            <span className="text-xs text-slate-500">
              Showing page <strong className="font-bold text-slate-850 dark:text-slate-200">{page}</strong> of <strong className="font-bold text-slate-850 dark:text-slate-200">{totalPages}</strong> ({count} total records)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
                className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-650 hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-850"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
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
  );
}
