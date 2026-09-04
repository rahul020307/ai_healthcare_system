/**
 * CuraAssist API Client
 * Centralized async HTTP fetch client with automatic Bearer token injection
 */
const AppApi = {
  getBaseUrl() {
    if (typeof window !== 'undefined') {
      const host = window.location.hostname;
      if (host === 'localhost' || host === '127.0.0.1') {
        return 'http://127.0.0.1:8000';
      }
    }
    return '';
  },

  async getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders
    };

    // Inject Supabase / session token if available
    let token = null;
    if (typeof supabaseClient !== 'undefined' && supabaseClient?.auth) {
      try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session && session.access_token) {
          token = session.access_token;
        }
      } catch (e) {}
    }

    if (!token && typeof localStorage !== 'undefined') {
      token = localStorage.getItem('supabase_access_token') || localStorage.getItem('auth_token');
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const baseUrl = this.getBaseUrl();
    const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = await this.getHeaders(options.headers || {});

    const config = {
      ...options,
      headers
    };

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        throw new Error((data && data.detail) || (data && data.message) || `HTTP error! status: ${response.status}`);
      }
      return data;
    } catch (error) {
      console.warn(`[AppApi] Request failed for ${endpoint}:`, error.message);
      throw error;
    }
  },

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  },

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body });
  },

  put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body });
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
};

if (typeof window !== 'undefined') {
  window.AppApi = AppApi;
}
