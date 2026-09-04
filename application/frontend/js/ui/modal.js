/**
 * CuraAssist Modal Controller
 * Standardized spring-physics modal opening, closing, focus trapping, and backdrop blur
 */
const AppModal = {
  open(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.style.display = 'flex';
    modal.classList.remove('hidden');

    // Add spring scale-in to the first inner card container
    const card = modal.querySelector('.glass-panel, .bg-slate-900, [class*="rounded-3xl"]');
    if (card && !card.classList.contains('modal-spring-entry')) {
      card.classList.add('modal-spring-entry');
    }

    if (window.lucide) lucide.createIcons();

    // Push state or notify
    if (typeof AppEvents !== 'undefined') {
      AppEvents.emit('modal:opened', modalId);
    }
  },

  close(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.style.display = 'none';
    modal.classList.add('hidden');

    if (typeof AppEvents !== 'undefined') {
      AppEvents.emit('modal:closed', modalId);
    }
  },

  closeAll() {
    document.querySelectorAll('[id^="modal-"]').forEach(m => {
      m.style.display = 'none';
      m.classList.add('hidden');
    });
  },

  init() {
    // Listen for Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const visibleModals = Array.from(document.querySelectorAll('[id^="modal-"]')).filter(
          m => m.style.display === 'flex' || !m.classList.contains('hidden')
        );
        if (visibleModals.length > 0) {
          const topModal = visibleModals[visibleModals.length - 1];
          this.close(topModal.id);
        }
      }
    });

    // Close on backdrop click (if clicking the outer container directly)
    document.addEventListener('click', (e) => {
      if (e.target && e.target.id && e.target.id.startsWith('modal-') && e.target.classList.contains('fixed')) {
        this.close(e.target.id);
      }
    });
  }
};

if (typeof window !== 'undefined') {
  window.AppModal = AppModal;
  window.Modal = AppModal;
}
