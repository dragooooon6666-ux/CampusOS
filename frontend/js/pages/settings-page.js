/**
 * 设置页 — AI 配置 + 监控源 + 主题
 */
import { api, toast } from '../api.js';

export async function render(el) {
  const [aiConfig, monitorSources, orgs] = await Promise.all([
    api.get('/api/settings/ai').catch(()=>null),
    api.get('/api/monitor-sources').catch(()=>[]),
    api.get('/api/orgs').catch(()=>[]),
  ]);

  el.innerHTML = `
<div class="st-root">
  <h1>设置</h1>

  <!-- AI 配置 -->
  <section class="st-section">
    <h2>AI 模型配置</h2>
    <div class="st-card">
      <div class="st-field">
        <label>活跃模型</label>
        <select id="stProvider">
          ${aiConfig?.providers ? Object.entries(aiConfig.providers).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join('') : ''}
        </select>
      </div>
      <div class="st-field">
        <label>自定义模型名（可选，留空用默认）</label>
        <input id="stCustomModel" placeholder="如 deepseek-chat" value="${aiConfig?.custom_model||''}">
      </div>
      <div id="stKeys"></div>
      <div style="display:flex;gap:12px;margin-top:16px">
        <button id="btnSaveAI">💾 保存 AI 配置</button>
        <button id="btnTestAI">🔌 测试连接</button>
      </div>
      <p id="stAIStatus" style="margin-top:12px;font-size:0.8125rem"></p>
    </div>
  </section>

  <!-- 监控源 -->
  <section class="st-section">
    <h2>文件监控源</h2>
    <div class="st-card">
      <div id="stMonitors"></div>
      <div style="display:flex;gap:8px;margin-top:12px">
        <input id="stNewPath" placeholder="文件夹路径，如 C:\\Users\\...\\Desktop" style="flex:1">
        <button id="btnAddSource">+ 添加</button>
      </div>
    </div>
  </section>

  <!-- 组织架构 -->
  <section class="st-section">
    <h2>组织架构</h2>
    <div class="st-card">
      <div id="stOrgs"></div>
      <div style="display:flex;gap:8px;margin-top:12px">
        <input id="stNewOrg" placeholder="新组织名称" style="flex:1">
        <button id="btnAddOrg">+ 添加组织</button>
      </div>
    </div>
  </section>

  <!-- 主题 -->
  <section class="st-section">
    <h2>外观</h2>
    <div class="st-card">
      <div class="st-field">
        <label>主题模式</label>
        <select id="stTheme">
          <option value="light">浅色</option>
          <option value="dark">深色</option>
        </select>
      </div>
    </div>
  </section>
</div>
<style>
  .st-root{max-width:700px}
  .st-section{margin-top:28px}
  .st-section h2{font-size:1.0625rem;margin-bottom:12px;font-weight:600}
  .st-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
  .st-field{margin-bottom:14px}
  .st-field label{display:block;font-size:0.8125rem;font-weight:500;margin-bottom:4px;color:var(--ink)}
  .st-field input,.st-field select{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.875rem;font-family:inherit;background:var(--bg);color:var(--ink)}
  .st-field input:focus,.st-field select:focus{outline:none;border-color:var(--primary)}
  button{padding:8px 18px;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.8125rem;font-family:inherit;color:var(--ink);transition:background 150ms ease}
  button:hover{background:var(--surface)}
  .st-key-row{display:flex;align-items:center;gap:8px;margin-bottom:8px}
  .st-key-row span{font-size:0.8125rem;font-weight:500;min-width:60px}
  .st-key-row input{flex:1}
  .st-key-row .key-status{font-size:0.6875rem;padding:3px 8px;border-radius:6px;font-weight:500}
  .key-ok{background:oklch(0.97 0.03 170);color:oklch(0.50 0.12 170)}
  .key-none{background:oklch(0.97 0.02 80);color:oklch(0.55 0.10 80)}
  .st-monitor-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.8125rem}
  .st-monitor-row:last-child{border-bottom:none}
  .st-org-row{margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
  .st-org-row:last-child{border-bottom:none;margin-bottom:0}
  .st-org-info{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
  .st-org-name{font-weight:600;font-size:0.875rem}
  .st-org-del{cursor:pointer;color:var(--error);font-size:0.75rem}
  .st-folder-tag{display:inline-block;padding:2px 8px;border-radius:6px;background:var(--surface);font-size:0.75rem;margin:2px 4px 2px 0}
  .st-folder-del{cursor:pointer;color:var(--error);margin-left:2px;font-weight:700}
  .st-monitor-row .mon-path{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted)}
  .st-monitor-row .mon-del{color:var(--error);cursor:pointer;padding:2px 6px}
</style>`;

  // AI config
  if (aiConfig) {
    document.getElementById('stProvider').value = aiConfig.active_provider;
    renderKeyInputs(aiConfig);
  }
  document.getElementById('btnSaveAI').addEventListener('click', saveAIConfig);
  document.getElementById('btnTestAI').addEventListener('click', testAI);

  // Monitors
  renderMonitors(monitorSources);
  document.getElementById('btnAddSource').addEventListener('click', async ()=>{
    const input = document.getElementById('stNewPath');
    const path = input.value.trim();
    if(!path)return;
    try{
      await api.post('/api/monitor-sources',{path,label:'自定义监控源',enabled:true});
      const updated = await api.get('/api/monitor-sources');
      renderMonitors(updated);
      input.value = '';
    }catch(e){alert('添加失败：'+e.message);}
  });

  // Orgs
  renderOrgs(orgs);
  document.getElementById('btnAddOrg').addEventListener('click', async ()=>{
    const name = document.getElementById('stNewOrg').value.trim();
    if(!name)return;
    await api.post('/api/orgs',{name,icon:'📋'});
    document.getElementById('stNewOrg').value = '';
    const updated = await api.get('/api/orgs');
    renderOrgs(updated);
    toast('组织已添加','success');
  });

  // Theme
  const theme = document.documentElement.getAttribute('data-theme')||'light';
  document.getElementById('stTheme').value = theme;
  document.getElementById('stTheme').addEventListener('change', function(){
    document.documentElement.setAttribute('data-theme', this.value);
  });
}

