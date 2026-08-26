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

function saveStateToStorage() {
  try {
    localStorage.setItem('cura_schedule_v1', JSON.stringify(state.schedule));
    localStorage.setItem('cura_records_v1', JSON.stringify(state.records));
    localStorage.setItem('cura_cart_v1', JSON.stringify(state.cart));
  } catch (e) {
    console.warn("[CuraAssist] Storage save error:", e);
  }
}

function loadStateFromStorage() {
  try {
    const savedSch = localStorage.getItem('cura_schedule_v1');
    const savedRec = localStorage.getItem('cura_records_v1');
    const savedCart = localStorage.getItem('cura_cart_v1');

    if (savedSch) {
      state.schedule = JSON.parse(savedSch);
    } else if (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.medicineSchedule) {
      state.schedule = JSON.parse(JSON.stringify(INITIAL_DATA.medicineSchedule));
    }

    if (savedRec) {
      state.records = JSON.parse(savedRec);
    } else if (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.healthRecords) {
      state.records = JSON.parse(JSON.stringify(INITIAL_DATA.healthRecords));
    }

    if (savedCart) {
      state.cart = JSON.parse(savedCart);
    }
  } catch (e) {
    console.warn("[CuraAssist] Storage load error:", e);
  }
}

function ensureLucideIcons() {
  if (typeof lucide !== 'undefined' && lucide.createIcons) {
    try { lucide.createIcons(); } catch (e) {}
  } else {
    setTimeout(ensureLucideIcons, 150);
  }
}
window.addEventListener('load', ensureLucideIcons);

// Initialize app when DOM is ready safely
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
  safeRun(() => syncDatabaseRecordsWithBackend(), 'syncDatabaseRecordsWithBackend');
});

async function syncDatabaseRecordsWithBackend() {
  try {
    const res = await fetch(`${API_BASE}/profile/health-records`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.records && data.records.length > 0) {
        const existingIds = new Set(state.records.map(r => r.id));
        let added = false;
        data.records.forEach(r => {
          if (!existingIds.has(r.id)) {
            state.records.unshift(r);
            existingIds.add(r.id);
            added = true;
          }
        });
        if (added) {
          renderRecords();
        }
      }
    }
  } catch (e) {
    console.warn("SQL health-records sync note:", e);
  }
}

// TAB SWITCHING ENGINE
function switchTab(tabName) {
  state.currentTab = tabName;
  
  // Update sidebar & mobile bottom nav active highlights
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

  // Toggle Header visibility (Remove top header in Maps tab for full screen map view)
  const appHeader = document.getElementById('app-header');
  if (appHeader) {
    if (tabName === 'maps') {
      appHeader.classList.add('hidden');
    } else {
      appHeader.classList.remove('hidden');
    }
  }

  // Hide all sections
  ['home', 'store', 'maps', 'profile'].forEach(tab => {
    const sec = document.getElementById(`view-${tab}`);
    if (sec) sec.classList.add('hidden');
  });

  // Show active view section
  const targetSec = document.getElementById(`view-${tabName}`);
  if (targetSec) targetSec.classList.remove('hidden');

  // If switching to Maps tab, initialize map if needed
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
    // State 2: Expanded view (75% screen height) for full list scrolling
    drawer.classList.remove('max-h-56');
    drawer.classList.add('max-h-[75vh]');
  } else if (drawer.classList.contains('max-h-[75vh]')) {
    // State 3: Compact Bar view (h-12 overflow-hidden) for full map visibility
    drawer.classList.remove('max-h-[75vh]');
    drawer.classList.add('max-h-12', 'overflow-hidden');
  } else {
    // State 1: Reset back to standard height
    drawer.classList.remove('max-h-12', 'overflow-hidden');
    drawer.classList.add('max-h-56');
  }

  if (state.map) {
    setTimeout(() => state.map.invalidateSize(), 300);
  }
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

