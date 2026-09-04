/**
 * CuraAssist Toast Notification System
 * Non-blocking, stacked notifications replacing standard browser alert()
 */
const AppToast = {
  container: null,

  getContainer() {
    if (!this.container) {
      let el = document.getElementById('toast-container');
      if (!el) {
        el = document.createElement('div');
        el.id = 'toast-container';
        el.className = 'fixed bottom-20 right-4 z-[999999] flex flex-col gap-2 max-w-sm w-full pointer-events-none';
        document.body.appendChild(el);
      }
      this.container = el;
    }
    return this.container;
  },

  show(message, type = 'info', duration = 3500) {
    const container = this.getContainer();
    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center gap-3 p-4 rounded-2xl glass-panel border shadow-2xl transition-all duration-300 transform translate-y-4 opacity-0 text-xs font-semibold text-white';

    const colors = {
      success: 'border-emerald-500/40 text-emerald-300 bg-emerald-950/80',
      error: 'border-rose-500/40 text-rose-300 bg-rose-950/80',
      warning: 'border-amber-500/40 text-amber-300 bg-amber-950/80',
      info: 'border-teal-500/40 text-teal-300 bg-slate-950/90'
    };

    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };

    toast.classList.add(...(colors[type] || colors.info).split(' '));
    toast.innerHTML = `
      <span class="w-6 h-6 rounded-full flex items-center justify-center font-bold bg-white/10 shrink-0">${icons[type] || 'ℹ'}</span>
      <span class="flex-1 leading-snug">${message}</span>
      <button class="text-white/60 hover:text-white ml-2 text-sm leading-none shrink-0" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    // Spring slide in
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-4', 'opacity-0');
      toast.classList.add('translate-y-0', 'opacity-100');
    });

    // Auto dismiss
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success(msg, duration) { this.show(msg, 'success', duration); },
  error(msg, duration) { this.show(msg, 'error', duration); },
  warning(msg, duration) { this.show(msg, 'warning', duration); },
  info(msg, duration) { this.show(msg, 'info', duration); }
};

if (typeof window !== 'undefined') {
  window.AppToast = AppToast;
  window.Toast = AppToast;
}
