// CuraAssist CareHub - Complete Application Engine & Logic (11 Prototype Modules)

let state = {
  currentTab: 'home',
  currentLang: 'en',
  activeFamilyId: 'mem-1',
  cart: [
    { id: "med-1", qty: 1 },
    { id: "med-4", qty: 1 }
  ],
  schedule: JSON.parse(JSON.stringify(INITIAL_DATA.medicineSchedule)),
  records: JSON.parse(JSON.stringify(INITIAL_DATA.healthRecords)),
  activeRecordFilter: 'All',
  activeMapFilter: 'All',
  appliedPromo: null,
  theme: 'dark',
  map: null,
  mapMarkers: [],
  activeRoutePolyline: null
};

// Initialize app when DOM is ready safely
document.addEventListener('DOMContentLoaded', () => {
  const safeRun = (fn, name) => {
    try { fn(); } catch (err) { console.warn(`[CuraAssist] Init warning in ${name}:`, err); }
  };

  safeRun(() => lucide.createIcons(), 'lucide');
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
});

// TAB SWITCHING ENGINE
function switchTab(tabName) {
  state.currentTab = tabName;
  
  // Update sidebar active highlights
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  const activeNav = document.getElementById(`nav-${tabName}`);
  if (activeNav) activeNav.classList.add('active');

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
    setTimeout(initMap, 200);
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToSection(secId) {
  switchTab('home');
  setTimeout(() => {
    document.getElementById(secId)?.scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

// MODULE 1: USER AUTHENTICATION ENGINE
function openAuthModal() {
  document.getElementById('modal-auth').classList.remove('hidden');
}
function closeAuthModal() {
  document.getElementById('modal-auth').classList.add('hidden');
}

function switchAuthTab(mode) {
  ['login', 'register', 'otp'].forEach(m => {
    document.getElementById(`auth-form-${m}`)?.classList.add('hidden');
    document.getElementById(`btn-auth-${m === 'register' ? 'reg' : m}`)?.classList.remove('bg-teal-500', 'text-slate-950');
    document.getElementById(`btn-auth-${m === 'register' ? 'reg' : m}`)?.classList.add('text-slate-400');
  });

  document.getElementById(`auth-form-${mode}`)?.classList.remove('hidden');
  const btn = document.getElementById(`btn-auth-${mode === 'register' ? 'reg' : mode}`);
  if (btn) {
    btn.classList.add('bg-teal-500', 'text-slate-950');
    btn.classList.remove('text-slate-400');
  }
}

function submitAuth(message) {
  closeAuthModal();
  document.getElementById('auth-btn-text').innerText = "Account Active (Alex)";
  alert(message);
}

// FAMILY MEMBER SWITCHER ENGINE
function initFamilyDropdown() {
  const container = document.getElementById('family-members-list');
  if (!container) return;

  container.innerHTML = INITIAL_DATA.familyMembers.map(mem => `
    <button onclick="selectFamilyMember('${mem.id}')" class="w-full text-left px-3 py-2 text-xs rounded-xl flex items-center justify-between hover:bg-slate-800 transition-colors ${mem.id === state.activeFamilyId ? 'bg-teal-500/10 text-teal-300 font-bold border border-teal-500/30' : 'text-slate-300'}">
      <div class="flex items-center gap-2.5">
        <img src="${mem.avatar}" class="w-6 h-6 rounded-full object-cover">
        <span>${mem.name}</span>
      </div>
      <span class="text-[10px] text-slate-400 font-medium">${mem.relation}</span>
    </button>
  `).join('');

  const btn = document.getElementById('family-selector-btn');
  const dropdown = document.getElementById('family-dropdown');
  if (btn && dropdown) {
    btn.onclick = (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('hidden');
    };
    document.addEventListener('click', () => dropdown.classList.add('hidden'));
  }
}

function selectFamilyMember(memberId) {
  state.activeFamilyId = memberId;
  renderActiveFamilyContext();
  document.getElementById('family-dropdown').classList.add('hidden');
}

function renderActiveFamilyContext() {
  const member = INITIAL_DATA.familyMembers.find(m => m.id === state.activeFamilyId) || INITIAL_DATA.familyMembers[0];

  document.getElementById('active-family-avatar').src = member.avatar;
  document.getElementById('active-family-name').innerText = member.name;

  document.getElementById('sidebar-avatar').src = member.avatar;
  document.getElementById('sidebar-user-name').innerText = member.name;
  document.getElementById('sidebar-user-age').innerText = `${member.age} Yrs`;
  document.getElementById('sidebar-user-blood').innerText = member.bloodGroup;

  document.getElementById('home-welcome-name').innerText = member.name.split(' ')[0];

  document.getElementById('profile-main-avatar').src = member.avatar;
  document.getElementById('profile-main-name').innerText = member.name;
  document.getElementById('profile-main-relation').innerText = member.relation;
  document.getElementById('profile-main-age').innerText = member.age;
  document.getElementById('profile-main-gender').innerText = member.gender;
  document.getElementById('profile-main-blood').innerText = member.bloodGroup;

  document.getElementById('sos-id-name').innerText = member.name;
  document.getElementById('sos-id-blood').innerText = member.bloodGroup;

  renderSchedule();
  renderRecords();
}

// MEDICINE SCHEDULE ENGINE
function renderSchedule() {
  const container = document.getElementById('schedule-container');
  if (!container) return;

  const memberSchedule = state.schedule[state.activeFamilyId] || [];

  if (memberSchedule.length === 0) {
    container.innerHTML = `<div class="p-6 text-center text-xs text-slate-400">No scheduled medicine reminders for this member. Click "+ Add Reminder" to create one.</div>`;
    return;
  }

  container.innerHTML = memberSchedule.map(item => `
    <div class="p-4 rounded-2xl glass-card flex flex-col sm:flex-row sm:items-center justify-between gap-3 border ${item.taken ? 'border-emerald-500/30 opacity-75' : 'border-slate-800'} transition-all">
      <div class="flex items-center gap-3">
        <button onclick="togglePillTaken('${item.id}')" class="w-6 h-6 rounded-lg border flex items-center justify-center transition-colors ${item.taken ? 'bg-emerald-500 border-emerald-400 text-slate-950 font-bold' : 'border-slate-600 text-transparent hover:border-teal-400'}">
          ✓
        </button>
        <div>
          <div class="flex items-center gap-2">
            <h4 class="text-sm font-bold text-white ${item.taken ? 'line-through text-slate-400' : ''}">${item.name}</h4>
            <span class="text-[10px] bg-slate-800 text-teal-300 font-semibold px-2 py-0.5 rounded-full">${item.time}</span>
          </div>
          <p class="text-xs text-slate-400">${item.dose} • <span class="text-amber-400 font-medium">${item.refillsLeft} refills left</span></p>
        </div>
      </div>

      <div class="flex items-center gap-2 self-end sm:self-center">
        <button onclick="snoozePill('${item.id}')" class="px-2.5 py-1 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs border border-slate-700 font-medium">
          ⏰ Snooze 30m
        </button>
        <button onclick="togglePillTaken('${item.id}')" class="px-3 py-1 rounded-xl text-xs font-bold transition-colors ${item.taken ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-teal-600 hover:bg-teal-500 text-white'}">
          ${item.taken ? 'Taken ✓' : 'Mark Taken'}
        </button>
      </div>
    </div>
  `).join('');
}

function togglePillTaken(id) {
  const memberSchedule = state.schedule[state.activeFamilyId] || [];
  const pill = memberSchedule.find(p => p.id === id);
  if (pill) {
    pill.taken = !pill.taken;
    if (pill.taken && window.confetti) {
      confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 } });
    }
    renderSchedule();
  }
}

function snoozePill(id) {
  alert("Reminder snoozed for 30 minutes. Notification set.");
}

function openAddReminderModal() {
  document.getElementById('modal-add-reminder').classList.remove('hidden');
}
function closeAddReminderModal() {
  document.getElementById('modal-add-reminder').classList.add('hidden');
}

function saveNewReminder() {
  const name = document.getElementById('rem-name').value;
  const dose = document.getElementById('rem-dose').value;
  const slot = document.getElementById('rem-slot').value;

  if (!name) return alert("Please enter medicine name");

  if (!state.schedule[state.activeFamilyId]) {
    state.schedule[state.activeFamilyId] = [];
  }

  state.schedule[state.activeFamilyId].push({
    id: `sch-${Date.now()}`,
    name,
    dose: dose || "1 Tablet",
    time: `${slot.toUpperCase()} Slot`,
    slot,
    taken: false,
    refillsLeft: 30,
    total: 30
  });

  closeAddReminderModal();
  renderSchedule();
}

// MODULE 8: PRESCRIPTION MANAGEMENT & OCR EXTRACTION
function openPrescriptionScanModal() {
  document.getElementById('modal-presc-scan').classList.remove('hidden');
}
function closePrescriptionScanModal() {
  document.getElementById('modal-presc-scan').classList.add('hidden');
}

function simulatePrescriptionOCR() {
  closePrescriptionScanModal();
  state.records.unshift({
    id: `rec-${Date.now()}`,
    memberId: state.activeFamilyId,
    title: "Dr. Robert Chen Prescription Slip",
    category: "Prescriptions",
    date: new Date().toISOString().split('T')[0],
    doctor: "Dr. Robert Chen, MD",
    facility: "Metro Heart Care",
    tags: ["OCR Extracted", "Prescription"],
    summary: "Extracted Medicines: Lipitor 20mg (1x daily), Metoprolol 25mg (1x evening)."
  });

  if (window.confetti) confetti({ particleCount: 70, spread: 50 });
  alert("Prescription Scanned & OCR Text Extracted Successfully! Saved to Health Records.");
  renderRecords();
}

function renderRecords() {
  const container = document.getElementById('records-container');
  if (!container) return;

  const filtered = state.records.filter(r => r.memberId === state.activeFamilyId);

  if (filtered.length === 0) {
    container.innerHTML = `<div class="col-span-2 p-6 text-center text-xs text-slate-400">No medical prescriptions or records found for this patient.</div>`;
    return;
  }

  container.innerHTML = filtered.map(rec => `
    <div class="p-4 rounded-2xl glass-card space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
      <div class="flex items-start justify-between">
        <div>
          <span class="text-[10px] font-extrabold text-cyan-400 uppercase tracking-wider bg-cyan-500/10 px-2 py-0.5 rounded">${rec.category}</span>
          <h4 class="text-sm font-bold text-white mt-1">${rec.title}</h4>
          <p class="text-xs text-slate-400">${rec.doctor} • ${rec.facility}</p>
        </div>
        <span class="text-xs text-slate-400 font-medium">${rec.date}</span>
      </div>
      <p class="text-xs text-slate-300 bg-slate-900/80 p-2.5 rounded-xl">${rec.summary}</p>
    </div>
  `).join('');
}

// MODULE 7: MEDICINE INFORMATION & INSIGHTS ENGINE
function showMedInfoDetails(medId) {
  const med = INITIAL_DATA.medicines.find(m => m.id === medId) || INITIAL_DATA.medicines[0];
  const container = document.getElementById('med-info-content');
  if (!container) return;

  container.innerHTML = `
    <div class="space-y-4">
      <div class="flex items-center gap-3">
        <img src="${med.image}" class="w-16 h-16 rounded-2xl object-cover">
        <div>
          <span class="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Barcode: ${med.barcode}</span>
          <h3 class="text-lg font-extrabold text-white">${med.name} (${med.salt})</h3>
          <p class="text-xs text-teal-300 font-semibold">$${med.price.toFixed(2)} • ${med.brandName}</p>
        </div>
      </div>

      <div class="space-y-2 text-xs text-slate-300">
        <div class="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <strong class="text-teal-400 block mb-1">💊 Dosage Information:</strong>
          <p>${med.dosage}</p>
        </div>

        <div class="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <strong class="text-cyan-400 block mb-1">📋 Usage Instructions:</strong>
          <p>${med.usageInstructions}</p>
        </div>

        <div class="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <strong class="text-amber-400 block mb-1">⚠️ Possible Side Effects:</strong>
          <p>${med.sideEffects.join(', ')}</p>
        </div>

        <div class="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30">
          <strong class="text-rose-400 block mb-1">🚫 Safety Warnings & Precautions:</strong>
          <p>${med.safetyWarnings}</p>
        </div>
      </div>
    </div>
  `;

  document.getElementById('modal-med-info').classList.remove('hidden');
}

function closeMedInfoModal() {
  document.getElementById('modal-med-info').classList.add('hidden');
}

// STORE & CART ENGINE
function renderStoreCategories() {
  const container = document.getElementById('store-categories-list');
  if (!container) return;

  const categories = [
    { name: "All", label: "All Medicines", icon: "💊" },
    { name: "Pain Relief", label: "Pain Relief", icon: "🦵" },
    { name: "Vitamins & Supplements", label: "Vitamins", icon: "🧴" },
    { name: "Ayurveda", label: "Ayurveda", icon: "🌿" },
    { name: "Personal Care", label: "Personal Care", icon: "🧼" },
    { name: "Baby Care", label: "Baby Care", icon: "👶" }
  ];

  container.innerHTML = categories.map(cat => `
    <button onclick="filterStoreCategory('${cat.name}')" class="flex flex-col items-center gap-1.5 group p-1">
      <div class="w-12 h-12 rounded-full bg-slate-900 border ${activeStoreCat === cat.name ? 'border-teal-500 bg-teal-500/10' : 'border-slate-800'} text-xl flex items-center justify-center group-hover:border-teal-500 transition-colors shadow">
        ${cat.icon}
      </div>
      <span class="text-[11px] font-bold ${activeStoreCat === cat.name ? 'text-teal-400' : 'text-slate-300'} whitespace-nowrap">${cat.label}</span>
    </button>
  `).join('');
}

let activeStoreCat = 'All';
function filterStoreCategory(cat) {
  activeStoreCat = cat;
  renderStoreCategories();
  renderStoreMedicines();
}

let activeStoreLocation = 'Hyderabad, Telangana';

function changeStoreLocation(locationName) {
  activeStoreLocation = locationName;
  const select = document.getElementById('store-location-select');
  if (select) select.value = locationName;
  renderStoreMedicines();
}

function getCurrentLocationForStore() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  const infoEl = document.getElementById('store-fulfillment-info');
  if (infoEl) infoEl.innerHTML = `<span class="text-teal-300 font-bold">📍 Detecting live GPS location...</span>`;

  navigator.geolocation.getCurrentPosition((pos) => {
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
    activeStoreLocation = `GPS Location (${lat.toFixed(3)}, ${lng.toFixed(3)})`;
    
    const select = document.getElementById('store-location-select');
    if (select) {
      const opt = document.createElement('option');
      opt.value = activeStoreLocation;
      opt.innerText = `📍 ${activeStoreLocation}`;
      opt.selected = true;
      select.appendChild(opt);
    }
    renderStoreMedicines();
  }, (err) => {
    alert("Unable to fetch GPS position. Falling back to selected location.");
    renderStoreMedicines();
  });
}

