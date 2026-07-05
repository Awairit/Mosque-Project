"use client";

import Link from "next/link";
import { useState } from "react";
import { GlobalHeader } from "@/components/layout/GlobalHeader";
import { apiRequest, ApiError } from "@/lib/api/client";
import { ShieldAlert, Mail, MessageCircle, ClipboardList, CheckCircle2, AlertCircle } from "lucide-react";
import { PhoneInput } from "@/components/common/PhoneInput";

const SUPPORT_OPTIONS = [
  {
    icon: Mail,
    title: "Email Support",
    description: "Send your recovery request to our support email with your mosque name and any proof of identity.",
    action: "Send Email",
    href: "mailto:awaizmdir@gmail.com",
  },
  {
    icon: MessageCircle,
    title: "WhatsApp Support",
    description: "Contact our Admin directly on WhatsApp. Have your mosque registration details ready.",
    action: "WhatsApp Us",
    href: "https://wa.me/9011956596",
  },
];

export default function AccountRecoveryPage() {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    mosque_name: "",
    applicant_name: "",
    contact_email: "",
    contact_whatsapp: "",
    notes: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const updateField = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "", non_field_errors: "" }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.mosque_name.trim() || !form.applicant_name.trim() || !form.contact_whatsapp.trim()) {
      setErrors({
        non_field_errors: "Please fill in all required fields.",
      });
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    try {
      await apiRequest({
        path: "/auth/account-recovery/",
        method: "POST",
        body: JSON.stringify(form),
      });
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === "object") {
        const errs: Record<string, string> = {};
        for (const [key, val] of Object.entries(err.details)) {
          errs[key] = Array.isArray(val) ? val[0] : String(val);
        }
        setErrors(errs);
      } else {
        setErrors({ non_field_errors: "Failed to submit recovery request. Please try again." });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <GlobalHeader />
      <main className="flex flex-1 flex-col items-center px-4 py-12">
        <div className="w-full max-w-xl">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
              <ShieldAlert className="h-9 w-9 text-amber-600" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Account Recovery</h1>
            <p className="mt-3 text-sm leading-6 text-slate-600 max-w-md mx-auto">
              If you no longer have access to your registered WhatsApp number{" "}
              <strong>and</strong> registered email address, submit an Account Recovery request.
            </p>
            <p className="mt-2 text-sm text-slate-500">
              A Super Admin will verify your identity before restoring access.
            </p>
          </div>

          {/* Important note */}
          <div className="mb-8 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            <p className="font-semibold mb-1">Account Recovery is NOT Forgot Password</p>
            <p>
              If you still have access to your registered WhatsApp number or email,{" "}
              <Link href="/forgot-password" className="font-semibold underline underline-offset-2">
                use Forgot Password
              </Link>{" "}
              instead — it&apos;s instant and automated.
            </p>
          </div>

          {/* Success screen */}
          {success ? (
            <div className="rounded-2xl border border-emerald-200 bg-white p-6 text-center shadow-soft">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-slate-950">Recovery Request Submitted</h3>
              <p className="mt-2 text-sm text-slate-650">
                Your account recovery request has been logged. A Super Admin will manually review your case and reach out on the WhatsApp number or email provided.
              </p>
              <button
                onClick={() => {
                  setSuccess(false);
                  setShowForm(false);
                  setForm({ mosque_name: "", applicant_name: "", contact_email: "", contact_whatsapp: "", notes: "" });
                }}
                className="mt-6 rounded-full bg-emerald-900 px-6 py-2 text-sm font-semibold text-white transition hover:bg-emerald-950"
              >
                Done
              </button>
            </div>
          ) : showForm ? (
            /* Interactive Recovery Form */
            <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft space-y-4">
              <h2 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-emerald-800" />
                Account Recovery Request Form
              </h2>

              <div>
                <label className="block text-sm font-semibold text-slate-900">
                  Mosque Name <span className="text-red-700">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={form.mosque_name}
                  onChange={(e) => updateField("mosque_name", e.target.value)}
                  placeholder="Official name of the mosque"
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900">
                  Your Name <span className="text-red-700">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={form.applicant_name}
                  onChange={(e) => updateField("applicant_name", e.target.value)}
                  placeholder="Your full name"
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <PhoneInput
                  id="contact_whatsapp"
                  label="New WhatsApp Contact"
                  value={form.contact_whatsapp}
                  onChange={(val) => updateField("contact_whatsapp", val)}
                  disabled={isSubmitting}
                  error={errors.contact_whatsapp}
                  required
                />

                <div>
                  <label className="block text-sm font-semibold text-slate-900">
                    New Email Contact
                  </label>
                  <input
                    type="email"
                    value={form.contact_email}
                    onChange={(e) => updateField("contact_email", e.target.value)}
                    placeholder="e.g. admin@mosque.org"
                    className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900">
                  Reason / Proof of Authority
                </label>
                <p className="text-xs text-slate-500 mt-0.5">Explain why you lost access, and provide any details confirming your right to administer this mosque.</p>
                <textarea
                  rows={4}
                  value={form.notes}
                  onChange={(e) => updateField("notes", e.target.value)}
                  placeholder="E.g. The previous trustee who set up the account left, and we changed the official phone line."
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                />
              </div>

              {errors.non_field_errors && (
                <div className="rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-800 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  {errors.non_field_errors}
                </div>
              )}

              <div className="flex gap-3 justify-end pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="rounded-full border border-slate-200 px-6 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-full bg-emerald-900 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-950 disabled:opacity-50"
                >
                  {isSubmitting ? "Submitting..." : "Submit Recovery Request"}
                </button>
              </div>
            </form>
          ) : (
            /* Main Support Options */
            <div className="space-y-4">
              {/* Option 1: Support Form */}
              <div className="rounded-2xl border border-emerald-250 bg-white p-5 shadow-soft ring-1 ring-emerald-250">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                    <ClipboardList className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-900">Support Form</p>
                    <p className="mt-0.5 text-xs leading-5 text-slate-500">Submit a formal Account Recovery request online. A Super Admin will review it and contact you.</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowForm(true)}
                  className="mt-4 block w-full rounded-full bg-emerald-900 py-2.5 text-center text-sm font-semibold text-white transition hover:bg-emerald-950"
                >
                  Submit Recovery Request
                </button>
              </div>

              {/* Other Options */}
              {SUPPORT_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                return (
                  <div key={opt.title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-slate-900">{opt.title}</p>
                        <p className="mt-0.5 text-xs leading-5 text-slate-500">{opt.description}</p>
                      </div>
                    </div>
                    <a
                      href={opt.href}
                      className="mt-4 block w-full rounded-full border border-slate-200 py-2.5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    >
                      {opt.action}
                    </a>
                  </div>
                );
              })}
            </div>
          )}

          {/* Divider */}
          <div className="mt-8 border-t border-slate-200 pt-6 text-center text-sm text-slate-500">
            <Link href="/login" className="font-semibold text-emerald-900 hover:underline">
              ← Back to Login
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
