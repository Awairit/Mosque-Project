import Link from "next/link";

export const metadata = {
  title: "Privacy Policy",
  description: "Learn how we handle geolocation data, account credentials, and uploads.",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm sm:p-8 space-y-6">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-emerald-800 hover:text-emerald-950 transition-colors">
          ← Back to discovery
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">Privacy Policy</h1>
        <p className="text-xs text-slate-500">Last updated: June 4, 2026</p>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">1. Geolocation Usage</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            When you search for nearby mosques, we request permission to access your device's GPS coordinates. 
            <strong> This location data is processed entirely in-memory on your device and inside our API calculations to compute Haversine distances to the nearest mosques. We do not store, log, or track your physical coordinates on our servers.</strong>
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">2. Mosque Administrator Data</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            For registered mosque administrators, we securely store account details (username, encrypted passwords, email addresses, and phone numbers). This information is solely used to verify administration rights, allow console login, and send service updates.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">3. Mosque-Submitted Content & Images</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            Mosque coordinates, address parameters, facility checklists, daily timetables, and notice updates are made publicly accessible on the platform for public convenience. 
            Mosque administrators who upload images to the photo gallery are responsible for ensuring that they possess appropriate copyrights and usage permissions.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900">4. Contacting Us</h2>
          <p className="text-sm text-slate-600 leading-relaxed font-normal">
            If you have questions regarding location privacy or wish to request data deletions, please contact us at <a href="mailto:support@example.com" className="text-emerald-800 hover:underline font-semibold">support@example.com</a>.
          </p>
        </section>
      </div>
    </main>
  );
}
