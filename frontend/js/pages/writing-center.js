/**
 * 写作中心 — 引导式 AI 公文写作
 */
import { api } from '../api.js';

const DOC_TYPES = [
  "新闻稿", "活动总结", "会议纪要", "通知", "请示",
  "申请书", "发言稿", "工作汇报", "述职报告", "评优材料", "项目申报书",
];

export async function render(el) {
  el.innerHTML = `
    <div class="wc-layout">
      <aside class="wc-sidebar">
        <h3>选择文档类型</h3>
        <div class="wc-types" id="wcTypes"></div>
        <div id="wcForm" style="margin-top:20px"></div>
      </aside>
      <div class="wc-main">
        <div class="wc-toolbar">
          <h3 id="wcTitle">选择文档类型开始写作</h3>
          <div style="display:flex;gap:8px">
            <select id="wcProject" style="padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink)"><option value="">归属项目（可选）</option></select>
            <select id="wcTemplate" style="padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink)"><option value="">默认模板</option></select>
            <button id="btnImportTpl" style="padding:6px 12px;border:1px solid var(--border);border-radius:6px;font-size:0.75rem;cursor:pointer;background:var(--bg);color:var(--ink);font-family:inherit" title="从文档导入模板">📥 导入模板</button>
            <input type="file" id="tplFileInput" accept=".docx,.doc,.pdf" style="display:none">
            <button id="btnGenerate" class="btn-primary-sm" disabled>✨ 生成</button>
          </div>
        </div>
        <div class="wc-editor" id="wcEditor">
          <p style="color:var(--muted);text-align:center;padding:80px 20px">选择文档类型并填写信息后，点击「生成」开始写作</p>
        </div>
      </div>
    </div>
    <style>
      .wc-layout{display:flex;gap:24px;height:calc(100vh - 80px)}
      .wc-sidebar{width:260px;flex-shrink:0;overflow-y:auto}
      .wc-main{flex:1;display:flex;flex-direction:column}
      .wc-toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
      .wc-types{display:flex;flex-wrap:wrap;gap:6px}
      .wc-chip{padding:6px 14px;border-radius:20px;font-size:0.8125rem;cursor:pointer;border:1px solid var(--border);background:var(--bg);color:var(--ink);transition:all 150ms ease;user-select:none}
      .wc-chip:hover{background:oklch(0.55 0.18 255 / 0.06)}
      .wc-chip.active{background:var(--primary);color:#fff;border-color:var(--primary)}
      .wc-form-field{margin-bottom:12px}
      .wc-form-field label{display:block;font-size:0.8125rem;font-weight:500;margin-bottom:4px;color:var(--ink)}
      .wc-form-field input,.wc-form-field textarea{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:6px;font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink);resize:vertical}
      .wc-form-field textarea{min-height:60px}
      .wc-form-field input:focus,.wc-form-field textarea:focus{outline:none;border-color:var(--primary)}
      .btn-primary-sm{padding:8px 20px;border-radius:8px;font-size:0.875rem;font-weight:600;border:none;cursor:pointer;background:var(--primary);color:#fff;font-family:inherit;transition:background 150ms ease}
      .btn-primary-sm:hover{background:var(--primary-hover)}
      .btn-primary-sm:disabled{opacity:0.5;cursor:default}
      .wc-editor{flex:1;background:var(--surface);border-radius:12px;padding:24px;overflow-y:auto;border:1px solid var(--border);font-size:0.9375rem;line-height:1.8;white-space:pre-wrap}
      .wc-editor h2{font-size:1.125rem;margin:12px 0 8px}
      .wc-editor p{margin:6px 0}
      .wc-loading{display:flex;align-items:center;justify-content:center;height:200px;color:var(--muted)}
    </style>
  `;

  let activeType = '';
  let activeTemplateId = null;

  // 加载项目列表
  try {
    const projects = await api.get('/api/projects');
    const sel = document.getElementById('wcProject');
    projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      sel.appendChild(opt);
    });
  } catch {}

  // 渲染文档类型 chips
  const typesDiv = document.getElementById('wcTypes');
  DOC_TYPES.forEach(t => {
    const chip = document.createElement('span');
    chip.className = 'wc-chip';
    chip.textContent = t;
    chip.addEventListener('click', async () => {
      typesDiv.querySelectorAll('.wc-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activeType = t;
      document.getElementById('wcTitle').textContent = `📝 ${t}`;
      document.getElementById('btnGenerate').disabled = false;
      await loadForm(t);
      await loadTemplates(t);
    });
    typesDiv.appendChild(chip);
  });

  // 加载表单
  const loadForm = async (docType) => {
    const { fields } = await api.get(`/api/writing/form-fields/${encodeURIComponent(docType)}`);
    const formDiv = document.getElementById('wcForm');
    formDiv.innerHTML = fields.map(f => `
      <div class="wc-form-field">
        <label>${f.label} ${f.required ? '<span style="color:var(--error)">*</span>' : ''}</label>
        ${f.type === 'textarea'
          ? `<textarea name="${f.key}" placeholder="${f.label}"></textarea>`
          : `<input type="text" name="${f.key}" placeholder="${f.label}">`}
      </div>
    `).join('');
  }

  // 加载模板选项
  const loadTemplates = async (docType) => {
    const select = document.getElementById('wcTemplate');
    select.innerHTML = '<option value="">默认模板</option>';
    try {
      const templates = await api.get(`/api/writing/templates?doc_type=${encodeURIComponent(docType)}`);
      templates.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.name;
        select.appendChild(opt);
      });
    } catch {}
    select.onchange = () => { activeTemplateId = select.value || null; };
  }

  // 模板导入
  const fileInput = document.getElementById('tplFileInput');
  document.getElementById('btnImportTpl').addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file || !activeType) return;

    const btn = document.getElementById('btnImportTpl');
    btn.textContent = '⏳ 分析结构...';
    btn.disabled = true;

    try {
      const text = await file.text();
      const preview = text.slice(0, 2000);

      // Step 1: AI 提取文档结构
      const extractResp = await fetch('/api/writing/templates/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: preview }),
      });
      if (!extractResp.ok) throw new Error('提取失败');
      const { sections } = await extractResp.json();

      if (!sections || sections.length === 0) {
        throw new Error('未能识别文档结构');
      }

      // Step 2: 保存为模板
      btn.textContent = '💾 保存...';
      const saveResp = await fetch('/api/writing/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: file.name.replace(/\.[^.]+$/, ''),
          doc_type: activeType,
          sections,
        }),
      });

      if (saveResp.ok) {
        btn.textContent = '✅ 导入成功';
        await loadTemplates(activeType);
      } else {
        throw new Error((await saveResp.json()).detail);
      }
    } catch (e) {
      btn.textContent = '❌ 失败';
      alert('模板导入失败：' + e.message);
    }
    btn.disabled = false;
    setTimeout(() => { btn.textContent = '📥 导入模板'; }, 3000);
    fileInput.value = '';
  });

  // 生成文档
  document.getElementById('btnGenerate').addEventListener('click', async () => {
    if (!activeType) return;
    const btn = document.getElementById('btnGenerate');
    const editor = document.getElementById('wcEditor');

    // 收集表单数据
    const formData = {};
    document.querySelectorAll('#wcForm input, #wcForm textarea').forEach(el => {
      if (el.value.trim()) formData[el.name] = el.value.trim();
    });

    btn.textContent = '⏳ 生成中...';
    btn.disabled = true;
    editor.innerHTML = '<div class="wc-loading">AI 正在撰写...</div>';

    try {
      const projectId = document.getElementById('wcProject').value || null;
      currentDoc = await api.post('/api/writing/generate', {
        doc_type: activeType,
        form_data: formData,
        template_id: activeTemplateId,
        project_id: projectId ? parseInt(projectId) : null,
      });
      renderEditor(currentDoc);
    } catch (e) {
      editor.innerHTML = `<p style="color:var(--error)">生成失败：${e.message}</p>`;
    }

    btn.textContent = '✨ 重新生成';
    btn.disabled = false;
  });
}

