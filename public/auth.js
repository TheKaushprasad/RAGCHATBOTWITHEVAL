// Shared Supabase Auth client for every page. Needs supabase-js loaded first (window.supabase).
// The URL and public anon key come from /api/public-config, so nothing is hard-coded here.

let authClientPromise;

function getAuthClient() {
  if (!authClientPromise) {
    authClientPromise = fetch("/api/public-config")
      .then((r) => {
        if (!r.ok) throw new Error("Sign-in isn't available right now.");
        return r.json();
      })
      .then((cfg) =>
        window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
          // Implicit flow: password-reset and confirmation links work even when opened in another browser.
          auth: { flowType: "implicit", persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
        }),
      );
  }
  return authClientPromise;
}

async function getSession() {
  const client = await getAuthClient();
  const { data } = await client.auth.getSession();
  return data.session;
}

// Send people who aren't logged in to /login/, then bring them back here afterwards.
async function requireLogin() {
  const session = await getSession().catch(() => null);
  if (!session) {
    const next = encodeURIComponent(location.pathname + location.search + location.hash);
    location.replace(`/login/?next=${next}`);
    return new Promise(() => {}); // stop the page while redirecting
  }
  return session;
}

// Only allow same-site relative redirects (prevents ?next=https://evil.example).
function safeNext(fallback = "/chat/") {
  const next = new URLSearchParams(location.search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : fallback;
}
