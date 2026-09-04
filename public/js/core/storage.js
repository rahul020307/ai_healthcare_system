/**
 * CuraAssist Storage
 * Safe, typed localStorage wrapper with versioning and JSON serialization
 */
const AppStorage = {
  PREFIX: 'curaassist_',

  get(key, defaultValue = null) {
    try {
      const val = localStorage.getItem(this.PREFIX + key);
      return val !== null ? JSON.parse(val) : defaultValue;
    } catch (e) {
      console.warn(`[AppStorage] Failed to read "${key}":`, e);
      return defaultValue;
    }
  },

  set(key, value) {
    try {
      localStorage.setItem(this.PREFIX + key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.warn(`[AppStorage] Failed to write "${key}":`, e);
      return false;
    }
  },

  remove(key) {
    try {
      localStorage.removeItem(this.PREFIX + key);
    } catch (e) {}
  },

  clear() {
    try {
      Object.keys(localStorage)
        .filter(k => k.startsWith(this.PREFIX))
        .forEach(k => localStorage.removeItem(k));
    } catch (e) {}
  }
};

if (typeof window !== 'undefined') {
  window.AppStorage = AppStorage;
}