async function renderStoreMedicines() {
  const container = document.getElementById('store-medicines-grid');
  if (!container) return;

  const query = (document.getElementById('store-search-input')?.value || '').toLowerCase();
  const infoEl = document.getElementById('store-fulfillment-info');

  try {
    const res = await fetch(`http://localhost:8000/store/medicines?location=${encodeURIComponent(activeStoreLocation)}&search=${encodeURIComponent(query)}&category=${encodeURIComponent(activeStoreCat)}`);
    const data = await res.json();

    if (infoEl && data.fulfillingStore) {
      infoEl.innerText = `Hub: ${data.fulfillingStore} • ${data.deliveryEta || '15-25 min delivery'}`;
    }

    const meds = data.medicines || [];

    if (meds.length === 0) {
      container.innerHTML = `
        <div class="p-8 rounded-2xl glass-card text-center text-slate-400 text-xs">
          No medicines found matching your search in ${activeStoreLocation}.
        </div>
      `;
      return;
    }

    container.innerHTML = meds.map(med => `
      <div class="p-4 rounded-2xl glass-panel glass-panel-hover border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        
        <!-- Left Thumbnail -->
        <div class="relative w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden bg-slate-900 shrink-0">
          <img src="${med.image}" class="w-full h-full object-cover">
          ${med.requiresRx ? `<span class="absolute top-1 left-1 bg-rose-500/90 text-white text-[9px] px-1.5 py-0.5 rounded font-extrabold">Rx</span>` : ''}
        </div>

        <!-- Center Product Info -->
        <div class="flex-1 min-w-0 space-y-1">
          <div class="flex flex-wrap items-center gap-2">
            <h4 class="text-sm font-extrabold text-white truncate">${med.name}</h4>
            <span class="bg-teal-500/20 text-teal-300 text-[10px] px-2 py-0.5 rounded-full font-bold border border-teal-500/30">${med.discount || 'Special Price'}</span>
          </div>

          <p class="text-[11px] text-slate-400 flex flex-wrap items-center gap-2">
            <span class="text-amber-400 font-bold flex items-center gap-0.5"><i data-lucide="star" class="w-3 h-3 fill-current"></i> ${med.rating} (${med.reviews})</span>
            <span>• ${med.dosage || 'Standard dosage'}</span>
          </p>

          <div class="flex flex-wrap items-center gap-2 text-[10px] text-slate-300 pt-0.5">
            <span class="bg-slate-900 px-2 py-0.5 rounded text-cyan-300 font-semibold border border-slate-800 flex items-center gap-1">
              <i data-lucide="store" class="w-3 h-3 text-cyan-400"></i> ${med.fulfillingStore || 'Partner Hub'}
            </span>
            <span class="bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded font-bold border border-emerald-500/20">
              ⚡ ${med.stockStatus || 'In Stock'}
            </span>
          </div>
        </div>

        <!-- Right Price & Add Button -->
        <div class="text-right space-y-2 shrink-0 w-full sm:w-auto flex sm:flex-col items-center sm:items-end justify-between">
          <div>
            <span class="text-base sm:text-lg font-extrabold text-teal-300">${med.currency || '₹'}${med.price.toFixed(2)}</span>
            ${med.originalPrice ? `<span class="text-xs text-slate-500 line-through ml-1">${med.currency || '₹'}${med.originalPrice.toFixed(2)}</span>` : ''}
          </div>

          <div class="flex items-center gap-1.5 justify-end">
            <button onclick="showMedInfoDetails('${med.id}')" class="bg-slate-900 border border-slate-800 text-teal-300 hover:text-white p-2 rounded-xl text-xs" title="View Insights">
              <i data-lucide="info" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="addToCart('${med.id}')" class="bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-xl text-xs flex items-center gap-1 shadow-lg shadow-teal-500/20 transition-all">
              <i data-lucide="shopping-cart" class="w-3.5 h-3.5"></i>
              <span>+ Add to Cart</span>
            </button>
          </div>
        </div>

      </div>
    `).join('');

    lucide.createIcons();
  } catch (err) {
    const filtered = INITIAL_DATA.medicines.filter(m => {
      const matchesCat = activeStoreCat === 'All' || m.category === activeStoreCat;
      const matchesSearch = m.name.toLowerCase().includes(query);
      return matchesCat && matchesSearch;
    });

    container.innerHTML = filtered.map(med => `
      <div class="p-4 rounded-2xl glass-panel border border-slate-800 flex items-center justify-between gap-4">
        <div class="space-y-1">
          <h4 class="text-sm font-extrabold text-white">${med.name}</h4>
          <p class="text-xs text-slate-400">${med.category} • Offline Mode</p>
        </div>
        <button onclick="addToCart('${med.id}')" class="bg-teal-500 text-slate-950 font-bold px-3 py-1.5 rounded-xl text-xs">
          + Add
        </button>
      </div>
    `).join('');
    lucide.createIcons();
  }
}

