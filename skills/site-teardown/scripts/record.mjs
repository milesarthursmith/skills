// record.mjs — record a scripted interaction on a page, trimmed to the action window.
// Usage: node record.mjs <url> <out.webm> '<json steps>' [width] [height]
// Steps: {"wait":ms} | {"scroll":y,"ms":duration} | {"scrollTo":"css selector","offset":-80,"ms":duration} (aligns clips when section heights differ) | {"hover":"css"} | {"click":"css"} | {"move":[x,y]} | {"wheel":dy,"ms":duration}
// Env RM=1 records with prefers-reduced-motion: reduce.
// Same steps on two pages → comparable clips for side-by-side (see sbs.sh).
import fs from 'fs';
let chromium; try { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); } catch { ({ chromium } = await import('playwright')); }
const [url, out, stepsJson, W = '1440', H = '900'] = process.argv.slice(2);
const steps = JSON.parse(stepsJson); const w = +W, h = +H; const sleep = ms => new Promise(r => setTimeout(r, ms));
const dir = out + '.tmp'; fs.mkdirSync(dir, { recursive: true });
const b = await chromium.launch({ args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
const ctx = await b.newContext({ viewport: { width: w, height: h }, locale: 'en-US', reducedMotion: process.env.RM ? 'reduce' : 'no-preference', isMobile: w < 1024, hasTouch: w < 1024, recordVideo: { dir, size: { width: w, height: h } } });
const t0 = Date.now(); const p = await ctx.newPage();
await p.goto(url, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
await sleep(2500); const start = (Date.now() - t0) / 1000;
for (const s of steps) {
  if (s.wait) await sleep(s.wait);
  else if (s.scrollTo) { const y = await p.evaluate(([sel, off]) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect().top + scrollY + off : null; }, [s.scrollTo, s.offset || 0]);
    if (y === null) { console.log('  scrollTo target not found:', s.scrollTo); await sleep(s.ms || 1000); } else steps.splice(steps.indexOf(s) + 1, 0, { scroll: y, ms: s.ms || 1000 }); }
  else if (s.scroll !== undefined) { // wall-clock driven so slow pages stay in sync with fast ones
    const from = await p.evaluate(() => scrollY); const dur = s.ms || 1000; const st = Date.now(); let t = 0;
    while (t < 1) { t = Math.min(1, (Date.now() - st) / dur); const e = t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2; await p.evaluate(y => scrollTo(0, y), from + (s.scroll - from) * e); await sleep(10); } }
  else if (s.wheel) { const n = Math.max(1, Math.round((s.ms || 1000) / 32)); for (let i = 0; i < n; i++) { await p.mouse.wheel(0, s.wheel / n); await sleep(32); } }
  else if (s.hover || s.click) { const st = Date.now(); const loc = p.locator(s.hover || s.click).first();
    try { if (s.hover) await loc.hover({ timeout: 1500, force: true }); else await loc.click({ timeout: 1500, force: true }); } catch { console.log('  step target not found:', s.hover || s.click); }
    await sleep(Math.max(0, 1500 - (Date.now() - st))); } // fixed 1.5s slot either way, so clips stay aligned
  else if (s.move) { await p.mouse.move(s.move[0], s.move[1], { steps: 12 }); }
}
const end = (Date.now() - t0) / 1000; const v = p.video(); await ctx.close(); await b.close();
const raw = await v.path();
const { execFileSync } = await import('child_process');
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', start.toFixed(2), '-to', end.toFixed(2), '-i', raw, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '38', '-row-mt', '1', '-deadline', 'realtime', out]);
fs.rmSync(dir, { recursive: true, force: true }); console.log('recorded', out, (end - start).toFixed(1) + 's');
