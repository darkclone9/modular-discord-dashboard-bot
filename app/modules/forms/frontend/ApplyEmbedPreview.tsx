import type { FormSummary } from "../../../../frontend/src/api/forms";

type Props = {
  form: FormSummary;
};

export function ApplyEmbedPreview({ form }: Props) {
  const preview = buildApplyPreview(form);

  return (
    <div className="min-w-0 rounded-md border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Discord preview
          </div>
          <div className="mt-1 text-sm text-muted-foreground">
            This matches the public Apply embed the bot posts.
          </div>
        </div>
        <span className="rounded-md bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground">
          Apply
        </span>
      </div>

      <div className="rounded-md border-l-4 border-primary bg-muted/25 p-4">
        <h2 className="text-xl font-semibold leading-tight">{form.title || "Untitled form"}</h2>
        <p className="mt-2 whitespace-pre-line text-sm leading-6 text-muted-foreground">
          {preview.intro || "Ready to apply? Click the Apply button below to begin."}
        </p>

        {preview.sections.map((section) => (
          <div key={section.title} className="mt-4">
            <h3 className="text-sm font-semibold">{section.title}</h3>
            <p className="mt-1 whitespace-pre-line text-sm leading-6 text-muted-foreground">
              {section.body}
            </p>
          </div>
        ))}

        {form.fields.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold">Questions ({form.fields.length})</h3>
            <ol className="mt-1 list-decimal space-y-1 pl-5 text-sm leading-6 text-muted-foreground">
              {form.fields.map((field, index) => (
                <li key={`${field.id ?? field.label}-${index}`}>{field.label || "Untitled question"}</li>
              ))}
            </ol>
          </div>
        )}

        <div className="mt-4">
          <h3 className="text-sm font-semibold">How to submit</h3>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Click <span className="font-semibold text-foreground">Apply</span> below. Your answers
            open a private review thread for the team.
          </p>
        </div>

        <div className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">
          Applications are handled privately by the reviewer team.
        </div>
      </div>
    </div>
  );
}

type PreviewSection = {
  title: string;
  body: string;
};

function buildApplyPreview(form: FormSummary): { intro: string; sections: PreviewSection[] } {
  const [intro, sections] = splitApplyDescription(form.description);
  return {
    intro: truncate(intro, 4096),
    sections: sections.slice(0, 8).map((section) => ({
      title: section.title,
      body: truncate(section.body),
    })),
  };
}

function splitApplyDescription(description: string): [string, PreviewSection[]] {
  const text = normalizeEmbedText(description);
  if (!text) {
    return ["", []];
  }

  const paragraphSections = text.split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean);
  if (paragraphSections.length > 1) {
    return [
      paragraphSections[0],
      paragraphSections.slice(1).map((paragraph, index) => ({
        title: `Details ${index + 1}`,
        body: paragraph,
      })),
    ];
  }

  const headingPattern =
    /\b(What officers do|What we're looking for|What we are looking for|Time commitment|How to apply|Requirements|Eligibility|What happens next|Deadline)\s*[:.]\s+/gi;
  const matches = Array.from(text.matchAll(headingPattern));
  if (matches.length === 0) {
    return splitLongIntro(text);
  }

  const intro = text.slice(0, matches[0].index).trim();
  const sections = matches
    .map((match, index) => {
      const start = (match.index ?? 0) + match[0].length;
      const end = matches[index + 1]?.index ?? text.length;
      return {
        title: canonicalSectionTitle(match[1]),
        body: text.slice(start, end).trim(),
      };
    })
    .filter((section) => section.body);
  return [intro, sections];
}

function splitLongIntro(text: string): [string, PreviewSection[]] {
  if (text.length <= 900) {
    return [text, []];
  }
  let splitAt = text.lastIndexOf(". ", 700);
  if (splitAt === -1) {
    splitAt = 700;
  }
  return [
    text.slice(0, splitAt + 1).trim(),
    [{ title: "Details", body: text.slice(splitAt + 1).trim() }],
  ];
}

function normalizeEmbedText(value: string) {
  return value.replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/[ \t]+/g, " ").trim();
}

function canonicalSectionTitle(value: string) {
  const titles: Record<string, string> = {
    "what officers do": "What officers do",
    "what we're looking for": "What we're looking for",
    "what we are looking for": "What we're looking for",
    "time commitment": "Time commitment",
    "how to apply": "How to apply",
    requirements: "Requirements",
    eligibility: "Eligibility",
    "what happens next": "What happens next",
    deadline: "Deadline",
  };
  return titles[value.trim().toLowerCase()] ?? value.trim();
}

function truncate(value: string, limit = 1024) {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit - 3).trimEnd()}...`;
}
