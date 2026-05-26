const TIMEOUT_MINUTES = 15;
const TIMEOUT_MS = TIMEOUT_MINUTES * 60 * 1000;

let timeoutId = null;
let warningId = null;

export function startAutoLogout(onLogout, onWarning) {
  clearTimers();

  // Warning at 13 minutes
  warningId = setTimeout(() => {
    if (onWarning) onWarning();
  }, (TIMEOUT_MINUTES - 2) * 60 * 1000);

  // Logout at 15 minutes
  timeoutId = setTimeout(() => {
    clearTimers();
    localStorage.clear();
    if (onLogout) onLogout();
  }, TIMEOUT_MS);
}

export function resetAutoLogout(onLogout, onWarning) {
  startAutoLogout(onLogout, onWarning);
}

export function clearTimers() {
  if (timeoutId) clearTimeout(timeoutId);
  if (warningId) clearTimeout(warningId);
}