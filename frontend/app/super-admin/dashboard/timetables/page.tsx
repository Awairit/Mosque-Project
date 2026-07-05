"use client";

import { useState, useEffect, useRef } from "react";
import { apiRequest } from "@/lib/api/client";

type City = {
  id: number;
  name: string;
  timetable_policy: string;
  timetable_status: {
    latest_uploaded_year: number | null;
    current_year: number;
    needs_update: boolean;
  };
};

type PreviewRecord = {
  date: string;
  fajr_time: string;
  sunrise_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
};

type PreviewResponse = {
  city: string;
  year: number;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  warnings: string[];
  errors: string[];
  sheet_names: string[];
  active_sheet: string;
  existing_records_for_year: number;
  requires_overwrite_confirmation: boolean;
  preview_data: PreviewRecord[];
};

export default function SuperAdminTimetables() {
  const [cities, setCities] = useState<City[]>([]);
  const [selectedCityId, setSelectedCityId] = useState("");
  const [year, setYear] = useState<string>(new Date().getFullYear().toString());
  const [file, setFile] = useState<File | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [overwriteConfirmed, setOverwriteConfirmed] = useState(false);
  const [selectedSheet, setSelectedSheet] = useState("");
  const [importMode, setImportMode] = useState<"replace" | "merge">("replace");
  const [warningsAcknowledged, setWarningsAcknowledged] = useState(false);
  
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [count, setCount] = useState(0);

  const fetchCities = (pageNum = page) => {
    apiRequest<any>({
      path: `/platform/cities/?page=${pageNum}`,
      method: "GET",
    })
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setCities(list);
        if (data && typeof data === "object" && "count" in data) {
          setCount(data.count);
          setTotalPages(Math.ceil(data.count / 20));
        } else {
          setCount(list.length);
          setTotalPages(1);
        }
      })
      .catch((err) => console.error("Failed to fetch cities", err));
  };

  useEffect(() => {
    fetchCities(1);
  }, []);

  const handleAcknowledge = async (cityId: number) => {
    try {
      await apiRequest({
        path: `/platform/cities/${cityId}/timetables-acknowledge/`,
        method: "POST",
      });
      fetchCities(page);
    } catch (err: any) {
      console.error("Failed to acknowledge", err);
    }
  };

  const handlePreview = async (e?: React.FormEvent, sheetName?: string) => {
    if (e) e.preventDefault();
    if (!selectedCityId || !file || !year) {
      setError("Please select a city, year, and file.");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setPreview(null);
    setImportSuccess(null);
    setOverwriteConfirmed(false);
    setWarningsAcknowledged(false);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("year", year);
    if (sheetName) {
      formData.append("sheet_name", sheetName);
    }
    
    try {
      const data = await apiRequest<PreviewResponse>({
        path: `/platform/cities/${selectedCityId}/timetables/preview/`,
        method: "POST",
        body: formData,
      });
      setPreview(data);
      if (data.active_sheet) {
        setSelectedSheet(data.active_sheet);
      }
    } catch (err: any) {
      const msg = err.details?.detail || err.message || "Failed to generate preview.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async () => {
    if (!selectedCityId || !file || !year) return;
    
    if (preview?.requires_overwrite_confirmation && !overwriteConfirmed) {
      setError("Please resolve duplicate conflict by confirming resolution mode.");
      return;
    }

    if (preview && preview.warnings && preview.warnings.length > 0 && !warningsAcknowledged) {
      setError("Please acknowledge warnings before proceeding with import.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setImportSuccess(null);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("year", year);
    formData.append("overwrite", overwriteConfirmed.toString());
    formData.append("import_mode", importMode);
    if (selectedSheet) {
      formData.append("sheet_name", selectedSheet);
    }
    
    try {
      const data = await apiRequest<{detail: string}>({
        path: `/platform/cities/${selectedCityId}/timetables/import/`,
        method: "POST",
        body: formData,
      });
      setImportSuccess(data.detail);
      setPreview(null);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setWarningsAcknowledged(false);
      fetchCities(page);
    } catch (err: any) {
      const msg = err.details?.detail || err.message || "Failed to import timetable.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Annual Prayer Timetables</h1>
        <p className="text-sm text-slate-500 mt-1">Upload and manage authoritative CSV or XLSX calendars for citywide default prayer times.</p>
      </div>

      {cities.some(c => c.timetable_status.needs_update || (c.timetable_policy === "CONTINUE_PREVIOUS" && c.timetable_status.latest_uploaded_year && c.timetable_status.latest_uploaded_year < c.timetable_status.current_year)) && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Timetable Status & Reminders</h2>
          {cities.map((city) => {
            const status = city.timetable_status;
            
            if (city.timetable_policy === "CONTINUE_PREVIOUS" && status.latest_uploaded_year && status.latest_uploaded_year < status.current_year) {
              return (
                <div key={city.id} className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-900/20 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-bold text-blue-800 dark:text-blue-300">Prayer Timetable Reminder - {city.name}</h3>
                    <p className="mt-1 text-sm text-blue-700 dark:text-blue-400">
                      Current Active Timetable: <strong>{status.latest_uploaded_year}</strong><br />
                      Policy: Continue Previous Timetable Until Replaced<br />
                      If your local Islamic scholars have issued a newer timetable, you may upload it at any time. The existing timetable remains active.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedCityId(city.id.toString());
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="shrink-0 rounded-xl bg-white px-4 py-2 text-sm font-medium text-blue-700 shadow-sm border border-blue-200 hover:bg-blue-50 dark:bg-slate-800 dark:text-blue-400 dark:border-blue-800 dark:hover:bg-slate-700 transition-colors"
                  >
                    Upload New Timetable
                  </button>
                </div>
              );
            }

            if (status.needs_update) {
              return (
                <div key={city.id} className="rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-900/20 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-bold text-amber-800 dark:text-amber-300">Prayer Timetable Needs Update - {city.name}</h3>
                    <p className="mt-1 text-sm text-amber-700 dark:text-amber-400">
                      Current Timetable: <strong>{status.latest_uploaded_year || "None"}</strong><br />
                      Required: <strong>{status.current_year}</strong><br />
                      Policy: Annual Upload Required
                    </p>
                  </div>
                  <div className="flex flex-col sm:flex-row shrink-0 gap-3">
                    <button
                      onClick={() => handleAcknowledge(city.id)}
                      className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-amber-700 shadow-sm border border-amber-200 hover:bg-amber-50 dark:bg-slate-800 dark:text-amber-400 dark:border-amber-800 dark:hover:bg-slate-700 transition-colors"
                    >
                      Continue Using Existing
                    </button>
                    <button
                      onClick={() => {
                        setSelectedCityId(city.id.toString());
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }}
                      className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-amber-500 transition-colors"
                    >
                      Upload New Timetable
                    </button>
                  </div>
                </div>
              );
            }

            return null;
          })}
          
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
              <span className="text-xs text-slate-500">
                Showing cities page <strong className="font-bold text-slate-850 dark:text-slate-200">{page}</strong> of <strong className="font-bold text-slate-850 dark:text-slate-200">{totalPages}</strong>
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
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Upload File</h2>
            
            <form onSubmit={handlePreview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">City</label>
                <select
                  required
                  value={selectedCityId}
                  onChange={(e) => setSelectedCityId(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="" disabled>Select City</option>
                  {cities.map((city) => (
                    <option key={city.id} value={city.id}>{city.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Year</label>
                <input
                  type="number"
                  required
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  placeholder="YYYY"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Timetable File (CSV or XLSX)</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  required
                  accept=".csv, .xlsx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-xl file:border-0 file:bg-indigo-50 file:px-4 file:py-2.5 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-900/30 dark:file:text-indigo-400"
                />
                <p className="mt-2 text-xs text-slate-500">Columns required: Date, Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha.</p>
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 transition-colors"
                >
                  {isLoading ? "Processing..." : "Generate Preview"}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6 dark:border-red-900/50 dark:bg-red-900/20">
              <div className="flex gap-3">
                <div className="text-red-600 dark:text-red-400">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-red-800 dark:text-red-300">Validation Error</h3>
                  <p className="mt-1 text-sm text-red-700 dark:text-red-400">{error}</p>
                </div>
              </div>
            </div>
          )}

          {importSuccess && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 dark:border-emerald-900/50 dark:bg-emerald-900/20">
              <div className="flex gap-3">
                <div className="text-emerald-600 dark:text-emerald-400">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-emerald-800 dark:text-emerald-300">Import Successful</h3>
                  <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-400">{importSuccess}</p>
                </div>
              </div>
            </div>
          )}

          {preview && (
            <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden dark:border-slate-800 dark:bg-slate-900 shadow-sm">
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Previewing: {preview.city} ({preview.year})</h3>
                    <p className="text-sm text-slate-500 mt-1">Active Sheet: <strong className="font-semibold text-indigo-650 dark:text-indigo-400">{preview.active_sheet}</strong></p>
                    
                    {preview.sheet_names && preview.sheet_names.length > 1 && (
                      <div className="mt-3 flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-650 dark:text-slate-400">Choose Sheet:</span>
                        <select
                          value={selectedSheet}
                          onChange={(e) => {
                            setSelectedSheet(e.target.value);
                            handlePreview(undefined, e.target.value);
                          }}
                          className="rounded-lg border border-slate-350 bg-white px-2.5 py-1 text-xs text-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                        >
                          {preview.sheet_names.map((name) => (
                            <option key={name} value={name}>{name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <button
                      onClick={handleImport}
                      disabled={
                        isLoading || 
                        (preview.errors && preview.errors.length > 0) ||
                        (preview.requires_overwrite_confirmation && !overwriteConfirmed) ||
                        (preview.warnings && preview.warnings.length > 0 && !warningsAcknowledged)
                      }
                      className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-indigo-500 transition-colors disabled:opacity-40"
                    >
                      {isLoading ? "Importing..." : "Confirm & Import"}
                    </button>
                  </div>
                </div>

                {/* Import Summary Card */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
                  <div className="bg-white dark:bg-slate-850 p-3 rounded-xl border border-slate-200/60 dark:border-slate-800 text-center shadow-xs">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Total Rows</div>
                    <div className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">{preview.total_rows}</div>
                  </div>
                  <div className="bg-emerald-50/40 dark:bg-emerald-950/10 p-3 rounded-xl border border-emerald-100 dark:border-emerald-950/30 text-center shadow-xs">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-600 dark:text-emerald-400">Valid Rows</div>
                    <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mt-0.5">{preview.valid_rows}</div>
                  </div>
                  <div className="bg-rose-50/40 dark:bg-rose-950/10 p-3 rounded-xl border border-rose-100 dark:border-rose-950/30 text-center shadow-xs">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-rose-600 dark:text-rose-400">Invalid Rows</div>
                    <div className="text-lg font-bold text-rose-700 dark:text-rose-400 mt-0.5">{preview.invalid_rows}</div>
                  </div>
                  <div className="bg-amber-50/40 dark:bg-amber-950/10 p-3 rounded-xl border border-amber-100 dark:border-amber-950/30 text-center shadow-xs">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-amber-600 dark:text-amber-400">Warnings</div>
                    <div className="text-lg font-bold text-amber-700 dark:text-amber-400 mt-0.5">{preview.warnings?.length || 0}</div>
                  </div>
                </div>

                {/* Errors Panel */}
                {preview.errors && preview.errors.length > 0 && (
                  <div className="mt-4 rounded-xl border border-red-200 bg-red-50/50 p-4 dark:border-red-900/50 dark:bg-red-900/10">
                    <h4 className="text-sm font-bold text-red-900 dark:text-red-300 flex items-center gap-1.5">
                      <svg className="h-4 w-4 text-red-650" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      File Cannot Be Imported ({preview.errors.length} Errors)
                    </h4>
                    <p className="text-xs text-red-700 dark:text-red-400 mt-0.5">Please fix these errors in your file and regenerate preview:</p>
                    <ul className="mt-2 list-disc list-inside text-xs text-red-705 dark:text-red-400 space-y-1 max-h-40 overflow-y-auto">
                      {preview.errors.map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings Panel */}
                {preview.warnings && preview.warnings.length > 0 && (
                  <div className="mt-4 rounded-xl border border-amber-250 bg-amber-50/30 p-4 dark:border-amber-900/40 dark:bg-amber-900/10">
                    <h4 className="text-sm font-bold text-amber-900 dark:text-amber-300 flex items-center gap-1.5">
                      <svg className="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      Import Warnings ({preview.warnings.length})
                    </h4>
                    <ul className="mt-2 list-disc list-inside text-xs text-amber-750 dark:text-amber-400 space-y-1 max-h-40 overflow-y-auto">
                      {preview.warnings.map((warn, idx) => (
                        <li key={idx}>{warn}</li>
                      ))}
                    </ul>
                    <label className="flex items-center gap-2 cursor-pointer mt-3 pt-3 border-t border-amber-200/50 dark:border-amber-900/20">
                      <input
                        type="checkbox"
                        checked={warningsAcknowledged}
                        onChange={(e) => setWarningsAcknowledged(e.target.checked)}
                        className="h-4 w-4 rounded border-amber-300 text-amber-600 focus:ring-amber-500"
                      />
                      <span className="text-xs text-amber-800 dark:text-amber-300 font-semibold">I acknowledge these warnings and want to proceed with import.</span>
                    </label>
                  </div>
                )}

                {/* Duplicate Conflict Resolution Panel */}
                {preview.requires_overwrite_confirmation && (
                  <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/30 p-4 dark:border-indigo-900/40 dark:bg-indigo-900/10">
                    <h4 className="text-sm font-bold text-indigo-950 dark:text-indigo-300 flex items-center gap-1.5">
                      <svg className="h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      Duplicate Timetable Conflict Resolution
                    </h4>
                    <p className="text-xs text-indigo-800 dark:text-indigo-400 mt-1">
                      There are already {preview.existing_records_for_year} records for {preview.city} in {preview.year}. Please choose resolution:
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 mt-3">
                      <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-350 cursor-pointer">
                        <input
                          type="radio"
                          name="importMode"
                          value="replace"
                          checked={importMode === "replace"}
                          onChange={() => setImportMode("replace")}
                          className="h-4 w-4 border-slate-350 text-indigo-650 focus:ring-indigo-550"
                        />
                        <span><strong>Replace Mode</strong> (Permanently delete all existing default timings and replace them)</span>
                      </label>
                      <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-350 cursor-pointer">
                        <input
                          type="radio"
                          name="importMode"
                          value="merge"
                          checked={importMode === "merge"}
                          onChange={() => setImportMode("merge")}
                          className="h-4 w-4 border-slate-350 text-indigo-650 focus:ring-indigo-550"
                        />
                        <span><strong>Merge Mode</strong> (Overwrite overlapping dates, keep unmatched dates intact)</span>
                      </label>
                    </div>
                    <label className="flex items-start gap-2.5 cursor-pointer mt-4 pt-3 border-t border-indigo-200/50 dark:border-indigo-900/20">
                      <input
                        type="checkbox"
                        checked={overwriteConfirmed}
                        onChange={(e) => setOverwriteConfirmed(e.target.checked)}
                        className="h-4 w-4 rounded border-indigo-300 text-indigo-600 focus:ring-indigo-500 mt-0.5"
                      />
                      <span className="text-xs text-indigo-900 dark:text-indigo-300 font-semibold">I authorize modifying the default timetables database using the chosen resolution mode.</span>
                    </label>
                  </div>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-650 dark:bg-slate-800/40 dark:text-slate-400">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Date</th>
                      <th className="px-6 py-3 font-semibold">Fajr</th>
                      <th className="px-6 py-3 font-semibold">Sunrise</th>
                      <th className="px-6 py-3 font-semibold">Dhuhr</th>
                      <th className="px-6 py-3 font-semibold">Asr</th>
                      <th className="px-6 py-3 font-semibold">Maghrib</th>
                      <th className="px-6 py-3 font-semibold">Isha</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {preview.preview_data.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors">
                        <td className="px-6 py-3 font-medium text-slate-900 dark:text-white whitespace-nowrap">{row.date}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.fajr_time}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.sunrise_time}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.dhuhr_time}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.asr_time}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.maghrib_time}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{row.isha_time}</td>
                      </tr>
                    ))}
                    {preview.total_rows > preview.preview_data.length && (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 text-center text-xs text-slate-500 font-medium bg-slate-50 dark:bg-slate-800/20">
                          ... showing subset of {preview.preview_data.length} records of {preview.total_rows} total rows ...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {!preview && !error && !importSuccess && (
            <div className="rounded-2xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-700">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 mb-4">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">No file previewed</h3>
              <p className="mt-1 text-sm text-slate-500 max-w-sm mx-auto">Upload a valid timetable file to preview the parsed prayer times and validate the format before importing.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
