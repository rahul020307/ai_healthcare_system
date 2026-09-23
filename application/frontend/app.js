// CuraAssist CareHub - Complete Application Engine & Logic (11 Prototype Modules)
const API_BASE = (window.CURAASSIST_API_BASE || 'https://curaassist-carehub-backend-2.fastapicloud.dev').replace(/\/$/, '');

let state = {
  currentTab: 'home',
  currentLang: 'en',
  activeFamilyId: 'mem-1',
  cart: [
    { id: "med-1", qty: 1 },
    { id: "med-4", qty: 1 }
  ],
  schedule: [],
  records: [],
  activeRecordFilter: 'All',
  activeMapFilter: 'All',
  appliedPromo: null,
  theme: 'dark',
  map: null,
  mapMarkers: [],
  activeRoutePolyline: null
};

function getSupabaseClient() {
  if (window._supabaseClient) return window._supabaseClient;
  if (typeof supabase !== 'undefined' && supabase.createClient) {
    const url = window.SUPABASE_URL || "https://ifwsijbkmuzqttwbvifp.supabase.co";
    const key = window.SUPABASE_ANON_KEY || "";
    try {
      window._supabaseClient = supabase.createClient(url, key);
      return window._supabaseClient;
    } catch (e) {
      console.warn("Supabase init note:", e);
    }
  }
  return null;
}

async function getAuthToken() {
  const client = getSupabaseClient();
  if (client && client.auth) {
    try {
      const { data: { session } } = await client.auth.getSession();
      if (session?.access_token) {
        window.authToken = session.access_token;
        return window.authToken;
      }
    } catch (e) {}
  }
  if (window.authToken) return window.authToken;
  return null;
}

async function getAuthHeaders() {
  const token = await getAuthToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function fetchUserDataFromBackend() {
  const headers = await getAuthHeaders();
  if (!headers['Authorization']) return;

  let localUser = null;
  try {
    const saved = localStorage.getItem('cura_active_user_v1');
    if (saved) localUser = JSON.parse(saved);
  } catch (e) {}

  try {
    const profRes = await fetch(`${API_BASE}/profile/user`, { headers });
    if (profRes.ok) {
      const profData = await profRes.json();
      if (profData.user) {
        const backendAvatar = profData.user.avatar || profData.user.avatarUrl;
        const mergedUser = {
          isLoggedIn: true,
          ...profData.user,
          ...(localUser || {})
        };
        if (backendAvatar) mergedUser.avatar = backendAvatar;
        if (profData.user.name) mergedUser.userName = profData.user.name;
        if (profData.user.phone) mergedUser.phone = profData.user.phone;
        if (profData.user.bloodGroup) mergedUser.blood = profData.user.bloodGroup;
        if (profData.user.location) mergedUser.city = profData.user.location;
        if (profData.user.age) mergedUser.age = profData.user.age;
        try { localStorage.setItem('cura_active_user_v1', JSON.stringify(mergedUser)); } catch (e) {}
        updateAuthUIState(mergedUser);
      }
    } else if (localUser) {
      updateAuthUIState(localUser);
    }

    const recRes = await fetch(`${API_BASE}/profile/health-records`, { headers });
    if (recRes.ok) {
      const recData = await recRes.json();
      if (Array.isArray(recData.records)) {
        state.records = recData.records;
        if (typeof renderRecords === 'function') renderRecords();
      }
    }

    const schRes = await fetch(`${API_BASE}/profile/schedules`, { headers });
    if (schRes.ok) {
      const schData = await schRes.json();
      if (Array.isArray(schData.schedules)) {
        state.schedule = schData.schedules;
        if (typeof renderSchedule === 'function') renderSchedule();
      }
    }
  } catch (e) {
    console.warn("[CuraAssist] Backend data sync note:", e);
    if (localUser) updateAuthUIState(localUser);
  }
}

function saveStateToStorage() {
  try {
    localStorage.setItem('cura_cart_v1', JSON.stringify(state.cart));
    if (state.schedule) localStorage.setItem('cura_schedules_v1', JSON.stringify(state.schedule));
  } catch (e) {
    console.warn("[CuraAssist] Storage save error:", e);
  }
}

function loadStateFromStorage() {
  try {
    const savedCart = localStorage.getItem('cura_cart_v1');
    if (savedCart) state.cart = JSON.parse(savedCart);
    const savedSchedules = localStorage.getItem('cura_schedules_v1');
    if (savedSchedules) {
      state.schedule = JSON.parse(savedSchedules);
    } else if (!state.schedule || state.schedule.length === 0) {
      state.schedule = [
        { id: "sch-demo-1", name: "Paracetamol 500mg", dosage: "1 Tablet", time: "08:00 AM", mealInstruction: "🍽️ After Meals", frequency: "Daily", refillsLeft: 28, totalPills: 30, taken: false },
        { id: "sch-demo-2", name: "Vitamin D3 60K", dosage: "1 Capsule", time: "08:00 PM", mealInstruction: "🥗 Before Meals", frequency: "Daily", refillsLeft: 14, totalPills: 15, taken: false }
      ];
    }
  } catch (e) {
    console.warn("[CuraAssist] Storage load error:", e);
  }
  fetchUserDataFromBackend();
}

function ensureLucideIcons() {
  if (typeof lucide !== 'undefined' && lucide.createIcons) {
    try { lucide.createIcons(); } catch (e) {}
  } else {
    setTimeout(ensureLucideIcons, 150);
  }
}
window.addEventListener('load', ensureLucideIcons);

function initSpotlightCards() {
  document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.kokonut-card');
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      if (e.clientX >= rect.left - 60 && e.clientX <= rect.right + 60 && e.clientY >= rect.top - 60 && e.clientY <= rect.bottom + 60) {
        card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
        card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
      }
    });
  }, { passive: true });
}

