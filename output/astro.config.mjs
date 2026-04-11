import { defineConfig } from 'astro/config';
import alpinejs from '@astrojs/alpinejs';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { readFileSync, writeFileSync } from 'fs';

import cloudflare from "@astrojs/cloudflare";

const __dirname = dirname(fileURLToPath(import.meta.url));

const BUILD_TIMESTAMP = Date.now().toString();

function swTimestampPlugin() {
  return {
    name: 'sw-timestamp-inject',
    enforce: 'post',
    closeBundle() {
      const swPath = resolve(__dirname, 'dist/sw.js');
      try {
        const src = readFileSync(swPath, 'utf-8');
        const patched = src.replace('__BUILD_TIMESTAMP__', BUILD_TIMESTAMP);
        writeFileSync(swPath, patched, 'utf-8');
      } catch {
        // dev mode — dist/sw.js doesn't exist yet, skip
      }
    },
  };
}

export default defineConfig({
  site: 'https://thefuelpulse.com',

  i18n: {
    defaultLocale: 'lv',
    locales: ['lv', 'en', 'ru'],
    routing: {
      prefixDefaultLocale: false,
    },
  },

  integrations: [
    alpinejs(),
    sitemap({
      i18n: {
        defaultLocale: 'lv',
        locales: {
          lv: 'lv-LV',
          en: 'en-US',
          ru: 'ru-RU',
        },
      },
    }),
  ],

  vite: {
    plugins: [tailwindcss(), swTimestampPlugin()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
  },

  adapter: cloudflare(),
});