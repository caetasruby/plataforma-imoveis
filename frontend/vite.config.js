import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em desenvolvimento, os pedidos /api e /media vão para o servidor Django
const servidor = process.env.API_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: { "/api": servidor, "/media": servidor },
  },
});