let currentDoc = null;

async function renderEditor(doc) {
  const editor = document.getElementById('wcEditor');
  // 解析 ## 标题为 sections
  const sections = parseSections(doc.content);
  editor.innerHTML = `
    <div class="ed-toolbar">
      <button class="ed-btn" id="btnEdit">✏️ 编辑正文</button>
      <button class="ed-btn" id="btnSave">💾 保存修改</button>
      <a class="ed-btn" id="btnExport" href="#" style="text-decoration:none">📥 导出 Word</a>
      <span style="font-size:0.8125rem;color:var(--muted);margin-left:8px">归属：</span>
      <select id="edProject" style="padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.8125rem;font-family:inherit;background:var(--bg);color:var(--ink)"><option value="">不关联</option></select>
      <button class="ed-btn" id="btnLinkProject">关联</button>
    </div>
    <div class="ed-sections" id="edSections">
      ${sections.map((s,i) => `
        <div class="ed-sec" data-idx="${i}">
          ${s.heading ? `<h2 contenteditable="true" class="ed-heading">${s.heading}</h2>` : ''}
          <div contenteditable="true" class="ed-body">${s.body}</div>
          <button class="ed-regen" data-idx="${i}">🔄 重写此段</button>
        </div>
      `).join('')}
    </div>
    <style>
      .ed-toolbar{display:flex;gap:8px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
      .ed-btn{padding:6px 14px;border-radius:6px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.8125rem;font-family:inherit}
      .ed-btn:hover{background:var(--surface)}
      .ed-sec{margin-bottom:20px;padding:16px;border-radius:10px;border:1px solid var(--border);position:relative}
      .ed-heading{font-size:1.0625rem;font-weight:600;margin-bottom:8px;outline:none;padding:4px 0}
      .ed-heading:focus{background:oklch(0.55 0.18 255 / 0.06);border-radius:4px}
      .ed-body{font-size:0.9375rem;line-height:1.8;outline:none;min-height:60px;white-space:pre-wrap}
      .ed-body:focus{background:oklch(0.55 0.18 255 / 0.04);border-radius:4px;padding:4px}
      .ed-regen{position:absolute;top:8px;right:8px;padding:4px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:0.75rem;font-family:inherit;opacity:0;transition:opacity 150ms ease}
      .ed-sec:hover .ed-regen{opacity:1}
      .ed-regen:hover{background:oklch(0.55 0.18 255 / 0.08)}
    </style>
  `;

  // 导出链接
  document.getElementById('btnExport').href = `/api/writing/documents/${doc.id}/export`;

  // 项目关联（生成后可随时改）
  const edProj = document.getElementById('edProject');
  try {
    const projects = await api.get('/api/projects');
    projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id; opt.textContent = p.name;
      edProj.appendChild(opt);
    });
  } catch {}
  document.getElementById('btnLinkProject').addEventListener('click', async ()=>{
    const pid = edProj.value;
    if (!pid) return;
    await fetch('/api/writing/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({doc_type:'_link_', form_data:{}, project_id:parseInt(pid), _doc_id:doc.id}),
    });
    toast('已关联到项目','success');
  });

  // 保存
  document.getElementById('btnSave').addEventListener('click', async ()=>{
    const btn = document.getElementById('btnSave');
    btn.textContent = '⏳ 保存中...';
    const newContent = buildContent();
    try {
      await fetch(`/api/writing/regenerate`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({doc_id: doc.id, section_key:'__save__', section_label:'', feedback: newContent}),
      });
      // Update content directly via regenerate with full content
      const resp = await fetch(`/api/writing/regenerate`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({doc_id: doc.id, section_key:'_save', section_label:'保存', feedback:'__FULL_REPLACE__:'+newContent}),
      });
      btn.textContent = '✅ 已保存';
    } catch(e) { btn.textContent = '❌ 失败'; }
    setTimeout(()=>{btn.textContent='💾 保存修改';},2000);
  });

  // 编辑模式切换
  document.getElementById('btnEdit').addEventListener('click', function(){
    const bodies = document.querySelectorAll('.ed-body, .ed-heading');
    const editing = bodies[0]?.contentEditable === 'true';
    bodies.forEach(el => el.contentEditable = editing ? 'false' : 'true');
    this.textContent = editing ? '✏️ 编辑正文' : '🔒 锁定编辑';
  });

  // 段落重生成
  editor.querySelectorAll('.ed-regen').forEach(btn => {
    btn.addEventListener('click', async function(){
      const idx = +this.dataset.idx;
      const sec = sections[idx];
      this.textContent = '⏳';
      try {
        const resp = await fetch('/api/writing/regenerate', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({
            doc_id: doc.id,
            section_key: sec.heading || 'section_'+idx,
            section_label: sec.heading || '段落',
            feedback: '请重新生成这一段，保持风格一致',
          }),
        });
        const updated = await resp.json();
        const newSections = parseSections(updated.content);
        if (newSections[idx]) {
          const el = document.querySelectorAll('.ed-sec')[idx];
          if (el) {
            if (newSections[idx].heading) el.querySelector('.ed-heading').textContent = newSections[idx].heading;
            el.querySelector('.ed-body').textContent = newSections[idx].body;
          }
        }
        this.textContent = '✅';
      } catch(e) { this.textContent = '❌'; }
      setTimeout(()=>{this.textContent='🔄 重写此段';},2000);
    });
  });
}

function parseSections(md) {
  const lines = md.split('\n');
  const sections = [];
  let current = { heading: '', body: '' };
  for (const line of lines) {
    if (/^##\s/.test(line)) {
      if (current.body.trim() || current.heading) sections.push({...current});
      current = { heading: line.replace(/^##\s*/, '').trim(), body: '' };
    } else if (line.trim()) {
      current.body += line + '\n';
    }
  }
  if (current.body.trim() || current.heading) sections.push({...current});
  if (!sections.length) sections.push({ heading: '', body: md });
  return sections;
}

function buildContent() {
  const secs = document.querySelectorAll('.ed-sec');
  let md = '';
  secs.forEach(sec => {
    const h = sec.querySelector('.ed-heading');
    const b = sec.querySelector('.ed-body');
    if (h?.textContent.trim()) md += '## ' + h.textContent.trim() + '\n\n';
    if (b?.textContent.trim()) md += b.textContent.trim() + '\n\n';
  });
  return md.trim();
}
