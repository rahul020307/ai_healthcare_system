// CuraAssist CareHub - Complete Application Engine & Logic (11 Prototype Modules)
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : '';

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
    const key = window.SUPABASE_ANON_KEY || "sb_publishable_k6UNxmH9fjYcrH6vledSZw_Aqm3ZgpH";
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
  if (window.authToken) return window.authToken;
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
  return null;
}

function getAuthHeaders() {
  const token = getAuthToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function fetchUserDataFromBackend() {
  const headers = getAuthHeaders();
  if (!headers['Authorization']) return;

  try {
    // 1. Fetch User Profile
    const profRes = await fetch(`${API_BASE}/profile/user`, { headers });
    if (profRes.ok) {
      const profData = await profRes.json();
      if (profData.user) {
        updateAuthUIState({ isLoggedIn: true, ...profData.user });
      }
    }

    // 2. Fetch Health Records
    const recRes = await fetch(`${API_BASE}/profile/health-records`, { headers });
    if (recRes.ok) {
      const recData = await recRes.json();
      if (Array.isArray(recData.records)) {
        state.records = recData.records;
        if (typeof renderRecords === 'function') renderRecords();
      }
    }

    // 3. Fetch Medicine Schedules
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
  }
}

function saveStateToStorage() {
  try {
    // UI temporary preferences only (e.g. cart). Healthcare data is saved to Supabase/SQL database.
    localStorage.setItem('cura_cart_v1', JSON.stringify(state.cart));
  } catch (e) {
    console.warn("[CuraAssist] Storage save error:", e);
  }
}

function loadStateFromStorage() {
  try {
    const savedCart = localStorage.getItem('cura_cart_v1');
    if (savedCart) {
      state.cart = JSON.parse(savedCart);
    }
  } catch (e) {
    console.warn("[CuraAssist] Storage load error:", e);
  }
  // Load persistent user healthcare data directly from authenticated backend APIs
  fetchUserDataFromBackend();
}