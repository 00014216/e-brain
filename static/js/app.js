// e-brain — Global App JavaScript

document.addEventListener('DOMContentLoaded', () => {
  initFlashDismiss();
});

function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
    el.addEventListener('click', () => el.remove());
  });
}

// Global helper: make a request and handle errors
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error('API error:', e.message);
    throw e;
  }
}

// Format a date string to "10 Apr 2026"
function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

// Truncate text
function truncate(str, len = 120) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '...' : str;
}
