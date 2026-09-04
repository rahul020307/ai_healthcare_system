/**
 * CuraAssist Sidebar & Navigation Controller
 * Controls desktop sidebar tabs, mobile bottom navigation, and notification badges
 */
const AppSidebar = {
  setActiveTab(tabName) {
    // Desktop sidebar
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const activeNav = document.getElementById(`nav-${tabName}`);
    if (activeNav) activeNav.classList.add('active');

    // Mobile bottom navigation
    document.querySelectorAll('.mobile-nav-btn').forEach(el => {
      el.classList.remove('text-teal-400', 'font-black', 'scale-105');
      el.classList.add('text-slate-400');
    });
    const activeMobileNav = document.getElementById(`mobile-nav-${tabName}`);
    if (activeMobileNav) {
      activeMobileNav.classList.remove('text-slate-400');
      activeMobileNav.classList.add('text-teal-400', 'font-black', 'scale-105');
    }
  },

  updateBadge(badgeId, count) {
    const el = document.getElementById(badgeId);
    if (el) {
      el.innerText = count;
      el.style.display = count > 0 ? 'inline-flex' : 'none';
    }
  }
};

if (typeof window !== 'undefined') {
  window.AppSidebar = AppSidebar;
}
