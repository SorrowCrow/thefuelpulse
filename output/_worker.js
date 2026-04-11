export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await env.ASSETS.fetch(request);

    if (url.hostname === "thefuelpulse.pages.dev") {
      const newHeaders = new Headers(response.headers);
      newHeaders.set("X-Robots-Tag", "noindex, nofollow");
      return new Response(response.body, {
        status: response.status,
        headers: newHeaders,
      });
    }
    return response;
  },
};
