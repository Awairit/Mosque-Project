"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { ApiError, apiRequest } from "@/lib/api/client";

type FieldErrors = Partial<Record<"mobile_number" | "password" | "non_field_errors", string>>;

export default function CityAdminLoginPage() {
  const router = useRouter();
  const [mobileNumber, setMobileNumber] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit = useMemo(
    () => mobileNumber.trim().length > 0 && password.trim().length > 0,
    [mobileNumber, password]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await apiRequest<any>({
        path: "/auth/login/",
        method: "POST",
        body: JSON.stringify({
          mobile_number: mobileNumber,
          password: password,
        }),
      });

      // Save token and metadata in localStorage
      localStorage.setItem("auth_token", response.token);
      localStorage.setItem("city_admin_mobile", response.mobile_number);
      localStorage.setItem("city_admin_city_id", String(response.city_id));
      localStorage.setItem("city_admin_city_name", response.city_name);
      localStorage.setItem("user_role", response.role);

      if (response.must_change_password) {
        localStorage.setItem("must_change_password", "true");
        router.push("/change-password");
      } else {
        localStorage.removeItem("must_change_password");
        router.push("/city-admin/dashboard");
      }
    } catch (error) {
      if (error instanceof ApiError && error.details && typeof error.details === "object") {
        const details = error.details as Record<string, any>;
        const fieldErrors: FieldErrors = {};
        Object.entries(details).forEach(([key, value]) => {
          fieldErrors[key as keyof FieldErrors] = Array.isArray(value) ? value.join(" ") : String(value);
        });
        setErrors(fieldErrors);
      } else {
        setErrors({
          non_field_errors: "Invalid login credentials. Please try again."
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-16 dark:bg-slate-950 sm:px-6 lg:px-8 flex flex-col justify-center">
      <div className="mx-auto w-full max-w-md">
        <div className="text-center mb-8">
          <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-inset ring-emerald-600/10 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-500/20">
            City Administration Portal
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            City Admin Login
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Sign in with your registered WhatsApp contact number and password.
          </p>
        </div>

        <div className="bg-white px-6 py-8 shadow-sm ring-1 ring-slate-900/5 rounded-2xl dark:bg-slate-900 dark:ring-white/10 sm:px-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            {errors.non_field_errors && (
              <div className="rounded-lg bg-red-50 p-4 dark:bg-red-950/30 ring-1 ring-red-200 dark:ring-red-900">
                <p className="text-sm font-medium text-red-800 dark:text-red-300">
                  {errors.non_field_errors}
                </p>
              </div>
            )}

            <div>
              <label
                htmlFor="mobile_number"
                className="block text-sm font-semibold text-slate-950 dark:text-slate-50"
              >
                Primary WhatsApp Contact
              </label>
              <div className="mt-1.5">
                <input
                  id="mobile_number"
                  name="mobile_number"
                  type="text"
                  placeholder="e.g. +919999999999"
                  autoComplete="tel"
                  required
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  className="block w-full rounded-lg border-0 py-2.5 px-3.5 text-slate-950 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-emerald-600 sm:text-sm sm:leading-6 dark:bg-slate-800 dark:text-slate-50 dark:ring-slate-700 dark:focus:ring-emerald-500"
                />
              </div>
              {errors.mobile_number && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.mobile_number}</p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold text-slate-950 dark:text-slate-50"
                >
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  Forgot Password?
                </Link>
              </div>
              <div className="mt-1.5 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-lg border-0 py-2.5 px-3.5 pr-10 text-slate-950 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-emerald-600 sm:text-sm sm:leading-6 dark:bg-slate-800 dark:text-slate-50 dark:ring-slate-700 dark:focus:ring-emerald-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <Eye className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.password}</p>
              )}
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting || !canSubmit}
                className="flex w-full justify-center rounded-lg bg-emerald-600 py-2.5 px-3.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isSubmitting ? "Signing in..." : "Sign In"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
