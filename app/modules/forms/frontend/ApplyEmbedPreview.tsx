import type { FormSummary } from "../../../../frontend/src/api/forms";

type Props = {
  form: FormSummary;
};

export function ApplyEmbedPreview({ form }: Props) {
  const preview = form.applyPreview;

  return (
    <div className="min-w-0 rounded-md border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Discord preview
          </div>
          <div className="mt-1 text-sm text-muted-foreground">
            This uses the same embed payload the bot posts.
          </div>
        </div>
        <span className="rounded-md bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground">
          Apply
        </span>
      </div>

      <div className="rounded-md border-l-4 border-primary bg-muted/25 p-4">
        <h2 className="text-xl font-semibold leading-tight">
          {preview?.title || form.title || "Untitled form"}
        </h2>
        <p className="mt-2 whitespace-pre-line text-sm leading-6 text-muted-foreground">
          {preview?.description || "Ready to apply? Click the Apply button below to begin."}
        </p>

        {preview?.fields.map((field) => (
          <div key={field.name} className="mt-4">
            <h3 className="text-sm font-semibold">{field.name}</h3>
            <p className="mt-1 whitespace-pre-line text-sm leading-6 text-muted-foreground">
              {field.value}
            </p>
          </div>
        ))}

        {preview?.footer?.text && (
          <div className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">
            {preview.footer.text}
          </div>
        )}
      </div>
    </div>
  );
}
