/**
 * API 封装 — fetch + 错误处理
 */

const BASE = '';

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const res = await fetch(url, config);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Toast 通知 ──
export function toast(msg, type='info') {
  const colors = {info:'var(--primary)',success:'var(--accent)',error:'var(--error)'};
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = msg;
  t.style.cssText = `
    position:fixed;bottom:24px;right:24px;z-index:9999;
    padding:12px 20px;border-radius:10px;font-size:0.875rem;font-weight:500;
    background:var(--bg);color:var(--ink);border:1px solid ${colors[type]||colors.info};
    box-shadow:0 4px 20px oklch(0 0 0/0.1);animation:toastIn 300ms var(--ease-out);
    max-width:380px;
  `;
  document.body.appendChild(t);
  setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity 200ms ease';setTimeout(()=>t.remove(),200);},3000);
}

// Inject toast CSS once
if (!document.getElementById('toast-css')) {
  const s = document.createElement('style');
  s.id = 'toast-css';
  s.textContent = `@keyframes toastIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}`;
  document.head.appendChild(s);
}

export const api = {
  get:    (path)            => request(path),
  post:   (path, body)      => request(path, { method: 'POST', body }),
  put:    (path, body)      => request(path, { method: 'PUT', body }),
  delete: (path)            => request(path, { method: 'DELETE' }),

  // Health
  health: () => api.get('/api/health'),

  // Organizations
  orgs: {
    list:   ()              => api.get('/api/orgs'),
    get:    (id)            => api.get(`/api/orgs/${id}`),
    create: (data)          => api.post('/api/orgs', data),
    update: (id, data)      => api.put(`/api/orgs/${id}`, data),
    delete: (id)            => api.delete(`/api/orgs/${id}`),
    folders: {
      list:   (orgId)       => api.get(`/api/orgs/${orgId}/folders`),
    },
  },
};
