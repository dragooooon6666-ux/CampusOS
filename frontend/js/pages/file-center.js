/**
 * 文件中心 v2 — 分类筛选 + 详情面板 + 右键菜单 + 批量操作
 */
import { api, toast } from '../api.js';

const CATS = {
  "活动全流程": ["策划案","方案","议程","新闻稿","活动总结","会议纪要"],
  "办公文书": ["通知","申请书","证明","发言稿","述职报告","报告"],
  "个人信息": ["简历","作业","论文","笔记"],
  "数据与表单": ["统计表","签到表","预算表","物资清单","通讯录","排班表","收集表"],
  "媒体文件": ["图片","视频"],
  "其他分类": ["其他文档","其他表格","Word文档","Excel表格","PDF文档","PPT演示","纯文本","压缩包","其他文件"],
};

const ALL_TYPES = Object.values(CATS).flat();
const CAT_ICON = {"活动全流程":"🎯","办公文书":"📋","个人信息":"👤","数据与表单":"📊","媒体文件":"🎬","其他分类":"📁"};
const FICON = {'.docx':'📄','.doc':'📄','.pdf':'📑','.xlsx':'📊','.xls':'📊','.pptx':'📽️','.txt':'📝','.md':'📝','.mp4':'🎬','.zip':'📦','.jpg':'🖼️','.png':'🖼️'};

let files=[], projects=[], orgs=[], selected=new Set(), activeFile=null, filtered=[];