function toggleWishlist(medId) {
  alert('Added to your Saved Wishlist!');
}

function addToCart(medId) {
  const existing = state.cart.find(c => c.id === medId);
  if (existing) existing.qty += 1;
  else state.cart.push({ id: medId, qty: 1 });
  renderCart();
  toggleCartDrawer(true);
}

function renderCart() {
  const listContainer = document.getElementById('cart-items-list');
  const countBadge = document.getElementById('cart-badge-side');
  const btnCount = document.getElementById('cart-btn-count');

  const totalItems = state.cart.reduce((sum, i) => sum + i.qty, 0);
  if (countBadge) countBadge.innerText = totalItems;
  if (btnCount) btnCount.innerText = totalItems;

  if (!listContainer) return;

  let subtotal = 0;
  listContainer.innerHTML = state.cart.map(item => {
    const med = INITIAL_DATA.medicines.find(m => m.id === item.id);
    if (!med) return '';
    subtotal += med.price * item.qty;

    return `
      <div class="p-3.5 rounded-2xl glass-card flex items-center justify-between border border-slate-800">
        <div>
          <h4 class="text-xs font-bold text-white">${med.name}</h4>
          <p class="text-[11px] text-teal-400 font-semibold">$${med.price.toFixed(2)} x ${item.qty}</p>
        </div>
        <button onclick="state.cart=state.cart.filter(c=>c.id!='${item.id}');renderCart();" class="text-rose-400 text-xs font-bold">Remove</button>
      </div>
    `;
  }).join('');

  document.getElementById('cart-total').innerText = `$${subtotal.toFixed(2)}`;
}

