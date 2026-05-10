import { Save, X } from "lucide-react";
import { useState } from "react";

import {
  createForm,
  type FormField,
  type FormSummary,
  updateForm,
} from "../../../../frontend/src/api/forms";
import { Button } from "../../../../frontend/src/components/ui/button";
import { Card } from "../../../../frontend/src/components/ui/card";
import { FieldEditor } from "./FieldEditor";
import { ReviewSettings } from "./ReviewSettings";

type Props = {
  guildId: string;
  initial: FormSummary;
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
};

export function FormEditor({ guildId, initial, onSaved, onCancel }: Props) {
  const [form, setForm] = useState<FormSummary>(initial);

  async function save() {
    const payload = {
      title: form.title,
      description: form.description,
      postChannelId: form.postChannelId,
      fields: form.fields,
      reviewSettings: form.reviewSettings,
    };
    if (form.id) {
      await updateForm(guildId, form.id, payload);
    } else {
      await createForm(guildId, payload);
    }
    await onSaved();
  }

  function updateField(index: number, field: FormField) {
    setForm((current) => ({
      ...current,
      fields: current.fields.map((item, fieldIndex) => (fieldIndex === index ? field : item)),
    }));
  }

  return (
    <Card className="p-4">
      <div className="grid gap-3">
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={form.title}
          onChange={(event) => setForm({ ...form, title: event.target.value })}
          placeholder="Form title"
        />
        <textarea
          className="min-h-20 rounded-md border border-border px-3 py-2 text-sm"
          value={form.description}
          onChange={(event) => setForm({ ...form, description: event.target.value })}
          placeholder="Description"
        />
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={form.postChannelId}
          onChange={(event) => setForm({ ...form, postChannelId: event.target.value })}
          placeholder="Apply button channel ID"
        />

        <div className="space-y-2">
          {form.fields.map((field, index) => (
            <FieldEditor
              key={index}
              field={field}
              onChange={(next) => updateField(index, next)}
              onRemove={() =>
                setForm((current) => ({
                  ...current,
                  fields: current.fields.filter((_, fieldIndex) => fieldIndex !== index),
                }))
              }
            />
          ))}
          <Button
            variant="secondary"
            onClick={() =>
              setForm((current) => ({
                ...current,
                fields: [
                  ...current.fields,
                  { label: "", fieldType: "short_text", required: true, options: [] },
                ],
              }))
            }
          >
            Add field
          </Button>
        </div>

        <ReviewSettings
          settings={form.reviewSettings}
          onChange={(reviewSettings) => setForm({ ...form, reviewSettings })}
        />

        <div className="flex gap-2">
          <Button onClick={save}>
            <Save aria-hidden="true" size={16} />
            Save
          </Button>
          {onCancel && (
            <Button variant="ghost" onClick={onCancel}>
              <X aria-hidden="true" size={16} />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

export function newFormDraft(): FormSummary {
  return {
    id: "",
    guildId: "",
    title: "",
    description: "",
    postChannelId: "",
    fields: [{ label: "Why do you want to apply?", fieldType: "long_text", required: true, options: [] }],
    reviewSettings: {
      reviewerRoleIds: [],
      reviewChannelId: "",
      autoRoleId: null,
      approvalMessage: "Your application has been approved.",
      denialMessage: "Your application was denied.",
    },
    isArchived: false,
    isPublished: false,
    publishedMessageId: null,
  };
}
