// Login, signup, forgot-password and reset-password pages. Each page sets <body data-page="...">.

const page = document.body.dataset.page;
const form = document.getElementById("auth-form");
const msg = document.getElementById("auth-msg");
const submit = form?.querySelector("button[type=submit]");

function show(text, kind = "error") {
  msg.textContent = text;
  msg.className = `auth-msg ${kind}`;
  msg.hidden = !text;
}

function busy(on, label) {
  if (!submit) return;
  submit.disabled = on;
  if (label) submit.textContent = label;
}

function friendly(error) {
  const m = (error && error.message) || String(error);
  if (/invalid login credentials/i.test(m)) return "That email and password don't match. Try again or reset your password.";
  if (/email not confirmed/i.test(m)) return "Please confirm your email first. Check your inbox for the link we sent.";
  if (/rate limit|too many/i.test(m)) return "Too many attempts. Please wait a few minutes and try again.";
  if (/password should be|weak password/i.test(m)) return "Please choose a stronger password (at least 8 characters).";
  return m;
}

async function onLogin(client) {
  const params = new URLSearchParams(location.search);
  if (params.get("confirmed")) show("Email confirmed. You can log in now.", "ok");
  if (params.get("reset")) show("Password updated. Log in with your new password.", "ok");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    show("");
    busy(true, "Logging in…");
    const { error } = await client.auth.signInWithPassword({
      email: form.email.value.trim(),
      password: form.password.value,
    });
    if (error) {
      show(friendly(error));
      busy(false, "Log in");
      return;
    }
    location.replace(safeNext());
  });
}

async function onSignup(client) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    show("");
    if (form.password.value.length < 8) return show("Password must be at least 8 characters.");
    if (form.password.value !== form.confirm.value) return show("Passwords don't match.");
    busy(true, "Creating account…");
    const { data, error } = await client.auth.signUp({
      email: form.email.value.trim(),
      password: form.password.value,
      options: { emailRedirectTo: `${location.origin}/login/?confirmed=1` },
    });
    if (error) {
      show(friendly(error));
      busy(false, "Create account");
      return;
    }
    if (data.session) {
      location.replace("/chat/"); // email confirmation is turned off in Supabase
      return;
    }
    // Same message whether or not the email was already registered, so accounts can't be probed.
    form.hidden = true;
    show(`Check ${form.email.value.trim()} for a confirmation link, then log in.`, "ok");
  });
}

async function onForgot(client) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    show("");
    busy(true, "Sending…");
    const { error } = await client.auth.resetPasswordForEmail(form.email.value.trim(), {
      redirectTo: `${location.origin}/reset-password/`,
    });
    if (error && /rate limit|too many/i.test(error.message)) {
      show(friendly(error));
      busy(false, "Send reset link");
      return;
    }
    form.hidden = true;
    show("If an account exists for that email, we've sent a link to reset your password.", "ok");
  });
}

async function onReset(client) {
  // The link in the email signs the user in with a short-lived recovery session (read from the URL).
  form.hidden = true;
  let ready = false;
  const enable = () => {
    if (ready) return;
    ready = true;
    form.hidden = false;
    show("");
    form.password.focus();
  };
  client.auth.onAuthStateChange((event, session) => {
    if (event === "PASSWORD_RECOVERY" || (session && event === "SIGNED_IN")) enable();
  });
  const { data } = await client.auth.getSession();
  if (data.session) enable();
  setTimeout(() => {
    if (!ready) show("This reset link is invalid or has expired. Request a new one below.");
  }, 2500);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    show("");
    if (form.password.value.length < 8) return show("Password must be at least 8 characters.");
    if (form.password.value !== form.confirm.value) return show("Passwords don't match.");
    busy(true, "Saving…");
    const { error } = await client.auth.updateUser({ password: form.password.value });
    if (error) {
      show(friendly(error));
      busy(false, "Set new password");
      return;
    }
    await client.auth.signOut();
    location.replace("/login/?reset=1");
  });
}

(async () => {
  let client;
  try {
    client = await getAuthClient();
  } catch (err) {
    show(err.message);
    if (submit) submit.disabled = true;
    return;
  }
  // Already logged in? Skip the login/signup forms.
  if (page === "login" || page === "signup") {
    const { data } = await client.auth.getSession();
    if (data.session) return location.replace(safeNext());
  }
  ({ login: onLogin, signup: onSignup, forgot: onForgot, reset: onReset })[page](client);
  if (page === "login" || page === "signup") addOAuth(client);
})();

// "Continue with Google", shown only when the Google provider is enabled in Supabase Auth.
async function addOAuth(client) {
  let enabled = false;
  try {
    const cfg = await (await fetch("/api/public-config")).json();
    const settings = await (await fetch(`${cfg.supabase_url}/auth/v1/settings`, { headers: { apikey: cfg.supabase_anon_key } })).json();
    enabled = Boolean(settings.external?.google);
  } catch {
    return; // no button if the settings can't be read
  }
  const form = document.getElementById("auth-form");
  if (!enabled || !form) return;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "oauth-btn";
  btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18"><path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5a5.6 5.6 0 0 1-2.4 3.6v3h3.9c2.2-2.1 3.5-5.1 3.5-8.8z"/><path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1A12 12 0 0 0 12 24z"/><path fill="#FBBC05" d="M5.3 14.3a7.2 7.2 0 0 1 0-4.6V6.6h-4a12 12 0 0 0 0 10.8z"/><path fill="#EA4335" d="M12 4.8c1.8 0 3.3.6 4.6 1.8l3.4-3.4A12 12 0 0 0 1.3 6.6l4 3.1c.9-2.9 3.6-4.9 6.7-4.9z"/></svg><span>Continue with Google</span>';
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    const { error } = await client.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: new URL(safeNext(), location.origin).href },
    });
    if (error) {
      show(friendly(error));
      btn.disabled = false;
    }
  });
  const or = document.createElement("p");
  or.className = "auth-or";
  or.innerHTML = "<span>or</span>";
  form.before(btn, or);
}
