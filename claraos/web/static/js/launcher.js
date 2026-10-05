// --- Desktop Launcher & Context Management ---
    const COMPOSE_FILE_UUIDS = {
      'prowlarr': '9f8e8f42-3c5a-4072-9564-8d036e308424',
      'plex': 'd563f297-6b32-45a8-b040-9cce362c93f4',
      'calibre-web': '0811ec4f-13f7-4d51-b21a-73b605f0f55d',
      'jellyfin': '5e6e3fec-92c2-46e2-a730-a49bdf7873f2',
      'sonarr': '6325250f-9c37-4312-8e9d-9e065b32fd69',
      'radarr': '5d2ce306-fcbd-4e5a-b3df-a37a15353ef0',
      'jellyseerr': '9a18f138-fa1c-4737-9b57-7fd8a2321f46',
      'filebrowser': 'fead0825-8752-4ed6-b114-0335be6f3984',
      'file': 'fead0825-8752-4ed6-b114-0335be6f3984',
      'torbox': '17844f34-f4a5-4d55-a204-69c27b1f78f2',
      'debrid-ingest': '17844f34-f4a5-4d55-a204-69c27b1f78f2',
      'debrid': '17844f34-f4a5-4d55-a204-69c27b1f78f2',
      'media-organizer': '4447bde7-3520-447a-a095-0d2115b01ace',
      'organizer': '4447bde7-3520-447a-a095-0d2115b01ace',
      'cloud-sync': '9b5d3880-60b8-4c2f-b472-bb5cf202970a',
      'rclone': '0122df61-d6f3-42f7-8b51-77a7c6c2739d',
      'claraos': 'bdbf710a-9bf1-4ba6-ab52-617971cab3e4',
      'metube': 'e867b36f-e3eb-460d-959c-70f90cb783db',
      'tdarr': '7d391b10-2f19-4933-bf7b-94c65306e93a',
      'ariang': '36b5ccf7-926b-4e1d-85fa-7f4153ca9812'
    };

    function openComposeEdit(appId, appUuid = null) {
      const app = (typeof appCatalogMap !== 'undefined' && appCatalogMap) ? appCatalogMap[appId] : null;
      const uuid = appUuid || (app && app.compose_uuid) || COMPOSE_FILE_UUIDS[appId];
      const host = window.location.hostname;
      let omvBase = '';
      if (isLocalOrIp(host)) {
        omvBase = `http://${host}:80`;
      } else {
        const parts = host.split('.');
        const baseDomain = parts.length > 2 ? parts.slice(-2).join('.') : host;
        omvBase = `${window.location.protocol}//omv.${baseDomain}`;
      }
      const targetUrl = uuid 
        ? `${omvBase}/#/services/compose/files/edit/${uuid}`
        : `${omvBase}/#/services/compose/files`;
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
    }


    // OMV's "create Compose file" page (the same host logic as openComposeEdit)
    function openOmvComposeCreate() {
      const host = window.location.hostname;
      let omvBase = '';
      if (isLocalOrIp(host)) {
        omvBase = `http://${host}:80`;
      } else {
        const parts = host.split('.');
        const baseDomain = parts.length > 2 ? parts.slice(-2).join('.') : host;
        omvBase = `${window.location.protocol}//omv.${baseDomain}`;
      }
      window.open(`${omvBase}/#/services/compose/files/create`, '_blank', 'noopener,noreferrer');
    }

    function isLocalOrIp(host) {
      if (!host || host === 'localhost' || host === '127.0.0.1') return true;
      const ipv4Pattern = /^(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
      if (ipv4Pattern.test(host)) return true;
      if (host.includes(':')) return true;
      return false;
    }

    function getAppUrl(app) {
      if (app.url) return app.url;
      if (app.native) {
        return app.url;
      }
      const host = window.location.hostname;
      if (isLocalOrIp(host)) {
        return `http://${host}:${app.default_port}`;
      } else {
        const parts = host.split('.');
        const baseDomain = parts.length > 2 ? parts.slice(-2).join('.') : host;
        const sub = app.subdomain || app.id;
        return `${window.location.protocol}//${sub}.${baseDomain}`;
      }
    }

    function getAppEndpointLabel(app) {
      if (app.url) {
        try { return new URL(app.url).hostname; } catch (e) { return app.url; }
      }
      if (app.native) return 'Core Module';
      const host = window.location.hostname;
      if (isLocalOrIp(host)) {
        return `:${app.default_port}`;
      } else {
        const parts = host.split('.');
        const baseDomain = parts.length > 2 ? parts.slice(-2).join('.') : host;
        const sub = app.subdomain || app.id;
        return `${sub}.${baseDomain}`;
      }
    }

    function openAppContextMenu(e, appId) {
      e.preventDefault();
      e.stopPropagation();

      const app = appCatalogMap[appId];
      if (!app) return;

      const appUrl = getAppUrl(app);
      const menu = document.getElementById('app-context-menu');
      const title = document.getElementById('context-menu-name');
      const statusEl = document.getElementById('context-menu-status');
      const actionsBox = document.getElementById('context-menu-actions');

      title.textContent = app.name;
      
      if (app.native) {
        statusEl.textContent = 'Core';
        statusEl.className = 'text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300';
      } else if (app.protected || app.manageable === false) {
        statusEl.textContent = 'Hệ thống';
        statusEl.className = 'text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300';
      } else if (app.is_running) {
        statusEl.textContent = 'Đang chạy';
        statusEl.className = 'text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400';
      } else if (app.installed) {
        statusEl.textContent = 'Đã dừng';
        statusEl.className = 'text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400';
      } else {
        statusEl.textContent = 'Chưa cài';
        statusEl.className = 'text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400';
      }

      let actionsHtml = '';

      // 0. Xem thông tin chi tiết
      actionsHtml += `
        <button onclick="openAppDetail('${app.id}'); closeContextMenu();" 
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-slate-800 text-left transition font-semibold">
          <i class="fa-solid fa-circle-info text-cyan-400 w-4 text-center"></i>
          <span>Xem thông tin chi tiết</span>
        </button>
        <div class="h-px bg-slate-800/80 my-1"></div>
      `;

      // 1. Mở ứng dụng
      actionsHtml += `
        <button onclick="openAppDirect('${app.id}'); closeContextMenu();" 
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-cyan-500/20 text-left transition font-semibold">
          <i class="fa-solid fa-arrow-up-right-from-square text-cyan-400 w-4 text-center"></i>
          <span>Mở ứng dụng</span>
        </button>
      `;

      // 2. Chỉnh sửa Docker Compose (nếu có cấu hình trong OpenMediaVault Compose)
      if (COMPOSE_FILE_UUIDS[app.id] || app.compose_uuid || app.installed) {
        actionsHtml += `
          <button onclick="openComposeEdit('${app.id}', '${app.compose_uuid || ''}'); closeContextMenu();" 
                  class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200
                         hover:text-white hover:bg-slate-800 text-left transition font-semibold">
            <i class="fa-solid fa-sliders text-cyan-400 w-4 text-center"></i>
            <span>Sửa cấu hình (OMV)</span>
          </button>
        `;
      }

      // 3. Các hành động quản lý Docker
      const canManage = app.manageable !== false && !app.protected;

      if (canManage) {
        if (app.is_running) {
          actionsHtml += `
            <button onclick="controlApp('${app.id}', 'restart'); closeContextMenu();" 
                    class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-indigo-500/20 text-left transition">
              <i class="fa-solid fa-rotate-right text-indigo-400 w-4 text-center"></i>
              <span>Khởi động lại</span>
            </button>
            <button onclick="controlApp('${app.id}', 'stop'); closeContextMenu();" 
                    class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-amber-500/20 text-left transition">
              <i class="fa-solid fa-stop text-amber-400 w-4 text-center"></i>
              <span>Dừng ứng dụng</span>
            </button>
          `;
        } else if (app.installed) {
          actionsHtml += `
            <button onclick="controlApp('${app.id}', 'start'); closeContextMenu();" 
                    class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-emerald-500/20 text-left transition">
              <i class="fa-solid fa-play text-emerald-400 w-4 text-center"></i>
              <span>Khởi động ứng dụng</span>
            </button>
          `;
        }
      }

      // Restart the app's own server when it is not a managed Docker container (those have "Khởi động lại" above)
      if (!canManage && app.restartable) {
        actionsHtml += `
          <button onclick="restartServer('${app.id}'); closeContextMenu();" 
                  class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-200 hover:text-white hover:bg-indigo-500/20 text-left transition">
            <i class="fa-solid fa-power-off text-indigo-400 w-4 text-center"></i>
            <span>Restart server</span>
          </button>
        `;
      }

      // 3. Sao chép URL
      actionsHtml += `
        <div class="h-px bg-slate-800/80 my-1"></div>
        <button onclick="copyToClipboard('${appUrl}'); closeContextMenu();" 
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-left transition">
          <i class="fa-solid fa-copy text-slate-400 w-4 text-center"></i>
          <span>Sao chép liên kết</span>
        </button>
      `;

      // 4. Gỡ cài đặt (CHỈ hiện khi app có quyền quản lý và đã cài đặt)
      if (canManage && app.installed) {
        actionsHtml += `
          <div class="h-px bg-slate-800/80 my-1"></div>
          <button onclick="confirmUninstall('${app.id}', '${app.name}'); closeContextMenu();" 
                  class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-400 hover:text-rose-300 hover:bg-rose-500/20 text-left transition">
            <i class="fa-solid fa-trash-can text-rose-400 w-4 text-center"></i>
            <span>Gỡ cài đặt</span>
          </button>
        `;
      }

      actionsBox.innerHTML = actionsHtml;

      // Position popup clamped within viewport
      menu.classList.remove('hidden');
      const menuWidth = 210;
      const menuHeight = 280;
      let posX = e.clientX;
      let posY = e.clientY;

      if (posX + menuWidth > window.innerWidth) {
        posX = window.innerWidth - menuWidth - 16;
      }
      if (posY + menuHeight > window.innerHeight) {
        posY = window.innerHeight - menuHeight - 16;
      }

      menu.style.left = `${Math.max(12, posX)}px`;
      menu.style.top = `${Math.max(12, posY)}px`;
    }

    function closeContextMenu() {
      const menu = document.getElementById('app-context-menu');
      if (menu) menu.classList.add('hidden');
    }

    function copyToClipboard(text) {
      navigator.clipboard.writeText(text);
    }

    // APP STORE CONTROLLER & APP DETAIL MODAL
    let storeSelectedCategory = 'all';
    let storeSearchTerm = '';


    async function loadAppCatalog(force = false) {
      try {
        const isStore = currentTab === 'store';
        const cache = isStore ? storeCatalogCache : appCatalogCache;
        if (!force && cache && cache.length > 0) {
          if (isStore) renderStoreItems();
          else renderAppCatalogGrid(cache);
          return;
        }
        const res = await fetch(isStore ? '/api/modules/apps/store' : '/api/modules/apps/catalog');
        const d = await res.json();
        if (isStore) storeCatalogCache = d.catalog;
        else appCatalogCache = d.catalog;
        d.catalog.forEach(app => { appCatalogMap[app.id] = app; });
        if (isStore) renderStoreItems();
        else {
          renderAppCatalogGrid(d.catalog);
          prewarmAppConnections(d.catalog);
        }
      } catch (e) {}
    }

    function renderAppCatalogGrid(catalog) {
      const grid = document.getElementById('app-catalog-grid');
      if (!grid) return;

      // Only display apps that are installed/running AND have a Web GUI on the desktop launcher
      const desktopApps = catalog
        .filter(app => (app.installed || app.is_running) && app.has_gui !== false && app.id !== 'flaresolverr')
        .sort((a, b) => a.name.localeCompare(b.name));
      grid.className = 'grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-y-7 sm:gap-y-12 gap-x-2.5 sm:gap-x-8 justify-items-center w-full py-4 sm:py-8 px-1 sm:px-4';

      if (desktopApps.length === 0) {
        grid.innerHTML = '<div class="col-span-full py-12 text-center text-slate-500 text-sm">Chưa có ứng dụng nào được cài đặt. Vào <button onclick="switchTab(\'store\')" class="text-cyan-400 underline font-semibold">App Store</button> để cài thêm.</div>';
        return;
      }

      grid.innerHTML = desktopApps.map(app => {
        const appUrl = getAppUrl(app);
        const inactive = !app.is_running;
        const clickAction = inactive ? `openAppDetail('${app.id}')` : `openAppDirect('${app.id}')`;
        const cardClass = inactive ? 'opacity-55 grayscale cursor-default' : 'cursor-pointer';
        const iconClass = inactive
          ? 'bg-slate-900 border-slate-800 shadow-none'
          : 'bg-gradient-to-br from-slate-800/90 via-slate-850/90 to-slate-900 border-white/10 shadow-[0_8px_20px_-4px_rgba(0,0,0,0.5)] group-hover:scale-105 group-hover:border-cyan-400/40 group-hover:shadow-[0_12px_25px_rgba(6,182,212,0.2)] group-active:scale-95';

        return `
          <div onclick="${clickAction}; return false;"
               oncontextmenu="openAppContextMenu(event, '${app.id}')"
               onmouseenter="${inactive ? '' : `prewarmApp('${appUrl}', false)`}"
               class="app-launcher-item flex flex-col items-center justify-center text-center relative group p-1 transition-all duration-150 select-none w-24 sm:w-28 md:w-36 focus:outline-none ${cardClass}"
               title="${app.name} (${inactive ? 'Chưa chạy — bấm để xem chi tiết' : 'Bấm để mở ứng dụng - Chuột phải để quản lý'})">
            
            <!-- App Icon Squircle Container (macOS Launchpad / iPadOS Ratio) -->
            <div class="relative w-20 h-20 sm:w-24 sm:h-24 md:w-28 md:h-28 flex items-center justify-center">
              
              <!-- Squircle Icon Box -->
              <div class="w-full h-full rounded-[20px] sm:rounded-[24px] md:rounded-[28px] border p-3 sm:p-4 md:p-5 flex items-center justify-center transition-all duration-150 relative overflow-hidden ${iconClass}">
                <img src="${app.logo || `https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/${app.logo_id || app.id}.png`}"
                     alt="${app.name}" 
                     loading="eager"
                     decoding="async"
                     class="w-full h-full object-contain filter drop-shadow-md transition-transform duration-150 ${inactive ? 'opacity-45 grayscale' : 'group-hover:scale-105'}"
                     onerror="this.onerror=null; this.parentElement.innerHTML='<i class=\\'fa-solid ${app.icon || 'fa-cubes'} text-cyan-400 text-2xl sm:text-3xl md:text-4xl\\'></i>';">
                
                <!-- Instant Click / Launching Spinner Overlay -->
                <div id="launcher-spinner-${app.id}" class="hidden absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center text-cyan-400 transition-opacity">
                  <i class="fa-solid fa-circle-notch fa-spin text-xl sm:text-2xl"></i>
                </div>
              </div>
            </div>

            <!-- App Label / Name (macOS SF Typography style) -->
            <span class="font-medium text-[11px] sm:text-xs md:text-sm ${inactive ? 'text-slate-500' : 'text-slate-100 group-hover:text-cyan-300'} mt-2 sm:mt-2.5 truncate w-full transition text-center drop-shadow px-1">
              ${app.name}
            </span>
          </div>
        `;
      }).join('');
    }

    async function controlApp(appId, action) {
      await fetch(`/api/modules/apps/${appId}/${action}`, { method: 'POST' });
      await loadAppCatalog(true);
    }

    function showToast(message, type = 'info', duration = 3500) {
      const container = document.getElementById('toast-container');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = 'glass-panel pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border shadow-2xl text-xs text-white backdrop-blur-md transition-all duration-300 opacity-0 translate-y-2';

      let icon = '<i class="fa-solid fa-circle-info text-cyan-400 text-sm"></i>';
      let border = 'border-slate-700/80';
      if (type === 'success') {
        icon = '<i class="fa-solid fa-circle-check text-emerald-400 text-sm"></i>';
        border = 'border-emerald-500/30';
      } else if (type === 'error') {
        icon = '<i class="fa-solid fa-circle-exclamation text-rose-400 text-sm"></i>';
        border = 'border-rose-500/30';
      } else if (type === 'warning') {
        icon = '<i class="fa-solid fa-triangle-exclamation text-amber-400 text-sm"></i>';
        border = 'border-amber-500/30';
      }

      toast.className += ` ${border}`;
      toast.innerHTML = `
        ${icon}
        <span class="font-medium">${message}</span>
      `;

      container.appendChild(toast);

      requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
      });

      setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
      }, duration);
    }
    window.showToast = showToast;

    let pendingAction = null;

    function openActionConfirmModal(title, message, confirmText, onConfirm) {
      const modal = document.getElementById('modal-action-confirm');
      if (!modal) {
        if (confirm(message)) onConfirm();
        return;
      }
      const titleEl = document.getElementById('modal-action-title');
      if (titleEl) titleEl.textContent = title;
      const msgEl = document.getElementById('modal-action-message');
      if (msgEl) msgEl.textContent = message;
      const btnTextEl = document.getElementById('modal-action-confirm-text');
      if (btnTextEl) btnTextEl.textContent = confirmText || 'Xác nhận';
      
      pendingAction = onConfirm;
      modal.classList.remove('hidden');
    }

    function closeActionConfirmModal() {
      pendingAction = null;
      const modal = document.getElementById('modal-action-confirm');
      if (modal) modal.classList.add('hidden');
    }
    window.closeActionConfirmModal = closeActionConfirmModal;

    const actionConfirmBtn = document.getElementById('modal-btn-confirm-action');
    if (actionConfirmBtn) {
      actionConfirmBtn.onclick = async () => {
        const action = pendingAction;
        closeActionConfirmModal();
        if (action) await action();
      };
    }

    async function restartServer(appId) {
      const app = appCatalogMap[appId];
      if (!app) return;
      const msg = (app.restart && app.restart.confirm) || `Mọi terminal và agent đang chạy trong ${app.name} sẽ bị ngắt kết nối tạm thời.`;

      openActionConfirmModal(
        `Khởi động lại ${app.name}?`,
        msg,
        'Khởi động lại',
        async () => {
          showToast(`Đang gửi yêu cầu khởi động lại ${app.name}...`, 'info');
          try {
            const res = await fetch(`/api/modules/apps/${appId}/restart`, { method: 'POST' });
            if (!res.ok) {
              const err = await res.json().catch(() => ({}));
              showToast(`Restart thất bại: ${err.detail || res.status}`, 'error', 5000);
              return;
            }
            showToast(`Đã gửi lệnh restart tới ${app.name}!`, 'success');
          } catch (e) {
            showToast(`Restart thất bại: ${e}`, 'error', 5000);
            return;
          }
          setTimeout(() => loadAppCatalog(true), 3000);
        }
      );
    }

    let pendingUninstallAppId = null;

    function confirmUninstall(appId, appName) {
      pendingUninstallAppId = appId;
      const titleEl = document.getElementById('modal-uninstall-title');
      if (titleEl) titleEl.textContent = `Gỡ cài đặt ${appName}?`;
      
      const pathEl = document.getElementById('uninstall-config-path');
      if (pathEl) pathEl.textContent = `/appdata/${appId}`;

      const purgeCb = document.getElementById('uninstall-purge-checkbox');
      if (purgeCb) purgeCb.checked = false;

      const modal = document.getElementById('modal-uninstall');
      if (modal) modal.classList.remove('hidden');
    }

    function closeUninstallModal() {
      pendingUninstallAppId = null;
      const modal = document.getElementById('modal-uninstall');
      if (modal) modal.classList.add('hidden');
    }

    const confirmDelBtn = document.getElementById('modal-btn-confirm-delete');
    if (confirmDelBtn) {
      confirmDelBtn.onclick = async () => {
        if (!pendingUninstallAppId) return;
        const appId = pendingUninstallAppId;
        const purgeCb = document.getElementById('uninstall-purge-checkbox');
        const purgeData = Boolean(purgeCb && purgeCb.checked);

        closeUninstallModal();
        try {
          await fetch(`/api/modules/apps/${appId}/uninstall`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purge_data: purgeData })
          });
          await loadAppCatalog(true);
          if (currentTab === 'store' && typeof renderStoreItems === 'function') {
            renderStoreItems();
          }
        } catch (e) {
          console.error('Lỗi khi gỡ cài đặt app:', e);
        }
      };
    }
