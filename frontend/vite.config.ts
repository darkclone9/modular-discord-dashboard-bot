import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "lucide-react": fileURLToPath(
        new URL("./node_modules/lucide-react/dist/esm/lucide-react.js", import.meta.url),
      ),
      react: fileURLToPath(new URL("./node_modules/react", import.meta.url)),
      "react/jsx-runtime": fileURLToPath(
        new URL("./node_modules/react/jsx-runtime.js", import.meta.url),
      ),
    },
  },
  server: {
    port: 5173,
    allowedHosts: process.env.CADDY_WEB_HOST
      ? [process.env.CADDY_WEB_HOST, "localhost", "127.0.0.1"]
      : ["localhost", "127.0.0.1"],
    fs: {
      allow: [".."],
    },
  },
});
