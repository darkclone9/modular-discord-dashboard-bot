import { LogIn } from "lucide-react";

import { API_BASE_URL } from "../api/client";
import { Button } from "./ui/button";

export function LoginButton() {
  return (
    <Button onClick={() => (window.location.href = `${API_BASE_URL}/auth/discord/login`)}>
      <LogIn aria-hidden="true" size={16} />
      Discord Login
    </Button>
  );
}