function toggleCartDrawer(forceOpen) {
  const drawer = document.getElementById('cart-drawer');
  if (forceOpen) drawer.classList.remove('hidden');
  else drawer.classList.toggle('hidden');
}

async function processCheckout() {
  if (state.cart.length === 0) {
    alert("Your cart is empty.");
    return;
  }

  const items = state.cart.map(c => {
    const med = INITIAL_DATA.medicines.find(m => m.id === c.id) || { name: "Medicine", price: 30 };
    return { id: c.id, name: med.name, price: med.price, quantity: c.qty };
  });

  const total = items.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0);

  try {
    const res = await fetch('http://localhost:8000/store/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId: state.activeFamilyId,
        items: items,
        totalAmount: total,
        address: "Home (Hyderabad, Telangana)",
        paymentMethod: "UPI / Cash on Delivery"
      })
    });
    const data = await res.json();
    alert(`✅ FastAPI Order Confirmed!\nOrder ID: ${data.orderId}\nMessage: ${data.message}`);
  } catch (err) {
    alert("✅ Checkout Complete! Order ORD-9923 created (Offline Mode).");
  }

  state.cart = [];
  renderCart();
  toggleCartDrawer(false);
}

// MODULE 10: BLOOD SUPPORT ENGINE
function renderBloodCompatibility() {
  const tbody = document.getElementById('blood-compatibility-body');
  if (!tbody) return;

  tbody.innerHTML = INITIAL_DATA.bloodCompatibility.map(item => `
    <tr class="hover:bg-slate-900/50">
      <td class="p-3 font-extrabold text-rose-400">${item.type}</td>
      <td class="p-3 font-medium text-slate-200">${item.canGiveTo}</td>
      <td class="p-3 font-medium text-teal-300">${item.canReceiveFrom}</td>
    </tr>
  `).join('');
}

function openBloodRequestModal() {
  alert("Blood Request Form Submitted! Notifying nearby blood banks and donors for O+ / A+ units.");
}

// MODULE 11: FEEDBACK & REVIEWS ENGINE
function renderFeedbackList() {
  const container = document.getElementById('feedback-list-container');
  if (!container) return;

  container.innerHTML = INITIAL_DATA.reviews.map(r => `
    <div class="p-4 rounded-2xl glass-card space-y-2 border border-slate-800">
      <div class="flex items-center justify-between">
        <h4 class="text-xs font-bold text-white">${r.name}</h4>
        <span class="text-[11px] text-amber-400 font-bold">⭐ ${r.rating}.0</span>
      </div>
      <p class="text-xs text-slate-300">"${r.comment}"</p>
    </div>
  `).join('');
}

function submitUserFeedback() {
  const name = document.getElementById('fb-name')?.value || "Anonymous User";
  const comment = document.getElementById('fb-comment')?.value;
  if (!comment) return alert("Please write your feedback comment.");

  INITIAL_DATA.reviews.unshift({
    id: `rev-${Date.now()}`,
    name,
    rating: 5,
    date: "Just now",
    comment,
    verified: true
  });

  renderFeedbackList();
  alert("Thank you! Your feedback & rating has been published.");
}

// MODULE 9: EMERGENCY FIRST AID GUIDE
function renderFirstAidGuide() {
  const container = document.getElementById('first-aid-accordion');
  if (!container) return;

  container.innerHTML = INITIAL_DATA.firstAidGuides.map(g => `
    <details class="glass-card p-2.5 rounded-xl cursor-pointer">
      <summary class="font-bold text-slate-100">${g.title}</summary>
      <ol class="mt-2 pl-4 list-decimal text-slate-300 space-y-1">
        ${g.steps.map(s => `<li>${s}</li>`).join('')}
      </ol>
    </details>
  `).join('');
}

// MAPS ENGINE (GOOGLE MAPS INTEGRATION & DYNAMIC LOCAL FACILITY GENERATION)
function initMap() {
  if (state.map) {
    state.map.invalidateSize();
    return;
  }

  const mapContainer = document.getElementById('map-container');
  if (!mapContainer) return;

  // Initialize Map with Google Maps Roadmap Tiles
  state.map = L.map('map-container').setView([37.7749, -122.4194], 13);
  
  L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
  }).addTo(state.map);

  // Automatically update Nearby Places when map is dragged/moved to a new location center
  state.map.on('moveend', () => {
    const center = state.map.getCenter();
    recalculateFacilitiesFromCoordinates(center.lat, center.lng);
  });

  // Automatically trigger user location on initial map load
  locateUserOnMap();
}

let userMarker = null;

