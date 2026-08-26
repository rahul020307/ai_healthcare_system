// CuraAssist CareHub - Complete Application Engine & Logic (11 Prototype Modules)
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : 'https://curaassist-carehub-backend-2.fastapicloud.dev';

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

async function getSupabaseSession() {
  if (!window.curaSupabase) return null;
  const { data, error } = await window.curaSupabase.auth.getSession();
  if (error) {
    console.warn('[CuraAssist] Unable to read Supabase session:', error.message);
    return null;
  }
  return data.session;
}

async function getAuthHeaders() {
  const session = await getSupabaseSession();
  if (!session?.access_token) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

function clearClientUserState() {
  state.records = [];
  state.schedule = [];
  if (typeof INITIAL_DATA !== 'undefined') {
    INITIAL_DATA.userAuth.isLoggedIn = false;
    INITIAL_DATA.userAuth.user = { name: 'Guest User', email: '', phone: '', token: '' };
  }
}

function saveStateToStorage() {
  // Deprecated: user data is no longer persisted in browser localStorage.
}

function loadStateFromStorage() {
  // Deprecated: user data is loaded from the authenticated backend/Supabase session.
}

async function loadAuthenticatedUser() {
  if (!window.curaSupabase) return false;
  const session = await getSupabaseSession();
  if (!session) {
    clearClientUserState();
    return false;
  }

  try {
    const response = await fetch(`${API_BASE}/profile/user`, {
      headers: await getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`profile request failed (${response.status})`);
    const payload = await response.json();
    const user = payload?.user;
    if (!user) throw new Error('profile response missing user');

    const userData = {
      isLoggedIn: true,
      userName: user.name,
      email: user.email,
      phone: user.phone,
      blood: user.bloodGroup,
      city: user.location,
      age: user.age,
      userId: user.id,
      token: session.access_token,
    };
    updateAuthUIState(userData);
    return true;
  } catch (err) {
    console.warn('[CuraAssist] Authenticated profile load failed:', err.message || err);
    clearClientUserState();
    await window.curaSupabase.auth.signOut();
    return false;
  }
}

async function initializeAuthenticatedState() {
  const authenticated = await loadAuthenticatedUser();
  if (authenticated) {
    await syncDatabaseRecordsWithBackend();
  }
  return authenticated;
}

function ensureLucideIcons() {
  if (typeof lucide !== 'undefined' && lucide.createIcons) {
    try { lucide.createIcons(); } catch (e) {}
  } else {
    setTimeout(ensureLucideIcons, 150);
  }
}
window.addEventListener('load', ensureLucideIcons);

document.addEventListener('DOMContentLoaded', () => {
  const safeRun = (fn, name) => {
    try { fn(); } catch (err) { console.warn(`[CuraAssist] Init warning in ${name}:`, err); }
  };

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
  safeRun(() => initializeAuthenticatedState(), 'initializeAuthenticatedState');

  if (window.curaSupabase) {
    window.curaSupabase.auth.onAuthStateChange(async () => {
      await initializeAuthenticatedState();
    });
  }
});

async function syncDatabaseRecordsWithBackend() {
  try {
    const res = await fetch(`${API_BASE}/profile/health-records`, {
      headers: await getAuthHeaders(),
    });
    if (!res.ok) return;
    const data = await res.json();
    state.records = Array.isArray(data?.records) ? data.records : [];
    renderRecords();
  } catch (e) {
    console.warn('SQL health-records sync note:', e);
  }
}

// TAB SWITCHING ENGINE
function switchTab(tabName) {
  state.currentTab = tabName;
  
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-btn').forEach(el => {
    el.classList.remove('text-teal-400', 'font-black', 'scale-105');
    el.classList.add('text-slate-400');
  });

  const activeNav = document.getElementById(`nav-${tabName}`);
  if (activeNav) activeNav.classList.add('active');

  const activeMobileNav = document.getElementById(`mobile-nav-${tabName}`);
  if (activeMobileNav) {
    activeMobileNav.classList.remove('text-slate-400');
    activeMobileNav.classList.add('text-teal-400', 'font-black', 'scale-105');
  }

  const appHeader = document.getElementById('app-header');
  if (appHeader) {
    if (tabName === 'maps') appHeader.classList.add('hidden');
    else appHeader.classList.remove('hidden');
  }

  ['home', 'store', 'maps', 'profile'].forEach(tab => {
    const sec = document.getElementById(`view-${tab}`);
    if (sec) sec.classList.add('hidden');
  });

  const targetSec = document.getElementById(`view-${tabName}`);
  if (targetSec) targetSec.classList.remove('hidden');

  if (tabName === 'maps') {
    setTimeout(() => {
      initMap();
      if (state.map) state.map.invalidateSize();
    }, 200);
  }

  const mainContent = document.querySelector('main');
  if (mainContent) mainContent.scrollTop = 0;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleNearbyPlacesLayout() {
  const drawer = document.getElementById('nearby-places-drawer');
  if (!drawer) return;

  if (drawer.classList.contains('max-h-56')) {
    drawer.classList.remove('max-h-56');
    drawer.classList.add('max-h-[75vh]');
  } else if (drawer.classList.contains('max-h-[75vh]')) {
    drawer.classList.remove('max-h-[75vh]');
    drawer.classList.add('max-h-12', 'overflow-hidden');
  } else {
    drawer.classList.remove('max-h-12', 'overflow-hidden');
    drawer.classList.add('max-h-56');
  }

  if (state.map) setTimeout(() => state.map.invalidateSize(), 300);
}

function scrollToSection(secId) {
  switchTab('home');
  setTimeout(() => {
    document.getElementById(secId)?.scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

// MODULE 1: USER AUTHENTICATION ENGINE
function openAuthModal() {
  switchAuthTab('login');
  const overlay = document.getElementById('auth-guard-overlay');
  if (overlay) overlay.classList.remove('hidden');
}

async function closeAuthModal() {
  const session = await getSupabaseSession();
  if (session) {
    const overlay = document.getElementById('auth-guard-overlay');
    if (overlay) overlay.classList.add('hidden');
  } else {
    alert('⚠️ Registration or Login is required to access the application.');
  }
}

function togglePasswordVisibility(fieldId) {
  const input = document.getElementById(fieldId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
}

function switchAuthTab(mode) {
  ['login', 'register', 'otp'].forEach(m => {
    document.getElementById(`auth-form-${m}`)?.classList.add('hidden');
    const btn = document.getElementById(`btn-auth-${m === 'register' ? 'reg' : m}`);
    if (btn) {
      btn.classList.remove('bg-teal-500', 'text-slate-950', 'shadow-md');
      btn.classList.add('text-slate-400');
    }
  });

  document.getElementById(`auth-form-${mode}`)?.classList.remove('hidden');
  const btn = document.getElementById(`btn-auth-${mode === 'register' ? 'reg' : mode}`);
  if (btn) {
    btn.classList.add('bg-teal-500', 'text-slate-950', 'shadow-md');
    btn.classList.remove('text-slate-400');
  }
}

async function submitAuth(message, overrideName, mode = 'login') {
  if (!window.curaSupabase) {
    alert('⚠️ Secure authentication is not configured. Please try again after configuration.');
    return;
  }

  const email = (mode === 'register'
    ? document.getElementById('auth-reg-email')?.value
    : document.getElementById('auth-login-identity')?.value || document.getElementById('auth-reg-email')?.value || '')?.trim();
  const password = (mode === 'register'
    ? document.getElementById('auth-reg-password')?.value
    : document.getElementById('auth-login-password')?.value || '')?.trim();

  if (!email || !password) {
    alert('⚠️ Email and password are required.');
    return;
  }

  let authResult;
  if (mode === 'register') {
    const name = (document.getElementById('auth-reg-name')?.value || email.split('@')[0]).trim();
    const phone = (document.getElementById('auth-reg-phone')?.value || '').trim();
    const city = (document.getElementById('auth-reg-city')?.value || 'Hyderabad').trim();
    const blood = (document.getElementById('auth-reg-blood')?.value || 'O+').trim();
    const age = Number((document.getElementById('auth-reg-age')?.value || '30').trim());

    authResult = await window.curaSupabase.auth.signUp({
      email,
      password,
      options: {
        data: { name, phone, city, blood_group: blood, age },
      },
    });
  } else {
    authResult = await window.curaSupabase.auth.signInWithPassword({ email, password });
  }

  if (authResult.error) {
    alert(`⚠️ ${authResult.error.message}`);
    return;
  }

  if (mode === 'register' && !authResult.data.session) {
    alert('✅ Registration created. Check your email to confirm your account, then sign in.');
    return;
  }

  const authenticated = await loadAuthenticatedUser();
  if (!authenticated) {
    alert('⚠️ Authentication succeeded, but the CuraAssist profile could not be loaded.');
    return;
  }

  const overlay = document.getElementById('auth-guard-overlay');
  if (overlay) overlay.classList.add('hidden');
  alert(message || `Welcome to CuraAssist Healthcare!`);
}

async function signOutCuraAssist() {
  if (!window.curaSupabase) return;
  const { error } = await window.curaSupabase.auth.signOut();
  if (error) {
    alert(`⚠️ ${error.message}`);
    return;
  }
  clearClientUserState();
  updateAuthUIState({ userName: 'Guest User', email: '', phone: '', city: 'Hyderabad, Telangana', age: '', blood: '' });
  openAuthModal();
}

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
  const user = (typeof userData === 'object' && userData !== null) ? userData : { userName: userData };
  let rawName = user.userName || user.name || "Guest User";
  if (rawName.includes('@')) rawName = rawName.split('@')[0];
  let cleanName = rawName.replace(/([a-zA-Z]+)(\d+)$/, '$1');
  cleanName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);

  const userName = cleanName;
  const userEmail = user.email || '';
  const userPhone = user.phone || '';
  const userBlood = user.blood || user.bloodGroup || '';
  const userCity = user.city || user.location || 'Hyderabad, Telangana';
  const userAge = user.age || '';
  const userAvatar = user.avatar || (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.familyMembers?.[0]?.avatar) || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250';

  const authText = document.getElementById('auth-btn-text');
  if (authText) authText.innerText = userName === 'Guest User' ? 'Login / Register' : `Account (${userName})`;
  const sidebarName = document.getElementById('sidebar-user-name');
  if (sidebarName) sidebarName.innerText = userName;
  const sidebarAge = document.getElementById('sidebar-user-age');
  if (sidebarAge) sidebarAge.innerText = userAge ? `${userAge} Yrs` : '';
  const sidebarBlood = document.getElementById('sidebar-user-blood');
  if (sidebarBlood) sidebarBlood.innerText = userBlood;
  const activeFamilyName = document.getElementById('active-family-name');
  if (activeFamilyName) activeFamilyName.innerText = userName;
  const welcomeName = document.getElementById('home-welcome-name');
  if (welcomeName) welcomeName.innerText = userName;
  const profileHeaderName = document.getElementById('prof-name');
  if (profileHeaderName) profileHeaderName.innerText = userName;

  const mainAvatar = document.getElementById('profile-main-avatar');
  if (mainAvatar) mainAvatar.src = userAvatar;
  const sidebarAvatar = document.getElementById('sidebar-avatar');
  if (sidebarAvatar) sidebarAvatar.src = userAvatar;
  const activeFamilyAvatar = document.getElementById('active-family-avatar');
  if (activeFamilyAvatar) activeFamilyAvatar.src = userAvatar;

  const profMainName = document.getElementById('profile-main-name');
  if (profMainName) profMainName.innerText = userName;
  const profMainPhone = document.getElementById('profile-main-phone');
  if (profMainPhone) profMainPhone.innerText = userPhone;
  const profMainEmail = document.getElementById('profile-main-email');
  if (profMainEmail) profMainEmail.innerText = userEmail;
  const profMainLocation = document.getElementById('profile-main-location');
  if (profMainLocation) profMainLocation.innerText = userCity;
  const profMainAge = document.getElementById('profile-main-age');
  if (profMainAge) profMainAge.innerText = userAge;
  const profMainBlood = document.getElementById('profile-main-blood');
  if (profMainBlood) profMainBlood.innerText = userBlood;
}

// REST OF FILE UNCHANGED
