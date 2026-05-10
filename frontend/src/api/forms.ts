import { apiFetch } from "./client";

export type FormSummary = {
  id: string;
  title: string;
  description: string;
  isArchived: boolean;
  isPublished: boolean;
};

export function listForms(guildId: string) {
  return apiFetch<FormSummary[]>(`/guilds/${guildId}/forms`);
}
