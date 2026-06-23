import Link from "next/link";

export const metadata = {
  title: "About Us",
  description: "Learn more about the mission, goals, and builders behind the Mosque Finder platform.",
};

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm sm:p-8 space-y-6">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-emerald-800 hover:text-emerald-950 transition-colors">
          ← Back to discovery
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">About Us</h1>
        <p className="text-sm text-slate-600 leading-relaxed font-normal">
          Welcome to <strong>Mosque Finder</strong>, a community-focused, geo-aware platform designed to help travelers and local residents find accurate prayer schedules, congregation (jamaat) timings, and community announcements directly from the source.
        </p>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">Our Mission</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Unlike standard scrape engines that contain stale records, our platform prioritizes verified, admin-managed profiles. We empower local mosque representatives to manage their profiles, upload announcements, publish community events, and organize congregation timings.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">Key Features</h2>
          <ul className="list-disc pl-5 text-sm text-slate-600 space-y-2 font-normal">
            <li><strong>Geolocation Search</strong>: Auto-detects coordinates and returns the 5 nearest mosques within a 100km radius.</li>
            <li><strong>Verified Times</strong>: Priority daily city schedules are preferred over fallback defaults.</li>
            <li><strong>Community Announcements</strong>: Urgent alerts, Jumuah sermon schedules, and local lecture schedules.</li>
            <li><strong>Janazah Notices</strong>: Verified, respectful funeral notices with built-in family contact controls.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">Development attribution</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Mosque Finder is designed and developed by <strong>Awair_it</strong>, dedicated to building lightweight, performant, and accessible digital products for local communities.
          </p>
        </section>
      </div>
    </main>
  );
}
