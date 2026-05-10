/* ============================================================
   TRAVELOOP - Global JavaScript Utilities
   ============================================================ */

// ──────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ──────────────────────────────────────────────
const Toast = (() => {
  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
    warn: '⚠️'
  };

  function show(message, type = 'info', duration = 3500) {
    const c = getContainer();
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-msg">${message}</span>
    `;
    c.appendChild(el);

    setTimeout(() => {
      el.classList.add('removing');
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  return {
    success: (msg, dur) => show(msg, 'success', dur),
    error: (msg, dur) => show(msg, 'error', dur),
    info: (msg, dur) => show(msg, 'info', dur),
    warn: (msg, dur) => show(msg, 'warn', dur),
  };
})();


// ──────────────────────────────────────────────
// API HELPER
// ──────────────────────────────────────────────
const API = {
  async request(method, url, body = null) {
    if (url.startsWith('/api') && window.location.port !== '5000') {
      url = `${window.location.protocol}//${window.location.hostname}:5000` + url;
    }
    const opts = {
      method,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);

    try {
      const res = await fetch(url, opts);
      const text = await res.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch (e) {
        throw new Error(`Invalid JSON response (Status ${res.status}): ${text.substring(0, 100)}`);
      }
      if (!res.ok) throw new Error(data?.error || 'Request failed');
      return data;
    } catch (err) {
      throw err;
    }
  },

  get: (url) => API.request('GET', url),
  post: (url, body) => API.request('POST', url, body),
  put: (url, body) => API.request('PUT', url, body),
  delete: (url) => API.request('DELETE', url),

  // File upload helper
  async upload(url, formData) {
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed');
    return data;
  }
};


// ──────────────────────────────────────────────
// AUTH / SESSION
// ──────────────────────────────────────────────
const Auth = {
  user: null,

  async fetchMe() {
    try {
      const data = await API.get('/api/me');
      this.user = data;
      return data;
    } catch {
      return null;
    }
  },

  async requireAuth() {
    const user = await this.fetchMe();
    if (!user) {
      window.location.href = 'index.html';
      return null;
    }
    return user;
  },

  async logout() {
    await API.post('/api/logout');
    window.location.href = 'index.html';
  }
};


// ──────────────────────────────────────────────
// SIDEBAR & NAVIGATION
// ──────────────────────────────────────────────
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const hamburger = document.getElementById('hamburger');

  if (hamburger && sidebar) {
    hamburger.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (backdrop) backdrop.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.style.display = 'none';
    });
  }

  // Set active nav link based on path
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (path === href || path.replace('.html', '') === href.replace('.html', '') || (href !== '/' && href !== 'dashboard.html' && path.startsWith(href)))) {
      link.classList.add('active');
    }
  });
}


// ──────────────────────────────────────────────
// USER DISPLAY
// ──────────────────────────────────────────────
function renderUserInSidebar(user) {
  const nameEl = document.getElementById('sidebar-user-name');
  const avatarEl = document.getElementById('sidebar-user-avatar');

  if (nameEl) nameEl.textContent = user.name || 'Traveler';

  if (avatarEl) {
    if (user.avatar) {
      avatarEl.innerHTML = `<img src="/static/uploads/${user.avatar}" alt="avatar">`;
    } else {
      const initials = (user.name || 'T').charAt(0).toUpperCase();
      avatarEl.textContent = initials;
    }
  }
}


// ──────────────────────────────────────────────
// MODAL HELPERS
// ──────────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.style.display = 'none';
    document.body.style.overflow = '';
  }
}

// Close modal on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    document.body.style.overflow = '';
  }
});


// ──────────────────────────────────────────────
// BUTTON LOADING STATE
// ──────────────────────────────────────────────
function setLoading(btn, loading) {
  if (loading) {
    btn._originalHTML = btn.innerHTML;
    btn.innerHTML = `<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div>`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._originalHTML || btn.innerHTML;
    btn.disabled = false;
  }
}


