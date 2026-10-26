import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em desenvolvimento, os pedidos /api e /media vão para o servidor Django
const servidor = process.env.API_URL || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,            // escuta em IPv4 e IPv6 (localhost e 127.0.0.1) e na rede local
    allowedHosts: true,    // aceita o endereço público de um túnel (ex.: Cloudflare) na demonstração
    proxy: { "/api": servidor, "/media": servidor },
  },
});
