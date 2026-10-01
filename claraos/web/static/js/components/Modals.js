/**
 * ClaraOS Clean Architecture - Presentation Layer
 * Modals & Overlay Components (Multi-Disk Inspector & App Detail)
 */

export class Modals {
  static showDisksModal(disks) {
    let modal = document.getElementById('modal-disks-container');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'modal-disks-container';
      document.body.appendChild(modal);
    }

    if (!disks || disks.length === 0) {
      alert('Không có dữ liệu ổ cứng.');
      return;
    }

    const rowsHtml = disks.map(d => {
      let typeBadge = '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">HDD</span>';
      if (d.type === 'SSD') {
        typeBadge = '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">NVMe SSD</span>';
      } else if (d.type === 'Pool') {
        typeBadge = '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">MergerFS Pool</span>';
      }

      let barColor = 'bg-cyan-500';
      if (d.percent >= 95) barColor = 'bg-rose-500';
      else if (d.percent >= 85) barColor = 'bg-amber-500';

      return `
        <div class="glass-panel p-4 rounded-xl border border-slate-700/50 hover:border-slate-600 transition space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 min-w-0">
              <i class="fa-solid fa-hard-drive text-cyan-400 text-sm"></i>
              <span class="font-bold text-sm text-white truncate">${d.name}</span>
            </div>
            ${typeBadge}
          </div>
          <div class="text-[11px] text-slate-400 font-mono truncate">${d.path} &bull; Phân vùng: ${d.id}</div>
          <div class="space-y-1 pt-1">
            <div class="flex justify-between text-xs font-mono">
              <span class="text-slate-300">${d.used_human} / ${d.total_human}</span>
              <span class="font-bold ${d.percent >= 90 ? 'text-rose-400' : 'text-cyan-400'}">${d.percent}%</span>
            </div>
            <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div class="${barColor} h-full rounded-full transition-all duration-300" style="width: ${d.percent}%"></div>
            </div>
            <div class="text-right text-[10px] text-slate-400">Dung lượng trống khả dụng: <span class="text-emerald-400 font-semibold">${d.free_human}</span></div>
          </div>
        </div>
      `;
    }).join('');

    modal.innerHTML = `
      <div id="modal-disks-backdrop" class="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150">
        <div class="glass-card w-full max-w-xl rounded-2xl border border-slate-700/80 shadow-2xl flex flex-col max-h-[85vh] overflow-hidden" onclick="event.stopPropagation()">
          <div class="p-5 border-b border-slate-800/80 flex items-center justify-between shrink-0">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center">
                <i class="fa-solid fa-server text-sm"></i>
              </div>
              <div>
                <h3 class="font-bold text-base text-white">Quản lý Phân vùng Ổ cứng NAS</h3>
                <span class="text-xs text-slate-400">Chi tiết dung lượng từng ổ cứng vật lý và Storage Pool</span>
              </div>
            </div>
            <button id="modal-disks-close-btn" class="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition flex items-center justify-center">
              <i class="fa-solid fa-xmark text-sm"></i>
            </button>
          </div>
          <div class="p-5 overflow-y-auto space-y-3">
            ${rowsHtml}
          </div>
        </div>
      </div>
    `;

    const close = () => { modal.innerHTML = ''; };
    document.getElementById('modal-disks-backdrop').addEventListener('click', (e) => {
      if (e.target.id === 'modal-disks-backdrop') close();
    });
    document.getElementById('modal-disks-close-btn').addEventListener('click', close);
  }
}
