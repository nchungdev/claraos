/**
 * ClaraOS Clean Architecture - State Management Layer
 * Centralized Reactive Store with pub/sub event bus
 */

import { api } from '../api/ApiClient.js';

class StateStore {
  constructor() {
    this.state = {
      currentTab: 'apps',
      system: null,
      disks: [],
      catalog: {},
      modules: [],
      storeFilter: {
        category: 'all',
        query: ''
      },
      isLoading: false
    };

    this.listeners = new Set();
  }

  getState() {
    return this.state;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify(event, payload) {
    for (const listener of this.listeners) {
      try {
        listener(event, this.state, payload);
      } catch (err) {
        console.error('[Store Listener Error]', err);
      }
    }
  }

  setCurrentTab(tab) {
    this.state.currentTab = tab;
    this.notify('TAB_CHANGED', tab);
  }

  async fetchSystemStatus() {
    try {
      const data = await api.get('/api/system/status');
      this.state.system = data;
      if (data.disks && Array.isArray(data.disks)) {
        this.state.disks = data.disks;
      }
      this.notify('SYSTEM_UPDATED', data);
      return data;
    } catch (err) {
      console.error('[Store] fetchSystemStatus failed:', err);
      throw err;
    }
  }

  async fetchCatalog() {
    try {
      const data = await api.get('/api/modules/apps/catalog');
      const catalogItems = Array.isArray(data.catalog) ? data.catalog : [];
      const map = {};
      for (const item of catalogItems) {
        map[item.id] = item;
      }
      this.state.catalog = map;
      this.notify('CATALOG_UPDATED', map);
      return map;
    } catch (err) {
      console.error('[Store] fetchCatalog failed:', err);
      throw err;
    }
  }

  async fetchModules() {
    try {
      const data = await api.get('/api/modules');
      this.state.modules = Array.isArray(data.modules) ? data.modules : [];
      this.notify('MODULES_UPDATED', this.state.modules);
      return this.state.modules;
    } catch (err) {
      console.error('[Store] fetchModules failed:', err);
      throw err;
    }
  }

  setStoreFilter(filter) {
    this.state.storeFilter = { ...this.state.storeFilter, ...filter };
    this.notify('STORE_FILTER_CHANGED', this.state.storeFilter);
  }
}

export const store = new StateStore();
