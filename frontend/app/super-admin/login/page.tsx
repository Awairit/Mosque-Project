import type { Metadata } from "next";

import { SuperAdminLoginForm } from "@/components/super-admin/SuperAdminLoginForm";

export const metadata: Metadata = {
  title: "Platform Console Login | Mosque Finder",
  description: "Secure administrative login portal for system administrators.",
};

export default function SuperAdminLoginPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-16 dark:bg-slate-950 sm:px-6 lg:px-8 flex flex-col justify-center">
      <div className="mx-auto w-full max-w-md">
        <div className="text-center mb-8">
          <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-inset ring-emerald-600/10 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-500/20">
            System Administration
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Mosque Finder Console
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Sign in with authorized super admin credentials to manage global platform operations.
          </p>
        </div>

        <SuperAdminLoginForm />
      </div>
    </main>
  );
}
