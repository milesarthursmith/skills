// check.mjs — quick health check for a page or one section after a try-on.
// Usage: node check.mjs <url> [css-selector] [outdir]
// Reports, at 1440 and 390: console/page errors, horizontal overflow, and with reduced motion how many animations still run.
// Saves a screenshot of the selector (or the viewport) per width to outdir (default ./check).
import fs from 'fs';
let chromium; try { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); } catch { ({ chromium } = await import('playwright')); }
const [url, sel, out = 'check'] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const b = await chromium.launch({ args: ['--no-sandbox', '--use-gl=swiftshader'] }); let fail = 0;
for (const [w, h, rm] of [[1440, 900, false], [390, 844, false], [1440, 900, true]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, locale: 'en-US', isMobile: w < 1024, hasTouch: w < 1024, reducedMotion: rm ? 'reduce' : 'no-preference' });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto(url, { waitUntil: 'networkidle', timeout: 90000 }).catch(e => errs.push('goto: ' + e.message));
  await sleep(1500);
  if (sel) await p.evaluate(s => document.querySelector(s)?.scrollIntoView({ block: 'start' }), sel); await sleep(1500);
  const r = await p.evaluate(() => ({ overflowX: document.documentElement.scrollWidth - innerWidth, running: document.getAnimations().filter(a => a.playState === 'running' && a.effect?.getTiming().iterations === Infinity).map(a => a.animationName || 'waapi').slice(0, 8) }));
  const tag = `${w}${rm ? '-reduced' : ''}`; const el = sel ? p.locator(sel).first() : null;
  await (el && await el.count() ? el.screenshot({ path: `${out}/${tag}.png` }) : p.screenshot({ path: `${out}/${tag}.png` })).catch(() => {});
  const bad = errs.length || r.overflowX > 1 || (rm && r.running.length);
  fail ||= bad;
  console.log(`${bad ? 'FAIL' : 'ok  '} ${tag.padEnd(13)} errors:${errs.length} overflowX:${r.overflowX}px infinite-anims:${r.running.length}${r.running.length ? ' (' + r.running.join(',') + ')' : ''}${errs.length ? '\n      ' + errs.slice(0, 3).join('\n      ') : ''}`);
  await ctx.close();
}
await b.close(); console.log(`screenshots → ${out}/`); process.exit(fail ? 1 : 0);
