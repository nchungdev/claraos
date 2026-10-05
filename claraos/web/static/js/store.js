// --- App Store & Community Catalog ---
    function openAppStore() {
      switchTab('store');
    }

    function closeAppStore() {
      switchTab('apps');
    }

    function setStoreCategory(cat) {
      storeSelectedCategory = cat;
      document.querySelectorAll('.store-cat-btn').forEach(b => {
        if (b.dataset.cat === cat) {
          b.className = 'store-cat-btn px-4 py-2 rounded-xl text-xs font-semibold transition bg-cyan-600 text-white shadow-md shadow-cyan-600/20';
        } else {
          b.className = 'store-cat-btn px-4 py-2 rounded-xl text-xs font-medium transition bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700/50';
        }
      });
      renderStoreItems();
    }

    function filterStoreCatalog() {
      storeSearchTerm = (document.getElementById('store-search-input')?.value || '').toLowerCase().trim();
      renderStoreItems();
    }

    function getAppHomepage(app) {
      if (app.homepage) return { url: app.homepage, label: 'Trang chủ', icon: 'fa-solid fa-globe' };
      if (app.github) return { url: app.github, label: 'GitHub', icon: 'fa-brands fa-github' };

      const img = app.image || '';
      if (img.includes('ghcr.io/')) {
        const clean = img.replace('ghcr.io/', '').split(':')[0];
        return { url: `https://github.com/${clean}`, label: 'GitHub', icon: 'fa-brands fa-github' };
      }
      if (img.includes('lscr.io/linuxserver/')) {
        const clean = img.replace('lscr.io/linuxserver/', '').split(':')[0];
        return { url: `https://github.com/linuxserver/docker-${clean}`, label: 'GitHub', icon: 'fa-brands fa-github' };
      }
      if (img.includes('/')) {
        const clean = img.split(':')[0];
        return { url: `https://hub.docker.com/r/${clean}`, label: 'DockerHub', icon: 'fa-brands fa-docker' };
      }
      if (img) {
        const clean = img.split(':')[0];
        return { url: `https://hub.docker.com/_/${clean}`, label: 'DockerHub', icon: 'fa-brands fa-docker' };
      }
      return { url: `https://github.com/search?q=${encodeURIComponent(app.name)}`, label: 'GitHub', icon: 'fa-brands fa-github' };
    }

    function renderStoreItems() {
      const container = document.getElementById('store-items-grid');
      if (!container) return;

      const list = Object.values(appCatalogMap).filter(app => {
        const cat = app.category || '';
        const matchesCategory = storeSelectedCategory === 'all' || 
          cat.toLowerCase() === storeSelectedCategory.toLowerCase() ||
          (storeSelectedCategory === 'Tools' && (cat === 'System' || cat === 'Tools')) ||
          (storeSelectedCategory === 'Downloads' && (cat.includes('Download') || cat === 'Downloads')) ||
          (storeSelectedCategory === 'Media' && (cat.includes('Media') || cat === 'Media workflow')) ||
          (storeSelectedCategory === 'Automation' && (cat.includes('Automation') || cat === 'Arr'));
        const matchesSearch = !storeSearchTerm || 
                              app.name.toLowerCase().includes(storeSearchTerm) || 
                              (app.description && app.description.toLowerCase().includes(storeSearchTerm)) ||
                              (app.image && app.image.toLowerCase().includes(storeSearchTerm));
        return matchesCategory && matchesSearch;
      });

      if (list.length === 0) {
        container.innerHTML = '<div class="col-span-full py-12 text-center text-slate-500 text-sm">Không tìm thấy ứng dụng phù hợp trong kho</div>';
        return;
      }

      const badge = document.getElementById('module-status-badge');
      if (badge && currentTab === 'store') {
        badge.textContent = `${list.length} Apps`;
      }

      container.innerHTML = list.map(app => {
        const isInstalled = Boolean(app.installed);
        const canManage = app.manageable !== false && !app.protected;
        const homepage = getAppHomepage(app);
        const cardAction = `openAppDetail('${app.id}')`;
        const cardTitle = `${app.name} (Bấm để xem chi tiết ứng dụng)`;
        const logoUrl = app.logo || `https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/${app.logo_id || app.id}.png`;

        // Tag & Status
        let statusBadgeHtml = '';
        if (app.is_running) {
          statusBadgeHtml = `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 shrink-0"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Đang chạy</span>`;
        } else if (app.installed) {
          statusBadgeHtml = `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1 shrink-0"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Đã dừng</span>`;
        } else {
          statusBadgeHtml = `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60 shrink-0">Chưa cài</span>`;
        }

        // Actions: Cài đặt / Mở & Github (Home page)
        let mainActionBtnHtml = '';
        if (isInstalled) {
          mainActionBtnHtml = `
            <button onclick="event.stopPropagation(); openAppDirect('${app.id}')"
                    title="Mở ứng dụng"
                    class="h-8 px-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400
                           hover:text-cyan-300 text-xs font-bold flex items-center justify-center
                           gap-1.5 border border-slate-700/60 transition">
              <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
              <span>Mở</span>
            </button>
            <button onclick="event.stopPropagation(); openComposeEdit('${app.id}', '${app.compose_uuid || ''}')"
                    title="Mở trang chỉnh sửa cấu hình Docker Compose trên OpenMediaVault"
                    class="h-8 px-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300
                           hover:text-white text-xs font-semibold flex items-center justify-center
                           gap-1.5 border border-slate-700/60 transition">
              <i class="fa-solid fa-sliders text-xs"></i>
              <span>Config</span>
            </button>
            ${canManage ? `
              <button onclick="event.stopPropagation(); confirmUninstall('${app.id}', '${app.name}')"
                      title="Gỡ cài đặt"
                      class="h-8 px-3.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400
                             hover:text-rose-300 text-xs font-semibold flex items-center justify-center
                             gap-1.5 border border-rose-500/30 transition">
                <i class="fa-solid fa-trash-can text-xs"></i>
                <span>Gỡ cài đặt</span>
              </button>
            ` : ''}
          `;
        } else {
          mainActionBtnHtml = `
            <button onclick="event.stopPropagation(); installAppFromStore('${app.id}', this)"
                    title="Cài đặt ứng dụng"
                    class="h-8 px-3.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-md shadow-cyan-600/20 transition">
              <i class="fa-solid fa-cloud-arrow-down text-xs"></i>
              <span>Cài đặt</span>
            </button>
          `;
        }

        return `
          <div onclick="${cardAction}" title="${cardTitle}"
               class="bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-4 flex flex-col justify-between gap-3.5 transition shadow-sm hover:shadow-md cursor-pointer group">
            
            <!-- 1. Title -->
            <div class="flex items-center justify-between gap-2 border-b border-slate-800/70 pb-2.5">
              <h4 class="font-bold text-sm sm:text-base text-white truncate group-hover:text-cyan-300 transition">${app.name}</h4>
            </div>

            <!-- 2. LOGO - Desc -->
            <div class="flex items-start gap-3.5 min-w-0">
              <div class="w-12 h-12 sm:w-13 sm:h-13 rounded-2xl bg-slate-800/90 border border-slate-700/40 p-2 shrink-0 flex items-center justify-center shadow group-hover:scale-105 transition-transform">
                <img src="${logoUrl}" 
                     alt="${app.name}" 
                     class="w-full h-full object-contain filter drop-shadow"
                     onerror="this.onerror=null; this.parentElement.innerHTML='<i class=\\'fa-solid ${app.icon || 'fa-cubes'} text-cyan-400 text-xl\\'></i>';">
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-slate-300/90 line-clamp-3 leading-relaxed" title="${app.description || ''}">
                  ${app.description || 'Không có mô tả chi tiết cho ứng dụng này.'}
                </p>
              </div>
            </div>

            <!-- 3. Tag & Status -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60 shrink-0">${app.category}</span>
              ${statusBadgeHtml}
            </div>

            <!-- 4. Actions: Cài đặt / Mở & Gỡ cài đặt & Github (Home page) -->
            <div class="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-800/70">
              ${mainActionBtnHtml}
              <a href="${homepage.url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();"
                 title="${homepage.label} của ${app.name}"
                 class="h-8 px-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center justify-center gap-1.5 border border-slate-700/60 transition">
                <i class="${homepage.icon} text-xs"></i>
                <span>${homepage.label}</span>
              </a>
            </div>

          </div>
        `;
      }).join('');
    }

    async function syncStoreCatalog(btn) {
      const origText = btn ? btn.innerHTML : '';
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-slate-400"></i> Đang đồng bộ...';
      }
      try {
        const res = await fetch('/api/modules/apps/catalog/sync', { method: 'POST' });
        const d = await res.json();
        await loadAppCatalog(true);
        renderStoreItems();
      } catch (err) {
        console.error('Lỗi sync catalog:', err);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = origText;
        }
      }
    }

    let currentSetupSchema = null;

    async function installAppFromStore(appId, btn) {
      await openAppSetupModal(appId, btn);
    }

    async function openAppSetupModal(appId, triggerBtn) {
      const app = appCatalogMap[appId];
      if (!app) return;

      const modal = document.getElementById('modal-app-setup');
      if (!modal) {
        // Fallback to direct install if modal missing
        return executeInstall(appId, {}, triggerBtn);
      }

      // Show temporary loading state if trigger button was provided
      let origHtml = '';
      if (triggerBtn) {
        origHtml = triggerBtn.innerHTML;
        triggerBtn.disabled = true;
        triggerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-xs"></i> Đang đọc cấu hình...';
      }

      try {
        const res = await fetch(`/api/modules/apps/${appId}/setup-schema`);
        if (!res.ok) throw new Error('Không thể tải cấu hình cài đặt');
        const schema = await res.json();
        currentSetupSchema = schema;

        // Populate modal UI
        const nameEl = document.getElementById('setup-app-name');
        if (nameEl) nameEl.textContent = `Cài đặt ${schema.name}`;

        const iconBox = document.getElementById('setup-app-icon-box');
        const iconImg = document.getElementById('setup-app-icon');
        if (iconImg) {
          iconImg.src = `https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/${app.logo_id || app.id}.png`;
          iconImg.onerror = function() {
            this.onerror = null;
            if (iconBox) iconBox.innerHTML = `<i class="fa-solid ${app.icon || 'fa-cubes'} text-cyan-400 text-lg"></i>`;
          };
        }

        // Existing data warning & options
        const alertBox = document.getElementById('setup-existing-alert');
        const alertPath = document.getElementById('setup-existing-path');
        if (alertBox) {
          if (schema.has_existing_data) {
            alertBox.classList.remove('hidden');
            if (alertPath) alertPath.textContent = schema.config_path || `/appdata/${schema.id}`;
            const keepRadio = document.querySelector('input[name="setup-data-mode"][value="keep"]');
            if (keepRadio) keepRadio.checked = true;
          } else {
            alertBox.classList.add('hidden');
          }
        }

        // Port input
        const portInput = document.getElementById('setup-input-port');
        if (portInput) {
          portInput.value = schema.default_port || '';
        }

        // Volumes list
        const volContainer = document.getElementById('setup-volumes-list');
        if (volContainer) {
          if (!schema.volumes || schema.volumes.length === 0) {
            volContainer.innerHTML = '<p class="text-slate-500 italic py-1">Không có volume lưu trữ cần ánh xạ.</p>';
          } else {
            volContainer.innerHTML = schema.volumes.map((v, idx) => {
              const parts = v.split(':');
              const host = parts[0] || '';
              const container = parts[1] || '';
              const isConfig = host.startsWith('/appdata') || host.startsWith('/config');
              const badge = isConfig
                ? '<span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono border border-amber-500/20">Config / Database</span>'
                : '<span class="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono border border-cyan-500/20">Data / Storage Pool</span>';

              return `
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] text-slate-400 font-mono truncate max-w-[200px]" title="Đích trong container: ${container}">➜ Container: <strong class="text-slate-200">${container}</strong></span>
                    ${badge}
                  </div>
                  <input type="text" data-vol-index="${idx}" data-vol-container="${container}" value="${host}"
                         class="setup-vol-input w-full bg-slate-900 border border-slate-700/70 rounded-xl px-3 py-2 text-white font-mono text-xs focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition">
                </div>
              `;
            }).join('');
          }
        }

        // Bind Confirm Install Button
        const confirmBtn = document.getElementById('setup-btn-confirm-install');
        if (confirmBtn) {
          confirmBtn.onclick = async () => {
            await doConfirmInstall(schema, confirmBtn);
          };
        }

        const hostRadio = document.querySelector('input[name="setup-target"][value="host"]');
        if (hostRadio) hostRadio.checked = true;
        updateSetupTarget();

        modal.classList.remove('hidden');
      } catch (err) {
        alert('Lỗi khởi tạo cấu hình app: ' + (err.message || err));
      } finally {
        if (triggerBtn) {
          triggerBtn.disabled = false;
          triggerBtn.innerHTML = origHtml;
        }
      }
    }

    // Host (docker run) or OMV Compose (generate a file to create in OMV)
    function getSetupTarget() {
      const r = document.querySelector('input[name="setup-target"]:checked');
      return r ? r.value : 'host';
    }

    function updateSetupTarget() {
      const omv = getSetupTarget() === 'omv';
      const label = document.querySelector('#setup-btn-confirm-install span');
      const icon = document.querySelector('#setup-btn-confirm-install i');
      if (label) label.textContent = omv ? 'Tạo file Compose' : 'Bắt đầu cài đặt';
      if (icon) icon.className = omv ? 'fa-solid fa-layer-group text-xs' : 'fa-solid fa-cloud-arrow-down text-xs';
    }

    function closeAppSetupModal() {
      const modal = document.getElementById('modal-app-setup');
      if (modal) modal.classList.add('hidden');
      currentSetupSchema = null;
    }

    async function doConfirmInstall(schema, btn) {
      if (!schema) return;
      const appId = schema.id;

      // Read configured port
      const portInput = document.getElementById('setup-input-port');
      const targetPort = portInput ? portInput.value.trim() : '';
      let ports = { ...(schema.ports || {}) };
      if (targetPort && schema.default_port) {
        // If container port exists, map chosen host port to original container port
        const originalContainerPort = ports[schema.default_port] || schema.default_port;
        ports = { [targetPort]: String(originalContainerPort) };
      }

      // Read configured volumes
      const volInputs = document.querySelectorAll('.setup-vol-input');
      const volumes = [];
      volInputs.forEach(inp => {
        const h = inp.value.trim();
        const c = inp.getAttribute('data-vol-container') || '';
        if (h && c) {
          volumes.push(`${h}:${c}`);
        }
      });

      // Read wipe data choice
      let wipeExisting = false;
      const wipeRadio = document.querySelector('input[name="setup-data-mode"][value="wipe"]');
      if (wipeRadio && wipeRadio.checked) {
        wipeExisting = true;
      }

      // OMV Compose: nothing is deployed here, we hand over a Compose file for OMV to run
      if (getSetupTarget() === 'omv') {
        try {
          const res = await fetch(`/api/modules/apps/${appId}/compose`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ports: Object.keys(ports).length > 0 ? ports : null,
              volumes: volumes.length > 0 ? volumes : null
            })
          });
          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Không thể tạo file Compose');
          }
          const out = await res.json();
          closeAppSetupModal();
          showComposeResult(out.filename, out.yaml);
        } catch (e) {
          alert('Lỗi tạo file Compose: ' + (e.message || e));
        }
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-xs"></i> Đang triển khai...';
      }

      try {
        await executeInstall(appId, {
          ports: Object.keys(ports).length > 0 ? ports : null,
          volumes: volumes.length > 0 ? volumes : null,
          wipe_existing_data: wipeExisting
        });
        closeAppSetupModal();
        renderStoreItems();
        if (currentTab === 'apps' && typeof loadAppCatalog === 'function') {
          loadAppCatalog(true);
        }
      } catch (e) {
        alert('Lỗi cài đặt: ' + (e.message || e));
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down text-xs"></i> <span>Bắt đầu cài đặt</span>';
        }
      }
    }

    function showComposeResult(filename, yaml) {
      document.getElementById('compose-result-name').textContent = filename;
      document.getElementById('compose-result-yaml').value = yaml;
      document.getElementById('compose-copy-label').textContent = 'Sao chép';
      document.getElementById('modal-compose-result').classList.remove('hidden');
    }

    function closeComposeResult() {
      document.getElementById('modal-compose-result').classList.add('hidden');
    }

    async function copyComposeYaml() {
      const ta = document.getElementById('compose-result-yaml');
      try {
        await navigator.clipboard.writeText(ta.value);
      } catch (e) {
        ta.select(); // clipboard API needs HTTPS: fall back to the legacy copy
        document.execCommand('copy');
      }
      const label = document.getElementById('compose-copy-label');
      label.textContent = 'Đã sao chép';
      setTimeout(() => { label.textContent = 'Sao chép'; }, 1500);
    }

    function downloadComposeYaml() {
      const name = document.getElementById('compose-result-name').textContent || 'docker-compose';
      const blob = new Blob([document.getElementById('compose-result-yaml').value], { type: 'text/yaml' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${name}.yml`;
      a.click();
      URL.revokeObjectURL(a.href);
    }

    async function executeInstall(appId, payload = {}, btn = null) {
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-xs"></i> Đang kéo & chạy...';
      }
      try {
        const res = await fetch(`/api/modules/apps/${appId}/install`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Không thể triển khai container');
        }
        await loadAppCatalog(true);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down text-xs"></i> Cài';
        }
      }
    }

    // APP DETAIL MODAL CONTROLLER
    function openAppDetail(appId) {
      const app = appCatalogMap[appId];
      if (!app) return;

      const appUrl = getAppUrl(app);
      const isNative = Boolean(app.native);
      const targetTab = NATIVE_TAB_MAP[app.id] || app.id;

      // Set icon
      const iconImg = document.getElementById('detail-app-icon');
      const iconBox = document.getElementById('detail-app-icon-box');
      if (iconImg) {
        iconImg.src = `https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/${app.logo_id || app.id}.png`;
        iconImg.alt = app.name;
        iconImg.onerror = function() {
          this.onerror = null;
          if (iconBox) iconBox.innerHTML = `<i class="fa-solid ${app.icon || 'fa-cubes'} text-cyan-400 text-3xl"></i>`;
        };
      }

      // Set titles
      document.getElementById('detail-app-name').textContent = app.name;
      document.getElementById('detail-app-desc').textContent = app.description || 'Không có mô tả chi tiết.';
      document.getElementById('detail-app-category').textContent = app.category || 'General';
      
      const isInstalled = Boolean(app.installed || app.is_running);

      const portEl = document.getElementById('detail-app-port');
      if (portEl) {
        if (app.default_port) {
          portEl.textContent = isInstalled ? `Port ${app.default_port}` : `Port dự kiến ${app.default_port}`;
        } else {
          portEl.textContent = isInstalled ? 'Host / Web UI' : 'Chưa cấu hình port';
        }
      }

      // Set status badge
      const statusBadge = document.getElementById('detail-app-status-badge');
      if (statusBadge) {
        if (app.is_running) {
          statusBadge.className = 'text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5';
          statusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Đang chạy';
        } else if (app.installed) {
          statusBadge.className = 'text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1.5';
          statusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Đã dừng';
        } else {
          statusBadge.className = 'text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5';
          statusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span> Chưa cài';
        }
      }

      // URL links
      const urlTxt = document.getElementById('detail-app-url-txt');
      const urlLink = document.getElementById('detail-app-url-link');
      if (urlTxt && urlLink) {
        const icon = urlLink.querySelector('i');
        if (isInstalled) {
          urlTxt.textContent = appUrl;
          urlLink.href = appUrl;
          urlLink.target = '_blank';
          urlLink.className = 'text-cyan-400 hover:underline truncate max-w-[240px] flex items-center gap-1';
          if (icon) icon.classList.remove('hidden');
        } else {
          urlTxt.textContent = 'Chưa cài đặt';
          urlLink.removeAttribute('href');
          urlLink.removeAttribute('target');
          urlLink.className = 'text-slate-500 italic truncate max-w-[240px] flex items-center gap-1 cursor-default select-none';
          if (icon) icon.classList.add('hidden');
        }
      }

      // Docker Image & Container
      const imgEl = document.getElementById('detail-app-image');
      if (imgEl) imgEl.textContent = app.image || (app.protected ? 'Dịch vụ hệ thống' : 'Dịch vụ NAS');

      const cEl = document.getElementById('detail-app-container');
      if (cEl) {
        if (isInstalled) {
          cEl.textContent = app.container_name || app.id;
          cEl.className = 'text-slate-200 truncate max-w-[240px]';
        } else {
          cEl.textContent = `${app.container_name || app.id} (chưa tạo)`;
          cEl.className = 'text-slate-500 italic truncate max-w-[240px]';
        }
      }

      // Actions
      const actionsEl = document.getElementById('detail-app-actions');
      if (actionsEl) {
        let html = '';

        if (app.installed || app.is_running) {
          html += `
            <button onclick="closeAppDetail(); openAppDirect('${app.id}');" 
                    title="Mở ứng dụng"
                    class="flex-1 h-10 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/30 whitespace-nowrap">
              <i class="fa-solid fa-arrow-up-right-from-square text-xs"></i>
              <span>Mở</span>
            </button>
          `;

          if (COMPOSE_FILE_UUIDS[app.id] || app.compose_uuid || app.installed) {
            html += `
              <button onclick="openComposeEdit('${app.id}', '${app.compose_uuid || ''}'); closeAppDetail();" 
                      title="Sửa cấu hình Docker Compose trên OMV"
                      class="h-10 px-3 bg-slate-800 hover:bg-slate-700 text-cyan-400
                             hover:text-cyan-300 rounded-xl transition flex items-center justify-center
                             gap-1.5 border border-slate-700/60 shadow-sm text-xs font-semibold">
                <i class="fa-solid fa-sliders text-xs"></i>
                <span>Config</span>
              </button>
            `;
          }

          const canManage = app.manageable !== false && !app.protected;
          if (canManage) {
            if (app.is_running) {
              html += `
                <button onclick="controlApp('${app.id}', 'restart'); closeAppDetail();" 
                        title="Khởi động lại ứng dụng"
                        class="w-10 h-10 shrink-0 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl transition flex items-center justify-center border border-slate-700/60 shadow-sm">
                  <i class="fa-solid fa-rotate text-sm"></i>
                </button>
                <button onclick="controlApp('${app.id}', 'stop'); closeAppDetail();" 
                        title="Dừng ứng dụng"
                        class="w-10 h-10 shrink-0 bg-slate-800 hover:bg-slate-700 text-amber-400 hover:text-amber-300 rounded-xl transition flex items-center justify-center border border-slate-700/60 shadow-sm">
                  <i class="fa-solid fa-stop text-sm"></i>
                </button>
              `;
            } else {
              html += `
                <button onclick="controlApp('${app.id}', 'start'); closeAppDetail();" 
                        title="Khởi chạy ứng dụng"
                        class="w-10 h-10 shrink-0 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded-xl transition flex items-center justify-center border border-emerald-500/30 shadow-sm">
                  <i class="fa-solid fa-play text-sm"></i>
                </button>
              `;
            }

            html += `
              <button onclick="closeAppDetail(); confirmUninstall('${app.id}', '${app.name}');" 
                      title="Gỡ cài đặt ứng dụng"
                      class="w-10 h-10 shrink-0 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 rounded-xl transition flex items-center justify-center border border-rose-500/30 shadow-sm">
                <i class="fa-solid fa-trash-can text-sm"></i>
              </button>
            `;
          }
        } else {
          html += `
            <button onclick="closeAppDetail(); installAppFromStore('${app.id}', null);" 
                    class="flex-1 h-10 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/30 whitespace-nowrap">
              <i class="fa-solid fa-cloud-arrow-down text-sm"></i>
              <span>Cài đặt ứng dụng</span>
            </button>
          `;
        }

        actionsEl.innerHTML = html;
      }

      document.getElementById('modal-app-detail').classList.remove('hidden');
    }

    function closeAppDetail() {
      const modal = document.getElementById('modal-app-detail');
      if (modal) modal.classList.add('hidden');
    }

    function openAppDirect(appId) {
      const app = appCatalogMap[appId];
      if (!app) return;
      const appUrl = getAppUrl(app);

      // Visual feedback: show spinner briefly on the clicked card
      const spinner = document.getElementById(`launcher-spinner-${appId}`);
      if (spinner) {
        spinner.classList.remove('hidden');
        setTimeout(() => spinner.classList.add('hidden'), 1500);
      }

      if (!app.is_running && app.installed && app.manageable !== false) {
        controlApp(appId, 'start').then(() => {
          setTimeout(() => window.open(appUrl, '_blank', 'noopener,noreferrer'), 1200);
        });
      } else {
        window.open(appUrl, '_blank', 'noopener,noreferrer');
      }
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('#app-context-menu')) {
        closeContextMenu();
      }
    });
    window.addEventListener('scroll', closeContextMenu, true);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeContextMenu();
        closeAppDetail();
        closeAppSetupModal();
        closeUninstallModal();
      }
    });

    let appCatalogCache = null;
    let storeCatalogCache = null;

