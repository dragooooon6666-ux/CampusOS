# 宣传页 v3 重设计 — 飞书风格

## 目标

参照飞书官网简洁大气风格，放大所有视觉元素，重做页眉页脚。

## 配色（不变）

- 主色：`#2563eb`（蓝）
- 背景：白灰交替 `#f8fafc` / `#fff`
- 文字：`#111827`（深）/ `#6b7280`（灰）/ `#9ca3af`（浅灰）

## 改动清单

### 全局
- 最小字号基准从 `0.6875rem` 提升到 `0.875rem`（14px）
- 页面最大宽度 `max-width: 1200px`（原 1100px）
- section padding `padding: 120px 40px`（原 80px 32px）

### 页眉（Top Bar）
- 白色底 + `backdrop-filter: blur(20px)` + `border-bottom`
- Logo：`1.25rem` 粗体 + 品牌色
- 右侧链接：产品功能跳转 + CTA 按钮（实心蓝底）
- 滚动后显示底部阴影 `box-shadow`

### Hero（P1）
- 主标题放大：`clamp(4rem, 10vw, 9rem)`（原 3rem-8rem）
- 副标题：`1.25rem`（原 0.9375rem）
- 按钮：`padding: 16px 48px; font-size: 1rem`
- 呼吸光晕保留

### 痛点（P2）
- 标题 `2.5rem`
- 正文 `1.125rem`（原 1rem）
- 卡片 padding `24px`（原 18px）

### 产品展示（P3-P5）
- 标题 `2.5rem`
- 描述文字 `1.125rem`
- 列表项 `1rem`
- Mockup 窗口整体放大 1.2 倍

### 统计数据（P6）
- 数字 `clamp(3rem, 7vw, 5rem)`
- 标签 `1rem`

### 使用步骤（P7）
- 标题 `2.5rem`
- 步骤卡片放大，图标圈 `64px`，标题 `1.125rem`

### CTA（P8）
- 标题 `2.5rem`
- 卡片 padding `48px 80px`（原 32px 56px）
- CTA 图标 `3rem`

### 页脚（Footer）
- 深灰底 `#f8fafc`，四列网格
- 列：CampusOS 简介 / 产品功能 / 相关资源 / 联系方式
- 底部版权线

### 滚动动画（保留不动）
- scroll-snap 逐页滚动
- 逐字弹入 `charIn` keyframes
- 数字计数器 `requestAnimationFrame`
- scroll reveal `IntersectionObserver`
- 呼吸光晕 `breathe` keyframes

### 移动端（@media < 768px）
- 取消 scroll-snap
- 页脚改为两列
- 产品展示改为上下堆叠

## 不修改
- 8 页内容结构
- HTML 语义结构（只改 CSS + 少量 HTML 调整）
- JS 动画逻辑
