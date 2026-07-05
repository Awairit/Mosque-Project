import React, { useState, useEffect } from "react";
import { Clock } from "lucide-react";

interface ResendTimerProps {
  onResend: () => void;
  disabled: boolean;
  maxAttempts?: number;
}

export function ResendTimer({
  onResend,
  disabled,
  maxAttempts = 3,
}: ResendTimerProps) {
  const [seconds, setSeconds] = useState(30);
  const [canResend, setCanResend] = useState(false);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    if (seconds <= 0) {
      setCanResend(true);
      return;
    }
    const t = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [seconds]);

  const handleResend = () => {
    if (attempts >= maxAttempts) return;
    setSeconds(30);
    setCanResend(false);
    setAttempts((a) => a + 1);
    onResend();
  };

  if (attempts >= maxAttempts) {
    return (
      <div className="mt-4 text-center text-sm text-red-500 font-medium select-none animate-fade-in">
        Maximum resend attempts reached. Please verify the WhatsApp number or contact support.
      </div>
    );
  }

  return (
    <div className="mt-4 text-center text-sm text-slate-500 flex flex-col sm:flex-row items-center justify-center gap-1">
      <span>Didn&apos;t receive the OTP?</span>
      {canResend ? (
        <button
          type="button"
          onClick={handleResend}
          disabled={disabled}
          className="font-semibold text-emerald-900 hover:text-emerald-950 hover:underline focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:text-emerald-500 dark:hover:text-emerald-450"
        >
          Resend OTP
        </button>
      ) : (
        <span className="flex items-center gap-1 font-medium text-slate-650 dark:text-slate-450 select-none">
          <Clock className="h-3.5 w-3.5 animate-pulse text-emerald-800 dark:text-emerald-500" />
          Resend in {seconds}s
        </span>
      )}
    </div>
  );
}
