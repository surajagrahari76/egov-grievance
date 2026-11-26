export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const BACKEND_ORIGIN = API_BASE.replace(/\/api\/v1\/?$/, "");

export const STAFF_ROLES = ["officer", "dept_head", "district_head", "admin"] as const;

export function isStaffRole(role?: string | null): boolean {
  return Boolean(role && (STAFF_ROLES as readonly string[]).includes(role));
}

export interface OfficerSummary {
  id: number;
  user_id: number;
  name: string;
  email?: string | null;
  dept_id: number;
  ward_id?: number | null;
  level: string;
  designation: string;
}

export interface User {
  id: number;
  name: string;
  phone?: string | null;
  email?: string | null;
  role: string;
  preferred_lang: string;
  is_2fa_enabled: boolean;
  created_at: string;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  name_hi: string;
  helpline?: string | null;
}

export interface Ward {
  id: number;
  code: string;
  name: string;
  zone: string;
  city: string;
  center_lat?: number | null;
  center_lng?: number | null;
}

export interface StatusHistoryItem {
  id: number;
  from_status?: string | null;
  to_status: string;
  remarks?: string | null;
  is_system_action: boolean;
  created_at: string;
}

export interface AttachmentItem {
  id: number;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  file_path: string;
  uploaded_at: string;
}

export interface Grievance {
  id: number;
  ticket_id: string;
  user_id?: number | null;
  is_anonymous: boolean;
  title: string;
  text: string;
  language: string;
  category: string;
  priority: string;
  status: string;
  lat?: number | null;
  lng?: number | null;
  address?: string | null;
  ward_id?: number | null;
  dept_id?: number | null;
  is_emergency: boolean;
  sla_deadline?: string | null;
  estimated_resolution_at?: string | null;
  created_at: string;
  resolved_at?: string | null;
  attachments: AttachmentItem[];
  status_history: StatusHistoryItem[];
  department?: Department | null;
  ward?: Ward | null;
}

export interface PublicTrackResponse {
  ticket_id: string;
  title: string;
  category: string;
  priority: string;
  status: string;
  language: string;
  address?: string | null;
  ward_name?: string | null;
  department_name?: string | null;
  is_emergency: boolean;
  sla_deadline?: string | null;
  estimated_resolution_at?: string | null;
  created_at: string;
  resolved_at?: string | null;
  status_history: StatusHistoryItem[];
  attachments: AttachmentItem[];
}

export interface PaginatedGrievances {
  items: Grievance[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const TOKEN_KEY = "jansamadhan_token";
const USER_KEY = "jansamadhan_user";

export function saveAuth(token: string, user: User): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event("auth-changed"));
}

export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event("auth-changed"));
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg || "Validation error").join(", ");
    }
    return `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function requestOtp(phone: string, name?: string) {
  const res = await fetch(`${API_BASE}/auth/otp/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, name: name || undefined }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{
    message: string;
    mock_otp_hint: string;
    expires_in_seconds: number;
  }>;
}

export async function verifyOtp(
  phone: string,
  otp: string,
  name?: string,
  consentAccepted = true
) {
  const res = await fetch(`${API_BASE}/auth/otp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      phone,
      otp,
      name: name || undefined,
      consent_accepted: consentAccepted,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; token_type: string; user: User }>;
}

export async function passwordLogin(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; token_type: string; user: User }>;
}

export async function fetchDepartments(): Promise<Department[]> {
  const res = await fetch(`${API_BASE}/reference/departments`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchWards(): Promise<Ward[]> {
  const res = await fetch(`${API_BASE}/reference/wards`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function submitGrievance(formData: FormData) {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/grievances`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{
    grievance: Grievance;
    anonymous_tracking_code?: string | null;
  }>;
}

export async function fetchMyGrievances(page = 1, statusFilter = "") {
  const token = getToken();
  if (!token) throw new Error("Please log in to view your complaints");
  const params = new URLSearchParams({ page: String(page), page_size: "10" });
  if (statusFilter) params.set("status", statusFilter);

  const res = await fetch(`${API_BASE}/grievances/mine?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<PaginatedGrievances>;
}

export async function trackGrievance(ticketId: string, anonymousCode?: string) {
  const params = new URLSearchParams();
  if (anonymousCode?.trim()) params.set("anonymous_code", anonymousCode.trim());
  const qs = params.toString() ? `?${params.toString()}` : "";

  const res = await fetch(
    `${API_BASE}/grievances/track/${encodeURIComponent(ticketId.trim())}${qs}`
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<PublicTrackResponse>;
}

export async function fetchStaffGrievances(params: {
  page?: number;
  page_size?: number;
  status?: string;
  dept_id?: string;
  ward_id?: string;
  priority?: string;
}) {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const qs = new URLSearchParams({
    page: String(params.page || 1),
    page_size: String(params.page_size || 20),
  });
  if (params.status) qs.set("status", params.status);
  if (params.dept_id) qs.set("dept_id", params.dept_id);
  if (params.ward_id) qs.set("ward_id", params.ward_id);
  if (params.priority) qs.set("priority", params.priority);

  const res = await fetch(`${API_BASE}/officer/grievances?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<PaginatedGrievances>;
}

export async function fetchStaffGrievanceDetail(ticketId: string) {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const res = await fetch(
    `${API_BASE}/officer/grievances/${encodeURIComponent(ticketId)}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<Grievance>;
}

export async function updateStaffGrievanceStatus(
  ticketId: string,
  status: string,
  remarks?: string,
  assignedOfficerId?: number
) {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const res = await fetch(
    `${API_BASE}/officer/grievances/${encodeURIComponent(ticketId)}/status`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        status,
        remarks: remarks?.trim() || undefined,
        assigned_officer_id: assignedOfficerId || undefined,
      }),
    }
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<Grievance>;
}

export async function assignStaffGrievance(
  ticketId: string,
  officerId?: number,
  remarks?: string
) {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const res = await fetch(
    `${API_BASE}/officer/grievances/${encodeURIComponent(ticketId)}/assign`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        officer_id: officerId || undefined,
        remarks: remarks?.trim() || undefined,
      }),
    }
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<Grievance>;
}

export async function reassignStaffDepartment(
  ticketId: string,
  deptCode: string,
  remarks?: string
) {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const res = await fetch(
    `${API_BASE}/officer/grievances/${encodeURIComponent(ticketId)}/reassign`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        dept_code: deptCode,
        remarks: remarks?.trim() || undefined,
      }),
    }
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<Grievance>;
}

export async function fetchOfficerTeam(): Promise<OfficerSummary[]> {
  const token = getToken();
  if (!token) throw new Error("Staff authentication required");
  const res = await fetch(`${API_BASE}/officer/team`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
