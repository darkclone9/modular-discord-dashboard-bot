import { apiFetch, setCsrfToken } from "./client";

export type DashboardUser = {
  id: string;
  username: string;
  avatar: string | null;
  csrfToken: string;
};

function rememberSession(user: DashboardUser) {
  setCsrfToken(user.csrfToken);
  return user;
}

export async function getCurrentUser() {
  return rememberSession(await apiFetch<DashboardUser>("/auth/me"));
}

export async function loginWithPassword(username: string, password: string) {
  return rememberSession(await apiFetch<DashboardUser>("/auth/local/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  }));
}

export async function logout() {
  try {
    return await apiFetch<{ status: string }>("/auth/logout", { method: "POST" });
  } finally {
    setCsrfToken(null);
  }
}
