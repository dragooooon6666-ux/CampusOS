/**
 * 首页 — 品牌理念展示
 */
import { api } from '../api.js';

export async function render(el) {
  el.innerHTML = `
<div class="home-root">
  <div class="hero-bg"></div>
  <div class="hero-content">
    <div class="hero-text">
      <div class="hero-line">
        <span class="char" style="--d:0">文</span><span class="char" style="--d:1">件</span>
        <span class="char gap" style="--d:2">不</span><span class="char" style="--d:3">再</span>
        <span class="char" style="--d:4">散</span><span class="char" style="--d:5">落</span>
      </div>
      <div class="hero-line">
        <span class="char" style="--d:6">经</span><span class="char" style="--d:7">验</span>
        <span class="char gap" style="--d:8">不</span><span class="char" style="--d:9">再</span>
        <span class="char" style="--d:10">归</span><span class="char" style="--d:11">零</span>
      </div>
    </div>
    <p class="hero-desc">让每个学生干部都有一个数字办公室</p>
    <p class="hero-detail">AI 驱动的校园事务智能系统 · 自动整理 · 智能写作 · 项目归档</p>
    <div class="hero-actions">
      <a href="#/files" class="btn-hero-primary">开始使用</a>
    </div>
  </div>
  <div class="scroll-hint"><span></span></div>
</div>
<style>
  .home-root{height:100vh;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;background:var(--bg)}
  .hero-bg{position:absolute;inset:0;pointer-events:none}
  .hero-bg::before{content:'';position:absolute;top:-40%;left:50%;transform:translateX(-50%);width:min(1000px,120vw);height:min(1000px,120vw);background:radial-gradient(circle,oklch(0.55 0.18 255 / 0.05) 0%,transparent 70%)}
  .hero-content{text-align:center;position:relative;z-index:1;padding:0 40px}
  .hero-text{margin-bottom:32px}
  .hero-line{display:flex;justify-content:center;gap:0;line-height:1.05}
  .hero-line .char{display:inline-block;font-size:clamp(3.5rem,10vw,9rem);font-weight:850;letter-spacing:-0.05em;color:var(--ink);opacity:0;animation:charIn 0.55s var(--ease-out) forwards;animation-delay:calc(0.06s * var(--d))}
  .hero-line .char.gap{margin-left:0.25em}
  @keyframes charIn{0%{opacity:0;transform:translateY(0.4em) scale(0.95);filter:blur(4px)}60%{opacity:1;transform:translateY(-0.03em) scale(1.01);filter:blur(0)}100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}
  .hero-desc{font-size:clamp(1rem,2.5vw,1.375rem);color:var(--muted);margin-bottom:8px;opacity:0;animation:fadeUp 0.5s ease forwards;animation-delay:1.2s;font-weight:400}
  .hero-detail{font-size:0.9375rem;color:oklch(0.55 0.01 255 / 0.6);opacity:0;animation:fadeUp 0.5s ease forwards;animation-delay:1.4s}
  @keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
  .hero-actions{display:flex;gap:14px;justify-content:center;margin-top:40px;opacity:0;animation:fadeUp 0.5s ease forwards;animation-delay:1.7s}
  .btn-hero-primary{padding:14px 36px;border-radius:12px;font-size:0.9375rem;font-weight:600;background:var(--primary);color:#fff;text-decoration:none;transition:transform 150ms ease,box-shadow 150ms ease}
  .btn-hero-primary:hover{transform:translateY(-1px);box-shadow:0 6px 24px oklch(0.55 0.18 255 / 0.3);text-decoration:none}
  .btn-hero-outline{padding:14px 36px;border-radius:12px;font-size:0.9375rem;font-weight:500;border:1.5px solid var(--border);color:var(--ink);text-decoration:none;transition:background 150ms ease}
  .btn-hero-outline:hover{background:var(--surface);text-decoration:none}
  .scroll-hint{position:absolute;bottom:32px;left:50%;transform:translateX(-50%);animation:bob 2s ease-in-out infinite;opacity:0;animation-delay:2.2s}
  @keyframes bob{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(10px)}}
  .scroll-hint span{display:block;width:20px;height:20px;border-right:2px solid oklch(0.55 0.01 255 / 0.3);border-bottom:2px solid oklch(0.55 0.01 255 / 0.3);transform:rotate(45deg)}
  @media(prefers-reduced-motion:reduce){.char,.hero-desc,.hero-detail,.hero-actions{animation:none;opacity:1}}
</style>`;
}
