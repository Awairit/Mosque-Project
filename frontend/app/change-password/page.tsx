"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState, useEffect } from "react";
import { Eye, EyeOff, CheckCircle2, XCircle } from "lucide-react";
import { ApiError, apiRequest } from "@/lib/api/client";
import { GlobalHeader } from "@/components/layout/GlobalHeader";

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <div className="mt-1 text-sm text-red-600">{message}</div>;
}

export default function ChangePasswordPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const [form, setForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [success, setSuccess] = useState(false);

  const canSubmit = useMemo(
    () => form.current_password.trim().length > 0 && form.new_password.trim().length >= 8 && form.confirm_password.trim().length > 0 && form.new_password === form.confirm_password,
    [form]
  );

  const getStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };
  const strengthScore = getStrength(form.new_password);
  
  const strengthColor = () => {
    if (strengthScore === 0) return "bg-slate-200";
    if (strengthScore <= 1) return "bg-red-500";
    if (strengthScore === 2) return "bg-amber-500";
    if (strengthScore === 3) return "bg-emerald-500";
    return "bg-emerald-600";
  };

  const strengthLabel = () => {
    if (strengthScore === 0) return "";
    if (strengthScore <= 1) return "Weak";
    if (strengthScore === 2) return "Fair";
    if (strengthScore >= 3) return "Strong";
    return "";
  };

  const updateField = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "", non_field_errors: "" }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    
    if (form.new_password !== form.confirm_password) {
      setErrors({ confirm_password: "Passwords do not match." });
      return;
    }
    
    if (form.new_password.length < 8) {
      setErrors({ new_password: "Password must be at least 8 characters." });
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      await apiRequest({
        path: "/auth/change-password/",
        method: "POST",
        body: JSON.stringify({
          current_password: form.current_password,
          new_password: form.new_password,
        }),
      });

      localStorage.removeItem("must_change_password");
      setSuccess(true);
      
      // Automatic redirect after success
      setTimeout(() => {
        router.push("/dashboard");
      }, 2000);
      
    } catch (error) {
      if (error instanceof ApiError && error.details && typeof error.details === "object") {
        const errs: Record<string, string> = {};
        for (const [key, val] of Object.entries(error.details)) {
          errs[key] = Array.isArray(val) ? val[0] : String(val);
        }
        setErrors(errs);
      } else {
        setErrors({ non_field_errors: "An unexpected error occurred." });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <GlobalHeader />
        <main className="flex flex-1 items-center justify-center p-4">
          <div className="w-full max-w-md text-center py-10 bg-white rounded-2xl shadow-soft">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 mb-4">
              <CheckCircle2 className="h-10 w-10 text-emerald-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Password Updated</h3>
            <p className="text-sm text-slate-600 mb-6 px-6">
              Your password has been changed successfully. Redirecting to dashboard...
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <GlobalHeader />
      <main className="flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Change Password
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              Please change your temporary password to continue.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-soft sm:p-6"
          >
            <div className="grid gap-5">
              <div>
                <label
                  htmlFor="current_password"
                  className="block text-sm font-semibold text-slate-900"
                >
                  Current Password <span className="text-red-700">*</span>
                </label>
                <div className="relative mt-2">
                  <input
                    id="current_password"
                    name="current_password"
                    type={showCurrent ? "text" : "password"}
                    value={form.current_password}
                    onChange={(e) => updateField("current_password", e.target.value)}
                    className="min-h-12 w-full rounded-xl border border-slate-200 pl-4 pr-12 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                    disabled={isSubmitting}
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent(!showCurrent)}
                    className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 hover:text-slate-600 focus:outline-none"
                    tabIndex={-1}
                  >
                    {showCurrent ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                <FieldError message={errors.current_password} />
              </div>

              <div>
                <label
                  htmlFor="new_password"
                  className="block text-sm font-semibold text-slate-900"
                >
                  New Password <span className="text-red-700">*</span>
                </label>
                <div className="relative mt-2">
                  <input
                    id="new_password"
                    name="new_password"
                    type={showNew ? "text" : "password"}
                    value={form.new_password}
                    onChange={(e) => updateField("new_password", e.target.value)}
                    className="min-h-12 w-full rounded-xl border border-slate-200 pl-4 pr-12 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                    disabled={isSubmitting}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew(!showNew)}
                    className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 hover:text-slate-600 focus:outline-none"
                    tabIndex={-1}
                  >
                    {showNew ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                
                {form.new_password.length > 0 && (
                  <div className="mt-2">
                    <div className="flex gap-1 h-1.5">
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} className={`flex-1 rounded-full ${strengthScore >= i ? strengthColor() : 'bg-slate-200'}`}></div>
                      ))}
                    </div>
                    <div className="mt-1 flex justify-between items-center text-xs text-slate-500">
                      <span className={strengthColor().replace("bg-", "text-")}>{strengthLabel()}</span>
                    </div>
                  </div>
                )}
                
                <ul className="text-xs text-slate-600 space-y-1 mt-2">
                  <li className="flex items-center gap-1.5">
                    {form.new_password.length >= 8 ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    At least 8 characters
                  </li>
                  <li className="flex items-center gap-1.5">
                    {/[A-Z]/.test(form.new_password) ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    One uppercase letter
                  </li>
                  <li className="flex items-center gap-1.5">
                    {/[0-9]/.test(form.new_password) ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    One number
                  </li>
                </ul>

                <FieldError message={errors.new_password} />
              </div>

              <div>
                <label
                  htmlFor="confirm_password"
                  className="block text-sm font-semibold text-slate-900"
                >
                  Confirm Password <span className="text-red-700">*</span>
                </label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showNew ? "text" : "password"}
                  value={form.confirm_password}
                  onChange={(e) => updateField("confirm_password", e.target.value)}
                  className={`mt-2 min-h-12 w-full rounded-xl border px-4 text-slate-950 outline-none transition focus:ring-4 ${
                    form.confirm_password.length > 0 && form.new_password !== form.confirm_password
                      ? "border-red-300 focus:border-red-500 focus:ring-red-500/10"
                      : "border-slate-200 focus:border-emerald-900 focus:ring-emerald-900/10"
                  }`}
                  disabled={isSubmitting}
                />
                <FieldError message={errors.confirm_password} />
              </div>

              {errors.non_field_errors ? (
                <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
                  {errors.non_field_errors}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isSubmitting || !canSubmit}
                className="min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    Changing password...
                  </span>
                ) : "Change Password"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
