"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ShieldCheck, Sun, Moon, LogOut, UserCircle2 } from "lucide-react";
import { clearAuth, getStoredUser, isStaffRole, User } from "@/lib/api";

export function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [scheme, setScheme] = useState<"light dark" | "light" | "dark">("light dark");

  useEffect(() => {
    setUser(getStoredUser());
    const syncAuth = () => setUser(getStoredUser());
    window.addEventListener("auth-changed", syncAuth);

    try {
      const saved = localStorage.getItem("color-scheme");
      if (saved === "light" || saved === "dark") setScheme(saved);
    } catch {
      // ignore storage errors
    }

    return () => window.removeEventListener("auth-changed", syncAuth);
  }, []);

  const toggleTheme = () => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const currentlyDark =
      scheme === "dark" || (scheme === "light dark" && prefersDark);
    const target = currentlyDark ? "light" : "dark";
    const matchesSystem =
      (target === "dark" && prefersDark) || (target === "light" && !prefersDark);

    try {
      if (matchesSystem) {
        localStorage.removeItem("color-scheme");
        setScheme("light dark");
      } else {
        localStorage.setItem("color-scheme", target);
        setScheme(target);
      }
    } catch {
      setScheme(target);
    }
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) {
      meta.setAttribute("content", matchesSystem ? "light dark" : target);
    }
  };

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <a
        href="#main-content"
        className="visually-hidden focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-900 focus:text-white focus:rounded"
      >
        Skip to main content
      </a>
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 font-bold text-lg text-blue-900 dark:text-blue-300">
          <ShieldCheck className="w-7 h-7 text-amber-600 shrink-0" aria-hidden="true" />
          <span>
            JanSamadhan <span className="text-amber-600">AI</span>
            <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
              E-Governance Grievance Portal
            </span>
          </span>
        </Link>

        <nav aria-label="Primary" className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm font-medium">
          <Link href="/submit" className="px-3 py-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">
            File Complaint
          </Link>
          <Link href="/track" className="px-3 py-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">
            Track Ticket
          </Link>
          <Link href="/my-complaints" className="px-3 py-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">
            My Complaints
          </Link>
          {isStaffRole(user?.role) && (
            <Link
              href="/officer"
              className="px-3 py-2 rounded-md bg-amber-100 text-amber-950 dark:bg-amber-950/60 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-900/60 font-semibold"
            >
              Officer Portal
            </Link>
          )}

          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className="p-2 rounded-md border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 min-h-[40px] min-w-[40px] inline-flex items-center justify-center"
          >
            {scheme === "dark" ? (
              <Sun className="w-4 h-4" aria-hidden="true" />
            ) : (
              <Moon className="w-4 h-4" aria-hidden="true" />
            )}
          </button>

          {user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-300 dark:border-slate-700">
              <span className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold">
                <UserCircle2 className="w-4 h-4 text-blue-700 dark:text-blue-300" aria-hidden="true" />
                {user.name}
                <span className="px-2 py-0.5 text-[11px] rounded-full bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200 uppercase">
                  {user.role}
                </span>
              </span>
              <button
                type="button"
                onClick={() => clearAuth()}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-md border border-slate-300 dark:border-slate-700 hover:bg-red-50 dark:hover:bg-red-950/40 text-red-700 dark:text-red-300"
              >
                <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="px-4 py-2 rounded-md bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold"
            >
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
