"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";
import { Eye, EyeOff, CheckCircle2, XCircle } from "lucide-react";
import { PhoneInput } from "@/components/common/PhoneInput";
import { OTPInput } from "@/components/common/OTPInput";
import { ResendTimer } from "@/components/common/ResendTimer";

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <div className="mt-1 text-sm text-red-600">{message}</div>;
}

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1); // 1: Request, 2: Verify, 3: Reset, 4: Success
  
  // State for Step 1
  const [mobileNumber, setMobileNumber] = useState("");
  
  // State for Step 2
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  
  // State for Step 3
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Password strength logic
  const getStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };
  const strengthScore = getStrength(newPassword);
  
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

  const handleRequestOTP = async (e: FormEvent) => {
    e.preventDefault();
    if (!mobileNumber.trim()) return;

    setIsSubmitting(true);
    setError("");

    try {
      await apiRequest({
        path: "/auth/forgot-password/request/",
        method: "POST",
        body: JSON.stringify({ mobile_number: mobileNumber }),
      });
      setStep(2);
    } catch (err: any) {
      setError(err.details?.mobile_number?.[0] || err.details?.non_field_errors?.[0] || err.message || "Failed to process request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOTP = async (e: FormEvent) => {
    e.preventDefault();
    if (!otp.trim()) return;

    setIsSubmitting(true);
    setError("");

    try {
      const res = await apiRequest<{ reset_token: string }>({
        path: "/auth/forgot-password/verify/",
        method: "POST",
        body: JSON.stringify({ mobile_number: mobileNumber, otp }),
      });
      setResetToken(res.reset_token);
      setStep(3);
    } catch (err: any) {
      setError(err.details?.non_field_errors?.[0] || err.message || "Invalid OTP.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOTP = async () => {
    setError("");
    try {
      await apiRequest({
        path: "/auth/forgot-password/request/",
        method: "POST",
        body: JSON.stringify({ mobile_number: mobileNumber }),
      });
    } catch (err: any) {
      setError(
        err.details?.mobile_number?.[0] ||
          err.details?.non_field_errors?.[0] ||
          err.message ||
          "Failed to resend OTP."
      );
    }
  };

  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      await apiRequest({
        path: "/auth/forgot-password/reset/",
        method: "POST",
        body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
      });
      setStep(4);
    } catch (err: any) {
      setError(err.details?.new_password?.[0] || err.details?.non_field_errors?.[0] || err.message || "Failed to reset password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <main className="flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-md">
          
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              {step === 1 && "Forgot Password"}
              {step === 2 && "Verify OTP"}
              {step === 3 && "Reset Password"}
              {step === 4 && "Success"}
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              {step === 1 && "Enter your WhatsApp number to receive a verification code."}
              {step === 2 && `We've sent a 6-digit code to ${mobileNumber}.`}
              {step === 3 && "Create a new strong password."}
              {step === 4 && "Your password has been reset successfully."}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-soft sm:p-6">
            
            {/* Step 1: Request OTP */}
            {step === 1 && (
              <form onSubmit={handleRequestOTP} className="grid gap-5">
                <PhoneInput
                  id="mobile_number"
                  label="Primary WhatsApp Contact"
                  value={mobileNumber}
                  onChange={setMobileNumber}
                  disabled={isSubmitting}
                  error={error}
                  required
                />

                <button
                  type="submit"
                  disabled={isSubmitting || !mobileNumber.trim()}
                  className="min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      Sending OTP...
                    </span>
                  ) : "Send OTP"}
                </button>
              </form>
            )}

            {/* Step 2: Verify OTP */}
            {step === 2 && (
              <form onSubmit={handleVerifyOTP} className="grid gap-5">
                <div>
                  <label htmlFor="otp" className="mb-3 block text-center text-sm font-semibold text-slate-900">
                    Verification Code <span className="text-red-700">*</span>
                  </label>
                  <OTPInput
                    value={otp}
                    onChange={setOtp}
                    disabled={isSubmitting}
                  />
                  <FieldError message={error} />
                </div>

                <ResendTimer
                  onResend={handleResendOTP}
                  disabled={isSubmitting}
                />

                <button
                  type="submit"
                  disabled={isSubmitting || otp.length !== 6}
                  className="min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      Verifying...
                    </span>
                  ) : "Verify Code"}
                </button>
                
                <div className="text-center text-sm text-slate-650 border-t border-slate-100 pt-3">
                  <button type="button" onClick={() => { setStep(1); setOtp(""); setError(""); }} className="hover:underline hover:text-slate-900">
                    Change WhatsApp Contact
                  </button>
                </div>
              </form>
            )}

            {/* Step 3: Reset Password */}
            {step === 3 && (
              <form onSubmit={handleResetPassword} className="grid gap-5">
                <div>
                  <label htmlFor="new_password" className="block text-sm font-semibold text-slate-900">
                    New Password <span className="text-red-700">*</span>
                  </label>
                  <div className="relative mt-2">
                    <input
                      id="new_password"
                      name="new_password"
                      type={showPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="min-h-12 w-full rounded-xl border border-slate-200 px-4 pr-12 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
                      disabled={isSubmitting}
                      placeholder="At least 8 characters"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                  
                  {/* Password Strength Indicator */}
                  {newPassword.length > 0 && (
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

                  <FieldError message={error} />
                </div>

                <ul className="text-xs text-slate-600 space-y-1 mt-2">
                  <li className="flex items-center gap-1.5">
                    {newPassword.length >= 8 ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    At least 8 characters
                  </li>
                  <li className="flex items-center gap-1.5">
                    {/[A-Z]/.test(newPassword) ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    One uppercase letter
                  </li>
                  <li className="flex items-center gap-1.5">
                    {/[0-9]/.test(newPassword) ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}
                    One number
                  </li>
                </ul>

                <button
                  type="submit"
                  disabled={isSubmitting || newPassword.length < 8}
                  className="mt-2 min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      Resetting...
                    </span>
                  ) : "Reset Password"}
                </button>
              </form>
            )}

            {/* Step 4: Success */}
            {step === 4 && (
              <div className="text-center py-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 mb-4">
                  <CheckCircle2 className="h-10 w-10 text-emerald-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">Password Reset Complete</h3>
                <p className="text-sm text-slate-600 mb-6">
                  You can now log in to your account with your new password.
                </p>
                <Link
                  href="/login"
                  className="block w-full min-h-12 flex items-center justify-center rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950"
                >
                  Go to Login
                </Link>
              </div>
            )}

            {step === 1 && (
              <div className="mt-6 space-y-3 text-center text-sm text-slate-600">
                <div>
                  Remember your password?{" "}
                  <Link
                    href="/login"
                    className="font-semibold text-emerald-900 hover:underline"
                  >
                    Login
                  </Link>
                </div>
                <div className="border-t border-slate-100 pt-3">
                  Lost access to both WhatsApp and email?{" "}
                  <Link
                    href="/account-recovery"
                    className="font-semibold text-slate-700 hover:underline"
                  >
                    Account Recovery
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
