import { Save, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  createForm,
  type FormField,
  type FormSummary,
  updateForm,
} from "../../../../frontend/src/api/forms";
import { Button } from "../../../../frontend/src/components/ui/button";
import { Card } from "../../../../frontend/src/components/ui/card";
import { FieldEditor } from "./FieldEditor";
import { InfoBubble } from "./InfoBubble";
import { ReviewSettings } from "./ReviewSettings";

type Props = {
  guildId: string;
  initial: FormSummary;
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
};

export function FormEditor({ guildId, initial, onSaved, onCancel }: Props) {
  const [form, setForm] = useState<FormSummary>(initial);
  const isExistingForm = Boolean(initial.id);

  useEffect(() => {
    setForm(initial);
  }, [initial]);

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
      <div className="grid gap-5">
        <div className="rounded-md border border-border bg-muted/30 p-3">
          <div className="flex items-center gap-2 text-sm font-semibold">
            {isExistingForm ? "Edit saved form" : "Setup checklist"}
            <InfoBubble label="Forms setup help">
              Create the form, save it, then publish it. Publishing tells the bot to post the Apply
              button in the channel ID below.
            </InfoBubble>
          </div>
          {isExistingForm ? (
            <p className="mt-2 text-sm text-muted-foreground">
              Change the details below and save. Question and review changes affect future
              submissions immediately.
            </p>
          ) : (
            <ol className="mt-2 grid gap-1 text-sm text-muted-foreground sm:grid-cols-2">
              <li>1. Add the public title and description.</li>
              <li>2. Choose where the Apply button is posted.</li>
              <li>3. Add the questions members answer.</li>
              <li>4. Set the review channel and reviewer roles.</li>
            </ol>
          )}
        </div>

        <section className="grid gap-3">
          <div>
            <h3 className="text-sm font-semibold">Public form details</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Members see this information in Discord before they start the application.
            </p>
          </div>
          <label className="grid gap-1 text-sm font-medium text-foreground">
            Form title
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              placeholder="Staff Application"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium text-foreground">
            Description
            <textarea
              className="min-h-20 rounded-md border border-border px-3 py-2 text-sm font-normal"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Tell members who should apply and what happens after they submit."
            />
          </label>
          <label className="grid gap-1 text-sm font-medium text-foreground">
            <span className="flex items-center gap-2">
              Apply button channel ID
              <InfoBubble label="Apply channel help">
                Copy the channel ID from Discord. The bot posts the public application embed and
                Apply button there when you publish the form.
              </InfoBubble>
            </span>
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={form.postChannelId}
              onChange={(event) => setForm({ ...form, postChannelId: event.target.value })}
              placeholder="123456789012345678"
            />
          </label>
        </section>

        <section className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold">Application questions</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Discord modals show up to five fields at a time. Longer forms continue in the next
              modal automatically.
            </p>
          </div>
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
        </section>

        <ReviewSettings
          settings={form.reviewSettings}
          onChange={(reviewSettings) => setForm({ ...form, reviewSettings })}
        />

        <div className="flex gap-2">
          <Button onClick={save}>
            <Save aria-hidden="true" size={16} />
            Save form
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
