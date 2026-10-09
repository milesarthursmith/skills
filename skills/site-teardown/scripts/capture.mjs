// capture.mjs — one-shot evidence capture for a site teardown.
// Usage: node capture.mjs <url> <outdir> [--quick]
// Needs Playwright (node). In Claude Code cloud: import path below works; locally `npm i playwright`.
//
// Writes into <outdir>/:
//   shots/<vp>/NN-yNNNN.jpg   viewport shots every 0.75vh (reveals forced on per step)
//   shots/<vp>/full.jpg       full page with every reveal forced on
//   video/<vp>.webm           scroll-through recording
//   geometry.json             per breakpoint: section tops/heights, containers, key boxes, abs-positioned props
//   media-queries.json        every @media / @supports condition + the selectors inside it
//   keyframes.json            every @keyframes rule verbatim
//   timeline.json             class + inline-style mutations from navigation start (load-in, scripted loops)
//   animations.json           getAnimations(): name, duration, delay, easing, iterations, keyframes, target
//   components.json           repeated UI pieces: signature, count, box, key computed styles (+ shots/components/*.jpg)
//   effects.json              WebGL shader sources + uniforms seen, SVG <filter> markup, canvases, Rive/Lottie/video assets
//   tokens.json               colour / type / radius / shadow / backdrop / gradient frequencies + CSS variables
//   scroll.json               per-scroll-step inline transforms (scroll-linked motion) on desktop
//   hovers.json               hover deltas + transition strings for interactive elements
//   copy.json  meta.json  network.json  stack.json
import fs from 'fs';
let chromium;
try { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
catch { ({ chromium } = await import('playwright')); }

const [URL, OUT] = process.argv.slice(2);
const QUICK = process.argv.includes('--quick');
if (!URL || !OUT) { console.error('usage: node capture.mjs <url> <outdir> [--quick]'); process.exit(2); }
const BPS = QUICK ? [['desktop', 1440, 900]] : [['desktop', 1440, 900], ['laptop', 1024, 768], ['tablet', 834, 1194], ['mobile', 390, 844]];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const W = (f, d) => fs.writeFileSync(`${OUT}/${f}`, JSON.stringify(d, null, 1));
fs.mkdirSync(`${OUT}/shots/components`, { recursive: true }); fs.mkdirSync(`${OUT}/video`, { recursive: true });

// Runs before any page script: record mutations from t=0 and hook WebGL to capture shaders + uniforms.
const INIT = () => {
  window.__tl = []; const t0 = performance.now();
  const sig = el => (el.tagName + (el.id ? '#' + el.id : '') + '.' + (el.getAttribute('class') || '').trim().split(/\s+/).slice(0, 3).join('.')).slice(0, 70);
  new MutationObserver(ms => { for (const m of ms) { const el = m.target; if (el.nodeType !== 1) continue;
    const v = el.getAttribute(m.attributeName) || '';
    if (m.attributeName === 'style' && !/opacity|transform|translate|scale|rotate|filter|clip|width|height/.test(v)) continue;
    if (window.__tl.length < 6000) window.__tl.push([Math.round(performance.now() - t0), m.attributeName, sig(el), v.slice(0, 140)]); } })
    .observe(document, { subtree: true, attributes: true, attributeFilter: ['class', 'style'] });
  // sample running animations during the first 4s so load-in delays/durations are caught before they finish
  window.__early = {}; const samp = () => { for (const a of document.getAnimations()) { const t = a.effect?.getTiming?.() || {}; const el = a.effect?.target; if (!el) continue;
      const k = (a.animationName || a.transitionProperty || 'waapi') + '@' + sig(el); if (!window.__early[k]) window.__early[k] = { firstSeen: Math.round(performance.now() - t0), duration: t.duration, delay: t.delay, easing: t.easing, iterations: t.iterations }; } };
  const iv = setInterval(samp, 50); setTimeout(() => clearInterval(iv), 4000);
  // scroll root: the window, or the biggest overflow container when the page itself doesn't scroll (app-like / wrapper sites)
  window.__root = () => { const de = document.documentElement; if (de.scrollHeight > innerHeight + 50) return null;
    let best = null; for (const e of document.querySelectorAll('body *')) { const c = getComputedStyle(e); if (!/(auto|scroll)/.test(c.overflowY)) continue;
      const extra = e.scrollHeight - e.clientHeight; if (extra > 200 && e.clientHeight > innerHeight * 0.5 && (!best || extra > best.scrollHeight - best.clientHeight)) best = e; } return best; };
  window.__H = () => { const r = window.__root(); return r ? r.scrollHeight : document.documentElement.scrollHeight; };
  window.__to = y => { const r = window.__root(); if (r) { r.scrollTop = y; r.dispatchEvent(new Event('scroll')); } else scrollTo(0, y); };
  window.__y = () => { const r = window.__root(); return r ? r.scrollTop : scrollY; };
  window.__gl = { shaders: [], uniforms: {} };
  for (const C of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) { if (!C) continue; const P = C.prototype;
    const ss = P.shaderSource; P.shaderSource = function (s, src) { if (window.__gl.shaders.length < 20) window.__gl.shaders.push(src); return ss.call(this, s, src); };
    const gul = P.getUniformLocation; P.getUniformLocation = function (p, name) { const l = gul.call(this, p, name); if (l) l.__n = name; return l; };
    for (const fn of ['uniform1f', 'uniform2f', 'uniform3f', 'uniform4f', 'uniform1i']) { const o = P[fn]; if (!o) continue;
      P[fn] = function (loc, ...a) { if (loc && loc.__n) { const u = window.__gl.uniforms[loc.__n] ??= { fn, samples: [] }; if (u.samples.length < 30 && Math.random() < 0.05) u.samples.push(a.map(x => +(+x).toFixed(4))); } return o.call(this, loc, ...a); }; } }
};

const b = await chromium.launch({ args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
const geometry = {};
for (const [vp, w, h] of BPS) {
  const mobile = w < 1024;
  fs.mkdirSync(`${OUT}/shots/${vp}`, { recursive: true });
  const ctx = await b.newContext({ locale: 'en-US', timezoneId: 'UTC', viewport: { width: w, height: h }, isMobile: mobile, hasTouch: mobile, recordVideo: { dir: `${OUT}/video/_${vp}`, size: { width: w, height: h } } });
  const p = await ctx.newPage(); const errors = []; p.on('pageerror', e => errors.push(e.message.slice(0, 160)));
  await p.addInitScript(INIT);
  await p.goto(URL, { waitUntil: 'networkidle', timeout: 90000 }).catch(e => errors.push('goto ' + e.message));
  await sleep(8000); // let load-in cascades and scripted loops run so the timeline catches them

  if (vp === 'desktop') {
    // ---------- page-level evidence (desktop only) ----------
    W('timeline-load.json', await p.evaluate(() => window.__tl.slice()));
    W('load-animations.json', await p.evaluate(() => window.__early));
    W('keyframes.json', await p.evaluate(() => { const out = []; const walk = rules => { for (const r of rules) { if (r.type === 7) out.push(r.cssText); else if (r.cssRules) walk(r.cssRules); } };
      for (const s of document.styleSheets) { try { walk(s.cssRules) } catch { } } return out; }));
    W('media-queries.json', await p.evaluate(() => { const out = {}; const walk = (rules, cond) => { for (const r of rules) {
        if (r.conditionText !== undefined && r.cssRules) { const c = (r.type === 4 ? '@media ' : '@supports ') + r.conditionText; walk(r.cssRules, c); }
        else if (cond && r.selectorText) { (out[cond] ??= []).length < 60 && out[cond].push(r.selectorText.slice(0, 80) + ' {' + r.style.cssText.slice(0, 120) + '}'); } } };
      for (const s of document.styleSheets) { try { walk(s.cssRules, null) } catch { } } return out; }));
    W('animations.json', await p.evaluate(() => document.getAnimations().slice(0, 120).map(a => { const t = a.effect?.getTiming?.() || {}; const el = a.effect?.target;
      return { name: a.animationName || a.transitionProperty || 'waapi', type: a.constructor.name, state: a.playState, duration: t.duration, delay: t.delay, easing: t.easing, iterations: t.iterations, fill: t.fill,
        target: el ? (el.tagName + '.' + (el.getAttribute('class') || '').split(' ').slice(0, 2).join('.')).slice(0, 60) : null,
        keyframes: a.effect?.getKeyframes?.().map(k => { const o = { o: +k.computedOffset.toFixed(3) }; for (const [kk, v] of Object.entries(k)) if (!['offset', 'computedOffset', 'composite'].includes(kk) && v !== undefined) o[kk] = v; return o; }) }; })));
    W('tokens.json', await p.evaluate(() => { const c = {}; const add = (k, v) => { if (!v || v === 'none' || v === 'normal' || v === '0px' || v === 'rgba(0, 0, 0, 0)' || v === 'auto') return; (c[k] ??= {})[v] = (c[k][v] || 0) + 1; };
      for (const e of document.querySelectorAll('body *')) { if (!e.getClientRects().length) continue; const s = getComputedStyle(e);
        add('color', s.color); add('background', s.backgroundColor); add('border', s.borderTopWidth !== '0px' ? s.borderTopWidth + ' ' + s.borderTopStyle + ' ' + s.borderTopColor : null);
        add('radius', s.borderRadius); add('shadow', s.boxShadow); add('backdrop', s.backdropFilter); add('filter', s.filter); add('gradient', /gradient/.test(s.backgroundImage) ? s.backgroundImage.slice(0, 220) : null);
        add('transition', s.transition !== 'all 0s ease 0s' ? s.transition.slice(0, 160) : null); add('gap', s.gap); add('padding', s.padding);
        if ([...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) add('type', `${s.fontFamily.split(',')[0]}|${s.fontSize}|${s.fontWeight}|lh ${s.lineHeight}|ls ${s.letterSpacing}|${s.textTransform}`); }
      const o = {}; for (const k in c) o[k] = Object.entries(c[k]).sort((a, b) => b[1] - a[1]).slice(0, 40);
      o.cssVars = {}; for (const s of document.styleSheets) { try { for (const r of s.cssRules) if (/^(:root|html|body)$/.test(r.selectorText || '')) for (const pr of r.style) if (pr.startsWith('--')) o.cssVars[pr] = r.style.getPropertyValue(pr).trim(); } catch { } }
      o.fontsLoaded = [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight); return o; }));
    W('copy.json', await p.evaluate(() => [...document.querySelectorAll('header,nav,main>*,section,footer')].filter(s => !s.parentElement.closest('section,footer')).map(s => ({ sel: s.tagName.toLowerCase() + '.' + (s.getAttribute('class') || '').split(' ')[0] + (s.id ? '#' + s.id : ''), text: s.innerText.replace(/\n{2,}/g, '\n').trim() }))));
    W('meta.json', await p.evaluate(() => ({ title: document.title, lang: document.documentElement.lang, metas: [...document.querySelectorAll('meta')].map(m => [m.name || m.getAttribute('property'), m.content]).filter(m => m[0]),
      headings: [...document.querySelectorAll('h1,h2,h3')].map(h => h.tagName + ' ' + h.textContent.trim().slice(0, 60)), links: [...document.querySelectorAll('a[href]')].map(a => [a.innerText.trim().slice(0, 30), a.getAttribute('href')]).filter(x => x[0]).slice(0, 80) })));
    // components: group by class signature, keep repeated or prominent groups
    const comps = await p.evaluate(() => { const g = {};
      for (const e of document.querySelectorAll('body *')) { const r = e.getBoundingClientRect(); if (r.width < 24 || r.height < 16) continue; const cls = (e.getAttribute('class') || '').trim().split(/\s+/)[0]; if (!cls || cls.length > 40) continue;
        (g[cls] ??= []).push(e); }
      const out = []; let i = 0;
      for (const [cls, els] of Object.entries(g)) { const e = els[0]; const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
        const prominent = r.width * r.height > 20000 && ['button', 'a', 'section', 'article', 'header', 'nav', 'footer', 'form', 'details', 'li'].includes(e.tagName.toLowerCase());
        if (els.length < 2 && !prominent && !/btn|button|card|pill|chip|badge|window|win|modal|tab|toggle|nav|menu|tag|bubble|row|item|cta/i.test(cls)) continue;
        e.setAttribute('data-capc', i);
        out.push({ i: i++, cls, tag: e.tagName.toLowerCase(), count: els.length, w: Math.round(r.width), h: Math.round(r.height),
          style: { bg: s.backgroundColor, bgImg: s.backgroundImage.slice(0, 160), color: s.color, font: `${s.fontSize}/${s.lineHeight} ${s.fontWeight}`, radius: s.borderRadius, shadow: s.boxShadow.slice(0, 160), border: s.border, padding: s.padding, gap: s.gap, display: s.display, backdrop: s.backdropFilter, transition: s.transition.slice(0, 140) },
          children: [...e.children].slice(0, 8).map(c => c.tagName.toLowerCase() + '.' + ((c.getAttribute('class') || '').split(' ')[0] || '')), text: (e.innerText || '').trim().slice(0, 60) }); }
      return out.sort((a, b) => b.count - a.count).slice(0, 80); });
    for (const c of comps.slice(0, 50)) { try { const el = p.locator(`[data-capc="${c.i}"]`).first(); await el.scrollIntoViewIfNeeded({ timeout: 1500 }); await sleep(250);
      const bx = await el.boundingBox(); if (bx && bx.width < w && bx.height < h * 1.5) await el.screenshot({ path: `${OUT}/shots/components/${String(c.i).padStart(2, '0')}-${c.cls.replace(/[^a-z0-9-]/gi, '')}.jpg`, type: 'jpeg', quality: 70, timeout: 3000 }); } catch { } }
    W('components.json', comps);
    // hovers
    const hv = []; const targets = await p.$$('a, button, [role=button], summary, label, [class*=card], [class*=btn]');
    for (const el of targets.slice(0, 80)) { try { if (!(await el.isVisible())) continue; await el.scrollIntoViewIfNeeded({ timeout: 1000 }); await p.mouse.move(1, 1); await sleep(220);
      const read = () => el.evaluate(e => { const c = getComputedStyle(e); return { o: c.opacity, t: c.transform, bg: c.backgroundColor, col: c.color, sh: c.boxShadow.slice(0, 80), f: c.filter, tr: c.transition.slice(0, 120) }; });
      const a = await read(); await el.hover({ timeout: 1200 }); await sleep(450); const z = await read(); const d = {};
      for (const k of ['o', 't', 'bg', 'col', 'sh', 'f']) if (a[k] !== z[k]) d[k] = [a[k], z[k]];
      if (Object.keys(d).length) hv.push({ el: await el.evaluate(e => (e.tagName + '.' + (e.getAttribute('class') || '').split(' ')[0] + ' ' + (e.innerText || '').trim().slice(0, 20))), delta: d, transition: a.tr }); } catch { } }
    W('hovers.json', hv);
    // scroll-linked motion: inline transforms per 200px step
    await p.evaluate(() => window.__to(0)); await sleep(600); const H0 = await p.evaluate(() => window.__H()); const sc = [];
    for (let y = 0; y <= H0; y += 200) { await p.evaluate(y => window.__to(y), y); await sleep(140);
      sc.push(await p.evaluate(() => [window.__y(), ...[...document.querySelectorAll('[style*="transform"],[style*="translate"],[style*="opacity"]')].filter(e => { const r = e.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && r.height > 0; }).slice(0, 8).map(e => ((e.getAttribute('class') || e.tagName).split(' ')[0]) + ':' + (e.style.transform || e.style.translate || '') + (e.style.opacity ? ' o' + e.style.opacity : ''))])); }
    W('scroll.json', sc);
    W('timeline-scroll.json', await p.evaluate(() => window.__tl.slice()));
    W('stack.json', await p.evaluate(() => { const res = performance.getEntriesByType('resource').map(r => r.name); const g = k => { try { return !!window[k] } catch { return false } };
      return { next: !!document.querySelector('script[src*="/_next/"]'), nuxt: g('__NUXT__'), astro: !!document.querySelector('[data-astro-cid],astro-island'), webflow: !!document.querySelector('[data-wf-page]'), framer: !!document.querySelector('[data-framer-name],[data-framer-component-type]'),
        gsap: g('gsap'), scrollTrigger: g('ScrollTrigger'), lenis: g('Lenis') || !!document.querySelector('.lenis,html.lenis'), three: g('THREE') || res.some(u => /three/.test(u)), lottie: g('lottie') || g('bodymovin') || res.some(u => /lottie|bodymovin/.test(u)) || !!document.querySelector('lottie-player,dotlottie-player'), rive: res.some(u => /\.riv|rive\.wasm/.test(u)), spline: res.some(u => /spline/.test(u)),
        generator: document.querySelector('meta[name=generator]')?.content || null } }));
    W('effects.json', await p.evaluate(() => ({ shaders: window.__gl.shaders, uniforms: window.__gl.uniforms,
      svgFilters: [...document.querySelectorAll('filter')].map(f => f.outerHTML.slice(0, 2500)),
      canvases: [...document.querySelectorAll('canvas')].map(c => { const r = c.getBoundingClientRect(); return { cls: c.getAttribute('class'), parent: (c.parentElement?.getAttribute('class') || '').slice(0, 40), attr: [c.width, c.height], css: [Math.round(r.width), Math.round(r.height)] }; }),
      media: performance.getEntriesByType('resource').map(r => r.name).filter(u => /\.(riv|wasm|json|lottie|mp4|webm|glb|gltf|hdr|svg)(\?|$)/i.test(u)).slice(0, 80) })));
    W('network.json', await p.evaluate(() => performance.getEntriesByType('resource').map(r => [r.initiatorType, r.name.replace(location.origin, ''), Math.round(r.transferSize / 1024)])));
  }

  // ---------- per-breakpoint geometry ----------
  await p.evaluate(() => window.__to(0)); await sleep(700);
  geometry[vp] = await p.evaluate(() => { const sY = window.__y(); const root = window.__root(); const box = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + sY), Math.round(r.width), Math.round(r.height)]; };
    const secs = [...document.querySelectorAll('body header, body nav, body section, body footer, main > *')].filter(s => !s.parentElement.closest('section,footer') && s.offsetHeight > 30);
    let uniq = [...new Set(secs)];
    // fallback for div-only builders (Framer, Webflow, Wix): descend single-child wrappers, then take the tall full-width children
    if (root || uniq.filter(s => s.offsetHeight > 200).length < 3) {
      // flatten display:contents wrappers (Framer's ssr-variant) and use rect heights (offsetHeight is 0 for some positioned/contents nodes)
      const kidsOf = e => [...e.children].flatMap(k => getComputedStyle(k).display === 'contents' ? kidsOf(k) : [k]).filter(k => !/^(SCRIPT|STYLE|LINK|NOSCRIPT|IFRAME)$/.test(k.tagName));
      const hh = k => k.getBoundingClientRect().height;
      let el = root || document.querySelector('main') || document.body; let best = [];
      for (let d = 0; d < 16; d++) { const kids = kidsOf(el).filter(k => hh(k) > 40);
        const blocks = kids.filter(k => k.getBoundingClientRect().width > innerWidth * 0.6);
        if (blocks.length >= 3) { best = blocks; break; }
        if (blocks.length > best.length) best = blocks;
        const next = kids.sort((a, b) => hh(b) - hh(a))[0]; if (!next) break; el = next; }
      uniq = best; }
    return { viewport: [innerWidth, innerHeight], pageHeight: window.__H(), scrollRoot: root ? (root.tagName + '.' + (root.getAttribute('class') || '').split(' ')[0]) : 'window',
      sections: uniq.map(s => { const kids = [...s.querySelectorAll('*')].filter(k => { const r = k.getBoundingClientRect(); return r.width * r.height > 6000 && k.children.length < 30; }).slice(0, 40);
        const cs = getComputedStyle(s);
        return { sel: s.tagName.toLowerCase() + (s.id ? '#' + s.id : '') + '.' + (s.getAttribute('class') || '').split(' ')[0], box: box(s), padding: cs.padding, display: cs.display, position: cs.position, sticky: /sticky|fixed/.test(cs.position),
          contentWidth: Math.max(0, ...kids.map(k => k.getBoundingClientRect().width).filter(x => x < innerWidth - 20)),
          keyBoxes: kids.slice(0, 25).map(k => [(k.tagName + '.' + (k.getAttribute('class') || '').split(' ')[0]).slice(0, 40), ...box(k)]),
          absProps: [...s.querySelectorAll('*')].filter(k => getComputedStyle(k).position === 'absolute' && k.getBoundingClientRect().width > 20).slice(0, 40).map(k => { const c = getComputedStyle(k); return [(k.tagName + '.' + (k.getAttribute('class') || '').split(' ').slice(0, 3).join('.')).slice(0, 50), ...box(k), c.transform === 'none' ? '' : c.transform, c.zIndex]; }) }; }) }; });
  // ---------- per-breakpoint shots: step, force reveals on each step ----------
  const H = geometry[vp].pageHeight; let i = 0;
  for (let y = 0; y < H; y += Math.round(h * 0.75)) { await p.evaluate(y => window.__to(y), y); await sleep(QUICK ? 500 : 1100);
    await p.screenshot({ path: `${OUT}/shots/${vp}/${String(i++).padStart(2, '0')}-y${y}.jpg`, type: 'jpeg', quality: 62 }); }
  await p.evaluate(() => { document.querySelectorAll('[class*=reveal],[class*=fade],[class*=dim],[data-reveal],[data-aos]').forEach(e => { e.style.opacity = 1; e.style.transform = 'none'; e.style.translate = 'none'; e.style.scale = 'none'; }); scrollTo(0, 0); });
  await sleep(800); await p.screenshot({ path: `${OUT}/shots/${vp}/full.jpg`, type: 'jpeg', quality: 55, fullPage: true }).catch(() => { });
  geometry[vp].errors = errors;
  const v = p.video(); await ctx.close(); if (v) { try { fs.renameSync(await v.path(), `${OUT}/video/${vp}.webm`); } catch { } }
  fs.rmSync(`${OUT}/video/_${vp}`, { recursive: true, force: true });
}
W('geometry.json', geometry);
// reduced-motion pass: what still runs
const rc = await b.newContext({ locale: 'en-US', viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' }); const rp = await rc.newPage();
await rp.goto(URL, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => { }); await sleep(3000);
W('reduced-motion.json', await rp.evaluate(() => document.getAnimations().filter(a => a.playState === 'running').map(a => a.animationName || a.transitionProperty || 'waapi')));
await rc.close(); await b.close();
console.log('capture done →', OUT);
