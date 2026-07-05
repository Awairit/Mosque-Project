"use client";

import { FormEvent, useState, useRef, useEffect } from "react";
import { apiRequest, ApiError } from "@/lib/api/client";
import {
  CheckCircle2,
  MessageCircle,
  ShieldCheck,
  ClipboardList,
  Clock,
} from "lucide-react";
import { PhoneInput } from "@/components/common/PhoneInput";
import { OTPInput } from "@/components/common/OTPInput";
import { ResendTimer } from "@/components/common/ResendTimer";


// ─── Types ───────────────────────────────────────────────────────────────────

type Step = 1 | 2 | 3 | 4;

type FormData = {
  mosque_name: string;
  admin_name: string;
  mobile_number: string;
  email: string;
  city: string;
  address: string;
  google_maps_link: string;
  women_prayer_available: boolean;
  imam_name: string;
  notes: string;
};

type FieldErrors = Partial<Record<keyof FormData | "non_field_errors" | "otp", string>>;

const initialForm: FormData = {
  mosque_name: "",
  admin_name: "",
  mobile_number: "",
  email: "",
  city: "",
  address: "",
  google_maps_link: "",
  women_prayer_available: false,
  imam_name: "",
  notes: "",
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1.5 text-sm text-red-600">{message}</p>;
}

function InputField({
  id,
  label,
  required,
  hint,
  type = "text",
  value,
  onChange,
  disabled,
  inputMode,
  autoComplete,
  placeholder,
  error,
}: {
  id: string;
  label: string;
  required?: boolean;
  hint?: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
  autoComplete?: string;
  placeholder?: string;
  error?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-slate-900">
        {label} {required && <span className="text-red-600">*</span>}
      </label>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        inputMode={inputMode}
        autoComplete={autoComplete}
        placeholder={placeholder}
        className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10 disabled:bg-slate-50 disabled:text-slate-400"
      />
      <FieldError message={error} />
    </div>
  );
}

// ─── Step indicators ─────────────────────────────────────────────────────────

const STEPS = [
  { label: "Mosque Info", icon: ClipboardList },
  { label: "Verify WhatsApp", icon: MessageCircle },
  { label: "Submitted", icon: CheckCircle2 },
];