function generateNearbyFacilitiesForUserLocation(userLat, userLng) {
  INITIAL_DATA.mapFacilities = [
    {
      id: "fac-1",
      name: "MedPlus Pharmacy",
      type: "Nearby Pharmacies",
      lat: userLat + 0.0032,
      lng: userLng + 0.0028,
      address: "Main Avenue Market Road",
      phone: "+1 800-555-0211",
      distanceKm: 0.4,
      etaMins: 2,
      rating: 4.9,
      is24x7: true,
      openHours: "Open 24 hours",
      icon: "plus",
      colorClass: "teal",
      image: "https://images.unsplash.com/photo-1576602976047-174e57a47881?auto=format&fit=crop&q=80&w=400"
    },
    {
      id: "fac-2",
      name: "City Care Hospital & ER",
      type: "Hospitals",
      lat: userLat - 0.0058,
      lng: userLng + 0.0045,
      address: "Healthcare Boulevard, Sector 4",
      phone: "+1 800-555-0199",
      distanceKm: 0.8,
      etaMins: 4,
      rating: 4.9,
      is24x7: true,
      openHours: "Open 24 hours",
      bedsAvailable: 14,
      icuBeds: 5,
      erWaitTimeMins: 12,
      icon: "building-2",
      colorClass: "indigo",
      image: "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&q=80&w=400"
    },
    {
      id: "fac-3",
      name: "Health First Diagnostics & Labs",
      type: "Labs",
      lat: userLat + 0.0085,
      lng: userLng - 0.0068,
      address: "Science Park Drive, Block C",
      phone: "+1 800-555-0455",
      distanceKm: 1.2,
      etaMins: 6,
      rating: 4.8,
      is24x7: false,
      openHours: "Open 7:00 AM – 9:00 PM",
      icon: "flask-conical",
      colorClass: "purple",
      image: "https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&q=80&w=400"
    },
    {
      id: "fac-4",
      name: "LifeLine Family Clinic",
      type: "Clinics",
      lat: userLat - 0.0094,
      lng: userLng - 0.0042,
      address: "Civil Lines Commercial Hub",
      phone: "+1 800-555-0344",
      distanceKm: 1.5,
      etaMins: 8,
      rating: 4.7,
      is24x7: false,
      openHours: "Open 9:00 AM – 8:00 PM",
      icon: "stethoscope",
      colorClass: "amber",
      image: "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&q=80&w=400"
    },
    {
      id: "fac-5",
      name: "Emergency Care & Trauma Center",
      type: "Hospitals",
      lat: userLat + 0.0140,
      lng: userLng + 0.0120,
      address: "Expressway Emergency Gate 1",
      phone: "+1 108",
      distanceKm: 2.1,
      etaMins: 9,
      rating: 4.9,
      is24x7: true,
      openHours: "Open 24 hours",
      icon: "ambulance",
      colorClass: "rose",
      image: "https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&q=80&w=400"
    },
    {
      id: "fac-6",
      name: "Regional Emergency Blood Bank",
      type: "Blood Banks",
      lat: userLat - 0.0048,
      lng: userLng + 0.0082,
      address: "Red Cross Road, Central Wing",
      phone: "+1 800-555-0788",
      distanceKm: 1.1,
      etaMins: 5,
      rating: 4.9,
      is24x7: true,
      openHours: "Open 24 hours",
      bloodStock: { "O-": 12, "O+": 28, "A+": 19, "B+": 14, "AB+": 8 },
      icon: "droplet",
      colorClass: "rose",
      image: "https://images.unsplash.com/photo-1615461066841-6116e61058f4?auto=format&fit=crop&q=80&w=400"
    }
  ];
}

