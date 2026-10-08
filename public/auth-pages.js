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
})();
