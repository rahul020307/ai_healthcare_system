/**
 * CuraAssist State
 * Centralized, reactive application state singleton
 */
const AppState = {
  currentTab: 'home',
  user: null,
  activeFamilyMember: 'Self',
  cart: [],
  schedules: [],
  records: [],
  map: null,
  markers: [],
  userLocation: [17.4065, 78.4772], // Default: Hyderabad, India
  searchRadiusKm: 5,
  isAudioMuted: false,

  init(initialData = {}) {
    if (initialData.schedules) this.schedules = [...initialData.schedules];
    if (initialData.records) this.records = [...initialData.records];
    if (typeof AppStorage !== 'undefined') {
      const savedUser = AppStorage.get('active_user');
      if (savedUser) this.user = savedUser;
      const savedCart = AppStorage.get('cart', []);
      if (savedCart) this.cart = savedCart;
    }
  },

  setUser(userData) {
    this.user = userData;
    if (typeof AppStorage !== 'undefined') {
      AppStorage.set('active_user', userData);
    }
    if (typeof AppEvents !== 'undefined') {
      AppEvents.emit('user:changed', userData);
    }
  },

  setCart(cartItems) {
    this.cart = cartItems;
    if (typeof AppStorage !== 'undefined') {
      AppStorage.set('cart', cartItems);
    }
    if (typeof AppEvents !== 'undefined') {
      AppEvents.emit('cart:updated', cartItems);
    }
  }
};

if (typeof window !== 'undefined') {
  window.AppState = AppState;
}