function closeAuthModal() {
  const saved = localStorage.getItem('cura_auth_session');
  if (saved) {
    const overlay = document.getElementById('auth-guard-overlay');
    if (overlay) overlay.classList.add('hidden');
  } else {
    alert("⚠️ Registration or Login is required to access the application.");
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
  let userName = overrideName;
  let identity = (document.getElementById('auth-login-identity')?.value || '').trim();
  let email = (document.getElementById('auth-reg-email')?.value || '').trim();
  let phone = (document.getElementById('auth-reg-phone')?.value || '').trim();
  let blood = (document.getElementById('auth-reg-blood')?.value || 'O+').trim();
  let city = (document.getElementById('auth-reg-city')?.value || 'Hyderabad').trim();
  let age = (document.getElementById('auth-reg-age')?.value || '30').trim();
  let password = (document.getElementById('auth-login-password')?.value || document.getElementById('auth-reg-password')?.value || '').trim();
  let name = (document.getElementById('auth-reg-name')?.value || '').trim();

  if (!userName) {
    if (mode === 'register' && name) {
      userName = name;
    } else if (identity) {
      userName = identity.split('@')[0];
    } else if (email) {
      userName = email.split('@')[0];
    } else {
      userName = "User";
    }
  }

  // Capitalize first letter of userName for clean display
  userName = userName.charAt(0).toUpperCase() + userName.slice(1);
  const userEmail = email || `${userName.toLowerCase().replace(/\s+/g, '')}@curahealth.in`;
  const userPhone = phone || "+91 98765 43210";

  const userSessionData = {
    isLoggedIn: true,
    userName: userName,
    email: userEmail,
    phone: userPhone,
    blood: blood,
    city: city,
    age: age,
    token: `jwt-token-${Date.now()}`
  };

  // Attempt backend API call if server is active
  try {
    const endpoint = mode === 'register' ? `${API_BASE}/profile/register` : `${API_BASE}/profile/login`;
    await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identity: identity || userName,
        email: userEmail,
        name: userName,
        phone: userPhone,
        blood_group: blood,
        city: city,
        age: age,
        password: password || "demo123"
      })
    });
  } catch (err) {
    console.warn("Backend auth notification note:", err);
  }

  // Update App State & Dataset
  if (typeof INITIAL_DATA !== 'undefined') {
    INITIAL_DATA.userAuth.isLoggedIn = true;
    INITIAL_DATA.userAuth.user.name = userName;
    if (INITIAL_DATA.familyMembers && INITIAL_DATA.familyMembers[0]) {
      INITIAL_DATA.familyMembers[0].name = userName;
      INITIAL_DATA.familyMembers[0].phone = userPhone;
      INITIAL_DATA.familyMembers[0].email = userEmail;
      INITIAL_DATA.familyMembers[0].bloodGroup = blood;
      INITIAL_DATA.familyMembers[0].age = age;
    }
  }

  // Save Session in localStorage for persistence across refreshes
  try {
    localStorage.setItem('cura_auth_session', JSON.stringify(userSessionData));
  } catch (e) {}

  // Update UI Elements across the application
  updateAuthUIState(userSessionData);
  
  // Unlock application overlay
  const overlay = document.getElementById('auth-guard-overlay');
  if (overlay) overlay.classList.add('hidden');

  alert(message || `Welcome to CuraAssist Healthcare, ${userName}! Your profile is connected.`);
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
  
  if (rawName.includes('@')) {
    rawName = rawName.split('@')[0];
  }
  let cleanName = rawName.replace(/([a-zA-Z]+)(\d+)$/, '$1');
  cleanName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);

  const userName = cleanName;
  const userEmail = user.email || `${userName.toLowerCase().replace(/\s+/g, '')}@curahealth.in`;
  const userPhone = user.phone || "+91 98765 43210";
  const userBlood = user.blood || user.bloodGroup || "O+";
  const userCity = user.city || "Hyderabad, Telangana";
  const userAge = user.age || "30";
  const userAvatar = user.avatar || (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA.familyMembers?.[0]?.avatar) || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250";

  const authText = document.getElementById('auth-btn-text');
  if (authText) authText.innerText = `Account (${userName})`;

  const sidebarName = document.getElementById('sidebar-user-name');
  if (sidebarName) sidebarName.innerText = userName;

  const sidebarAge = document.getElementById('sidebar-user-age');
  if (sidebarAge) sidebarAge.innerText = `${userAge} Yrs`;

  const activeFamilyName = document.getElementById('active-family-name');
  if (activeFamilyName) activeFamilyName.innerText = userName;

  const welcomeName = document.getElementById('home-welcome-name');
  if (welcomeName) welcomeName.innerText = userName;

  const profileHeaderName = document.getElementById('prof-name');
  if (profileHeaderName) profileHeaderName.innerText = userName;

  // Sync Avatars Across App
  const mainAvatar = document.getElementById('profile-main-avatar');
  if (mainAvatar) mainAvatar.src = userAvatar;

  const sidebarAvatar = document.getElementById('sidebar-avatar');
  if (sidebarAvatar) sidebarAvatar.src = userAvatar;

  const activeFamilyAvatar = document.getElementById('active-family-avatar');
  if (activeFamilyAvatar) activeFamilyAvatar.src = userAvatar;

  // Profile Card Dynamic Sync
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
