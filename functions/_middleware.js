export async function onRequest({ request, next }) {
  const response = await next();
  const url = new URL(request.url);
  if (url.hostname === "thefuelpulse.pages.dev") {
    const newHeaders = new Headers(response.headers);
    newHeaders.set("X-Robots-Tag", "noindex, nofollow");
    return new Response(response.body, {
      status: response.status,
      headers: newHeaders,
    });
  }
  return response;
}