function updateLocationCenter(lat, lng, locationName) {
  if (!state.map) initMap();

  state.currentCenter = { lat, lng };

  // Generate local facilities dynamically around new location center!
  generateNearbyFacilitiesForUserLocation(lat, lng);

  // Update marker position
  if (userMarker) {
    userMarker.setLatLng([lat, lng]);
  } else {
    const userIcon = L.divIcon({
      className: 'custom-user-marker',
      html: `<div class="w-6 h-6 rounded-full bg-cyan-400 border-2 border-white ring-4 ring-cyan-500/40 animate-pulse shadow-lg"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(state.map);
  }
  userMarker.bindPopup(`<b class="text-xs text-slate-900">📍 Your Location: ${locationName || 'Active'}</b>`).openPopup();

  // Update UI Badge text
  const badge = document.getElementById('active-location-name');
  if (badge) badge.innerText = `${locationName || 'Your Location'} (${lat.toFixed(4)}, ${lng.toFixed(4)})`;

  // Fly to location
  state.map.flyTo([lat, lng], 15, { animate: true, duration: 1.2 });

  // Recalculate distances and sort nearby list
  recalculateFacilitiesFromCoordinates(lat, lng);
}

function recalculateFacilitiesFromCoordinates(centerLat, centerLng) {
  INITIAL_DATA.mapFacilities.forEach(fac => {
    fac.distanceKm = parseFloat(calculateDistanceKm(centerLat, centerLng, fac.lat, fac.lng).toFixed(1));
  });

  // Sort facilities from closest to farthest
  INITIAL_DATA.mapFacilities.sort((a, b) => a.distanceKm - b.distanceKm);

  renderMapFacilities();
}

function changeMapLocationPreset(presetKey) {
  const presets = {
    gps: null, // triggers navigator.geolocation
    downtown: { lat: 37.7710, lng: -122.4230, name: "🏙️ Downtown Central Hub" },
    bayarea: { lat: 37.7780, lng: -122.4150, name: "🌊 Bay Area Market Street" },
    medical: { lat: 37.7795, lng: -122.4280, name: "🏥 Medical District & Labs" },
    suburbs: { lat: 37.7900, lng: -122.4000, name: "🏘️ North Suburbs Residential" }
  };

  if (presetKey === 'gps') {
    locateUserOnMap();
  } else if (presets[presetKey]) {
    const loc = presets[presetKey];
    updateLocationCenter(loc.lat, loc.lng, loc.name);
  }
}

function locateUserOnMap() {
  if (!state.map) initMap();

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLat = position.coords.latitude;
        const userLng = position.coords.longitude;
        updateLocationCenter(userLat, userLng, "📍 Live GPS Location");
      },
      (error) => {
        console.warn("Geolocation fallback:", error);
        updateLocationCenter(37.7749, -122.4194, "📍 City Center (GPS Fallback)");
        alert("GPS Location acquired (Using local location fallback). Nearby places updated!");
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  } else {
    updateLocationCenter(37.7749, -122.4194, "📍 City Center");
  }
}

// Helper to calculate distance between two coordinates (Haversine Formula)
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in KM
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function filterFacilities(type) {
  state.activeMapFilter = type;
  document.querySelectorAll('.fac-filter-btn').forEach(btn => {
    btn.classList.remove('bg-teal-500', 'text-slate-950', 'font-bold');
    btn.classList.add('bg-slate-900', 'text-slate-300');
  });
  renderMapFacilities();
}

function renderMapFacilities() {
  const listContainer = document.getElementById('facilities-list');
  if (!listContainer) return;

  const query = (document.getElementById('maps-search-input')?.value || '').toLowerCase();

  const filtered = INITIAL_DATA.mapFacilities.filter(f => {
    const matchesFilter = state.activeMapFilter === 'All' || f.type === state.activeMapFilter;
    const matchesSearch = f.name.toLowerCase().includes(query) || f.address.toLowerCase().includes(query) || f.type.toLowerCase().includes(query);
    return matchesFilter && matchesSearch;
  });

  if (filtered.length === 0) {
    listContainer.innerHTML = `<div class="p-6 text-center text-xs text-slate-400 glass-card rounded-2xl">No facilities found matching your search.</div>`;
    return;
  }

  // Clear previous markers
  if (state.mapMarkers) {
    state.mapMarkers.forEach(m => state.map.removeLayer(m));
  }
  state.mapMarkers = [];

  listContainer.innerHTML = filtered.map(fac => {
    let iconName = 'plus';
    let colorClasses = 'bg-teal-500/20 text-teal-400 border-teal-500/40';

    if (fac.type === 'Hospitals') {
      iconName = 'building-2';
      colorClasses = 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40';
    } else if (fac.type === 'Labs') {
      iconName = 'flask-conical';
      colorClasses = 'bg-purple-500/20 text-purple-400 border-purple-500/40';
    } else if (fac.type === 'Clinics') {
      iconName = 'stethoscope';
      colorClasses = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    } else if (fac.type === 'Blood Banks' || fac.name.includes('Emergency')) {
      iconName = 'ambulance';
      colorClasses = 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    }

    // Add Google Map marker for facility
    if (state.map) {
      const marker = L.marker([fac.lat, fac.lng]).addTo(state.map);
      marker.bindPopup(`
        <div class="p-1 space-y-1 text-slate-900">
          <b class="text-xs font-bold">${fac.name}</b>
          <p class="text-[10px] text-slate-600">${fac.address}</p>
          <a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(fac.address || fac.name)}" target="_blank" class="inline-block mt-1 text-[10px] text-teal-600 font-bold underline">Open in Google Maps ➔</a>
        </div>
      `);
      state.mapMarkers.push(marker);
    }

    return `
      <div class="p-4 rounded-2xl glass-panel glass-panel-hover border border-slate-800 flex items-center justify-between gap-4">
        
        <!-- Left Icon Box -->
        <div class="w-12 h-12 rounded-2xl ${colorClasses} border flex items-center justify-center shrink-0">
          <i data-lucide="${iconName}" class="w-6 h-6"></i>
        </div>

        <!-- Center Details -->
        <div class="flex-1 min-w-0 space-y-0.5">
          <h4 class="text-sm font-extrabold text-white truncate">${fac.name}</h4>
          <p class="text-[11px] text-slate-400 truncate">${fac.type.replace('Nearby ', '')} • ${fac.distanceKm} km</p>
          <p class="text-[10px] font-bold text-emerald-400 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            ${fac.openHours || 'Open 24 hours'}
          </p>
        </div>

        <!-- Right Action Button -->
        <button onclick="routeToFacility('${fac.id}', '${fac.name}', '${fac.address}')" class="bg-teal-500/10 hover:bg-teal-500 text-teal-300 hover:text-slate-950 border border-teal-500/30 px-3.5 py-2 rounded-xl text-xs font-extrabold flex items-center gap-1.5 shrink-0 transition-colors shadow">
          <i data-lucide="navigation" class="w-3.5 h-3.5"></i>
          <span>Get Directions</span>
        </button>

      </div>
    `;
  }).join('');

  lucide.createIcons();
}

function routeToFacility(facId, name, address) {
  const fac = INITIAL_DATA.mapFacilities.find(f => f.id === facId);
  const dest = address || name || 'Facility';
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(dest)}`, '_blank');
}

// AI ASSISTANT CHAT ENGINE
function openAIAssistantModal() {
  document.getElementById('modal-ai-assistant')?.classList.remove('hidden');
  document.getElementById('modal-ai-backdrop')?.classList.remove('hidden');
}
function closeAIAssistantModal() {
  document.getElementById('modal-ai-assistant')?.classList.add('hidden');
  document.getElementById('modal-ai-backdrop')?.classList.add('hidden');
}

function sendQuickAIPrompt(text) {
  document.getElementById('ai-chat-input').value = text;
  sendAIMessage();
}

function formatMarkdownToHTML(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-teal-300 font-bold">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="text-slate-400">$1</em>')
    .replace(/^### (.*$)/gim, '<h4 class="text-xs font-extrabold text-teal-300 mt-2 mb-1">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 class="text-sm font-extrabold text-white mt-2 mb-1">$1</h3>')
    .replace(/^[•\-\*] (.*$)/gim, '<div class="flex items-start gap-1.5 my-0.5"><span class="text-teal-400 font-bold shrink-0">•</span><span>$1</span></div>')
    .replace(/\n/g, '<br>');
}

async function sendAIMessage() {
  const input = document.getElementById('ai-chat-input');
  const container = document.getElementById('ai-chat-messages');
  if (!input || !container || !input.value.trim()) return;

  const userText = input.value.trim();
  input.value = '';

  const memberName = document.getElementById('active-family-name')?.innerText || 'Rahul Sharma';

  container.innerHTML += `
    <div class="flex justify-end">
      <div class="bg-teal-600 text-white p-3 rounded-2xl max-w-[85%] text-xs shadow-lg">
        ${userText}
      </div>
    </div>
  `;
  container.scrollTop = container.scrollHeight;

  const typingId = 'typing-' + Date.now();
  container.innerHTML += `
    <div id="${typingId}" class="flex justify-start">
      <div class="bg-slate-900 border border-slate-800 text-slate-400 p-3 rounded-2xl max-w-[85%] text-xs flex items-center gap-2">
        <i data-lucide="loader" class="w-4 h-4 animate-spin text-teal-400"></i>
        <span>Connecting to CuraBot AI...</span>
      </div>
    </div>
  `;
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();

  try {
    const res = await fetch('http://localhost:8000/chat/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText, patientContext: memberName })
    });
    const data = await res.json();
    document.getElementById(typingId)?.remove();

    const formattedReply = formatMarkdownToHTML(data.reply || '');

    container.innerHTML += `
      <div class="flex justify-start">
        <div class="bg-slate-900 border border-teal-500/30 text-slate-200 p-4 rounded-2xl max-w-[88%] space-y-1.5 text-xs shadow-xl">
          <div class="flex items-center justify-between text-[10px] text-teal-400 font-bold border-b border-slate-800 pb-1.5 mb-1.5">
            <span class="flex items-center gap-1"><i data-lucide="bot" class="w-3.5 h-3.5"></i> ${data.sender || 'CuraBot AI'}</span>
            <span class="text-slate-400 font-normal">Medical Assistant</span>
          </div>
          <div class="leading-relaxed text-slate-300">
            ${formattedReply}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    document.getElementById(typingId)?.remove();
    container.innerHTML += `
      <div class="flex justify-start">
        <div class="bg-slate-900 border border-slate-800 text-slate-200 p-3.5 rounded-2xl max-w-[85%] space-y-1 text-xs">
          <p class="font-semibold text-teal-300">🤖 CuraBot Care Advice:</p>
          <p>For "${userText}": Stay hydrated, rest, and consult your doctor if symptoms persist.</p>
        </div>
      </div>
    `;
  }
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}
        </div>
      </div>
    `;
  }
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

// EMERGENCY ENGINE
let sosInterval = null;
function triggerEmergencySOS() {
  document.getElementById('modal-emergency-sos').classList.remove('hidden');
  let count = 5;
  const countdownEl = document.getElementById('sos-countdown');
  
  if (sosInterval) clearInterval(sosInterval);
  sosInterval = setInterval(() => {
    count -= 1;
    if (count > 0) {
      countdownEl.innerText = `Dispatching in ${count}s...`;
    } else {
      clearInterval(sosInterval);
      countdownEl.innerText = "EMERGENCY BEACON DISPATCHED!";
      if (window.confetti) confetti({ particleCount: 150, spread: 90 });
    }
  }, 1000);
}

function cancelEmergencySOS() {
  if (sosInterval) clearInterval(sosInterval);
  document.getElementById('modal-emergency-sos').classList.add('hidden');
}

function openEmergencyBloodBanks() {
  cancelEmergencySOS();
  switchTab('maps');
  filterFacilities('Blood Banks');
}

function openEmergencyHospitals() {
  cancelEmergencySOS();
  switchTab('maps');
  filterFacilities('Hospitals');
}

// GENERIC CALCULATOR ENGINE
function renderGenericDropdown() {
  const select = document.getElementById('generic-select');
  if (!select) return;

  select.innerHTML = INITIAL_DATA.medicines.map(m => `
    <option value="${m.id}">${m.brandName} - $${m.price.toFixed(2)}</option>
  `).join('');

  updateGenericComparison();
}

function openGenericCalculatorModal() {
  document.getElementById('modal-generic-calc').classList.remove('hidden');
}
function closeGenericCalculatorModal() {
  document.getElementById('modal-generic-calc').classList.add('hidden');
}

function updateGenericComparison() {
  const select = document.getElementById('generic-select');
  const container = document.getElementById('generic-comparison-result');
  if (!select || !container) return;

  const med = INITIAL_DATA.medicines.find(m => m.id === select.value) || INITIAL_DATA.medicines[0];

  container.innerHTML = `
    <div class="p-4 rounded-2xl glass-card space-y-2">
      <span class="text-xs font-bold text-rose-400">Brand Name</span>
      <h4 class="text-sm font-bold text-white">${med.brandName} - $${med.price.toFixed(2)}</h4>
    </div>
    <div class="p-4 rounded-2xl glass-card space-y-2 border border-emerald-500/40">
      <span class="text-xs font-bold text-emerald-400">Generic Alternative (Save ${med.savingsPercent}%)</span>
      <h4 class="text-sm font-bold text-white">${med.genericName} - $${med.genericPrice.toFixed(2)}</h4>
    </div>
  `;
}

// ITEM & PRESCRIPTION SCANNER ENGINE WITH LIVE WEBRTC CAMERA & DOCUMENT UPLOAD
let activeCameraStream = null;

async function startWebRTCCamera(videoElementId, placeholderId, laserId) {
  try {
    stopAllCameraStreams();
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    activeCameraStream = stream;
    const video = document.getElementById(videoElementId);
    const placeholder = document.getElementById(placeholderId);
    const laser = document.getElementById(laserId);

    if (video) {
      video.srcObject = stream;
      video.classList.remove('hidden');
    }
    if (placeholder) placeholder.classList.add('hidden');
    if (laser) laser.classList.remove('hidden');
  } catch (err) {
    console.warn("Camera access fallback:", err);
    alert("🎥 Camera Access Note: Please grant camera permissions in your browser or select an image file directly.");
  }
}

function stopAllCameraStreams() {
  if (activeCameraStream) {
    activeCameraStream.getTracks().forEach(track => track.stop());
    activeCameraStream = null;
  }
  const prescVideo = document.getElementById('presc-camera-video');
  const itemVideo = document.getElementById('item-camera-video');
  if (prescVideo) { prescVideo.pause(); prescVideo.classList.add('hidden'); }
  if (itemVideo) { itemVideo.pause(); itemVideo.classList.add('hidden'); }

  document.getElementById('presc-upload-placeholder')?.classList.remove('hidden');
  document.getElementById('item-camera-placeholder')?.classList.remove('hidden');
  document.getElementById('presc-laser-line')?.classList.add('hidden');
  document.getElementById('item-laser-bar')?.classList.add('hidden');
}

function togglePrescriptionCameraStream() {
  const video = document.getElementById('presc-camera-video');
  if (video && !video.classList.contains('hidden')) {
    stopAllCameraStreams();
  } else {
    startWebRTCCamera('presc-camera-video', 'presc-upload-placeholder', 'presc-laser-line');
  }
}

function toggleItemCameraStream() {
  const video = document.getElementById('item-camera-video');
  if (video && !video.classList.contains('hidden')) {
    stopAllCameraStreams();
  } else {
    startWebRTCCamera('item-camera-video', 'item-camera-placeholder', 'item-laser-bar');
  }
}

function openPrescriptionScanModal() {
  document.getElementById('modal-presc-scan').classList.remove('hidden');
}

function closePrescriptionScanModal() {
  stopAllCameraStreams();
  document.getElementById('modal-presc-scan').classList.add('hidden');
}

function openItemScanModal() {
  document.getElementById('modal-item-scan').classList.remove('hidden');
}

function closeItemScanModal() {
  stopAllCameraStreams();
  document.getElementById('modal-item-scan').classList.add('hidden');
}

// DOCUMENT UPLOADING & OCR EXTRACTION HANDLERS
let uploadedDocumentData = null;

function handlePrescriptionFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  stopAllCameraStreams();

  const previewBox = document.getElementById('presc-upload-placeholder');
  if (previewBox) {
    previewBox.innerHTML = `
      <i data-lucide="file-check-2" class="w-10 h-10 text-teal-400 mx-auto animate-bounce"></i>
      <p class="text-xs text-white font-extrabold">${file.name}</p>
      <p class="text-[10px] text-teal-300 font-bold">${(file.size / 1024).toFixed(1)} KB • ${file.type || 'Document'}</p>
    `;
    lucide.createIcons();
  }

  uploadedDocumentData = {
    fileName: file.name,
    fileSize: (file.size / 1024).toFixed(1) + ' KB',
    uploadTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    doctor: "Dr. K. S. Somasekhar (Apollo Hospitals)",
    medicines: [
      { name: "Dolo 650mg", dosage: "1-0-1 Post Meals", duration: "5 Days" },
      { name: "Augmentin 625 Duo", dosage: "1-0-1 Post Meals", duration: "5 Days" },
      { name: "Pantocid 40mg", dosage: "1-0-0 Before Meal", duration: "7 Days" }
    ]
  };

  const resultBox = document.getElementById('presc-extracted-result');
  const badge = document.getElementById('presc-file-name-badge');
  const body = document.getElementById('presc-extracted-body');

  if (resultBox && body) {
    resultBox.classList.remove('hidden');
    if (badge) badge.innerText = file.name;
    body.innerHTML = `
      <p class="font-bold text-white">👨‍⚕️ Prescribing Physician: ${uploadedDocumentData.doctor}</p>
      <div class="space-y-1 pt-1 border-t border-slate-800">
        <p class="text-[10px] text-cyan-400 font-extrabold uppercase">Extracted Prescribed Medicines:</p>
        ${uploadedDocumentData.medicines.map(m => `
          <div class="flex items-center justify-between text-slate-200">
            <span>• <b>${m.name}</b></span>
            <span class="text-teal-400 font-semibold">${m.dosage} (${m.duration})</span>
          </div>
        `).join('')}
      </div>
    `;
  }
}

function handleItemScanFile(event) {
  const file = event.target.files[0];
  if (!file) return;

  stopAllCameraStreams();
  triggerBarcodeScanProcess('8901234567890');
}

function triggerBarcodeScanProcess(barcodeVal) {
  const container = document.getElementById('item-scan-results');
  if (!container) return;

  container.classList.remove('hidden');
  container.innerHTML = `
    <div class="p-4 rounded-2xl bg-teal-950/40 border border-teal-500/40 space-y-2 text-xs">
      <div class="flex items-center justify-between">
        <span class="text-teal-400 font-extrabold flex items-center gap-1"><i data-lucide="barcode" class="w-4 h-4"></i> Barcode Recognized</span>
        <span class="text-[10px] bg-teal-500/20 text-teal-300 font-bold px-2 py-0.5 rounded">EAN-13 Verified</span>
      </div>
      <h4 class="text-sm font-extrabold text-white">Lipitor (Atorvastatin 20mg)</h4>
      <p class="text-slate-300">Barcode: ${barcodeVal} • Manufacturer: Pfizer Inc.</p>
      <div class="grid grid-cols-3 gap-2 pt-2">
        <button onclick="showMedInfoDetails('med-1')" class="bg-teal-600 hover:bg-teal-500 text-white text-[11px] font-bold py-2 rounded-xl">
          📖 Insights
        </button>
        <button onclick="addScannedToSchedule()" class="bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] font-bold py-2 rounded-xl">
          + Reminder
        </button>
        <button onclick="askAIAboutScanned()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold py-2 rounded-xl">
          🤖 Ask AI
        </button>
      </div>
    </div>
  `;
  lucide.createIcons();
}

function simulatePrescriptionOCR() {
  if (!uploadedDocumentData) {
    uploadedDocumentData = {
      fileName: "doctor_prescription_scan.pdf",
      fileSize: "420 KB",
      uploadTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      doctor: "Dr. K. S. Somasekhar (Apollo Hospitals)",
      medicines: [
        { name: "Dolo 650mg", dosage: "1-0-1 Post Meals", duration: "5 Days" },
        { name: "Augmentin 625 Duo", dosage: "1-0-1 Post Meals", duration: "5 Days" }
      ]
    };
  }

  // Save document to Health Records
  state.records.unshift({
    id: `rec-${Date.now()}`,
    title: `Prescription: ${uploadedDocumentData.fileName}`,
    date: `Today, ${uploadedDocumentData.uploadTime}`,
    doctor: uploadedDocumentData.doctor,
    category: "Prescriptions",
    medicines: uploadedDocumentData.medicines.map(m => m.name).join(', '),
    fileSize: uploadedDocumentData.fileSize
  });

  renderHealthRecords();
  closePrescriptionScanModal();

  alert(`✅ Prescription Document Saved Successfully!\nExtracted ${uploadedDocumentData.medicines.length} medicines and saved to your Health Records.`);
}

// NOTIFICATION DRAWER CONTROLLER
function toggleNotifDrawer(forceOpen) {
  const drawer = document.getElementById('drawer-notifications');
  if (!drawer) return;

  if (forceOpen === true) {
    drawer.classList.remove('hidden');
  } else if (forceOpen === false) {
    drawer.classList.add('hidden');
  } else {
    drawer.classList.toggle('hidden');
  }
}

function filterNotifications(category) {
  const container = document.getElementById('notifications-feed-list');
  if (!container) return;

  document.querySelectorAll('.notif-tab-btn').forEach(btn => {
    btn.classList.remove('bg-teal-500', 'text-slate-950', 'font-bold');
    btn.classList.add('text-slate-400');
  });

  if (category === 'all') {
    renderNotifsFeed(container, [
      { title: "Time for Paracetamol 650mg", type: "Pill Reminder", typeClass: "teal", time: "8:00 AM Today", desc: "Take 1 tablet after breakfast for fever & pain relief.", action: "alert('Marked Paracetamol 650mg as Taken!')", actionText: "Mark Taken" },
      { title: "Order ORD-982415 Out for Delivery", type: "Order Update", typeClass: "cyan", time: "25 mins ago", desc: "MedPlus Express partner is 1.2 km away. ETA 15 mins.", action: "toggleCartDrawer(true)", actionText: "Track Delivery" },
      { title: "B+ Blood Request Nearby", type: "Emergency Alert", typeClass: "rose", time: "1 hour ago", desc: "Apollo Hospital requested B+ blood. 0.8 km from your location.", action: "scrollToSection('sec-blood')", actionText: "View Request" },
      { title: "Vitamin C 500mg Low Stock", type: "Refill Alert", typeClass: "amber", time: "Yesterday", desc: "Only 3 chewable tablets remaining in your medical locker.", action: "switchTab('store')", actionText: "Reorder Now" }
    ]);
  } else if (category === 'reminders') {
    renderNotifsFeed(container, [
      { title: "Time for Paracetamol 650mg", type: "Pill Reminder", typeClass: "teal", time: "8:00 AM Today", desc: "Take 1 tablet after breakfast for fever & pain relief.", action: "alert('Marked Paracetamol 650mg as Taken!')", actionText: "Mark Taken" },
      { title: "Evening Metoprolol 25mg Dose", type: "Pill Reminder", typeClass: "teal", time: "8:00 PM Today", desc: "Take 1 tablet with water for blood pressure management.", action: "alert('Marked Metoprolol as Taken!')", actionText: "Mark Taken" }
    ]);
  } else if (category === 'orders') {
    renderNotifsFeed(container, [
      { title: "Order ORD-982415 Out for Delivery", type: "Order Update", typeClass: "cyan", time: "25 mins ago", desc: "MedPlus Express partner is 1.2 km away. ETA 15 mins.", action: "toggleCartDrawer(true)", actionText: "Track Delivery" }
    ]);
  } else if (category === 'emergency') {
    renderNotifsFeed(container, [
      { title: "B+ Blood Request Nearby", type: "Emergency Alert", typeClass: "rose", time: "1 hour ago", desc: "Apollo Hospital requested B+ blood. 0.8 km from your location.", action: "scrollToSection('sec-blood')", actionText: "View Request" }
    ]);
  }
}

function renderNotifsFeed(container, list) {
  container.innerHTML = list.map(item => `
    <div class="p-4 rounded-2xl glass-panel border border-${item.typeClass}-500/30 bg-slate-900/60 space-y-2 relative">
      <div class="flex items-center justify-between text-xs">
        <span class="text-${item.typeClass}-400 font-extrabold flex items-center gap-1">
          <i data-lucide="bell" class="w-3.5 h-3.5"></i> ${item.type}
        </span>
        <span class="text-[10px] text-slate-500">${item.time}</span>
      </div>
      <h4 class="text-xs font-bold text-white">${item.title}</h4>
      <p class="text-[11px] text-slate-300">${item.desc}</p>
      <div class="pt-1">
        <button onclick="${item.action}" class="px-3 py-1 rounded-xl bg-${item.typeClass}-500 text-slate-950 font-bold text-[11px]">${item.actionText}</button>
      </div>
    </div>
  `).join('');
  lucide.createIcons();
}

// UTILS & THEMING
function changeLanguage(langKey) {
  state.currentLang = langKey;
  const dict = I18N[langKey] || I18N['en'];
  Object.keys(dict).forEach(key => {
    const el = document.getElementById(`txt-${key}`);
    if (el) el.innerText = dict[key];
  });
}

function toggleTheme() {
  document.body.classList.toggle('light-theme');
}