function renderKeyInputs(config){
  const container = document.getElementById('stKeys');
  container.innerHTML = Object.entries(config.providers).map(([k,v])=>`
    <div class="st-key-row">
      <span>${v.label} Key</span>
      <input type="password" id="key_${k}" placeholder="${v.has_key?'••••••••（已保存）':'粘贴 API Key'}" autocomplete="off">
      <span class="key-status ${v.has_key?'key-ok':'key-none'}">${v.has_key?'已配置':'未配置'}</span>
    </div>
  `).join('');
}

async function saveAIConfig(){
  const provider = document.getElementById('stProvider').value;
  const customModel = document.getElementById('stCustomModel').value.trim();
  const btn = document.getElementById('btnSaveAI');
  btn.textContent = '保存中...';

  try{
    await api.put('/api/settings/ai',{active_provider:provider,custom_model:customModel});
    // Save keys for each provider
    for(const pid of ['deepseek','kimi']){
      const input = document.getElementById('key_'+pid);
      if(input?.value.trim()){
        await api.put('/api/settings/ai',{provider:pid,api_key:input.value.trim()});
        input.value = '';
        input.placeholder = '••••••••（已保存）';
      }
    }
    document.getElementById('stAIStatus').innerHTML = '<span style="color:var(--accent)">✅ 保存成功</span>';
  }catch(e){
    document.getElementById('stAIStatus').innerHTML = `<span style="color:var(--error)">❌ ${e.message}</span>`;
  }
  btn.textContent = '💾 保存 AI 配置';
}

