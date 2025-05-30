import { Outlet, Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { Menu } from "lucide-react";      // or any hamburger icon

export default function Layout() {
  const { pathname } = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex min-h-screen font-sans">
      {/* Hamburger button, only on small screens */}
      <button
        className="p-2 m-2 rounded-md bg-white shadow-md md:hidden"
        onClick={() => setIsOpen(o => !o)}
      >
        <Menu size={24} />
      </button>

      {/* Sidebar: hidden on mobile unless isOpen, always shown on md+ */}
      <nav
        className={`
          fixed inset-y-0 left-0 bg-gradient-to-b from-green-100 to-stone-100 p-5
          shadow-md flex flex-col gap-4
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:relative md:w-64
        `}
      >
        <h2 className="text-2xl font-semibold text-stone-700 mb-6">
          🌊 Lahn Avatar
        </h2>

        {["/chat", "/voice-chat", "/experience", "/mirror"].map((to, i) => {
          const labels = {
            "/chat": "🧠 Chat with the River",
            "/voice-chat": "🗣 Voice Chat",
            "/experience": "✍️ Share Experience",
            "/mirror": "🪞 Mirror",
          };
          return (
            <Link
              key={to}
              to={to}
              className={`px-4 py-2 rounded-md font-medium transition-colors
                ${
                  pathname === to
                    ? "bg-amber-300 text-amber-900"
                    : "text-stone-700 hover:bg-amber-100 hover:text-amber-900"
                }`}
            >
              {labels[to]}
            </Link>
          );
        })}
      </nav>

      {/* Main content shifts over on md+; on mobile it sits under the fixed nav */}
      <main className="flex-1 p-8 bg-gradient-to-br from-stone-50 to-green-50 md:ml-64">
        <Outlet />
      </main>
    </div>
  );
}