export async function render(el) {
  [files, projects, orgs] = await Promise.all([
    api.get('/api/files?limit=50').catch(()=>[]),
    api.get('/api/projects').catch(()=>[]),
    api.get('/api/orgs').catch(()=>[]),
  ]);
  filtered = files;

  el.innerHTML = `
<div class="fc-root">
  <div class="fc-left">
    <h3 style="margin-bottom:12px">文档分类</h3>
    <div id="catTree"></div>
  </div>
  <div class="fc-mid">
    <div class="fc-bar">
      <input class="fc-search" id="fcSearch" placeholder="搜索文件名...">
      <label class="fc-cb-all"><input type="checkbox" id="checkAll"> 全选</label>
      <span class="fc-batch" id="batchBar" style="display:none">
        已选 <b id="batchN">0</b> 个
        <button id="btnBatchLink">📎 关联</button>
        <button id="btnBatchDel" class="danger">🗑️ 删除</button>
      </span>
      <button id="btnScan">🔄 扫描</button>
    </div>
    <div class="dropzone" id="dropZone">
      <div class="dz-inner">
        <span style="font-size:2rem">📥</span>
        <span style="font-weight:600;font-size:0.9375rem">拖拽文件到此处上传</span>
        <span style="font-size:0.8125rem;color:var(--muted)">或点击选择文件 · 支持批量上传 · 自动 AI 归档</span>
      </div>
      <input type="file" id="fileInput" multiple style="display:none" accept=".docx,.doc,.pdf,.xlsx,.xls,.csv,.pptx,.ppt,.txt,.md,.jpg,.jpeg,.png,.gif,.mp4,.zip">
    </div>
    <div class="upload-queue" id="uploadQueue"></div>
    <div id="fileList" class="flist"></div>
  </div>
  <div class="fc-right" id="detailPanel" style="display:none">
    <div id="detailInner"></div>
  </div>
</div>
<style>
  .fc-root{display:flex;height:calc(100vh - 80px);gap:0}
  .fc-left{width:190px;flex-shrink:0;overflow-y:auto;padding-right:16px;border-right:1px solid var(--border)}
  .fc-mid{flex:1;overflow-y:auto;padding:0 20px;min-width:0}
  .fc-right{width:280px;flex-shrink:0;border-left:1px solid var(--border);overflow-y:auto;animation:slideR 250ms var(--ease-out)}
  @keyframes slideR{from{transform:translateX(20px);opacity:0}to{transform:translateX(0);opacity:1}}
  .fc-bar{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
  .fc-search{padding:7px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.875rem;font-family:inherit;background:var(--bg);color:var(--ink);width:180px}
  .fc-cb-all{font-size:0.75rem;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;user-select:none;white-space:nowrap}
  .fc-batch{font-size:0.8125rem;display:flex;align-items:center;gap:6px;animation:fadeDown 200ms ease}
  @keyframes fadeDown{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
  .fc-batch button{padding:5px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.75rem;font-family:inherit}
  .fc-batch button:hover{background:var(--surface)}
  .fc-batch button.danger{color:var(--error);border-color:var(--error)}
  #btnScan{padding:7px 14px;border:1px solid var(--border);border-radius:8px;background:var(--bg);cursor:pointer;font-size:0.8125rem;font-family:inherit;margin-left:auto}
  .dropzone{border:2px dashed var(--border);border-radius:12px;padding:28px;text-align:center;cursor:pointer;transition:border-color 200ms ease,background 200ms ease;margin-bottom:16px}
  .dropzone:hover,.dropzone.drag-over{border-color:var(--primary);background:oklch(0.55 0.18 255 / 0.04)}
  .dz-inner{display:flex;flex-direction:column;align-items:center;gap:8px}
  .upload-queue{display:flex;flex-direction:column;gap:6px;margin-bottom:12px}
  .upload-bar{padding:8px 14px;border-radius:8px;background:oklch(0.97 0.03 255);color:var(--primary);font-size:0.8125rem;font-weight:500;animation:fadeDown 200ms ease;display:flex;align-items:center;gap:8px}
  .ub-icon{flex-shrink:0;font-size:1rem}
  .ctxmenu{position:fixed;background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:6px;box-shadow:0 8px 30px oklch(0 0 0/0.12);z-index:500;min-width:160px;animation:popIn 150ms var(--ease-out)}
  @keyframes popIn{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}
  .cmi{padding:8px 14px;border-radius:6px;cursor:pointer;font-size:0.8125rem;display:flex;align-items:center;gap:8px}
  .cmi:hover{background:var(--surface)}
  .flist{display:flex;flex-direction:column;gap:2px}
  .frow{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;cursor:pointer;transition:background 150ms ease;animation:fadeIn 0.3s var(--ease-out) both}
  @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
  .frow:hover{background:var(--surface)}
  .frow.sel{background:oklch(0.55 0.18 255 / 0.08)}
  .frow .fi{font-size:1.25rem;flex-shrink:0}
  .frow .fn{font-size:0.875rem;font-weight:500;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .frow .ft{font-size:0.75rem;padding:2px 8px;border-radius:10px;background:oklch(0.97 0.03 255);color:var(--primary);font-weight:500;flex-shrink:0}
  .frow .fd{font-size:0.75rem;color:var(--muted);flex-shrink:0}
  .frow .fs{font-size:0.75rem;color:var(--muted);flex-shrink:0;min-width:45px;text-align:right}
  .detail-inner{padding:20px}
  .detail-inner h3{font-size:1rem;margin-bottom:16px;word-break:break-all}
  .df{margin-bottom:12px}
  .df .dfl{font-size:0.6875rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em}
  .df .dfv{font-size:0.875rem;margin-top:2px}
  .da{display:flex;flex-direction:column;gap:8px;margin-top:20px;padding-top:16px;border-top:1px solid var(--border)}
  .da button{width:100%;padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.8125rem;font-family:inherit;text-align:left}
  .da button:hover{background:var(--surface)}
  .da .danger{color:var(--error);border-color:var(--error)}
  /* Tree */
  .ct-item{margin-bottom:2px}
  .ct-name{padding:7px 10px;border-radius:6px;cursor:pointer;font-size:0.875rem;font-weight:500;display:flex;align-items:center;gap:6px;transition:background 150ms ease;user-select:none}
  .ct-name:hover{background:oklch(0.55 0.18 255/0.06)}
  .ct-name.on{background:oklch(0.55 0.18 255/0.12);color:var(--primary)}
  .ct-sub{margin-left:18px;max-height:0;overflow:hidden;transition:max-height 0.3s var(--ease-out)}
  .ct-sub.open{max-height:400px}
  .ct-sub div{padding:4px 10px;border-radius:4px;cursor:pointer;font-size:0.8125rem;color:var(--muted)}
  .ct-sub div:hover{background:oklch(0.55 0.18 255/0.04);color:var(--ink)}
  .ct-sub div.on{color:var(--primary);font-weight:500}
  .ct-all{padding:7px 10px;border-radius:6px;cursor:pointer;font-size:0.875rem;font-weight:500;margin-bottom:6px}
  .ct-all:hover{background:oklch(0.55 0.18 255/0.06)}
  .ct-all.on{background:oklch(0.55 0.18 255/0.12);color:var(--primary)}
</style>`;

  buildTree();
  renderList();
  bindEvents();
}

