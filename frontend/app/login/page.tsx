import type { Metadata } from "next";

import { LoginForm } from "@/components/login/LoginForm";

export const metadata: Metadata = {
  title: "Mosque Admin Login",
  description: "Login page for verified mosque administrators.",
};

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-page px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-4xl gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-start pt-8 lg:pt-16">
        <section className="pt-4">
          <p className="inline-flex rounded-full border border-emerald-900/10 bg-white px-4 py-2 text-sm font-medium text-emerald-900 shadow-sm">
            Mosque Admin Portal
          </p>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Access your dashboard.
          </h1>
          <p className="mt-5 max-w-xl leading-7 text-slate-600">
            Log in with your registered WhatsApp number and password to
            manage your mosque&apos;s jamaat timings, facilities, events, and schedules.
          </p>
        </section>

        <LoginForm />
      </div>
    </main>
  );
}