async function testAI(){
  const btn = document.getElementById('btnTestAI');
  const provider = document.getElementById('stProvider').value;
  const status = document.getElementById('stAIStatus');
  btn.textContent = '测试中...';

  // Use the key from input if filled, otherwise use saved key
  const keyInput = document.getElementById('key_'+provider);
  const apiKey = keyInput?.value.trim()||'';

  try{
    const r = await api.post('/api/settings/ai/test',{provider,api_key:apiKey});
    if(r.ok){
      status.innerHTML = `<span style="color:var(--accent)">✅ 连接成功！模型：${r.model}</span>`;
    }else{
      status.innerHTML = `<span style="color:var(--error)">❌ 连接失败：${r.error}</span>`;
    }
  }catch(e){
    status.innerHTML = `<span style="color:var(--error)">❌ 测试失败：${e.message}</span>`;
  }
  btn.textContent = '🔌 测试连接';
}

function renderOrgs(orgs){
  const container = document.getElementById('stOrgs');
  if(!orgs.length){ container.innerHTML='<p style="font-size:0.8125rem;color:var(--muted)">暂无组织</p>'; return; }
  container.innerHTML = orgs.map(o=>`
    <div class="st-org-row">
      <div class="st-org-info">
        <span class="st-org-name">${o.icon} ${o.name}</span>
        <span class="st-org-del" data-id="${o.id}">🗑️</span>
      </div>
      <div class="st-folders" id="folders${o.id}"></div>
      <div style="display:flex;gap:6px;margin-top:4px">
        <input id="newFolder${o.id}" placeholder="添加子分类..." style="flex:1;padding:4px 8px;border:1px solid var(--border);border-radius:4px;font-size:0.75rem;font-family:inherit;background:var(--bg);color:var(--ink)">
        <button data-org="${o.id}" class="btn-add-folder" style="padding:4px 10px;font-size:0.75rem">+</button>
      </div>
    </div>
  `).join('');

  // Load folders
  orgs.forEach(async o=>{
    const folders = await api.orgs.folders.list(o.id);
    const fc = document.getElementById('folders'+o.id);
    fc.innerHTML = folders.map(f=>`
      <span class="st-folder-tag">${f.name} <span class="st-folder-del" data-oid="${o.id}" data-fid="${f.id}">×</span></span>
    `).join('') || '<span style="font-size:0.6875rem;color:var(--muted)">暂无子分类</span>';
  });

  // Delete org
  container.querySelectorAll('.st-org-del').forEach(el=>{
    el.addEventListener('click',async ()=>{
      if(!confirm('删除该组织？'))return;
      await api.delete('/api/orgs/'+el.dataset.id);
      const updated = await api.get('/api/orgs');
      renderOrgs(updated);
    });
  });

  // Add folder
  container.querySelectorAll('.btn-add-folder').forEach(btn=>{
    btn.addEventListener('click',async ()=>{
      const orgId = btn.dataset.org;
      const input = document.getElementById('newFolder'+orgId);
      const name = input.value.trim();
      if(!name)return;
      await api.post(`/api/orgs/${orgId}/folders`,{name});
      input.value = '';
      const updated = await api.get('/api/orgs');
      renderOrgs(updated);
    });
  });

  // Delete folder
  container.querySelectorAll('.st-folder-del').forEach(el=>{
    el.addEventListener('click',async (e)=>{
      e.stopPropagation();
      await api.delete(`/api/orgs/${el.dataset.oid}/folders/${el.dataset.fid}`);
      const updated = await api.get('/api/orgs');
      renderOrgs(updated);
    });
  });
}

function renderMonitors(sources){
  const container = document.getElementById('stMonitors');
  if(!sources.length){
    container.innerHTML = '<p style="font-size:0.8125rem;color:var(--muted)">暂无监控源</p>';
    return;
  }
  container.innerHTML = sources.map(s=>`
    <div class="st-monitor-row">
      <span>${s.enabled?'🟢':'⭕'} ${s.label||'监控源'}</span>
      <span class="mon-path">${s.path}</span>
      <span class="mon-del" data-id="${s.id}">🗑️</span>
    </div>
  `).join('');
  container.querySelectorAll('.mon-del').forEach(el=>{
    el.addEventListener('click', async ()=>{
      await api.delete('/api/monitor-sources/'+el.dataset.id);
      const updated = await api.get('/api/monitor-sources');
      renderMonitors(updated);
    });
  });
}
