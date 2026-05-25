import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss()],
  base: "/static/dist/",
  build: {
    outDir: "website/static/dist",
    manifest: true,
    rollupOptions: {
      input: {
        main: "assets/js/main.js",
        style: "assets/css/main.css",
      },
    },
    emptyOutDir: true,
  },
});
