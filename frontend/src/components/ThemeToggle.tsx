import { Moon, Sun } from "lucide-react";

import { Button } from "./ui/button";

type Props = {
  theme: "light" | "dark";
  onToggle: () => void;
};

export function ThemeToggle({ theme, onToggle }: Props) {
  const isDark = theme === "dark";
  return (
    <Button
      variant="ghost"
      onClick={onToggle}
      title={isDark ? "Use light mode" : "Use dark mode"}
      aria-label={isDark ? "Use light mode" : "Use dark mode"}
    >
      {isDark ? <Sun aria-hidden="true" size={16} /> : <Moon aria-hidden="true" size={16} />}
    </Button>
  );
}