function buildTree(){
  const tree = document.getElementById('catTree');
  const all = ce('div',{className:'ct-all on',textContent:'📁 全部文件'});
  all.onclick = ()=>{ clearSel(); filtered=files; renderList(); };
  tree.appendChild(all);

  for(const [cat,types] of Object.entries(CATS)){
    const div = ce('div',{className:'ct-item'});
    const name = ce('div',{className:'ct-name',innerHTML:`${CAT_ICON[cat]} ${cat}`});
    const sub = ce('div',{className:'ct-sub'});
    types.forEach(t=>{
      const s = ce('div',{textContent:t});
      s.onclick = ()=>{ clearSel(); filtered=files.filter(f=>f.doc_type===t); renderList(); };
      sub.appendChild(s);
    });
    name.onclick = ()=>{
      sub.classList.toggle('open');
      clearSel(); filtered=files.filter(f=>types.includes(f.doc_type)); renderList();
    };
    div.appendChild(name); div.appendChild(sub); tree.appendChild(div);
  }
}

function clearSel(){ selected.clear(); updateBatch(); hideDetail(); }
function updateBatch(){
  document.getElementById('batchBar').style.display = selected.size?'flex':'none';
  document.getElementById('batchN').textContent = selected.size;
}

function renderList(){
  const list = document.getElementById('fileList');
  if(!filtered.length){ list.innerHTML='<div style="text-align:center;padding:60px;color:var(--muted)">暂无文件</div>'; return; }
  list.innerHTML = filtered.map((f,i)=>{
    const icon = FICON[f.extension]||'📎';
    const size = f.size_bytes>1024*1024?`${(f.size_bytes/1024/1024).toFixed(1)}MB`:Math.round(f.size_bytes/1024)+'KB';
    const sel = selected.has(f.id)?' sel':'';
    return `<div class="frow${sel}" data-id="${f.id}" style="animation-delay:${i*25}ms">
      <input type="checkbox" class="fcb" data-id="${f.id}" ${sel?'checked':''}>
      <span class="fi">${icon}</span>
      <span class="fn" title="${f.original_name}">${f.title||f.original_name}</span>
      <span class="ft">${f.doc_type}</span>
      <span class="fd">${f.doc_date||''}</span>
      <span class="fs">${size}</span>
    </div>`;
  }).join('');
  updateBatch();
}

