import { apiFetch } from "./client";

export type FieldType =
  | "short_text"
  | "long_text"
  | "select"
  | "multi_select"
  | "number"
  | "boolean";

export type FormField = {
  id?: string;
  position?: number;
  label: string;
  fieldType: FieldType;
  required: boolean;
  options: string[];
};

export type ReviewSettings = {
  reviewerRoleIds: string[];
  viewerRoleIds: string[];
  reviewChannelId: string;
  autoRoleId: string | null;
  approvalMessage: string;
  denialMessage: string;
};

export type FormSummary = {
  id: string;
  guildId: string;
  title: string;
  description: string;
  postChannelId: string;
  fields: FormField[];
  reviewSettings: ReviewSettings;
  isArchived: boolean;
  isPublished: boolean;
  publishedMessageId: string | null;
};

export type Submission = {
  id: string;
  formId: string;
  status: "pending" | "approved" | "denied";
  username: string;
  userId: string;
  threadId: string | null;
  createdAt: string;
  decidedAt: string | null;
  actions: SubmissionAction[];
};

export type SubmissionAction = {
  actorId: string;
  action: string;
  note: string | null;
  createdAt: string;
};

export function listForms(guildId: string) {
  return apiFetch<FormSummary[]>(`/guilds/${guildId}/forms`);
}

export function createForm(guildId: string, payload: Omit<FormSummary, "id" | "guildId" | "isArchived" | "isPublished" | "publishedMessageId">) {
  return apiFetch<FormSummary>(`/guilds/${guildId}/forms`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateForm(guildId: string, formId: string, payload: Partial<FormSummary>) {
  return apiFetch<FormSummary>(`/guilds/${guildId}/forms/${formId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function publishForm(guildId: string, formId: string) {
  return apiFetch<FormSummary>(`/guilds/${guildId}/forms/${formId}/publish`, { method: "POST" });
}

export function archiveForm(guildId: string, formId: string) {
  return apiFetch<FormSummary>(`/guilds/${guildId}/forms/${formId}/archive`, { method: "POST" });
}

export function duplicateForm(guildId: string, formId: string) {
  return apiFetch<FormSummary>(`/guilds/${guildId}/forms/${formId}/duplicate`, { method: "POST" });
}

export function deleteForm(guildId: string, formId: string) {
  return apiFetch<void>(`/guilds/${guildId}/forms/${formId}`, { method: "DELETE" });
}

export function listSubmissions(guildId: string, formId: string, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<Submission[]>(`/guilds/${guildId}/forms/${formId}/submissions${query}`);
}
