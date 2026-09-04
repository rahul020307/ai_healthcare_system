/**
 * CuraAssist Loading Manager
 * Reusable button progress states, skeletons, and loading indicators
 */
const AppLoading = {
  button(btnOrId, loadingText = 'Processing...') {
    const btn = typeof btnOrId === 'string' ? document.getElementById(btnOrId) : btnOrId;
    if (!btn) return () => {};

    const originalHtml = btn.innerHTML;
    const originalDisabled = btn.disabled;

    btn.disabled = true;
    btn.classList.add('opacity-70', 'cursor-not-allowed');
    btn.innerHTML = `
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
      <span>${loadingText}</span>
    `;

    return () => {
      btn.disabled = originalDisabled;
      btn.classList.remove('opacity-70', 'cursor-not-allowed');
      btn.innerHTML = originalHtml;
      if (window.lucide) lucide.createIcons();
    };
  }
};

if (typeof window !== 'undefined') {
  window.AppLoading = AppLoading;
  window.Loading = AppLoading;
}
