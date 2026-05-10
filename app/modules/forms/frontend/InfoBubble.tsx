import type { ReactNode } from "react";
import { Info } from "lucide-react";

type InfoBubbleProps = {
  label: string;
  children: ReactNode;
  side?: "left" | "right";
};

export function InfoBubble({ label, children, side = "right" }: InfoBubbleProps) {
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-label={label}
        title={typeof children === "string" ? children : undefined}
        className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-border bg-white text-muted-foreground transition hover:border-primary hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <Info size={14} />
      </button>
      <span
        role="tooltip"
        className={`pointer-events-none absolute top-8 z-20 hidden w-72 max-w-[calc(100vw-2rem)] rounded-md border border-border bg-white p-3 text-left text-xs leading-5 text-muted-foreground shadow-lg group-hover:block group-focus-within:block ${
          side === "left" ? "right-0" : "left-0"
        }`}
      >
        {children}
      </span>
    </span>
  );
}
