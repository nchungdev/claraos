/**
 * ClaraOS Clean Architecture - Infrastructure Layer
 * ApiClient: Decoupled HTTP Client with flexible Base URL configuration
 * Supports both Web Browser (same-origin) and Tauri Desktop/Mobile (.dmg, .exe, .apk)
 */

export class ApiClient {
  constructor() {
    this.storageKey = 'CLARA_API_BASE_URL';
    this._baseUrl = this._detectBaseUrl();
  }

  _detectBaseUrl() {
    // 1. Check user override in localStorage (crucial for Tauri Desktop & Android Mobile)
    const stored = localStorage.getItem(this.storageKey);
    if (stored && stored.trim() !== '') {
      return stored.trim().replace(/\/+$/, '');
    }

    // 2. Fallback to current browser origin if in standard web environment
    if (typeof window !== 'undefined' && window.location && window.location.origin) {
      if (window.location.protocol.startsWith('http')) {
        return window.location.origin;
      }
    }

    // 3. Default fallback for local testing / Tauri dev
    return 'http://localhost:8090';
  }

  getBaseUrl() {
    return this._baseUrl;
  }

  setBaseUrl(newUrl) {
    if (!newUrl) {
      localStorage.removeItem(this.storageKey);
      this._baseUrl = this._detectBaseUrl();
    } else {
      const sanitized = newUrl.trim().replace(/\/+$/, '');
      localStorage.setItem(this.storageKey, sanitized);
      this._baseUrl = sanitized;
    }
  }

  isRemoteClient() {
    // Returns true if running outside standard web origin (e.g. Tauri or custom remote host)
    return Boolean(localStorage.getItem(this.storageKey)) || 
           (typeof window !== 'undefined' && window.location && !window.location.protocol.startsWith('http'));
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this._baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    
    const defaultHeaders = {
      'Accept': 'application/json',
    };

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        let errDetail = `${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson && errJson.detail) errDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errDetail);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return await response.text();
    } catch (err) {
      console.error(`[ApiClient Error] ${options.method || 'GET'} ${url}:`, err);
      throw err;
    }
  }

  get(endpoint, params = null) {
    let url = endpoint;
    if (params) {
      const query = new URLSearchParams(params).toString();
      url += (url.includes('?') ? '&' : '?') + query;
    }
    return this.request(url, { method: 'GET' });
  }

  post(endpoint, body = {}) {
    return this.request(endpoint, { method: 'POST', body });
  }

  put(endpoint, body = {}) {
    return this.request(endpoint, { method: 'PUT', body });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
