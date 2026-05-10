import { apiFetch } from "./client";

export type Guild = {
  id: string;
  name: string;
  icon: string | null;
  owner?: boolean;
  permissions: string;
};

export function listGuilds() {
  return apiFetch<Guild[]>("/guilds");
}