async function showDetail(f){
  activeFile = f;
  const panel = document.getElementById('detailPanel');
  panel.style.display = 'block';

  // 查询该文件已关联的项目
  let linkedProjects = [];
  try{
    const allProjects = await api.get('/api/projects');
    for(const p of allProjects){
      const detail = await api.get(`/api/projects/${p.id}`);
      if(detail.files?.some(x=>x.id===f.id)) linkedProjects.push(p);
    }
  }catch{}

  const linkSection = linkedProjects.length
    ? `<div style="font-size:0.8125rem;color:var(--muted);margin-bottom:8px">已关联：${linkedProjects.map(p=>`
        <span style="display:inline-flex;align-items:center;gap:4px;background:oklch(0.97 0.03 255);padding:2px 8px;border-radius:6px;margin:2px">
          📋 ${p.name}
          <span class="unlink-badge" data-pid="${p.id}" style="cursor:pointer;color:var(--error);font-weight:700" title="取消关联">×</span>
        </span>`).join('')}
      </div>`
    : '';

  const projectOptions = projects.length
    ? projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join('')
    : '<option value="">暂无项目</option>';

  document.getElementById('detailInner').innerHTML = `
    <div class="detail-inner">
      <h3>${f.title||f.original_name}</h3>
      <div class="df"><div class="dfl">原始文件名</div><div class="dfv">${f.original_name}</div></div>
      <div class="df"><div class="dfl">类型</div><div class="dfv">${f.doc_type}</div></div>
      <div class="df"><div class="dfl">日期</div><div class="dfv">${f.doc_date||'—'}</div></div>
      <div class="df"><div class="dfl">大小</div><div class="dfv">${f.size_bytes>1024*1024?(f.size_bytes/1024/1024).toFixed(1)+'MB':Math.round(f.size_bytes/1024)+'KB'}</div></div>
      <div class="da">
        ${linkSection}
        <div style="display:flex;gap:8px">
          <select id="selProject" style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink)">${projectOptions}</select>
          <button id="btnLinkNow" style="padding:8px 14px;border-radius:8px;border:none;background:var(--primary);color:#fff;cursor:pointer;font-size:0.8125rem;font-family:inherit;font-weight:500;white-space:nowrap">关联</button>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <span style="font-size:0.75rem;color:var(--muted);white-space:nowrap">改分类</span>
          <select id="selReclass" style="flex:1;padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.75rem;font-family:inherit;background:var(--bg);color:var(--ink)">
            ${ALL_TYPES.map(t=>`<option value="${t}" ${t===f.doc_type?'selected':''}>${t}</option>`).join('')}
          </select>
          <button id="btnReclass" style="padding:6px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.75rem;font-family:inherit;white-space:nowrap">更新</button>
        </div>
        <button id="btnOpenFile" style="width:100%;padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.8125rem;font-family:inherit;text-align:left">📂 打开文件位置</button>
        <button class="danger act-del">🗑️ 删除文件</button>
      </div>
    </div>`;

  // 关联按钮
  document.getElementById('btnLinkNow').onclick = async ()=>{
    const sel = document.getElementById('selProject');
    if(!sel.value)return;
    const pid = +sel.value;
    await api.post(`/api/projects/${pid}/link-file`,{file_id:f.id});
    // 刷新详情
    const updated = files.find(x=>x.id===f.id);
    if(updated) showDetail(updated);
  };

  // 取消关联
  document.querySelectorAll('.unlink-badge').forEach(badge=>{
    badge.onclick = async (e)=>{
      e.stopPropagation();
      const pid = +badge.dataset.pid;
      await api.delete(`/api/projects/${pid}/link-file/${f.id}`);
      const updated = files.find(x=>x.id===f.id);
      if(updated) showDetail(updated);
    };
  });

  // 打开文件位置
  document.getElementById('btnOpenFile').onclick = async ()=>{
    try {
      const resp = await api.get(`/api/files/${f.id}`);
      const path = resp.stored_path || resp.original_path;
      if (path) {
        // 通过后端打开资源管理器
        window.open(`/api/files/${f.id}/open`, '_blank');
      }
    } catch {}
  };

  // 手动改分类
  document.getElementById('btnReclass').onclick = async ()=>{
    const newType = document.getElementById('selReclass').value;
    try {
      await api.put(`/api/files/${f.id}`, {doc_type: newType});
      toast(`已更新为 ${newType}`, 'success');
      files = await api.get('/api/files?limit=50');
      filtered = files;
      renderList();
      // 刷新详情
      const updated = files.find(x=>x.id===f.id);
      if(updated) showDetail(updated);
    } catch(e) { toast('更新失败','error'); }
  };

  panel.querySelector('.act-del').onclick = ()=>confirmDel([f.id]);
}
function hideDetail(){ document.getElementById('detailPanel').style.display='none'; activeFile=null; }

