// Pure input checks shared by server.js and the node:test unit tests.
// Each check* function returns an error message for the client, or null when the value is valid.

const PASSWORD_MIN_LENGTH = 15;
const PASSWORD_MAX_BYTES = 1024;
const USERNAME_PATTERN = /^[A-Za-z0-9._-]{1,64}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const EMAIL_MAX_LENGTH = 254;

function isIsoDate(value) {
  if (value === "") return true;
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

function checkUsername(username) {
  return USERNAME_PATTERN.test(username)
    ? null
    : "Username must be 1-64 characters and use only letters, numbers, periods, underscores, or hyphens.";
}

function checkEmail(email) {
  return email.length <= EMAIL_MAX_LENGTH && EMAIL_PATTERN.test(email) ? null : "Enter a valid email address.";
}

// Length is counted in characters (code points), so "😀" counts once; the limit is in UTF-8 bytes.
function checkPassword(password) {
  if ([...password].length < PASSWORD_MIN_LENGTH) return `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`;
  if (Buffer.byteLength(password) > PASSWORD_MAX_BYTES) return `Password must be ${PASSWORD_MAX_BYTES} bytes or fewer.`;
  return null;
}

module.exports = { PASSWORD_MIN_LENGTH, PASSWORD_MAX_BYTES, isIsoDate, checkUsername, checkEmail, checkPassword };