// ──────────────────────────────────────────────
// CONFETTI BURST
// ──────────────────────────────────────────────
function launchConfetti() {
  const colors = ['#7c3aed', '#3b82f6', '#14b8a6', '#f59e0b', '#f43f5e', '#a78bfa', '#60a5fa'];
  for (let i = 0; i < 80; i++) {
    setTimeout(() => {
      const el = document.createElement('div');
      el.className = 'confetti-piece';
      el.style.left = Math.random() * 100 + 'vw';
      el.style.background = colors[Math.floor(Math.random() * colors.length)];
      el.style.width = (6 + Math.random() * 8) + 'px';
      el.style.height = (6 + Math.random() * 8) + 'px';
      el.style.animationDuration = (2 + Math.random() * 2) + 's';
      el.style.animationDelay = (Math.random() * 0.5) + 's';
      el.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 4000);
    }, i * 20);
  }
}


// ──────────────────────────────────────────────
// DATE UTILITIES
// ──────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + (dateStr.includes('T') ? '' : 'T00:00:00'));
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const diff = new Date(dateStr) - new Date();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function tripDuration(start, end) {
  if (!start || !end) return null;
  const diff = new Date(end) - new Date(start);
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}


// ──────────────────────────────────────────────
// COVER IMAGE PLACEHOLDERS
// ──────────────────────────────────────────────
const TRIP_EMOJIS = ['🗼', '🏖️', '🗽', '🏯', '🗿', '🌋', '🏔️', '🏝️', '🌉', '🎡', '⛩️', '🏰'];

function getTripEmoji(tripId) {
  return '✈️';
}

function renderTripCover(trip) {
  if (trip.cover_image) {
    return `<img src="/static/uploads/${trip.cover_image}" class="trip-card-image" alt="${trip.title}" loading="lazy">`;
  }
  const logo = '✈️';
  const gradients = [
    'linear-gradient(135deg,#7c3aed,#3b82f6)',
    'linear-gradient(135deg,#14b8a6,#3b82f6)',
    'linear-gradient(135deg,#f59e0b,#ef4444)',
    'linear-gradient(135deg,#6366f1,#a78bfa)',
    'linear-gradient(135deg,#f43f5e,#7c3aed)',
  ];
  const grad = gradients[trip.id % gradients.length];
  return `<div class="trip-card-image-placeholder" style="background:${grad}">${logo}</div>`;
}

// ──────────────────────────────────────────────
// CURRENCY FORMATTER
// ──────────────────────────────────────────────
function formatCurrency(amount, currency = 'INR') {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency, maximumFractionDigits: 0
  }).format(amount || 0);
}

// ──────────────────────────────────────────────
// CATEGORY META
// ──────────────────────────────────────────────
const CATEGORIES = {
  sightseeing: { label: 'Sightseeing', icon: '🏛️', class: 'cat-sightseeing' },
  food: { label: 'Food & Dining', icon: '🍜', class: 'cat-food' },
  transport: { label: 'Transport', icon: '✈️', class: 'cat-transport' },
  adventure: { label: 'Adventure', icon: '🧗', class: 'cat-adventure' },
  culture: { label: 'Culture', icon: '🎭', class: 'cat-culture' },
  shopping: { label: 'Shopping', icon: '🛍️', class: 'cat-shopping' },
  hotels: { label: 'Hotels', icon: '🏨', class: 'cat-sightseeing' },
  misc: { label: 'Misc', icon: '📌', class: 'cat-transport' },
};

function getCatMeta(cat) {
  return CATEGORIES[cat] || { label: cat, icon: '📌', class: 'cat-transport' };
}

const PACK_CATS = {
  clothing: { label: 'Clothing', icon: '👕' },
  electronics: { label: 'Electronics', icon: '💻' },
  documents: { label: 'Documents', icon: '📄' },
  toiletries: { label: 'Toiletries', icon: '🧴' },
  general: { label: 'General', icon: '🎒' },
};

const MOODS = {
  happy: '😊',
  excited: '🤩',
  tired: '😴',
  amazing: '🌟',
  meh: '😐',
};