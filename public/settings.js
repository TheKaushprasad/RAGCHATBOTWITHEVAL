// Settings: change password, delete chat history, delete account.

function show(id, text, kind = "error") {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `auth-msg ${kind}`;
  el.hidden = !text;
}

async function call(path, method) {
  const session = await getSession();
  if (!session) return location.replace("/login/?next=/settings/");
  const res = await fetch(path, { method, headers: { Authorization: `Bearer ${session.access_token}` } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
  return data;
}

(async () => {
  const session = await requireLogin();
  const client = await getAuthClient();
  const email = session.user.email;
  document.getElementById("email").textContent = email;
  document.body.classList.remove("is-loading");

  const pw = document.getElementById("pw-form");
  pw.addEventListener("submit", async (e) => {
    e.preventDefault();
    show("pw-msg", "");
    if (pw.password.value.length < 8) return show("pw-msg", "New password must be at least 8 characters.");
    if (pw.password.value !== pw.confirm.value) return show("pw-msg", "New passwords don't match.");
    const btn = pw.querySelector("button");
    btn.disabled = true;
    // Re-check the current password first, so an unattended logged-in browser can't change it.
    const { error: authErr } = await client.auth.signInWithPassword({ email, password: pw.current.value });
    if (authErr) {
      btn.disabled = false;
      return show("pw-msg", "Your current password is incorrect.");
    }
    const { error } = await client.auth.updateUser({ password: pw.password.value });
    btn.disabled = false;
    if (error) return show("pw-msg", error.message);
    pw.reset();
    show("pw-msg", "Password updated.", "ok");
  });

  document.getElementById("clear-history").addEventListener("click", async (e) => {
    if (!confirm("Delete all your conversations? This can't be undone.")) return;
    e.target.disabled = true;
    try {
      await call("/api/conversations", "DELETE");
      show("hist-msg", "All chat history deleted.", "ok");
    } catch (err) {
      show("hist-msg", err.message);
    } finally {
      e.target.disabled = false;
    }
  });

  const del = document.getElementById("del-form");
  del.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (del.confirm.value.trim() !== "DELETE") return show("del-msg", "Type DELETE to confirm.");
    const btn = del.querySelector("button");
    btn.disabled = true;
    try {
      await call("/api/account", "DELETE");
      await client.auth.signOut();
      location.replace("/?account=deleted");
    } catch (err) {
      show("del-msg", err.message);
      btn.disabled = false;
    }
  });

  document.getElementById("logout").addEventListener("click", async () => {
    await client.auth.signOut();
    location.replace("/");
  });
})();
