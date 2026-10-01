// --- ClaraOS Core Application Shell ---
    let currentTab = 'apps';
    let appCatalogMap = {};

    function renderAppShell(tab) {
      const shell = APP_SHELLS[tab] || APP_SHELLS['apps'];

      // 1. Update Document Title
      document.title = shell.docTitle;

      // 2. Update Sidebar Brand Box
      const brandBox = document.getElementById('sidebar-brand-box');
      if (brandBox) {
        brandBox.innerHTML = `
          <div class="w-9 h-9 rounded-xl bg-gradient-to-tr ${shell.iconGradient} flex items-center justify-center text-white shadow-lg shrink-0">
            <i class="fa-solid ${shell.icon} text-lg"></i>
          </div>
          <div class="min-w-0">
            <span class="font-bold text-lg tracking-wide bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent truncate block">${shell.title}</span>
            <span class="text-[9px] uppercase tracking-wider block font-semibold text-slate-400 -mt-0.5 truncate">${shell.subtitle}</span>
          </div>
        `;
      }

      // 3. Update Sidebar Nav List
      const navList = document.getElementById('nav-list');
      if (navList) {
        navList.innerHTML = shell.navHtml;
      }

      // 4. Update Header Title & Status Badge
      const pageTitle = document.getElementById('page-title');
      if (pageTitle) pageTitle.textContent = shell.headerTitle;

      const badge = document.getElementById('module-status-badge');
      if (badge) {
        badge.textContent = shell.badgeText;
        badge.className = `text-xs px-2.5 py-0.5 rounded-full font-medium ${shell.badgeClass}`;
      }

      // 5. Update Header Actions
      const headerActions = document.getElementById('header-actions');
      if (headerActions) {
        headerActions.innerHTML = shell.headerActionsHtml;
      }
    }

    function toggleMobileSidebar(open) {
      const sidebar = document.getElementById('sidebar');
      const backdrop = document.getElementById('sidebar-backdrop');
      if (!sidebar) return;

      const isClosed = sidebar.classList.contains('-translate-x-full');
      const shouldOpen = open !== undefined ? open : isClosed;

      if (shouldOpen) {
        sidebar.classList.remove('-translate-x-full');
        if (backdrop) backdrop.classList.remove('hidden');
      } else {
        sidebar.classList.add('-translate-x-full');
        if (backdrop) backdrop.classList.add('hidden');
      }
    }

    function switchTab(tab) {
      if (window.innerWidth < 768) {
        toggleMobileSidebar(false);
      }

      const targetTab = NATIVE_TAB_MAP[tab] || tab;
      currentTab = targetTab;

      // Update URL hash without scroll jumps
      if (window.location.hash !== '#' + targetTab) {
        history.replaceState(null, '', '#' + targetTab);
      }

      // Hide all panes and display active one
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      const activePane = document.getElementById(`tab-${targetTab}`);
      if (activePane) activePane.classList.remove('hidden');

      // Transform UI shell to the selected app
      renderAppShell(targetTab);

      if (targetTab === 'store') {
        renderStoreItems();
      }

      refreshCurrentTab();
    }

    function prewarmAppConnections(catalog) {
      const host = window.location.hostname;
      if (isLocalOrIp(host)) return;
      const parts = host.split('.');
      const baseDomain = parts.length > 2 ? parts.slice(-2).join('.') : host;

      catalog.forEach(app => {
        if (!app.native) {
          const sub = app.subdomain || app.id;
          const origin = app.url || `${window.location.protocol}//${sub}.${baseDomain}`;
          
          if (!document.querySelector(`link[rel="dns-prefetch"][href="${origin}"]`)) {
            const dns = document.createElement('link');
            dns.rel = 'dns-prefetch';
            dns.href = origin;
            document.head.appendChild(dns);
          }

          if (!document.querySelector(`link[rel="preconnect"][href="${origin}"]`)) {
            const preconnect = document.createElement('link');
            preconnect.rel = 'preconnect';
            preconnect.href = origin;
            preconnect.crossOrigin = 'anonymous';
            document.head.appendChild(preconnect);
          }
        }
      });
    }

    function prewarmApp(url, isNative) {
      if (isNative || !url || url.startsWith('/#')) return;
      try {
        const u = new URL(url);
        const origin = u.origin;
        if (!document.querySelector(`link[rel="preconnect"][href="${origin}"]`)) {
          const p = document.createElement('link');
          p.rel = 'preconnect';
          p.href = origin;
          p.crossOrigin = 'anonymous';
          document.head.appendChild(p);
        }
      } catch (e) {}
    }

    function handleAppClick(e, appId, isRunning, url, isNative) {
      if (e.target.closest('#app-context-menu')) return;

      if (isNative) {
        e.preventDefault();
        const targetTab = NATIVE_TAB_MAP[appId] || appId;
        switchTab(targetTab);
        return;
      }

      if (!isRunning) {
        e.preventDefault();
        const spinner = document.getElementById(`launcher-spinner-${appId}`);
        if (spinner) spinner.classList.remove('hidden');
        controlApp(appId, 'start').finally(() => {
          if (spinner) spinner.classList.add('hidden');
        });
        return;
      }

      // If running, provide instant tactile click feedback spinner on icon while opening in new tab
      const spinner = document.getElementById(`launcher-spinner-${appId}`);
      if (spinner) {
        spinner.classList.remove('hidden');
        setTimeout(() => { if (spinner) spinner.classList.add('hidden'); }, 1200);
      }
    }

    async function sendAgentPrompt() {
      const input = document.getElementById('agent-prompt-input');
      const prompt = input.value.trim();
      if (!prompt) return;

      const consoleBox = document.getElementById('agent-console');
      const selectedEngine = document.querySelector('input[name="agent_choice"]:checked')?.value || 'antigravity';
      const workspace = document.getElementById('agent-workspace-input').value;

      consoleBox.innerHTML += `<div class="text-white mt-2 font-bold">User: ${prompt}</div>`;
      consoleBox.innerHTML += `<div class="text-purple-300 animate-pulse">Running ${selectedEngine} in ${workspace}...</div>`;
      consoleBox.scrollTop = consoleBox.scrollHeight;
      input.value = '';

      try {
        const res = await fetch('/api/modules/agents/prompt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ engine: selectedEngine, prompt: prompt, workspace: workspace })
        });
        const d = await res.json();
        consoleBox.innerHTML += `<div class="text-emerald-400 whitespace-pre-wrap">${d.output}</div>`;
        consoleBox.scrollTop = consoleBox.scrollHeight;
      } catch (e) {
        consoleBox.innerHTML += `<div class="text-rose-400">Error executing agent: ${e.message}</div>`;
      }
    }


    async function loadSettings() {
      try {
        const res = await fetch('/api/modules');
        const d = await res.json();
        const box = document.getElementById('module-toggle-list');
        box.innerHTML = d.modules.map(m => `
          <div class="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div class="flex items-center justify-between mb-3">
              <span class="font-bold text-sm text-white">${m.title}</span>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" onchange="toggleModule('${m.name}', this.checked)" ${m.enabled ? 'checked' : ''} class="sr-only peer">
                <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
            <p class="text-xs text-slate-400 mb-3">${m.description}</p>
            <div class="text-[11px] font-mono ${m.is_running ? 'text-emerald-400' : 'text-slate-500'}">
              Trạng thái: ${m.is_running ? '🟢 Đang chạy' : '⚪ Đã tắt'}
            </div>
          </div>
        `).join('');
      } catch (e) {}
    }

    async function toggleModule(name, enable) {
      await fetch(`/api/modules/${name}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enable })
      });
      loadSettings();
      updateNavigationVisibility();
    }

    async function updateNavigationVisibility() {
      const res = await fetch('/api/modules');
      const d = await res.json();
      d.modules.forEach(m => {
        const nav = document.querySelector(`#nav-list a[data-tab="${m.name}"]`);
        if (nav) {
          if (m.enabled) nav.classList.remove('hidden');
          else nav.classList.add('hidden');
        }
      });
    }

    function refreshCurrentTab() {
      if (currentTab === 'apps') loadAppCatalog();
      else if (currentTab === 'store') { loadAppCatalog().then(renderStoreItems); }
      else if (currentTab === 'settings') loadSettings();
    }

    // Polling loops
    setInterval(updateSystemStatus, 3000);

    // Initial boot
    updateSystemStatus();
    loadAppCatalog();
    loadSettings();
    updateNavigationVisibility();

    // Hash routing: #apps (default), #store, #agents, #settings
    const initialRaw = window.location.hash.replace('#', '');
    const initialTab = NATIVE_TAB_MAP[initialRaw] || initialRaw;
    if (initialTab && document.getElementById(`tab-${initialTab}`)) {
      switchTab(initialTab);
    } else {
      switchTab('apps');
    }

    window.addEventListener('hashchange', () => {
      const raw = window.location.hash.replace('#', '');
      const tab = NATIVE_TAB_MAP[raw] || raw;
      if (tab && document.getElementById(`tab-${tab}`)) {
        switchTab(tab);
      }
    });
