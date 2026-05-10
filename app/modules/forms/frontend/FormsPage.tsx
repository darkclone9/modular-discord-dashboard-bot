import { Copy, FilePlus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  archiveForm,
  deleteForm,
  duplicateForm,
  type FormSummary,
  listForms,
  publishForm,
} from "../../../../frontend/src/api/forms";
import { Button } from "../../../../frontend/src/components/ui/button";
import { Card } from "../../../../frontend/src/components/ui/card";
import { FormEditor, newFormDraft } from "./FormEditor";
import { InfoBubble } from "./InfoBubble";
import { SubmissionsTable } from "./SubmissionsTable";

type Props = {
  guildId: string;
};

export function FormsPage({ guildId }: Props) {
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [selected, setSelected] = useState<FormSummary | null>(null);
  const [drafting, setDrafting] = useState(false);

  async function reload() {
    const loaded = await listForms(guildId);
    setForms(loaded);
    setSelected((current) => loaded.find((form) => form.id === current?.id) ?? loaded[0] ?? null);
  }

  useEffect(() => {
    void reload();
  }, [guildId]);

  async function mutate(action: () => Promise<unknown>) {
    await action();
    await reload();
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
      <aside>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold">Forms</h2>
              <InfoBubble label="Forms list help">
                Forms are reusable application templates. Edit a form, save it, then publish it to
                post the Apply button in Discord.
              </InfoBubble>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Create and manage application flows for this server.
            </p>
          </div>
          <Button variant="secondary" onClick={() => setDrafting(true)} title="Create form">
            <FilePlus aria-hidden="true" size={16} />
          </Button>
        </div>
        <div className="space-y-2">
          {forms.length === 0 && (
            <Card className="p-3 text-sm text-muted-foreground">
              No forms yet. Use the create button to start your first application.
            </Card>
          )}
          {forms.map((form) => (
            <button key={form.id} className="w-full text-left" onClick={() => setSelected(form)}>
              <Card
                className={`p-3 ${selected?.id === form.id ? "border-primary" : "hover:border-primary"}`}
              >
                <div className="font-medium">{form.title}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {form.isPublished ? "Published" : "Draft"}
                </div>
                {form.isPublished && !form.publishedMessageId && (
                  <div className="mt-1 text-xs text-muted-foreground">Waiting for bot post</div>
                )}
              </Card>
            </button>
          ))}
        </div>
      </aside>

      <section className="space-y-5">
        {drafting && (
          <FormEditor
            guildId={guildId}
            initial={newFormDraft()}
            onCancel={() => setDrafting(false)}
            onSaved={async () => {
              setDrafting(false);
              await reload();
            }}
          />
        )}

        {selected && !drafting && (
          <>
            <Card className="p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{selected.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{selected.description}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-2">
                    <Button onClick={() => mutate(() => publishForm(guildId, selected.id))}>
                      Publish
                    </Button>
                    <InfoBubble label="Publish help" side="left">
                      Publish marks the form active. The bot then posts or refreshes the Discord
                      embed with the Apply button in the configured channel.
                    </InfoBubble>
                  </span>
                  <Button
                    variant="secondary"
                    onClick={() => mutate(() => duplicateForm(guildId, selected.id))}
                    title="Duplicate form"
                  >
                    <Copy aria-hidden="true" size={16} />
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => mutate(() => archiveForm(guildId, selected.id))}
                  >
                    Archive
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => mutate(() => deleteForm(guildId, selected.id))}
                    title="Delete form"
                  >
                    <Trash2 aria-hidden="true" size={16} />
                  </Button>
                </div>
              </div>
            </Card>
            <FormEditor guildId={guildId} initial={selected} onSaved={reload} />
            <SubmissionsTable guildId={guildId} formId={selected.id} />
          </>
        )}
      </section>
    </div>
  );
}