function initScrollProgress() {
  const bar = document.getElementById('scroll-progress-bar');
  if (!bar) return;
  const handleScroll = (scroller) => {
    const docEl = document.documentElement;
    const st = scroller.scrollTop || window.scrollY || docEl.scrollTop || 0;
    const sh = (scroller.scrollHeight || docEl.scrollHeight) - (scroller.clientHeight || window.innerHeight);
    const pct = sh > 0 ? (st / sh) * 100 : 0;
    bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  };
  window.addEventListener('scroll', () => handleScroll(document.documentElement), { passive: true });
  document.addEventListener('scroll', () => handleScroll(document.documentElement), { passive: true });
  const main = document.querySelector('main');
  if (main) main.addEventListener('scroll', () => handleScroll(main), { passive: true });
}

function initScrollReveals() {
  const reveals = document.querySelectorAll('.scroll-reveal:not(.is-revealed)');
  if (!reveals.length) return;
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
    reveals.forEach(el => observer.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('is-revealed'));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const safeRun = (fn, name) => {
    try { fn(); } catch (err) { console.warn(`[CuraAssist] Init warning in ${name}:`, err); }
  };
  safeRun(() => loadStateFromStorage(), 'initDataState');
  safeRun(() => checkSavedSession(), 'checkSavedSession');
  safeRun(() => ensureLucideIcons(), 'lucide');
  setTimeout(ensureLucideIcons, 300);
  setTimeout(ensureLucideIcons, 800);
  safeRun(() => initFamilyDropdown(), 'initFamilyDropdown');
  safeRun(() => renderActiveFamilyContext(), 'renderActiveFamilyContext');
  safeRun(() => renderSchedule(), 'renderSchedule');
  safeRun(() => renderRecords(), 'renderRecords');
  safeRun(() => renderStoreCategories(), 'renderStoreCategories');
  safeRun(() => renderStoreMedicines(), 'renderStoreMedicines');
  safeRun(() => renderCart(), 'renderCart');
  safeRun(() => renderBloodCompatibility(), 'renderBloodCompatibility');
  safeRun(() => renderFeedbackList(), 'renderFeedbackList');
  safeRun(() => renderFirstAidGuide(), 'renderFirstAidGuide');
  safeRun(() => renderGenericDropdown(), 'renderGenericDropdown');
  safeRun(() => updateUploadsBadgeCount(), 'updateUploadsBadgeCount');
  safeRun(() => initSpotlightCards(), 'initSpotlightCards');
  safeRun(() => initScrollProgress(), 'initScrollProgress');
  safeRun(() => initScrollReveals(), 'initScrollReveals');
  safeRun(() => typeof AppModal !== 'undefined' && AppModal.init(), 'AppModal.init');
  safeRun(() => typeof AppAlarms !== 'undefined' && AppAlarms.start(), 'AppAlarms.start');
  safeRun(() => typeof AppState !== 'undefined' && AppState.init(typeof INITIAL_DATA !== 'undefined' ? INITIAL_DATA : {}), 'AppState.init');
});

