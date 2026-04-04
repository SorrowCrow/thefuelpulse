import { defineConfig } from 'astro/config';
import alpinejs from '@astrojs/alpinejs';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

import cloudflare from "@astrojs/cloudflare";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  integrations: [alpinejs()],

  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
  },

  adapter: cloudflare()
});