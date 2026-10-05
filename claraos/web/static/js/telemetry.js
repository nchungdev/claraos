// --- Telemetry & Hardware Inspection ---
let currentDisksData = [];

    function openDisksModal() {
      renderDisksModal();
      const m = document.getElementById('modal-disks');
      if (m) m.classList.remove('hidden');
    }

    function closeDisksModal() {
      const m = document.getElementById('modal-disks');
      if (m) m.classList.add('hidden');
    }

    function renderDisksModal() {
      const list = document.getElementById('disks-modal-list');
      if (!list) return;

      if (!currentDisksData || currentDisksData.length === 0) {
        list.innerHTML = '<div class="py-8 text-center text-slate-500 text-sm">Đang tải dữ liệu ổ đĩa...</div>';
        return;
      }

      list.innerHTML = currentDisksData.map(d => {
        const pct = Math.round(d.percent);
        let barColor = 'bg-cyan-500';
        let badgeColor = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
        let icon = 'fa-hard-drive';

        if (d.type === 'SSD') {
          badgeColor = 'bg-purple-500/10 text-purple-400 border-purple-500/20';
          icon = 'fa-microchip';
        } else if (d.type === 'Pool') {
          badgeColor = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
          icon = 'fa-layer-group';
        }

        if (pct >= 95) {
          barColor = 'bg-rose-500';
        } else if (pct >= 85) {
          barColor = 'bg-amber-500';
        }

        return `
          <div class="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60 hover:border-slate-600 transition flex flex-col gap-2.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700/50 flex items-center justify-center text-slate-300">
                  <i class="fa-solid ${icon} text-xs"></i>
                </div>
                <div>
                  <div class="text-sm font-bold text-white flex items-center gap-2">
                    ${d.name}
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border ${badgeColor}">${d.type}</span>
                  </div>
                  <div class="text-[11px] font-mono text-slate-400">${d.path}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xs font-mono font-semibold text-white">${d.used_human} / ${d.total_human}</div>
                <div class="text-[10px] font-mono text-slate-400">Còn trống: <span class="text-emerald-400 font-semibold">${d.free_human}</span></div>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="space-y-1">
              <div class="flex justify-between text-[10px] font-mono text-slate-400">
                <span>Đã sử dụng</span>
                <span class="${pct >= 90 ? 'text-rose-400 font-bold' : ''}">${pct}%</span>
              </div>
              <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/40">
                <div class="${barColor} h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    const NATIVE_TAB_MAP = {
      'agents': 'agents',
      'settings': 'settings'
    };

    const APP_SHELLS = {
      apps: {
        title: 'ClaraOS',
        subtitle: 'AI Homelab OS',
        icon: 'fa-brain',
        iconGradient: 'from-purple-600 to-indigo-500 shadow-purple-500/30',
        docTitle: 'ClaraOS - The AI-Native Homelab Operating System',
        headerTitle: 'Ứng dụng & Dịch vụ',
        badgeText: 'Clara Core Active',
        badgeClass: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
        navHtml: `
          <div class="px-3 pt-2 pb-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Hệ thống</div>
          <a href="#apps" onclick="switchTab('apps'); return false;" data-tab="apps" class="nav-item active flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-white bg-slate-800/80 transition">
            <i class="fa-solid fa-shapes text-cyan-400 w-5 text-center"></i>
            <span>Ứng dụng</span>
          </a>
          <a href="#store" onclick="switchTab('store'); return false;" data-tab="store" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-bag-shopping text-cyan-400 w-5 text-center"></i>
            <span>App Store</span>
          </a>
          <a href="#settings" onclick="switchTab('settings'); return false;" data-tab="settings" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-sliders text-amber-400 w-5 text-center"></i>
            <span>Cài đặt</span>
          </a>
        `,
        headerActionsHtml: `
          <button onclick="refreshCurrentTab()" class="px-3.5 py-1.5 text-xs font-medium rounded-xl glass-panel hover:bg-slate-700/50 text-slate-300 transition flex items-center gap-1.5">
            <i class="fa-solid fa-rotate text-slate-400"></i> Làm mới
          </button>
        `
      },
      store: {
        title: 'ClaraOS',
        subtitle: 'AI Homelab OS',
        icon: 'fa-bag-shopping',
        iconGradient: 'from-cyan-600 to-blue-500 shadow-cyan-500/30',
        docTitle: 'App Store - ClaraOS',
        headerTitle: 'App Store',
        badgeText: '450 Apps',
        badgeClass: 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-mono',
        navHtml: `
          <div class="px-3 pt-2 pb-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Hệ thống</div>
          <a href="#apps" onclick="switchTab('apps'); return false;" data-tab="apps" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-shapes text-cyan-400 w-5 text-center"></i>
            <span>Ứng dụng</span>
          </a>
          <a href="#store" onclick="switchTab('store'); return false;" data-tab="store" class="nav-item active flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-white bg-slate-800/80 transition">
            <i class="fa-solid fa-bag-shopping text-cyan-400 w-5 text-center"></i>
            <span>App Store</span>
          </a>
          <a href="#settings" onclick="switchTab('settings'); return false;" data-tab="settings" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-sliders text-amber-400 w-5 text-center"></i>
            <span>Cài đặt</span>
          </a>
        `,
        headerActionsHtml: `
          <div class="flex items-center gap-2">
            <div class="relative w-40 sm:w-56 md:w-64">
              <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
              <input type="text" id="store-search-input" oninput="filterStoreCatalog()" placeholder="Tìm kiếm ứng dụng, image..."
                     class="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition shadow-inner">
            </div>
            <button onclick="syncStoreCatalog(this)" class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition flex items-center gap-1.5 shrink-0 shadow-sm" title="Đồng bộ 450+ ứng dụng từ cộng đồng">
              <i class="fa-solid fa-arrows-rotate text-xs"></i>
              <span class="hidden sm:inline">Đồng bộ</span>
            </button>
          </div>
        `
      },
      agents: {
        title: 'Agent Studio',
        subtitle: 'Autonomous AI Agents',
        icon: 'fa-robot',
        iconGradient: 'from-purple-600 to-indigo-500 shadow-purple-500/30',
        docTitle: 'Agent Studio - ClaraOS',
        headerTitle: 'Clara AI Agent Studio',
        badgeText: 'Hub Active',
        badgeClass: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
        navHtml: `
          <a href="#apps" onclick="switchTab('apps'); return false;" class="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition mb-3 border border-slate-800">
            <i class="fa-solid fa-arrow-left text-purple-400"></i>
            <span>← Quay về ClaraOS</span>
          </a>
          <div class="px-3 pt-2 pb-1 text-[11px] font-semibold text-purple-400 uppercase tracking-wider">Agent Studio</div>
          <a href="#console" class="nav-item active flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-200 transition">
            <i class="fa-solid fa-terminal text-purple-400 w-5 text-center"></i>
            <span>Coding Console</span>
          </a>
          <a href="#antigravity" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-microchip text-purple-400 w-5 text-center"></i>
            <span>Antigravity (AGY)</span>
          </a>
          <a href="#claude" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition">
            <i class="fa-solid fa-brain text-purple-400 w-5 text-center"></i>
            <span>Claude Code</span>
          </a>
        `,
        headerActionsHtml: `
          <button onclick="document.getElementById('agent-console').innerHTML='<div class=\\'text-purple-400\\'>Console cleared. Sẵn sàng nhận lệnh mới.</div>';" class="px-3 py-1.5 text-xs font-medium rounded-xl glass-panel hover:bg-slate-700/50 text-slate-300 transition flex items-center gap-1.5">
            <i class="fa-solid fa-trash-can text-slate-400"></i> Xóa Console
          </button>
          <button onclick="switchTab('apps')" class="px-3 py-1.5 text-xs font-medium rounded-xl glass-panel hover:bg-slate-700/50 text-slate-300 transition flex items-center gap-1.5">
            <i class="fa-solid fa-house text-slate-400"></i> OS Home
          </button>
        `
      },
      settings: {
        title: 'Cài đặt Hệ thống',
        subtitle: 'ClaraOS Configuration',
        icon: 'fa-sliders',
        iconGradient: 'from-amber-600 to-orange-500 shadow-amber-500/30',
        docTitle: 'Cài đặt Hệ thống - ClaraOS',
        headerTitle: 'Cài đặt Hệ thống',
        badgeText: 'Config Mode',
        badgeClass: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
        navHtml: `
          <a href="#apps" onclick="switchTab('apps'); return false;" class="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition mb-3 border border-slate-800">
            <i class="fa-solid fa-arrow-left text-amber-400"></i>
            <span>← Quay về ClaraOS</span>
          </a>
          <div class="px-3 pt-2 pb-1 text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Cấu hình Hệ thống</div>
          <a href="#modules" class="nav-item active flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-200 transition">
            <i class="fa-solid fa-cubes text-amber-400 w-5 text-center"></i>
            <span>Quản lý Modules</span>
          </a>
        `,
        headerActionsHtml: `
          <button onclick="switchTab('apps')" class="px-3 py-1.5 text-xs font-medium rounded-xl glass-panel hover:bg-slate-700/50 text-slate-300 transition flex items-center gap-1.5">
            <i class="fa-solid fa-house text-slate-400"></i> OS Home
          </button>
        `
      }
    };


    async function updateSystemStatus() {
      try {
        const res = await fetch('/api/system/status');
        const d = await res.json();
        const uptimeMin = Math.floor(d.uptime_seconds / 60);
        document.getElementById('sys-uptime').textContent = `${Math.floor(uptimeMin/60)}h ${uptimeMin%60}m`;
        document.getElementById('sys-cpu-txt').textContent = `${Math.round(d.cpu_percent)}%`;
        document.getElementById('sys-ram-txt').textContent = `${d.memory.used_gb}/${d.memory.total_gb}GB (${Math.round(d.memory.percent)}%)`;
        document.getElementById('sys-ram-bar').style.width = `${d.memory.percent}%`;

        if (d.disk) {
          const usedStr = d.disk.used_human || `${d.disk.used_gb}GB`;
          const totalStr = d.disk.total_human || `${d.disk.total_gb}GB`;
          const freeStr = d.disk.free_human || `${d.disk.free_gb}GB`;
          document.getElementById('sys-disk-txt').textContent = `${usedStr}/${totalStr} (${Math.round(d.disk.percent)}%)`;
          document.getElementById('sys-disk-free').textContent = freeStr;
          
          const diskBar = document.getElementById('sys-disk-bar');
          if (diskBar) {
            diskBar.style.width = `${d.disk.percent}%`;
            if (d.disk.percent >= 95) {
              diskBar.className = 'bg-rose-500 h-1.5 rounded-full transition-all duration-300';
            } else if (d.disk.percent >= 85) {
              diskBar.className = 'bg-amber-500 h-1.5 rounded-full transition-all duration-300';
            } else {
              diskBar.className = 'bg-cyan-500 h-1.5 rounded-full transition-all duration-300';
            }
          }
        }

        if (d.disks && d.disks.length > 0) {
          currentDisksData = d.disks;
          const badge = document.getElementById('sys-disks-count-badge');
          if (badge) badge.textContent = `${d.disks.length} ổ`;
          const modalCount = document.getElementById('disks-modal-count');
          if (modalCount) modalCount.textContent = `${d.disks.length} ổ đĩa`;
          
          const modal = document.getElementById('modal-disks');
          if (modal && !modal.classList.contains('hidden')) {
            renderDisksModal();
          }
        }
      } catch (e) {}
    }


