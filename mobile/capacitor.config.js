// Capacitor reads this when it syncs and builds the native projects in ios/ and android/.
// FAR_NOTES_API_URL is the server the app talks to (see scripts/build-www.js). Plain http is allowed
// only while it points at a development server; a hosted https server turns those exceptions off.
const apiUrl = process.env.FAR_NOTES_API_URL || "";
const allowHttp = !apiUrl.startsWith("https://");

/** @type {import('@capacitor/cli').CapacitorConfig} */
module.exports = {
  appId: "com.farnotes.studylog",
  appName: "FAR Notes",
  webDir: "www",
  server: {
    cleartext: allowHttp
  },
  android: {
    // The Android shell is served from https://localhost, so calls to an http dev server count as mixed content.
    allowMixedContent: allowHttp
  }
};
