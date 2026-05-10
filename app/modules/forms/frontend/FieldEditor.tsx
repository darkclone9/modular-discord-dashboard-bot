import { GripVertical, Trash2 } from "lucide-react";

import type { FieldType, FormField } from "../../../../frontend/src/api/forms";
import { Button } from "../../../../frontend/src/components/ui/button";

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
      <div className="grid gap-2 sm:grid-cols-[24px_1fr_160px_110px_40px] sm:items-center">
        <GripVertical aria-hidden="true" className="hidden text-muted-foreground sm:block" size={16} />
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={field.label}
          onChange={(event) => onChange({ ...field, label: event.target.value })}
          placeholder="Field label"
        />
        <select
          className="h-9 rounded-md border border-border bg-white px-3 text-sm"
          value={field.fieldType}
          onChange={(event) => onChange({ ...field, fieldType: event.target.value as FieldType })}
        >
          {FIELD_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
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
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
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
          placeholder="Options separated by commas"
        />
      )}
    </div>
  );
}
