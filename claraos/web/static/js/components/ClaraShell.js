/**
 * ClaraOS Clean Architecture - Presentation / Shared Component
 * ClaraShell: Standalone Left Sidebar + Mobile Slide-over Drawer + Topbar
 * Reusable across ClaraOS, DriveSync Pro, Media Organizer, and TorBox Manager.
 */

export class ClaraShell {
  constructor(options = {}) {
    this.options = {
      containerId: options.containerId || 'clara-shell-root',
      appName: options.appName || 'ClaraOS',
      appSubtitle: options.appSubtitle || 'AI Homelab OS',
      appIconHtml: options.appIconHtml || '<i class="fa-solid fa-cube text-cyan-400 text-lg"></i>',
      brandGradient: options.brandGradient || 'from-cyan-500 to-indigo-600',
      activeTab: options.activeTab || '',
      navItems: options.navItems || [],
      onNavClick: options.onNavClick || (() => {}),
      headerActionsHtml: options.headerActionsHtml || '',
      showStorageWidget: options.showStorageWidget !== false,
      onStorageClick: options.onStorageClick || null,
      ...options
    };

    this.isMobileOpen = false;
  }

  mount() {
    const root = document.getElementById(this.options.containerId);
    if (!root) {
      console.warn(`[ClaraShell] Container #${this.options.containerId} not found.`);
      return;
    }

    root.innerHTML = this._generateHtml();
    this._bindEvents();
  }

  _generateHtml() {
    const { appName, appSubtitle, appIconHtml, brandGradient, navItems, activeTab } = this.options;

    const navItemsHtml = navItems.map(item => {
      const isActive = item.id === activeTab;
      const activeClass = isActive 
        ? 'bg-cyan-500/10 text-cyan-400 font-semibold border-l-2 border-cyan-400' 
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 font-medium';
      
      return `
        <button data-tab="${item.id}" class="clara-nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition duration-150 ${activeClass}">
          <div class="flex items-center gap-3">
            <span class="w-5 text-center text-sm shrink-0">${item.iconHtml}</span>
            <span class="truncate">${item.label}</span>
          </div>
          ${item.badge ? `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full ${item.badgeClass || 'bg-slate-800 text-slate-400'}">${item.badge}</span>` : ''}
        </button>
      `;
    }).join('');

    return `
      <!-- Mobile Backdrop Overlay -->
      <div id="clara-sidebar-backdrop" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-30 transition-opacity md:hidden"></div>

      <!-- LEFT SIDEBAR (Slide-over on Mobile) -->
      <aside id="clara-sidebar" class="fixed md:static inset-y-0 left-0 -translate-x-full md:translate-x-0 w-64 min-w-64 glass-panel border-y-0 border-l-0 flex flex-col z-40 transition-transform duration-200 ease-in-out">
        <!-- Brand Header -->
        <div class="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr ${brandGradient} flex items-center justify-center shadow-lg shrink-0">
              ${appIconHtml}
            </div>
            <div class="min-w-0">
              <span class="font-bold text-sm text-white tracking-tight truncate block">${appName}</span>
              <span class="text-[9px] uppercase tracking-wider block font-semibold text-slate-400 -mt-0.5 truncate">${appSubtitle}</span>
            </div>
          </div>
          <button id="clara-mobile-close" class="md:hidden text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition shrink-0 ml-2" title="Đóng menu">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <!-- Navigation Menu -->
        <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider px-3 mb-2">Điều hướng</div>
          ${navItemsHtml}
        </nav>

        <!-- Sidebar Footer / Storage Widget -->
        ${this.options.showStorageWidget ? `
        <div class="p-3 border-t border-slate-800/80">
          <div id="clara-storage-widget" class="glass-panel p-3 rounded-xl border border-slate-700/40 text-xs cursor-pointer hover:border-cyan-500/40 transition group">
            <div class="flex items-center justify-between text-slate-400 mb-1.5">
              <span class="flex items-center gap-1.5 font-medium text-slate-300">
                <i class="fa-solid fa-hard-drive text-cyan-400 text-xs"></i>
                <span>Ổ cứng</span>
              </span>
              <span id="clara-disks-badge" class="text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono group-hover:bg-cyan-500/20 group-hover:text-cyan-300">--</span>
            </div>
            <div class="flex items-center justify-between text-[11px] mb-1">
              <span id="clara-storage-text" class="text-slate-300 font-mono">--/--</span>
              <span id="clara-storage-free" class="text-slate-400 text-[10px]">Trống --</span>
            </div>
            <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div id="clara-storage-bar" class="bg-cyan-500 h-1.5 rounded-full transition-all duration-300" style="width: 0%"></div>
            </div>
          </div>
        </div>
        ` : ''}
      </aside>
    `;
  }

  _bindEvents() {
    // Backdrop click
    const backdrop = document.getElementById('clara-sidebar-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', () => this.toggleMobileSidebar(false));
    }

    // Mobile close button
    const closeBtn = document.getElementById('clara-mobile-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.toggleMobileSidebar(false));
    }

    // Nav item clicks
    const navButtons = document.querySelectorAll('.clara-nav-item');
    navButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tabId = btn.getAttribute('data-tab');
        if (window.innerWidth < 768) {
          this.toggleMobileSidebar(false);
        }
        this.setActiveTab(tabId);
        this.options.onNavClick(tabId);
      });
    });

    // Storage widget click
    if (this.options.showStorageWidget && this.options.onStorageClick) {
      const storageWidget = document.getElementById('clara-storage-widget');
      if (storageWidget) {
        storageWidget.addEventListener('click', () => this.options.onStorageClick());
      }
    }
  }

  toggleMobileSidebar(open) {
    const sidebar = document.getElementById('clara-sidebar');
    const backdrop = document.getElementById('clara-sidebar-backdrop');
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

  setActiveTab(tabId) {
    this.options.activeTab = tabId;
    const navButtons = document.querySelectorAll('.clara-nav-item');
    navButtons.forEach(btn => {
      const currentTab = btn.getAttribute('data-tab');
      if (currentTab === tabId) {
        btn.className = 'clara-nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition duration-150 bg-cyan-500/10 text-cyan-400 font-semibold border-l-2 border-cyan-400';
      } else {
        btn.className = 'clara-nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition duration-150 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 font-medium';
      }
    });
  }

  updateStorageInfo({ text, free, percent, disksCount }) {
    const textEl = document.getElementById('clara-storage-text');
    const freeEl = document.getElementById('clara-storage-free');
    const barEl = document.getElementById('clara-storage-bar');
    const badgeEl = document.getElementById('clara-disks-badge');

    if (textEl && text) textEl.textContent = text;
    if (freeEl && free) freeEl.textContent = `Trống ${free}`;
    if (badgeEl && disksCount !== undefined) badgeEl.textContent = `${disksCount} ổ`;
    if (barEl && percent !== undefined) {
      barEl.style.width = `${Math.min(100, Math.max(0, percent))}%`;
      if (percent >= 95) barEl.className = 'bg-rose-500 h-1.5 rounded-full transition-all duration-300';
      else if (percent >= 85) barEl.className = 'bg-amber-500 h-1.5 rounded-full transition-all duration-300';
      else barEl.className = 'bg-cyan-500 h-1.5 rounded-full transition-all duration-300';
    }
  }
}
