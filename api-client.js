// Lets the same page scripts run on the website and inside the Capacitor app (mobile/).
// On the website (no window.FAR_NOTES_CONFIG) it changes nothing: same-origin fetch with the
// session cookie, and clean URLs like /login.
// In the app, mobile/scripts/build-www.js sets window.FAR_NOTES_CONFIG. Requests then go to the
// configured server with a bearer token, and page links point at the bundled .html files.
(function () {
  const config = window.FAR_NOTES_CONFIG;
  const TOKEN_KEY = "far-notes-session-token";
  const PAGES = {
    "/": "index.html",
    "/login": "login.html",
    "/create-account": "create-account.html",
    "/forgot-password": "forgot-password.html",
    "/reset-password": "reset-password.html"
  };

  function apiBase() {
    if (typeof config.apiBase === "string") return config.apiBase;
    const platform = window.Capacitor?.getPlatform?.() || "web";
    return config.apiBase[platform] || config.apiBase.default || "";
  }

  function readToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  function writeToken(token) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      // Storage unavailable: the user signs in again next launch.
    }
  }

  async function apiFetch(path, init = {}) {
    if (!config) return fetch(path, init);
    const headers = new Headers(init.headers);
    headers.set("X-Far-Notes-Client", "app");
    const token = readToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(apiBase() + path, { ...init, headers });
    if (path === "/api/auth/login" && response.ok) writeToken((await response.clone().json()).token);
    if (path === "/api/auth/logout" || response.status === 401) writeToken(null);
    return response;
  }

  function pageUrl(page) {
    return config ? PAGES[page] || page : page;
  }

  function goTo(page) {
    window.location.replace(pageUrl(page));
  }

  // The app has no server routes, so rewrite in-page links like href="/login" to the bundled files.
  if (config) {
    for (const link of document.querySelectorAll("a[href^='/']")) {
      link.setAttribute("href", pageUrl(link.getAttribute("href")));
    }
  }

  window.FarNotesApi = { fetch: apiFetch, pageUrl, goTo };
})();
