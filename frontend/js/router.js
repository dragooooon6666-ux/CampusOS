/**
 * Hash 路由 — 极简 SPA 导航
 */

const routes = {};

export function route(path, handler) {
  routes[path] = handler;
}

function match() {
  const hash = location.hash.slice(1) || '/';
  const outlet = document.getElementById('view');
  if (!outlet) return;

  // 首页全屏无侧边栏，其他页面恢复
  const sidebar = document.querySelector('.sidebar');
  const main = document.querySelector('.main-content');
  if (hash === '/') {
    if (sidebar) sidebar.style.display = 'none';
    if (main) { main.style.marginLeft = '0'; main.style.maxWidth = 'none'; main.style.padding = '0'; }
  } else {
    if (sidebar) sidebar.removeAttribute('style');
    if (main) main.removeAttribute('style');
  }

  // 精确匹配优先
  if (routes[hash]) {
    routes[hash](outlet);
    return;
  }

  // 动态路由匹配
  for (const [pattern, handler] of Object.entries(routes)) {
    if (pattern.includes(':')) {
      const regex = new RegExp('^' + pattern.replace(/:\w+/g, '([^/]+)') + '$');
      const m = hash.match(regex);
      if (m) {
        handler(outlet, ...m.slice(1));
        return;
      }
    }
  }

  // 回退首页
  if (routes['/']) routes['/'](outlet);
}

export function navigate(path) {
  location.hash = path;
}

export function initRouter() {
  window.addEventListener('hashchange', match);
  match();
}
