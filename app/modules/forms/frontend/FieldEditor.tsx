import { GripVertical, Trash2 } from "lucide-react";

import type { FieldType, FormField } from "../../../../frontend/src/api/forms";
import { Button } from "../../../../frontend/src/components/ui/button";
import { InfoBubble } from "./InfoBubble";

type Props = {
  field: FormField;
  onChange: (field: FormField) => void;
  onRemove: () => void;
};

const FIELD_TYPES: FieldType[] = [
  "short_text",
  "long_text",
  "select",
  "multi_select",
  "number",
  "boolean",
];

export function FieldEditor({ field, onChange, onRemove }: Props) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-white p-3">
      <div className="grid gap-3 sm:grid-cols-[24px_1fr_180px_110px_40px] sm:items-end">
        <GripVertical
          aria-hidden="true"
          className="hidden text-muted-foreground sm:mb-3 sm:block"
          size={16}
        />
        <label className="grid gap-1 text-sm font-medium text-foreground">
          Question label
          <input
            className="h-9 rounded-md border border-border px-3 text-sm font-normal"
            value={field.label}
            onChange={(event) => onChange({ ...field, label: event.target.value })}
            placeholder="Why do you want to apply?"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium text-foreground">
          <span className="flex items-center gap-2">
            Answer type
            <InfoBubble label="Answer type help">
              Short text is best for names or links. Long text is best for paragraphs. Select and
              multi-select use the choices box below. Number and boolean validate the answer format.
            </InfoBubble>
          </span>
          <select
            className="h-9 rounded-md border border-border bg-white px-3 text-sm font-normal"
            value={field.fieldType}
            onChange={(event) => onChange({ ...field, fieldType: event.target.value as FieldType })}
          >
            {FIELD_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 pb-2 text-sm">
          <input
            type="checkbox"
            checked={field.required}
            onChange={(event) => onChange({ ...field, required: event.target.checked })}
          />
          Required
        </label>
        <Button variant="ghost" onClick={onRemove} title="Remove field">
          <Trash2 aria-hidden="true" size={16} />
        </Button>
      </div>
      {(field.fieldType === "select" || field.fieldType === "multi_select") && (
        <label className="grid gap-1 text-sm font-medium text-foreground sm:pl-8">
          <span className="flex items-center gap-2">
            Choices
            <InfoBubble label="Choices help">
              Separate choices with commas. Members will pick from these values in Discord.
            </InfoBubble>
          </span>
          <input
            className="h-9 rounded-md border border-border px-3 text-sm font-normal"
            value={field.options.join(", ")}
            onChange={(event) =>
              onChange({
                ...field,
                options: event.target.value
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean),
              })
            }
            placeholder="Option one, Option two, Option three"
          />
        </label>
      )}
    </div>
  );
}
