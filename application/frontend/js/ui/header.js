/**
 * CuraAssist Header Controller
 * Controls top header navigation, scroll progress bar, and user profile sync
 */
const AppHeader = {
  init() {
    this.initScrollProgress();
  },

  initScrollProgress() {
    const bar = document.getElementById('scroll-progress-bar');
    if (!bar) return;

    const handleScroll = () => {
      const docEl = document.documentElement;
      const st = window.scrollY || docEl.scrollTop || 0;
      const sh = docEl.scrollHeight - window.innerHeight;
      const pct = sh > 0 ? (st / sh) * 100 : 0;
      bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    const main = document.querySelector('main');
    if (main) {
      main.addEventListener('scroll', () => {
        const st = main.scrollTop;
        const sh = main.scrollHeight - main.clientHeight;
        const pct = sh > 0 ? (st / sh) * 100 : 0;
        bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
      }, { passive: true });
    }
  },

  toggleMobileDrawer() {
    const drawer = document.getElementById('mobile-menu-drawer');
    if (!drawer) return;
    const isHidden = drawer.style.display === 'none' || drawer.classList.contains('hidden');
    if (isHidden) {
      drawer.style.display = 'flex';
      drawer.classList.remove('hidden');
      if (window.lucide) lucide.createIcons();
    } else {
      drawer.style.display = 'none';
      drawer.classList.add('hidden');
    }
  },

  setActiveTab(tabName) {
    document.querySelectorAll('.header-nav-btn').forEach(el => {
      el.classList.remove('active', 'text-teal-400', 'bg-teal-500/20', 'border', 'border-teal-500/40');
      el.classList.add('text-slate-400');
    });
    const activeHeaderNav = document.getElementById(`header-nav-${tabName}`);
    if (activeHeaderNav) {
      activeHeaderNav.classList.remove('text-slate-400');
      activeHeaderNav.classList.add('active', 'text-teal-400', 'bg-teal-500/20', 'border', 'border-teal-500/40');
    }
  }
};

if (typeof window !== 'undefined') {
  window.AppHeader = AppHeader;
}
