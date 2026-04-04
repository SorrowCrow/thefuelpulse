import { defineConfig } from 'astro/config';
import alpinejs from '@astrojs/alpinejs';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

import cloudflare from "@astrojs/cloudflare";

const __dirname = dirname(fileURLToPath(import.meta.url));

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
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
  },

  adapter: cloudflare()
});