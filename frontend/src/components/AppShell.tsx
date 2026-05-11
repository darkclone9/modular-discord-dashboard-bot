import { LogOut, Settings } from "lucide-react";
import type { ReactNode } from "react";

import { logout as logoutRequest } from "../api/auth";
import { Button } from "./ui/button";
import { ThemeToggle } from "./ThemeToggle";

type Props = {
  children: ReactNode;
  username?: string;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onLogout: () => void;
};

export function AppShell({ children, username, theme, onToggleTheme, onLogout }: Props) {
  async function logout() {
    await logoutRequest();
    onLogout();
  }

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-border bg-card flex-shrink-0">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Settings aria-hidden="true" size={17} />
            Modular Bot
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            {username && <span>{username}</span>}
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <Button variant="ghost" onClick={logout} title="Log out">
              <LogOut aria-hidden="true" size={16} />
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-1 mx-auto max-w-6xl w-full px-4 py-6 overflow-y-auto">{children}</main>
    </div>
  );
}
