/**
 * 项目看板 — 卡片网格 + 新建
 */
import { api } from '../api.js';

const STATUS_MAP = {
  active: { label: '进行中', cls: 'badge-active' },
  completed: { label: '已完成', cls: 'badge-done' },
  archived: { label: '已归档', cls: 'badge-prep' },
};

export async function render(el) {
  const projects = await api.get('/api/projects').catch(() => []);

  el.innerHTML = `
<div>
  <div class="db-header"><h1>项目看板</h1><button class="btn-primary" id="btnNewProject">+ 新建项目</button></div>
  <div class="project-grid" id="projectGrid"></div>
</div>
<div id="modalNew" style="display:none;position:fixed;inset:0;background:oklch(0 0 0/0.3);z-index:1000;align-items:center;justify-content:center" onclick="if(event.target===this)this.style.display='none'">
  <div class="modal-create" onclick="event.stopPropagation()">
    <h3 style="margin-bottom:20px">新建项目</h3>
    <div class="form-row">
      <div class="form-g" style="flex:2"><label>项目名称 <span style="color:var(--error)">*</span></label><input id="npName"></div>
      <div class="form-g" style="flex:1"><label>状态</label><select id="npStatus"><option value="active">进行中</option><option value="completed">已完成</option><option value="archived">已归档</option></select></div>
    </div>
    <div class="form-row">
      <div class="form-g" style="flex:1"><label>负责人</label><input id="npLeader"></div>
      <div class="form-g" style="flex:1"><label>开始</label><input type="date" id="npStart"></div>
      <div class="form-g" style="flex:1"><label>结束</label><input type="date" id="npEnd"></div>
    </div>
    <div class="form-g"><label>图标</label><div class="icon-picker" id="iconPicker"></div><input type="hidden" id="npIcon" value="📋"></div>
    <div class="form-g"><label>描述</label><textarea id="npDesc" rows="2"></textarea></div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="document.getElementById('modalNew').style.display='none'">取消</button>
      <button class="btn-primary" id="btnCreate">创建项目</button>
    </div>
  </div>
</div>
<style>
  .db-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
  .db-header h1{font-size:1.5rem}
  .project-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
  .p-card{background:var(--bg);border:1px solid var(--border);border-radius:14px;padding:22px;cursor:pointer;transition:transform 200ms ease,box-shadow 200ms ease}
  .p-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px oklch(0 0 0/0.08)}
  .p-card[data-status="active"]{border-top:4px solid var(--primary)}
  .p-card[data-status="completed"]{border-top:4px solid var(--accent)}
  .p-card[data-status="archived"]{border-top:4px solid oklch(0.55 0.01 255)}
  .pc-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}
  .pc-name{font-weight:650;font-size:1.0625rem}
  .pc-meta{font-size:0.75rem;color:var(--muted);margin-top:4px}
  .pc-stats{font-size:0.75rem;color:var(--muted);margin-top:8px}
  .badge-active{background:oklch(0.55 0.18 255/0.12);color:var(--primary);padding:3px 12px;border-radius:10px;font-size:0.6875rem;font-weight:600}
  .badge-done{background:oklch(0.62 0.16 170/0.12);color:oklch(0.50 0.14 170);padding:3px 12px;border-radius:10px;font-size:0.6875rem;font-weight:600}
  .badge-prep{background:oklch(0.55 0.01 255/0.08);color:var(--muted);padding:3px 12px;border-radius:10px;font-size:0.6875rem;font-weight:600}
  .modal-create{background:var(--bg);border-radius:16px;padding:32px;width:560px;max-width:92vw;box-shadow:var(--shadow-modal);max-height:90vh;overflow-y:auto;animation:modalIn 250ms var(--ease-out)}
  @keyframes modalIn{from{opacity:0;transform:scale(0.96) translateY(8px)}to{opacity:1;transform:scale(1) translateY(0)}}
  .form-row{display:flex;gap:12px;margin-bottom:14px}
  .form-g{margin-bottom:14px}
  .form-g label{display:block;font-size:0.8125rem;font-weight:500;margin-bottom:4px;color:var(--ink)}
  .form-g input,.form-g select,.form-g textarea{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:10px;font-size:0.875rem;font-family:inherit;background:var(--bg);color:var(--ink)}
  .form-g input:focus,.form-g select:focus,.form-g textarea:focus{outline:none;border-color:var(--primary)}
  .icon-picker{display:flex;flex-wrap:wrap;gap:8px}
  .icon-opt{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:1.25rem;border:2px solid transparent;transition:border-color 150ms ease}
  .icon-opt:hover{border-color:var(--border)}
  .icon-opt.sel{border-color:var(--primary);background:oklch(0.55 0.18 255/0.08)}
  .modal-actions{display:flex;gap:12px;justify-content:flex-end;margin-top:20px}
  .modal-actions button{padding:10px 24px;border-radius:10px;font-size:0.875rem;cursor:pointer;font-family:inherit}
  .btn-cancel{background:transparent;color:var(--ink);border:1px solid var(--border)}
  .btn-primary{padding:10px 24px;border-radius:10px;font-size:0.875rem;font-weight:600;border:none;cursor:pointer;background:var(--primary);color:#fff;font-family:inherit;transition:background 150ms ease;white-space:nowrap}
  .btn-primary:hover{background:var(--primary-hover)}
</style>`;

  const grid = document.getElementById('projectGrid');
  renderCards(projects);

  function renderCards(projs) {
    if (!projs.length) { grid.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:60px;color:var(--muted)">还没有项目<br><span style="font-size:0.8125rem">点击右上角「新建项目」开始</span></div>'; return; }
    grid.innerHTML = projs.map(p => {
      const s = STATUS_MAP[p.status] || STATUS_MAP.active;
      return `<div class="p-card" data-id="${p.id}" data-status="${p.status}"><div class="pc-header"><span class="pc-name">${p.icon||'📋'} ${p.name}</span><span class="${s.cls}">${s.label}</span></div><div class="pc-meta">👤 ${p.leader||'—'} | ${p.start_date||'—'} → ${p.end_date||'—'}</div><div class="pc-stats">📄 ${p.file_count||0} 个关联文件</div></div>`;
    }).join('');
  }

  grid.addEventListener('click', e => { const c=e.target.closest('.p-card'); if(c?.dataset.id) window.location.hash='#/project/'+c.dataset.id; });

  const ICONS = ['📋','🎉','🤝','🏆','📚','🎓','💡','🔬','🏀','🎨','🎵','💼','🌟','📅','📝'];
  ICONS.forEach(icon => { const o=document.createElement('span'); o.className='icon-opt'+(icon==='📋'?' sel':''); o.textContent=icon; o.onclick=()=>{document.querySelectorAll('.icon-opt').forEach(x=>x.classList.remove('sel'));o.classList.add('sel');document.getElementById('npIcon').value=icon;}; document.getElementById('iconPicker').appendChild(o); });

  document.getElementById('btnNewProject').addEventListener('click',()=>{document.getElementById('modalNew').style.display='flex';});
  document.getElementById('btnCreate').addEventListener('click',async()=>{
    const n=document.getElementById('npName').value.trim(); if(!n)return alert('请输入项目名称');
    const b=document.getElementById('btnCreate');b.textContent='创建中...';
    const icon = document.getElementById('npIcon').value||'📋';
    await api.post('/api/projects',{name:n,leader:document.getElementById('npLeader').value.trim(),description:document.getElementById('npDesc').value.trim(),status:document.getElementById('npStatus').value,icon,start_date:document.getElementById('npStart').value,end_date:document.getElementById('npEnd').value});
    document.getElementById('modalNew').style.display='none';['npName','npLeader','npDesc','npStart','npEnd'].forEach(id=>document.getElementById(id).value='');b.textContent='创建项目';
    renderCards(await api.get('/api/projects'));
  });
}
