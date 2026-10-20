// Shared CORS helper for all Edge Functions.
//
// Browsers block a page on one origin (jocelynperucca.github.io) from reading
// responses from another origin (*.supabase.co) unless the server says it's OK.
// We only say OK to origins on our allowlist.

// TODO 1: Fill in the two origins that may call your functions.
//   - your GitHub Pages site (scheme + host only, NO path, NO trailing slash)
//   - your local dev server on port 5500
//   Hint: an origin looks like "https://example.com" or "http://localhost:1234"
const ALLOWED_ORIGINS = [
  "https://jocelynperucca.github.io",
  "http://localhost:5500",
];

export function corsHeaders(req: Request): Record<string, string> {
  const origin = req.headers.get("Origin") ?? "";
  // Echo the caller's origin back only if it's on the allowlist.
  const allowOrigin = ALLOWED_ORIGINS.includes(origin)
    ? origin
    : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    Vary: "Origin",
  };
}

// Small helper so every response gets JSON + CORS headers.
export function jsonResponse(
  req: Request,
  body: unknown,
  status = 200,
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(req), "Content-Type": "application/json" },
  });
}
