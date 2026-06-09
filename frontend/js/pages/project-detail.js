/**
 * 项目详情页
 */
import { api } from '../api.js';

export async function render(el, projectId) {
  const project = await api.get(`/api/projects/${projectId}`);
  const allFiles = await api.get('/api/files?limit=100');

  const STATUS_MAP = {
    active: '进行中', completed: '已完成', archived: '已归档',
  };

  el.innerHTML = `
    <div>
      <a href="#/projects" class="back-link">← 返回看板</a>
      <div class="pd-header">
        <input id="editName" value="${escHtml(project.name)}" style="font-size:1.5rem;font-weight:700;border:none;background:transparent;color:var(--ink);font-family:inherit;width:100%;padding:4px 0;border-bottom:2px solid transparent" onfocus="this.style.borderBottomColor='var(--primary)'" onblur="this.style.borderBottomColor='transparent';saveProject()">
        <select id="editStatus" onchange="saveProject()" style="padding:4px 10px;border-radius:8px;border:1px solid var(--border);font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink)">
          <option value="active">进行中</option>
          <option value="completed">已完成</option>
          <option value="archived">已归档</option>
        </select>
      </div>
      <div class="pd-meta">
        <input id="editLeader" value="${escHtml(project.leader||'')}" placeholder="负责人" onchange="saveProject()" style="border:1px solid var(--border);border-radius:4px;padding:2px 6px;font-size:0.8125rem;font-family:inherit;width:120px;background:var(--bg);color:var(--ink)">
        <input id="editStart" value="${escHtml(project.start_date||'')}" placeholder="开始日期" onchange="saveProject()" style="border:1px solid var(--border);border-radius:4px;padding:2px 6px;font-size:0.8125rem;font-family:inherit;width:100px;background:var(--bg);color:var(--ink)"> →
        <input id="editEnd" value="${escHtml(project.end_date||'')}" placeholder="结束日期" onchange="saveProject()" style="border:1px solid var(--border);border-radius:4px;padding:2px 6px;font-size:0.8125rem;font-family:inherit;width:100px;background:var(--bg);color:var(--ink)">
      </div>
      <input id="editDesc" value="${escHtml(project.description||'')}" placeholder="添加描述..." onchange="saveProject()" style="margin-top:8px;width:100%;border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:0.875rem;font-family:inherit;background:var(--bg);color:var(--ink)">

      <div style="display:flex;justify-content:space-between;align-items:center">
        <div class="pd-tabs" style="border:none;margin:0">
          <button class="pd-tab active" data-tab="files">📄 关联文件 (${project.files.length})</button>
          <button class="pd-tab" data-tab="docs">📝 生成文档 (${project.documents.length})</button>
          <button class="pd-tab" data-tab="archive">📋 项目档案</button>
        </div>
        <a href="/api/export/project/${projectId}" style="padding:8px 16px;border-radius:8px;font-size:0.8125rem;font-weight:600;background:var(--primary);color:#fff;text-decoration:none;white-space:nowrap">📦 导出项目</a>
      </div>

      <div id="tabFiles">
        <div class="pd-add-file">
          <select id="selectFile" style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.875rem;font-family:inherit;background:var(--bg);color:var(--ink)">
            <option value="">关联已有文件...</option>
            ${allFiles.map(f => `<option value="${f.id}">${f.title || f.original_name} (${f.doc_type})</option>`).join('')}
          </select>
          <button id="btnLink" class="btn-primary-sm">关联</button>
        </div>
        <div id="fileList" class="pd-list"></div>
      </div>

      <div id="tabDocs" style="display:none">
        <div class="pd-list" id="docList"></div>
      </div>

      <div id="tabArchive" style="display:none">
        <div id="archiveContent" style="background:var(--surface);border-radius:12px;padding:24px;border:1px solid var(--border);white-space:pre-wrap;font-size:0.9375rem;line-height:1.8;min-height:200px"></div>
      </div>
    </div>
    <style>
      .back-link{display:inline-flex;align-items:center;gap:4px;padding:6px 14px;border:1px solid var(--border);border-radius:8px;font-size:0.8125rem;color:var(--muted);text-decoration:none;transition:background 150ms ease;margin-bottom:8px}
      .back-link:hover{background:var(--surface);text-decoration:none}
      .pd-header{display:flex;align-items:center;gap:12px;margin:16px 0 8px}
      .pd-status{font-size:0.75rem;padding:3px 12px;border-radius:10px;font-weight:600;background:oklch(0.97 0.03 255);color:var(--primary)}
      .pd-meta{font-size:0.8125rem;color:var(--muted)}
      .pd-tabs{display:flex;gap:0;margin:20px 0 16px;border-bottom:2px solid var(--border)}
      .pd-tab{padding:10px 20px;border:none;background:none;font-size:0.875rem;font-family:inherit;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-2px;transition:all 150ms ease}
      .pd-tab.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:500}
      .pd-add-file{display:flex;gap:8px;margin-bottom:12px}
      .pd-list{display:flex;flex-direction:column;gap:4px}
      .pd-item{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:8px;transition:background 150ms ease}
      .pd-item:hover{background:var(--surface)}
      .pd-item .pd-item-name{font-size:0.875rem;font-weight:500;flex:1}
      .pd-item .pd-item-meta{font-size:0.75rem;color:var(--muted);margin-right:12px}
      .pd-item .pd-unlink{font-size:0.75rem;color:var(--error);cursor:pointer;padding:2px 8px;border-radius:4px;border:1px solid transparent}
      .pd-item .pd-unlink:hover{background:oklch(0.97 0.03 25);border-color:var(--error)}
    </style>
  `;

  // 设置初始值
  document.getElementById('editStatus').value = project.status;

  // 自动保存
  window.saveProject = async function(){
    try {
      await api.put(`/api/projects/${projectId}`, {
        name: document.getElementById('editName').value.trim(),
        status: document.getElementById('editStatus').value,
        leader: document.getElementById('editLeader').value.trim(),
        start_date: document.getElementById('editStart').value.trim(),
        end_date: document.getElementById('editEnd').value.trim(),
        description: document.getElementById('editDesc').value.trim(),
      });
    } catch {}
  };

  // 渲染文件列表
  function renderFiles(files) {
    const list = document.getElementById('fileList');
    if (!files.length) {
      list.innerHTML = '<p style="color:var(--muted);padding:20px">暂无关联文件</p>';
      return;
    }
    list.innerHTML = files.map(f => `
      <div class="pd-item">
        <span class="pd-item-name">📄 ${f.title || f.original_name}</span>
        <span class="pd-item-meta">${f.doc_type} | ${f.doc_date || ''}</span>
        <span class="pd-unlink" data-file="${f.id}">解除</span>
      </div>
    `).join('');
  }

  function renderDocs(docs) {
    const list = document.getElementById('docList');
    if (!docs.length) {
      list.innerHTML = '<p style="color:var(--muted);padding:20px">暂无生成文档 <a href="#/writing" style="font-size:0.8125rem">去写作中心</a></p>';
      return;
    }
    list.innerHTML = docs.map(d => `
      <div class="pd-item">
        <span class="pd-item-name">📝 ${d.title}</span>
        <span class="pd-item-meta">${d.doc_type} | AI: ${d.ai_provider || ''}</span>
      </div>
    `).join('');
  }

  renderFiles(project.files);
  renderDocs(project.documents);

  // Tab 切换
  document.querySelector('.pd-tabs').addEventListener('click', (e) => {
    const tab = e.target.closest('.pd-tab');
    if (!tab) return;
    document.querySelectorAll('.pd-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tabFiles').style.display = tab.dataset.tab === 'files' ? 'block' : 'none';
    document.getElementById('tabDocs').style.display = tab.dataset.tab === 'docs' ? 'block' : 'none';
    document.getElementById('tabArchive').style.display = tab.dataset.tab === 'archive' ? 'block' : 'none';

    if (tab.dataset.tab === 'archive') {
      loadArchive();
    }
  });

  // 关联文件
  document.getElementById('btnLink').addEventListener('click', async () => {
    const fileId = document.getElementById('selectFile').value;
    if (!fileId) return;
    await api.post(`/api/projects/${projectId}/link-file`, { file_id: parseInt(fileId) });
    const updated = await api.get(`/api/projects/${projectId}`);
    renderFiles(updated.files);
  });

  // 解除关联
  document.getElementById('fileList').addEventListener('click', async (e) => {
    const unlink = e.target.closest('.pd-unlink');
    if (!unlink) return;
    const fileId = unlink.dataset.file;
    await api.delete(`/api/projects/${projectId}/link-file/${fileId}`);
    const updated = await api.get(`/api/projects/${projectId}`);
    renderFiles(updated.files);
  });

  // 加载档案
  async function loadArchive() {
    const content = document.getElementById('archiveContent');
    content.innerHTML = '<p style="color:var(--muted)">加载中...</p>';
    try {
      const { markdown } = await api.get(`/api/projects/${projectId}/archive`);
      content.textContent = markdown;
    } catch {
      content.innerHTML = '<p style="color:var(--error)">加载失败</p>';
    }
  }
}

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