// ── Events ──
function bindEvents(){
  // ── 拖拽上传 ──
  const dz = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');

  dz.addEventListener('click', ()=>fileInput.click());
  dz.addEventListener('dragover', e=>{e.preventDefault();dz.classList.add('drag-over');});
  dz.addEventListener('dragleave', ()=>{dz.classList.remove('drag-over');});
  dz.addEventListener('drop', async e=>{
    e.preventDefault();
    dz.classList.remove('drag-over');
    if(e.dataTransfer.files.length) await doUpload(e.dataTransfer.files);
  });
  fileInput.addEventListener('change', async ()=>{
    if(fileInput.files.length) await doUpload(fileInput.files);
    fileInput.value = '';
  });

  let batchId = 0;

  async function doUpload(fileList){
    const bid = ++batchId;
    const queue = document.getElementById('uploadQueue');

    // 创建此批次的进度条
    const bar = document.createElement('div');
    bar.className = 'upload-bar';
    bar.id = 'batch' + bid;
    bar.innerHTML = `<span class="ub-icon">⏳</span> <span class="ub-msg">分析 ${fileList.length} 个文件...</span>`;
    queue.prepend(bar);

    const form = new FormData();
    for(const f of fileList) form.append('files', f);

    try{
      const resp = await fetch('/api/files/upload',{method:'POST',body:form});
      const data = await resp.json();
      if(data.saved > 0){
        bar.innerHTML = `<span class="ub-icon">✅</span> <span class="ub-msg"><b>${data.saved}</b> 个归档：${data.files.map(f=>f.doc_type+'·'+f.title).slice(0,3).join('，')}${data.files.length>3?'...':''}</span>`;
        const linked = data.files.filter(f=>f.linked_projects?.length);
        if(linked.length) toast(`🔗 ${linked.length} 个文件已自动关联到项目`,'success');
      }else{
        bar.innerHTML = `<span class="ub-icon">⚠️</span> <span class="ub-msg">0 个新文件（重复或无法识别）</span>`;
      }
      files = await api.get('/api/files?limit=50');
      filtered = files;
      renderList();
    }catch(e){
      bar.innerHTML = `<span class="ub-icon">❌</span> <span class="ub-msg">上传失败：${e.message}</span>`;
    }
    // 3秒后淡出
    setTimeout(()=>{ bar.style.opacity='0'; bar.style.transition='opacity 300ms ease'; setTimeout(()=>bar.remove(),300); },4000);
  }

  const list = document.getElementById('fileList');

  // Click row → detail
  list.addEventListener('click', e=>{
    const cb = e.target.closest('.fcb');
    const row = e.target.closest('.frow');
    if(!row)return;
    const id = +row.dataset.id;
    if(cb){ toggleSel(id,row); e.stopPropagation(); return; }
    const f = files.find(x=>x.id===id); if(f)showDetail(f);
  });

  // Check all
  document.getElementById('checkAll').addEventListener('change', function(){
    document.querySelectorAll('.fcb').forEach(cb=>{
      const id=+cb.dataset.id; cb.checked=this.checked;
      if(this.checked)selected.add(id);else selected.delete(id);
      cb.closest('.frow')?.classList.toggle('sel',this.checked);
    });
    updateBatch();
  });

  // Batch
  document.getElementById('btnBatchLink').addEventListener('click', ()=>{
    if(!selected.size)return;
    popupProjects([...selected][0], document.getElementById('btnBatchLink'));
  });
  document.getElementById('btnBatchDel').addEventListener('click', ()=>{
    if(!selected.size)return;
    confirmDel([...selected]);
  });

  // Search
  document.getElementById('fcSearch').addEventListener('input', async e=>{
    const q=e.target.value.trim();
    filtered = q?await api.get(`/api/files?search=${encodeURIComponent(q)}&limit=50`):files;
    renderList();
  });

  // Scan
  document.getElementById('btnScan').addEventListener('click', async ()=>{
    const btn=document.getElementById('btnScan');btn.textContent='⏳ 扫描...';
    await api.post('/api/files/scan');
    files=await api.get('/api/files?limit=50');filtered=files;renderList();
    btn.textContent='🔄 扫描';
  });
}

