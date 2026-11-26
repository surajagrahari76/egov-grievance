"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { MapPin, CheckCircle2, Upload } from "lucide-react";
import {
  Department,
  fetchDepartments,
  fetchWards,
  getStoredUser,
  Grievance,
  submitGrievance,
  Ward,
} from "@/lib/api";

export default function SubmitGrievancePage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);

  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [category, setCategory] = useState("");
  const [language, setLanguage] = useState("en");
  const [wardId, setWardId] = useState("");
  const [address, setAddress] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [consent, setConsent] = useState(true);
  const [files, setFiles] = useState<FileList | null>(null);

  const [gpsStatus, setGpsStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState<{
    grievance: Grievance;
    anonymous_tracking_code?: string | null;
  } | null>(null);

  useEffect(() => {
    const user = getStoredUser();
    setLoggedIn(Boolean(user));
    if (!user) setIsAnonymous(true);

    fetchDepartments().then(setDepartments).catch(() => {});
    fetchWards().then(setWards).catch(() => {});
  }, []);

  const detectGps = () => {
    if (!navigator.geolocation) {
      setGpsStatus("Geolocation is not supported by your browser.");
      return;
    }
    setGpsStatus("Detecting coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLng(pos.coords.longitude.toFixed(6));
        setGpsStatus("Location captured via GPS.");
      },
      () => {
        setGpsStatus("Unable to detect GPS automatically. Please enter address or ward.");
      }
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("title", title);
      fd.append("text", text);
      if (category) fd.append("category", category);
      fd.append("language", language);
      if (wardId) fd.append("ward_id", wardId);
      if (address) fd.append("address", address);
      if (lat) fd.append("lat", lat);
      if (lng) fd.append("lng", lng);
      fd.append("is_anonymous", String(isAnonymous));
      fd.append("consent_accepted", String(consent));
      if (files) {
        Array.from(files).forEach((f) => fd.append("files", f));
      }

      const result = await submitGrievance(fd);
      setCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit complaint");
    } finally {
      setSubmitting(false);
    }
  };

  if (created) {
    return (
      <div className="max-w-2xl mx-auto gov-card p-6 sm:p-8 space-y-5">
        <div className="flex items-center gap-3 text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 className="w-8 h-8 shrink-0" aria-hidden="true" />
          <div>
            <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
              Complaint Submitted Successfully
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Save your Ticket ID to track progress at any time.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-100 dark:bg-slate-800 space-y-2 text-sm">
          <p>
            <strong>Ticket ID:</strong>{" "}
            <code className="text-base font-bold">{created.grievance.ticket_id}</code>
          </p>
          <p>
            <strong>Status:</strong> {created.grievance.status}
          </p>
          {created.anonymous_tracking_code && (
            <p className="p-2.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-950 dark:text-amber-200">
              <strong>Private Anonymous Tracking Code (save this!):</strong>{" "}
              <code className="font-bold">{created.anonymous_tracking_code}</code>
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            href={`/track?ticket=${encodeURIComponent(created.grievance.ticket_id)}`}
            className="px-5 py-2.5 rounded-lg bg-blue-900 text-white font-semibold"
          >
            Track This Ticket
          </Link>
          <button
            type="button"
            onClick={() => {
              setCreated(null);
              setTitle("");
              setText("");
              setFiles(null);
            }}
            className="px-5 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 font-semibold"
          >
            File Another Complaint
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto gov-card p-6 sm:p-8 space-y-6">
      <div>
        <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
          File a Public Grievance
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
          Submit in English, Hindi, or Hinglish. {!loggedIn && "Not logged in? Anonymous filing is pre-selected."}
        </p>
      </div>

      {error && (
        <div role="alert" className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 dark:border-red-800 text-sm text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="grv-title" className="block text-sm font-semibold mb-1">
            Complaint Title <span aria-hidden="true">*</span>
          </label>
          <input
            id="grv-title"
            name="title"
            type="text"
            className="gov-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            minLength={4}
            maxLength={200}
            aria-describedby="title-help"
          />
          <p id="title-help" className="text-xs text-slate-500 mt-1">
            Brief summary (4–200 characters).
          </p>
        </div>

        <div>
          <label htmlFor="grv-text" className="block text-sm font-semibold mb-1">
            Detailed Description (English / Hindi / Hinglish) <span aria-hidden="true">*</span>
          </label>
          <textarea
            id="grv-text"
            name="text"
            rows={4}
            className="gov-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
            minLength={10}
            maxLength={5000}
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="grv-category" className="block text-sm font-semibold mb-1">
              Department / Category (Optional)
            </label>
            <select
              id="grv-category"
              name="category"
              className="gov-input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">Auto-detect (Default)</option>
              {departments.map((d) => (
                <option key={d.id} value={d.code}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="grv-language" className="block text-sm font-semibold mb-1">
              Complaint Language
            </label>
            <select
              id="grv-language"
              name="language"
              className="gov-input"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>
        </div>

        <fieldset className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4">
          <legend className="px-2 text-sm font-semibold">Location Details</legend>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="grv-ward" className="block text-sm font-semibold mb-1">
                Ward / Zone
              </label>
              <select
                id="grv-ward"
                name="ward_id"
                className="gov-input"
                value={wardId}
                onChange={(e) => {
                  const val = e.target.value;
                  setWardId(val);
                  const w = wards.find((item) => String(item.id) === val);
                  if (w?.center_lat && w?.center_lng && !lat && !lng) {
                    setLat(String(w.center_lat));
                    setLng(String(w.center_lng));
                  }
                }}
              >
                <option value="">Select Ward (optional)</option>
                {wards.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.code} — {w.name} ({w.zone})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                type="button"
                onClick={detectGps}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-blue-700 text-blue-800 dark:border-blue-400 dark:text-blue-300 font-semibold min-h-[48px] hover:bg-blue-50 dark:hover:bg-blue-950/40"
              >
                <MapPin className="w-4 h-4" aria-hidden="true" />
                Auto-detect GPS
              </button>
            </div>
          </div>

          {gpsStatus && (
            <p role="status" className="text-xs text-slate-600 dark:text-slate-300">
              {gpsStatus}
            </p>
          )}

          <div>
            <label htmlFor="grv-address" className="block text-sm font-semibold mb-1">
              Street Address / Landmark
            </label>
            <textarea
              id="grv-address"
              name="address"
              rows={2}
              autoComplete="street-address"
              className="gov-input"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="grv-lat" className="block text-xs font-semibold mb-1">
                Latitude
              </label>
              <input
                id="grv-lat"
                name="lat"
                type="text"
                inputMode="decimal"
                className="gov-input"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                placeholder="28.6315"
              />
            </div>
            <div>
              <label htmlFor="grv-lng" className="block text-xs font-semibold mb-1">
                Longitude
              </label>
              <input
                id="grv-lng"
                name="lng"
                type="text"
                inputMode="decimal"
                className="gov-input"
                value={lng}
                onChange={(e) => setLng(e.target.value)}
                placeholder="77.2167"
              />
            </div>
          </div>
        </fieldset>

        <div>
          <label htmlFor="grv-files" className="block text-sm font-semibold mb-1">
            Attach Photo or PDF Evidence (Optional, max 5 MB each)
          </label>
          <div className="flex items-center gap-3">
            <Upload className="w-5 h-5 text-slate-500 shrink-0" aria-hidden="true" />
            <input
              id="grv-files"
              name="files"
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.pdf"
              multiple
              onChange={(e) => setFiles(e.target.files)}
              className="text-sm"
            />
          </div>
        </div>

        <div className="space-y-2.5 pt-2 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-start gap-2.5">
            <input
              id="grv-anon"
              type="checkbox"
              checked={isAnonymous}
              onChange={(e) => setIsAnonymous(e.target.checked)}
              disabled={!loggedIn}
              className="mt-1 h-4 w-4"
            />
            <label htmlFor="grv-anon" className="text-sm">
              File anonymously (generates a private tracking code instead of linking to an account)
              {!loggedIn && (
                <span className="block text-xs text-slate-500">
                  Required when not logged in — or{" "}
                  <Link href="/login" className="underline text-blue-700 dark:text-blue-400">
                    login here
                  </Link>
                  .
                </span>
              )}
            </label>
          </div>

          <div className="flex items-start gap-2.5">
            <input
              id="grv-consent"
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              required
              className="mt-1 h-4 w-4"
            />
            <label htmlFor="grv-consent" className="text-xs text-slate-600 dark:text-slate-300">
              I confirm the details provided are accurate and consent to grievance processing under the portal privacy policy.
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3.5 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px] disabled:opacity-60"
        >
          {submitting ? "Submitting Grievance..." : "Submit Grievance"}
        </button>
      </form>
    </div>
  );
}
