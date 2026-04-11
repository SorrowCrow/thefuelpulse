import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('text/html')) {
    const headers = new Headers(response.headers);
    headers.set('Cache-Control', 'no-cache, no-store, must-revalidate');
    headers.set('Pragma', 'no-cache');
    if (context.url.hostname !== 'thefuelpulse.com') {
      headers.set('X-Robots-Tag', 'noindex, nofollow');
    }
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  }

  return response;
});