function StepIndicator({ current }: { current: Step }) {
  return (
    <div className="mb-8 flex items-center justify-center gap-2">
      {STEPS.map((s, idx) => {
        const stepNum = (idx + 1) as Step;
        const done = current > stepNum;
        const active = current === stepNum;
        const Icon = s.icon;
        return (
          <div key={s.label} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                done
                  ? "bg-emerald-600 text-white"
                  : active
                  ? "bg-emerald-900 text-white"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {done ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
            </div>
            <span
              className={`hidden text-xs font-medium sm:block ${
                active ? "text-emerald-900" : done ? "text-emerald-700" : "text-slate-400"
              }`}
            >
              {s.label}
            </span>
            {idx < STEPS.length - 1 && (
              <div className={`mx-1 h-px w-6 sm:w-12 ${done ? "bg-emerald-400" : "bg-slate-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// OTPInput and ResendTimer are now imported from '@/components/common/'

// ─── Main Component ──────────────────────────────────────────────────────────

export function MosqueRegistrationForm() {
  const [step, setStep] = useState<Step>(1);
  const [form, setForm] = useState<FormData>(initialForm);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // OTP state
  const [otp, setOtp] = useState("");
  const [verificationToken, setVerificationToken] = useState("");

  const updateField = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: undefined, non_field_errors: undefined }));
  };

  // ── Step 1 → Step 2: Send OTP ─────────────────────────────────────────────

  const handleSendOTP = async () => {
    const nextErrors: FieldErrors = {};
    if (!form.mosque_name.trim()) nextErrors.mosque_name = "Mosque name is required.";
    if (!form.mobile_number.trim()) nextErrors.mobile_number = "WhatsApp number is required.";
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    try {
      await apiRequest({
        path: "/mosque-registration/otp/request/",
        method: "POST",
        body: JSON.stringify({ mobile_number: form.mobile_number }),
      });
      setOtp("");
      setStep(2);
    } catch (err: any) {
      if (err instanceof ApiError && err.details) {
        const e: FieldErrors = {};
        for (const [k, v] of Object.entries(err.details as Record<string, unknown>)) {
          e[k as keyof FieldErrors] = Array.isArray(v) ? v[0] : String(v);
        }
        setErrors(e);
      } else {
        setErrors({ non_field_errors: "Failed to send OTP. Please try again." });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOTP = async () => {
    setIsSubmitting(true);
    try {
      await apiRequest({
        path: "/mosque-registration/otp/request/",
        method: "POST",
        body: JSON.stringify({ mobile_number: form.mobile_number }),
      });
    } catch {
      // Silently fail – user will see an error on verify
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Step 2 → Step 3: Verify OTP + Submit ─────────────────────────────────

  const handleVerifyAndSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (otp.length !== 6) {
      setErrors({ otp: "Please enter the 6-digit code." });
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      // 1. Verify OTP → get verification_token
      const verifyRes = await apiRequest<{ verification_token: string }>({
        path: "/mosque-registration/otp/verify/",
        method: "POST",
        body: JSON.stringify({ mobile_number: form.mobile_number, otp }),
      });
      const token = verifyRes.verification_token;

      // 2. Submit registration with verification_token attached
      await apiRequest({
        path: "/mosque-registration/",
        method: "POST",
        body: JSON.stringify({ ...form, verification_token: token }),
      });

      setVerificationToken(token);
      setStep(3);
    } catch (err: any) {
      if (err instanceof ApiError && err.details) {
        const e: FieldErrors = {};
        for (const [k, v] of Object.entries(err.details as Record<string, unknown>)) {
          e[k as keyof FieldErrors] = Array.isArray(v) ? v[0] : String(v);
        }
        // Map non_field_errors to otp field for OTP step
        if (e.non_field_errors && step === 2) {
          e.otp = e.non_field_errors;
        }
        setErrors(e);
      } else {
        setErrors({ non_field_errors: "Something went wrong. Please try again." });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Success screen ─────────────────────────────────────────────────────────
  if (step === 3) {
    return (
      <div className="rounded-2xl border border-emerald-900/10 bg-white p-6 shadow-soft">
        <div className="text-center">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
            <ShieldCheck className="h-9 w-9 text-emerald-700" />
          </div>
          <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 mb-4">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Registration Submitted
          </div>
          <h2 className="text-2xl font-bold text-slate-950">
            Your registration has been received
          </h2>
          <div className="mt-5 space-y-4 text-sm text-slate-600 text-left bg-slate-50 rounded-xl p-5">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-600" />
              <p>
                <strong className="text-slate-900">WhatsApp Verified.</strong> Your WhatsApp number{" "}
                <strong>{form.mobile_number}</strong> has been verified.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <Clock className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
              <p>
                <strong className="text-slate-900">Pending Manual Verification.</strong> Our Super Admin will
                contact you on your verified WhatsApp number to confirm your identity and authority to
                represent the mosque.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-400" />
              <p>
                After approval, you will receive your <strong className="text-slate-900">temporary
                login credentials</strong> on your verified WhatsApp number.
              </p>
            </div>
          </div>
          <p className="mt-5 text-xs text-slate-400">
            This is a trust-based platform. We verify every mosque before it appears publicly.
          </p>
          <button
            type="button"
            onClick={() => { setStep(1); setForm(initialForm); setOtp(""); }}
            className="mt-6 text-sm font-semibold text-emerald-800 hover:underline"
          >
            Submit another registration
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-soft sm:p-6">
      <StepIndicator current={step} />

      {/* ── Step 1: Mosque Information ─────────────────────────────────────── */}
      {step === 1 && (
        <div className="grid gap-5">
          <InputField
            id="mosque_name"
            label="Mosque name"
            required
            value={form.mosque_name}
            onChange={(v) => updateField("mosque_name", v)}
            autoComplete="organization"
            error={errors.mosque_name}
          />

          <InputField
            id="admin_name"
            label="Your name"
            value={form.admin_name}
            onChange={(v) => updateField("admin_name", v)}
            autoComplete="name"
            error={errors.admin_name}
          />

          <PhoneInput
            id="mobile_number"
            label="Primary WhatsApp Contact"
            hint="This verified WhatsApp number will be used for communication, verification, account recovery, and important platform notifications."
            value={form.mobile_number}
            onChange={(val) => updateField("mobile_number", val)}
            disabled={isSubmitting}
            error={errors.mobile_number}
            required
          />

          <div>
            <label htmlFor="email" className="block text-sm font-semibold text-slate-900">
              Email address
              <span className="ml-1.5 text-xs font-normal text-slate-500">(optional — recommended for notifications)</span>
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              autoComplete="email"
              inputMode="email"
              className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            />
            <FieldError message={errors.email} />
          </div>

          <InputField
            id="city"
            label="City"
            value={form.city}
            onChange={(v) => updateField("city", v)}
            autoComplete="address-level2"
            error={errors.city}
          />

          <div>
            <label htmlFor="address" className="block text-sm font-semibold text-slate-900">Address</label>
            <textarea
              id="address"
              name="address"
              value={form.address}
              onChange={(e) => updateField("address", e.target.value)}
              rows={3}
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            />
            <FieldError message={errors.address} />
          </div>

          <InputField
            id="google_maps_link"
            label="Google Maps link"
            value={form.google_maps_link}
            onChange={(v) => updateField("google_maps_link", v)}
            inputMode="url"
            error={errors.google_maps_link}
          />

          <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 cursor-pointer">
            <input
              type="checkbox"
              checked={form.women_prayer_available}
              onChange={(e) => updateField("women_prayer_available", e.target.checked)}
              className="mt-0.5 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
            />
            <span>
              <span className="block text-sm font-semibold text-slate-900">Women&apos;s prayer space available</span>
              <span className="mt-0.5 block text-xs text-slate-500">Helps visitors know available facilities.</span>
            </span>
          </label>

          <InputField
            id="imam_name"
            label="Imam name"
            hint="(optional)"
            value={form.imam_name}
            onChange={(v) => updateField("imam_name", v)}
            error={errors.imam_name}
          />

          <div>
            <label htmlFor="notes" className="block text-sm font-semibold text-slate-900">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              rows={3}
              placeholder="Share anything useful for verification."
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            />
            <FieldError message={errors.notes} />
          </div>

          {errors.non_field_errors && (
            <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {errors.non_field_errors}
            </div>
          )}

          <button
            type="button"
            onClick={handleSendOTP}
            disabled={isSubmitting || !form.mosque_name.trim() || !form.mobile_number.trim()}
            className="min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Sending OTP...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4" />
                Continue — Verify WhatsApp
              </span>
            )}
          </button>
        </div>
      )}

      {/* ── Step 2: Verify WhatsApp OTP ───────────────────────────────────── */}
      {step === 2 && (
        <form onSubmit={handleVerifyAndSubmit} className="grid gap-6">
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-sm text-emerald-800 text-center">
            <MessageCircle className="mx-auto mb-2 h-6 w-6 text-emerald-600" />
            <strong>OTP sent to WhatsApp</strong>
            <br />
            <span className="text-emerald-700 font-mono">{form.mobile_number}</span>
          </div>

          <div>
            <label className="mb-3 block text-center text-sm font-semibold text-slate-900">
              Enter 6-digit verification code
            </label>
            <OTPInput value={otp} onChange={setOtp} disabled={isSubmitting} />
            <FieldError message={errors.otp} />
          </div>

          <ResendTimer onResend={handleResendOTP} disabled={isSubmitting} />

          {errors.non_field_errors && (
            <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 text-center">
              {errors.non_field_errors}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || otp.length !== 6}
            className="min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Verifying & Submitting...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" />
                Verify & Submit Registration
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => { setStep(1); setOtp(""); setErrors({}); }}
            className="text-center text-sm text-slate-500 hover:text-slate-800 hover:underline"
          >
            ← Change WhatsApp number
          </button>
        </form>
      )}
    </div>
  );
}
