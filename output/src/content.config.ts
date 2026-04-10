import { defineCollection, z } from 'astro:content';

const articles = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    lang: z.enum(['lv', 'en', 'ru']),
    tags: z.array(z.string()).optional(),
    updated: z.coerce.date().optional(),
  }),
});

export const collections = { articles };