function toggleSel(id,row){
  selected.has(id)?selected.delete(id):selected.add(id);
  row.classList.toggle('sel',selected.has(id));
  row.querySelector('.fcb').checked = selected.has(id);
  updateBatch();
}

// ── Project picker ──
function popupProjects(fileId, anchor){
  const rect = anchor.getBoundingClientRect();
  const m = ce('div',{className:'ctxmenu',style:`left:${Math.min(rect.left,innerWidth-200)}px;top:${rect.bottom+4}px`});
  m.innerHTML = projects.length
    ? projects.map(p=>`<div class="cmi" data-pid="${p.id}">📋 ${p.name}</div>`).join('')
    : '<div class="cmi" style="color:var(--muted)">暂无项目</div>';
  m.addEventListener('click', async ev=>{
    const item = ev.target.closest('.cmi');
    if(item?.dataset.pid){
      const pid = +item.dataset.pid;
      await api.post(`/api/projects/${pid}/link-file`,{file_id:fileId});
      m.innerHTML='<div class="cmi">✅ 已关联</div>';
      setTimeout(()=>m.remove(),1000);
    }
  });
  document.body.appendChild(m);
  setTimeout(()=>document.addEventListener('click',function c(ev){if(!m.contains(ev.target)){m.remove();document.removeEventListener('click',c);}}),0);
}

// ── Delete confirm ──
function confirmDel(ids){
  const targets = ids.map(id=>files.find(f=>f.id===id)).filter(Boolean);
  const overlay = ce('div',{className:'modal-overlay'});
  overlay.innerHTML = `<div class="modal-box" onclick="event.stopPropagation()">
    <h3>确认删除？</h3>
    <p style="font-size:0.875rem;color:var(--muted)">${targets.map(f=>f.title||f.original_name).join('<br>')}</p>
    <p style="font-size:0.75rem;color:var(--error);margin-top:8px">不可撤销</p>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px">
      <button class="btn-cancel">取消</button>
      <button class="btn-confirm">确认删除</button>
    </div>
  </div>
  <style>
    .modal-overlay{position:fixed;inset:0;background:oklch(0 0 0/0.3);z-index:600;display:flex;align-items:center;justify-content:center;animation:fadeIn 150ms ease}
    .modal-box{background:var(--bg);border-radius:14px;padding:28px;width:400px;max-width:90vw;box-shadow:var(--shadow-modal);animation:modalIn 250ms var(--ease-out)}
    @keyframes modalIn{from{opacity:0;transform:scale(0.96) translateY(8px)}to{opacity:1;transform:scale(1) translateY(0)}}
    .modal-box button{padding:8px 20px;border-radius:8px;font-size:0.875rem;cursor:pointer;font-family:inherit;border:1px solid var(--border);background:var(--bg)}
    .modal-box .btn-confirm{background:var(--error);color:#fff;border:none;font-weight:600}
  </style>`;
  overlay.addEventListener('click', function(e){if(e.target===this)this.remove();});
  overlay.querySelector('.btn-cancel').addEventListener('click',()=>overlay.remove());
  overlay.querySelector('.btn-confirm').addEventListener('click', async ()=>{
    for(const id of ids){
      try{await api.delete(`/api/files/${id}`);selected.delete(id);}catch{}
    }
    overlay.remove();
    files = await api.get('/api/files?limit=50');
    filtered = files;
    renderList();
    hideDetail();
  });
  document.body.appendChild(overlay);
}

// ── Helper ──
function ce(tag, props={}){
  const el=document.createElement(tag);
  for(const[k,v]of Object.entries(props)){
    if(k.startsWith('on'))el.addEventListener(k.slice(2),v);
    else if(k==='style')Object.assign(el.style,v);
    else el[k]=v;
  }
  return el;
}
