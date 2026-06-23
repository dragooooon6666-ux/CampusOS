/**
 * CampusOS 前端入口
 */
import { initRouter, route, navigate } from './router.js';
import { api } from './api.js';

// ── 首页 ──
route('/', async (el) => {
  el.innerHTML = '';
  const { render } = await import('./pages/dashboard.js');
  await render(el);
});

// ── 项目看板 ──
route('/projects', async (el) => {
  el.innerHTML = '<p style="padding:20px;color:var(--muted)">加载中...</p>';
  const { render } = await import('./pages/projects-page.js');
  await render(el);
});

// ── Writing Center ──
route('/writing', async (el) => {
  el.innerHTML = '<p style="padding:20px;color:var(--muted)">加载中...</p>';
  try {
    const mod = await import('./pages/writing-center.js?v=4');
    await mod.render(el);
  } catch(e) {
    el.innerHTML = `<p style="color:var(--error);padding:20px">加载失败：${e.message}<br><pre style="font-size:0.75rem;margin-top:8px">${e.stack}</pre></p>`;
  }
});

// ── Project Detail ──
route('/project/:id', async (el, id) => {
  el.innerHTML = '<p style="padding:20px;color:var(--muted)">加载中...</p>';
  const { render } = await import('./pages/project-detail.js?v=2');
  await render(el, id);
});

// ── Settings ──
route('/settings', async (el) => {
  el.innerHTML = '<p style="padding:20px;color:var(--muted)">加载中...</p>';
  const { render } = await import('./pages/settings-page.js');
  await render(el);
});

// ── File Center ──
route('/files', async (el) => {
  el.innerHTML = '<p style="padding:20px;color:var(--muted)">加载中...</p>';
  const { render } = await import('./pages/file-center.js');
  await render(el);
});

// ── 启动 ──
document.addEventListener('DOMContentLoaded', () => {
  initRouter();
});
