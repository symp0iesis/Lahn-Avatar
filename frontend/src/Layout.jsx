import { Outlet, Link, useLocation } from "react-router-dom";

export default function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-screen font-sans">
      {/* Sidebar */}
      <nav className="w-64 bg-gradient-to-b from-green-100 to-stone-100 p-5 shadow-md flex flex-col gap-4">
        <h2 className="text-2xl font-semibold text-stone-700 mb-6">🌿 Lahn Avatar</h2>

        <Link
          to="/chat"
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            pathname === "/chat"
              ? "bg-amber-300 text-amber-900"
              : "text-stone-700 hover:bg-amber-100 hover:text-amber-900"
          }`}
        >
          🧠 Chat with the River
        </Link>

        <Link
          to="/experience"
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            pathname === "/experience"
              ? "bg-amber-300 text-amber-900"
              : "text-stone-700 hover:bg-amber-100 hover:text-amber-900"
          }`}
        >
          ✍️ Share Experience
        </Link>
      </nav>

      {/* Main content */}
      <main className="flex-1 p-8 bg-gradient-to-br from-stone-50 to-green-50">
        <Outlet />
      </main>
    </div>
  );
}
