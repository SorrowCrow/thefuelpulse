export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await env.ASSETS.fetch(request);

    const newHeaders = new Headers(response.headers);
    newHeaders.set("X-Worker-Active", "true");
    if (url.hostname !== "thefuelpulse.com") {
      newHeaders.set("X-Robots-Tag", "noindex, nofollow");
    }
    return new Response(response.body, {
      status: response.status,
      headers: newHeaders,
    });
  },
};
