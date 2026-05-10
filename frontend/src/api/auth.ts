import { apiFetch } from "./client";

export type DashboardUser = {
  id: string;
  username: string;
  avatar: string | null;
  csrfToken: string;
};

export function getCurrentUser() {
  return apiFetch<DashboardUser>("/auth/me");
}

export function loginWithPassword(username: string, password: string) {
  return apiFetch<DashboardUser>("/auth/local/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function logout() {
  return apiFetch<{ status: string }>("/auth/logout", { method: "POST" });
}
