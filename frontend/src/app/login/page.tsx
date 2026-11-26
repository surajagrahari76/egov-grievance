"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { passwordLogin, requestOtp, saveAuth, verifyOtp } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"citizen" | "staff">("citizen");

  // Citizen OTP state
  const [phone, setPhone] = useState("9876543210");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpHint, setOtpHint] = useState("");
  const [consent, setConsent] = useState(true);

  // Staff login state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRequestOtp = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await requestOtp(phone, name);
      setOtpSent(true);
      setOtpHint(res.mock_otp_hint);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await verifyOtp(phone, otp, name, consent);
      saveAuth(res.access_token, res.user);
      router.push("/my-complaints");
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStaffLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await passwordLogin(email, password);
      saveAuth(res.access_token, res.user);
      router.push("/my-complaints");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="gov-card p-6 sm:p-8 space-y-6">
        <div>
          <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
            Portal Sign In
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            Citizens sign in with Mobile OTP (mocked). Officers & Admins sign in with email and password.
          </p>
        </div>

        <div role="tablist" aria-label="Login type" className="grid grid-cols-2 gap-2 p-1 rounded-lg bg-slate-100 dark:bg-slate-800">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "citizen"}
            onClick={() => {
              setMode("citizen");
              setError("");
            }}
            className={`py-2 rounded-md text-sm font-semibold ${
              mode === "citizen"
                ? "bg-white dark:bg-slate-900 shadow-sm text-blue-900 dark:text-blue-300"
                : "text-slate-600 dark:text-slate-300"
            }`}
          >
            Citizen (OTP)
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "staff"}
            onClick={() => {
              setMode("staff");
              setError("");
            }}
            className={`py-2 rounded-md text-sm font-semibold ${
              mode === "staff"
                ? "bg-white dark:bg-slate-900 shadow-sm text-blue-900 dark:text-blue-300"
                : "text-slate-600 dark:text-slate-300"
            }`}
          >
            Officer / Admin
          </button>
        </div>

        {error && (
          <div role="alert" className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 dark:border-red-800 text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {mode === "citizen" ? (
          !otpSent ? (
            <form onSubmit={handleRequestOtp} className="space-y-4">
              <div>
                <label htmlFor="phone" className="block text-sm font-semibold mb-1">
                  Mobile Number <span aria-hidden="true">*</span>
                </label>
                <input
                  id="phone"
                  name="phone"
                  type="text"
                  inputMode="numeric"
                  autoComplete="tel"
                  className="gov-input"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  minLength={10}
                  aria-describedby="phone-hint"
                />
                <p id="phone-hint" className="text-xs text-slate-500 mt-1">
                  Demo Citizen: <code>9876543210</code> (Mock OTP: <code>123456</code>)
                </p>
              </div>

              <div>
                <label htmlFor="citizen-name" className="block text-sm font-semibold mb-1">
                  Full Name (for new users)
                </label>
                <input
                  id="citizen-name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  className="gov-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Optional if already registered"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px] disabled:opacity-60"
              >
                {loading ? "Sending Mock OTP..." : "Send OTP"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              {otpHint && (
                <div role="status" className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200">
                  <strong>MOCK SMS GATEWAY:</strong> {otpHint}
                </div>
              )}

              <div>
                <label htmlFor="otp-code" className="block text-sm font-semibold mb-1">
                  Enter 6-digit OTP <span aria-hidden="true">*</span>
                </label>
                <input
                  id="otp-code"
                  name="otp"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\d{6}"
                  className="gov-input"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  required
                />
              </div>

              <div className="flex items-start gap-2.5">
                <input
                  id="dpdp-consent"
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  required
                  className="mt-1 h-4 w-4"
                />
                <label htmlFor="dpdp-consent" className="text-xs text-slate-600 dark:text-slate-300">
                  I consent to the processing of my grievance details in accordance with the portal privacy notice (DPDP Act spirit).
                </label>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setOtpSent(false)}
                  className="px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 font-semibold min-h-[48px]"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px] disabled:opacity-60"
                >
                  {loading ? "Verifying..." : "Verify & Sign In"}
                </button>
              </div>
            </form>
          )
        ) : (
          <form onSubmit={handleStaffLogin} className="space-y-4">
            <div>
              <label htmlFor="staff-email" className="block text-sm font-semibold mb-1">
                Official Email <span aria-hidden="true">*</span>
              </label>
              <input
                id="staff-email"
                name="email"
                type="email"
                autoComplete="username"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                className="gov-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label htmlFor="staff-password" className="block text-sm font-semibold mb-1">
                Password <span aria-hidden="true">*</span>
              </label>
              <input
                id="staff-password"
                name="password"
                type="password"
                autoComplete="current-password"
                className="gov-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="text-xs p-3 rounded-lg bg-slate-100 dark:bg-slate-800 space-y-1">
              <p className="font-semibold">Demo Staff Accounts:</p>
              <p>Officer (Water): <code>officer.water@demo.gov.in</code> / <code>Officer123!</code></p>
              <p>Admin: <code>admin@demo.gov.in</code> / <code>Admin123!</code></p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px] disabled:opacity-60"
            >
              {loading ? "Signing In..." : "Sign In"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