async function syncDatabaseRecordsWithBackend() {
  const headers = await getAuthHeaders();
  if (!headers['Authorization']) return;
  try {
    const res = await fetch(`${API_BASE}/profile/health-records`, { headers });
    if (res.ok) {
      const data = await res.json();
      if (data && data.records && data.records.length > 0) {
        const existingIds = new Set(state.records.map(r => r.id));
        let added = false;
        data.records.forEach(r => {
          if (!existingIds.has(r.id)) { state.records.unshift(r); existingIds.add(r.id); added = true; }
        });
        if (added && typeof renderRecords === 'function') renderRecords();
      }
    }
  } catch (e) {
    console.warn("SQL health-records sync note:", e);
  }
}

function toggleMobileMenuDrawer() {
  const drawer = document.getElementById('mobile-menu-drawer');
  if (!drawer) return;
  const isHidden = drawer.style.display === 'none' || drawer.classList.contains('hidden');
  if (isHidden) { drawer.style.display = 'flex'; drawer.classList.remove('hidden'); if (window.lucide) lucide.createIcons(); }
  else { drawer.style.display = 'none'; drawer.classList.add('hidden'); }
}

function switchTab(tabName) {
  state.currentTab = tabName;
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-btn').forEach(el => { el.classList.remove('text-teal-400', 'font-black', 'scale-105'); el.classList.add('text-slate-400'); });
  document.querySelectorAll('.header-nav-btn').forEach(el => { el.classList.remove('active', 'text-teal-400', 'bg-teal-500/20', 'border', 'border-teal-500/40'); el.classList.add('text-slate-400'); });
  const activeNav = document.getElementById(`nav-${tabName}`); if (activeNav) activeNav.classList.add('active');
  const activeMobileNav = document.getElementById(`mobile-nav-${tabName}`); if (activeMobileNav) { activeMobileNav.classList.remove('text-slate-400'); activeMobileNav.classList.add('text-teal-400', 'font-black', 'scale-105'); }
  const activeHeaderNav = document.getElementById(`header-nav-${tabName}`); if (activeHeaderNav) { activeHeaderNav.classList.remove('text-slate-400'); activeHeaderNav.classList.add('active', 'text-teal-400', 'bg-teal-500/20', 'border', 'border-teal-500/40'); }
  const appHeader = document.getElementById('app-header'); if (appHeader) { if (tabName === 'maps') appHeader.classList.add('hidden'); else appHeader.classList.remove('hidden'); }
  ['home', 'reminders', 'store', 'maps', 'profile'].forEach(tab => { const sec = document.getElementById(`view-${tab}`); if (sec) sec.classList.add('hidden'); });
  const targetSec = document.getElementById(`view-${tabName}`); if (targetSec) targetSec.classList.remove('hidden');
  if (tabName === 'reminders' || tabName === 'home') { if (typeof renderSchedule === 'function') renderSchedule(); }
  if (tabName === 'maps') setTimeout(() => { initMap(); if (state.map) state.map.invalidateSize(); }, 200);
  const mainContent = document.querySelector('main'); if (mainContent) mainContent.scrollTop = 0;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  setTimeout(initScrollReveals, 100);
}

function toggleNearbyPlacesLayout() {
  const drawer = document.getElementById('nearby-places-drawer');
  if (!drawer) return;
  if (drawer.classList.contains('max-h-56')) { drawer.classList.remove('max-h-56'); drawer.classList.add('max-h-[75vh]'); }
  else if (drawer.classList.contains('max-h-[75vh]')) { drawer.classList.remove('max-h-[75vh]'); drawer.classList.add('max-h-12', 'overflow-hidden'); }
  else { drawer.classList.remove('max-h-12', 'overflow-hidden'); drawer.classList.add('max-h-56'); }
  if (state.map) setTimeout(() => state.map.invalidateSize(), 300);
}

function scrollToSection(secId) { switchTab('home'); setTimeout(() => document.getElementById(secId)?.scrollIntoView({ behavior: 'smooth' }), 100); }

