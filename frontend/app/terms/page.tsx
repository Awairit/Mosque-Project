import Link from "next/link";

export const metadata = {
  title: "Terms of Service",
  description: "Read our rules of usage, content ownership guidelines, and admin responsibilities.",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm sm:p-8 space-y-6">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-emerald-800 hover:text-emerald-950 transition-colors">
          ← Back to discovery
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">Terms of Service</h1>
        <p className="text-xs text-slate-500">Last updated: June 4, 2026</p>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">1. Acceptance of Terms</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            By accessing and using this platform, you agree to comply with and be bound by these Terms of Service. If you do not agree, please refrain from using the platform services.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">2. Visitor Responsibilities</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Visitors are welcome to browse listings, check prayer timings, and view announcements for personal use. You agree not to scrape page details, launch automated request sweeps, or misuse location discovery features.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">3. Mosque Administrator Responsibilities</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Registered administrators are responsible for maintaining the accuracy of their congregation (jamaat) timings, schedules, facilities, and announcements. You agree to upload only accurate timing records and verify coordinates prior to listing activation.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">4. Prohibited Content</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Posting false timings, unauthorized photo gallery uploads, spam notice board announcements, or offensive comments is strictly prohibited. We reserve the right to revoke administrative accounts and delete content violating these standards immediately.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">5. Contact Information</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            For questions about administrative terms or content removal requests, please write to <a href="mailto:support@example.com" className="text-emerald-800 hover:underline font-semibold">support@example.com</a>.
          </p>
        </section>
      </div>
    </main>
  );
}
