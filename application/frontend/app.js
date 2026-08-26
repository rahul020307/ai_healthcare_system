// CuraAssist CareHub - Complete Application Engine & Logic (11 Prototype Modules)
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://curaassist-carehub-backend-2.fastapicloud.dev';

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

// REST OF FILE UNCHANGED