function openAuthModal() { switchAuthTab('login'); const overlay = document.getElementById('auth-guard-overlay'); if (overlay) overlay.classList.remove('hidden'); }

async function closeAuthModal() {
  const token = window.authToken || (await getAuthToken());
  if (token) { const overlay = document.getElementById('auth-guard-overlay'); if (overlay) overlay.classList.add('hidden'); }
  else alert("⚠️ Registration or Login is required to access the application.");
}

function togglePasswordVisibility(fieldId) { const input = document.getElementById(fieldId); if (!input) return; input.type = input.type === 'password' ? 'text' : 'password'; }

function showAuthInlineMessage(text, type = 'error') {
  const el = document.getElementById('auth-inline-msg');
  if (!el) return;
  if (!text) { el.classList.add('hidden'); el.innerText = ''; return; }
  el.classList.remove('hidden', 'bg-rose-500/10', 'border-rose-500/30', 'text-rose-300', 'bg-emerald-500/10', 'border-emerald-500/30', 'text-emerald-300', 'bg-teal-500/10', 'border-teal-500/30', 'text-teal-300');
  if (type === 'success') el.classList.add('bg-emerald-500/10', 'border-emerald-500/30', 'text-emerald-300');
  else if (type === 'loading') el.classList.add('bg-teal-500/10', 'border-teal-500/30', 'text-teal-300');
  else el.classList.add('bg-rose-500/10', 'border-rose-500/30', 'text-rose-300');
  el.innerText = text;
}

function switchAuthTab(mode) {
  showAuthInlineMessage(null);
  ['login', 'register', 'otp'].forEach(m => {
    document.getElementById(`auth-form-${m}`)?.classList.add('hidden');
    const btn = document.getElementById(`btn-auth-${m === 'register' ? 'reg' : m}`);
    if (btn) { btn.classList.remove('bg-teal-500', 'text-slate-950', 'shadow-md'); btn.classList.add('text-slate-400'); }
  });
  document.getElementById(`auth-form-${mode}`)?.classList.remove('hidden');
  const btn = document.getElementById(`btn-auth-${mode === 'register' ? 'reg' : mode}`);
  if (btn) { btn.classList.add('bg-teal-500', 'text-slate-950', 'shadow-md'); btn.classList.remove('text-slate-400'); }
}

function isSupabaseNetworkError(err) {
  if (!err) return false;
  const msg = (err.message || String(err)).toLowerCase();
  const url = window.SUPABASE_URL || "";
  return msg.includes('failed to fetch') || msg.includes('network') || msg.includes('fetcherror') || msg.includes('unreachable') || url.includes('curaassist-carehub.supabase.co');
}

