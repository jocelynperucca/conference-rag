// Shared auth helper: is the caller a real, logged-in user?
//
// We deploy with --no-verify-jwt, so Supabase does NOT check the token for us.
// Instead we pass the caller's JWT to Supabase Auth and ask "who is this?".
// - A logged-in user's JWT  -> returns their user record
// - The anon key (or junk)  -> returns an error -> we refuse with 401
import { createClient, type User } from "jsr:@supabase/supabase-js@2";

export async function getUser(req: Request): Promise<User | null> {
  const authHeader = req.headers.get("Authorization") ?? "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (!token) return null;

  // SUPABASE_URL and SUPABASE_ANON_KEY are provided automatically to every
  // Edge Function -- you don't set these yourself.
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
  );

  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) return null;
  return data.user;
}