// Added missing auth handler: real Supabase email/password authentication.
async function submitAuth(message, overrideName, mode = 'login') {
  const client = getSupabaseClient();
  if (!client || !client.auth) {
    showAuthInlineMessage('Authentication service is unavailable. Please refresh and try again.', 'error');
    return false;
  }

  const identity = (document.getElementById('auth-login-identity')?.value || '').trim();
  const loginPassword = (document.getElementById('auth-login-password')?.value || '').trim();
  const email = (document.getElementById('auth-reg-email')?.value || '').trim();
  const registerPassword = (document.getElementById('auth-reg-password')?.value || '').trim();
  const name = (document.getElementById('auth-reg-name')?.value || '').trim();
  const phone = (document.getElementById('auth-reg-phone')?.value || '').trim();
  const blood = (document.getElementById('auth-reg-blood')?.value || 'O+').trim();
  const city = (document.getElementById('auth-reg-city')?.value || 'Hyderabad').trim();
  const age = (document.getElementById('auth-reg-age')?.value || '30').trim();

  const loginEmail = identity || email;
  const password = mode === 'register' ? registerPassword : loginPassword;

  if (!loginEmail || !password) {
    showAuthInlineMessage('Please enter your email and password.', 'error');
    return false;
  }
  if (!loginEmail.includes('@')) {
    showAuthInlineMessage('Please enter a valid email address.', 'error');
    return false;
  }

  const button = document.getElementById('btn-submit-login');
  const originalButtonHtml = button?.innerHTML;
  if (button) { button.disabled = true; button.innerHTML = '⏳ Signing in…'; }
  showAuthInlineMessage('⏳ Authenticating with CuraAssist…', 'loading');

  try {
    let data;
    let error;

    if (mode === 'register') {
      ({ data, error } = await client.auth.signUp({
        email: loginEmail,
        password,
        options: {
          data: { name: name || loginEmail.split('@')[0], phone, blood, city, age },
          emailRedirectTo: window.location.href.split('#')[0]
        }
      }));
    } else {
      ({ data, error } = await client.auth.signInWithPassword({ email: loginEmail, password }));
    }

    if (error) {
      console.warn('[CuraAssist] Supabase auth error:', error);
      showAuthInlineMessage(error.message || 'Authentication failed. Please verify your credentials.', 'error');
      return false;
    }

    const session = data?.session;
    if (!session?.access_token) {
      showAuthInlineMessage(mode === 'register' ? 'Registration created. Check your email to confirm your account, then sign in.' : 'Authentication succeeded, but no active session was returned.', mode === 'register' ? 'success' : 'error');
      return false;
    }

    window.authToken = session.access_token;
    const meta = session.user?.user_metadata || {};
    const userName = meta.name || meta.user_name || overrideName || loginEmail.split('@')[0];
    const userData = {
      isLoggedIn: true,
      userName,
      email: session.user?.email || loginEmail,
      phone: meta.phone || phone || '',
      blood: meta.blood || blood || 'O+',
      city: meta.city || city || '',
      age: meta.age || age || '30',
      avatar: meta.avatar_url || null,
      token: session.access_token
    };

    try { localStorage.setItem('cura_active_user_v1', JSON.stringify(userData)); } catch (e) {}
    if (typeof INITIAL_DATA !== 'undefined') {
      INITIAL_DATA.userAuth.isLoggedIn = true;
      INITIAL_DATA.userAuth.user.name = userData.userName;
      INITIAL_DATA.userAuth.user.email = userData.email;
      INITIAL_DATA.userAuth.user.phone = userData.phone;
      INITIAL_DATA.userAuth.user.token = session.access_token;
      if (INITIAL_DATA.familyMembers?.[0]) {
        INITIAL_DATA.familyMembers[0].name = userData.userName;
        INITIAL_DATA.familyMembers[0].email = userData.email;
        INITIAL_DATA.familyMembers[0].phone = userData.phone;
        INITIAL_DATA.familyMembers[0].bloodGroup = userData.blood;
        INITIAL_DATA.familyMembers[0].age = userData.age;
        if (userData.avatar) INITIAL_DATA.familyMembers[0].avatar = userData.avatar;
      }
    }

    updateAuthUIState(userData);
    const overlay = document.getElementById('auth-guard-overlay');
    if (overlay) overlay.classList.add('hidden');
    showAuthInlineMessage(message || `Welcome to CuraAssist Healthcare, ${userData.userName}!`, 'success');
    await fetchUserDataFromBackend();
    setTimeout(() => showAuthInlineMessage(null), 1800);
    return true;
  } catch (err) {
    console.warn('[CuraAssist] Auth request failed:', err);
    showAuthInlineMessage(isSupabaseNetworkError(err) ? 'Unable to reach the authentication service. Please check your connection and try again.' : (err.message || 'Authentication failed. Please try again.'), 'error');
    return false;
  } finally {
    if (button) { button.disabled = false; if (originalButtonHtml) button.innerHTML = originalButtonHtml; }
  }
}

// GitHub & Social OAuth Authentication Engine
async function loginWithOAuth(provider = 'github') {
  const client = getSupabaseClient();
  if (client && client.auth && !isSupabaseNetworkError({ message: window.SUPABASE_URL })) {
    try {
      const redirectTo = new URL(window.location.href);
      redirectTo.search = '';
      redirectTo.hash = '';
      redirectTo.pathname = redirectTo.pathname.endsWith('/') ? redirectTo.pathname : `${redirectTo.pathname}/`;
      await client.auth.signInWithOAuth({ provider, options: { redirectTo: redirectTo.toString() } });
    } catch (err) {
      console.warn(`[CuraAssist] ${provider} OAuth fetch note:`, err);
      showAuthInlineMessage('Social sign-in is temporarily unavailable. Please try again.', 'error');
    }
  } else {
    showAuthInlineMessage('Social sign-in is temporarily unavailable. Please try again.', 'error');
  }
}

function loginWithGitHub() { return loginWithOAuth('github'); }

let currentPendingAvatarUrl = null;

function handleProfilePhotoUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    currentPendingAvatarUrl = e.target.result;
    const preview = document.getElementById('edit-prof-avatar-preview');
    if (preview) preview.src = currentPendingAvatarUrl;
  };
  reader.readAsDataURL(file);
}

function selectPresetAvatar(url) {
  currentPendingAvatarUrl = url;
  const preview = document.getElementById('edit-prof-avatar-preview');
  if (preview) preview.src = url;
}

function updateAuthUIState(userData) {
  const isGuest = userData === "Login / Register" || (typeof userData === 'object' && userData !== null && userData.isLoggedIn === false);
  const user = (typeof userData === 'object' && userData !== null) ? userData : { userName: userData };
  const bottomNav = document.getElementById('mobile-bottom-nav') || document.getElementById('bottom-mobile-nav');
  const floatingBtn = document.getElementById('floating-ai-chat-btn');
  const overlay = document.getElementById('auth-guard-overlay');
  if (isGuest) {
    if (bottomNav) bottomNav.classList.add('hidden');
    if (floatingBtn) floatingBtn.classList.add('hidden');
    if (overlay) overlay.classList.remove('hidden');
  } else {
    if (bottomNav) bottomNav.classList.remove('hidden');
    if (floatingBtn) floatingBtn.classList.remove('hidden');
    if (overlay) overlay.classList.add('hidden');
  }

  let rawName = isGuest ? "Guest User" : (user.userName || user.name || "User");
  let userName = rawName.includes('@') ? rawName.split('@')[0] : rawName;
  userName = userName.trim();
  if (userName) userName = userName.charAt(0).toUpperCase() + userName.slice(1);

  const userEmail = isGuest ? "" : (user.email || "");
  const userPhone = isGuest ? "" : (user.phone || "");
  const userBlood = isGuest ? "O+" : (user.blood || user.bloodGroup || "O+");
  const userCity = isGuest ? "" : (user.city || user.location || "");
  const userAge = isGuest ? "30" : String(user.age || "30");
  const userAvatar = isGuest ? "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250" : (user.avatar || (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.familyMembers?.[0]?.avatar) || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250");
  const authText = document.getElementById('auth-btn-text'); if (authText) authText.innerText = isGuest ? "Login / Register" : `Account (${userName})`;
  const sidebarName = document.getElementById('sidebar-user-name'); if (sidebarName) sidebarName.innerText = userName;
  const sidebarAge = document.getElementById('sidebar-user-age'); if (sidebarAge) sidebarAge.innerText = isGuest ? "-- Yrs" : `${userAge} Yrs`;
  const sidebarBlood = document.getElementById('sidebar-user-blood'); if (sidebarBlood) sidebarBlood.innerText = userBlood;
  const activeFamilyName = document.getElementById('active-family-name'); if (activeFamilyName) activeFamilyName.innerText = userName;
  const welcomeName = document.getElementById('home-welcome-name'); if (welcomeName) welcomeName.innerText = isGuest ? "Guest" : userName;
  const profileHeaderName = document.getElementById('prof-name'); if (profileHeaderName) profileHeaderName.innerText = userName;
  const mainAvatar = document.getElementById('profile-main-avatar'); if (mainAvatar) mainAvatar.src = userAvatar;
  const sidebarAvatar = document.getElementById('sidebar-avatar'); if (sidebarAvatar) sidebarAvatar.src = userAvatar;
  const activeFamilyAvatar = document.getElementById('active-family-avatar'); if (activeFamilyAvatar) activeFamilyAvatar.src = userAvatar;
  const drawerAvatar = document.getElementById('drawer-user-avatar'); if (drawerAvatar) drawerAvatar.src = userAvatar;
  const profMainName = document.getElementById('profile-main-name'); if (profMainName) profMainName.innerText = userName;
  const drawerName = document.getElementById('drawer-user-name'); if (drawerName) drawerName.innerText = userName;
  const profMainPhone = document.getElementById('profile-main-phone'); if (profMainPhone) profMainPhone.innerText = userPhone;
  const profMainEmail = document.getElementById('profile-main-email'); if (profMainEmail) profMainEmail.innerText = userEmail;
  const profMainLoc = document.getElementById('profile-main-location'); if (profMainLoc) profMainLoc.innerText = userCity;
  const profMainBlood = document.getElementById('profile-main-blood'); if (profMainBlood) profMainBlood.innerText = userBlood;
  const profMainAge = document.getElementById('profile-main-age'); if (profMainAge) profMainAge.innerText = userAge;
  if (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.familyMembers?.[0] && !isGuest) {
    INITIAL_DATA.familyMembers[0].name = userName;
    INITIAL_DATA.familyMembers[0].phone = userPhone;
    INITIAL_DATA.familyMembers[0].email = userEmail;
    INITIAL_DATA.familyMembers[0].bloodGroup = userBlood;
    INITIAL_DATA.familyMembers[0].age = userAge;
  }
  if (typeof initFamilyDropdown === 'function') initFamilyDropdown();
}

async function checkSavedSession() {
  const overlay = document.getElementById('auth-guard-overlay');
  const client = getSupabaseClient();
  if (client && client.auth) {
    try {
      const { data: { session } } = await client.auth.getSession();
      if (session?.access_token) {
        window.authToken = session.access_token;
        const meta = session.user?.user_metadata || {};
        const userEmail = session.user?.email || 'User';
        const userName = meta.name || meta.user_name || userEmail.split('@')[0];
        const sessionPayload = {
          isLoggedIn: true,
          userName,
          email: userEmail,
          phone: meta.phone || '',
          blood: meta.blood || 'O+',
          city: meta.city || '',
          age: meta.age || '30',
          avatar: meta.avatar_url || null,
          token: session.access_token
        };
        try { localStorage.setItem('cura_active_user_v1', JSON.stringify(sessionPayload)); } catch (e) {}
        updateAuthUIState(sessionPayload);
        if (overlay) overlay.classList.add('hidden');
        await fetchUserDataFromBackend();
        return true;
      }
    } catch (e) {
      console.warn('[CuraAssist] Session check note:', e);
    }
  }

  try {
    const backupSession = localStorage.getItem('cura_active_user_v1');
    if (backupSession) {
      const parsed = JSON.parse(backupSession);
      if (parsed?.isLoggedIn) {
        window.authToken = parsed.token || null;
        updateAuthUIState(parsed);
        if (overlay) overlay.classList.add('hidden');
        await fetchUserDataFromBackend();
        return true;
      }
    }
  } catch (e) {}

  switchAuthTab('login');
  updateAuthUIState({ isLoggedIn: false, userName: 'Guest User' });
  if (overlay) overlay.classList.remove('hidden');
  return false;
}

function clearAuthInputs() {
  ['auth-reg-name','auth-reg-email','auth-reg-phone','auth-reg-password','auth-login-identity','auth-login-password','auth-otp-input'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
}

async function logoutUser() {
  const client = getSupabaseClient();
  if (client?.auth) { try { await client.auth.signOut(); } catch (e) {} }
  window.authToken = null;
  currentPendingAvatarUrl = null;
  state.records = [];
  state.schedule = [];
  state.cart = [];
  try {
    localStorage.removeItem('cura_active_user_v1');
    localStorage.removeItem('cura_cart_v1');
    localStorage.removeItem('cura_scanned_uploads');
    sessionStorage.clear();
  } catch (e) {}
  clearAuthInputs();
  if (typeof INITIAL_DATA !== 'undefined') {
    INITIAL_DATA.userAuth.isLoggedIn = false;
    INITIAL_DATA.userAuth.user = { name: 'Guest User', email: '', phone: '', token: '' };
    INITIAL_DATA.healthRecords = [];
    INITIAL_DATA.medicineSchedule = {};
    if (INITIAL_DATA.familyMembers?.[0]) {
      INITIAL_DATA.familyMembers[0].name = 'Guest User';
      INITIAL_DATA.familyMembers[0].email = '';
      INITIAL_DATA.familyMembers[0].phone = '';
    }
  }
  updateAuthUIState({ isLoggedIn: false, userName: 'Guest User' });
  if (typeof renderRecords === 'function') renderRecords();
  if (typeof renderSchedule === 'function') renderSchedule();
  if (typeof renderCart === 'function') renderCart();
  switchAuthTab('login');
  if (overlay = document.getElementById('auth-guard-overlay')) overlay.classList.remove('hidden');
}

// =========================================================
// Existing application modules continue below this line.
// =========================================================

