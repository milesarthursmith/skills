// Run identical probes on a URL; write probe JSON + screenshots. Usage: node compare.mjs <url> <outdir>
let chromium; try { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); } catch { ({ chromium } = await import('playwright')); }
import fs from 'fs';
const [URL,OUT]=process.argv.slice(2); fs.mkdirSync(OUT+'/sec',{recursive:true}); fs.mkdirSync(OUT+'/m',{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const b=await chromium.launch({args:['--no-sandbox','--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
const res={};
for (const [vp,w,h] of [['desktop',1440,900],['mobile',390,844]]){
  const ctx=await b.newContext({locale:'en-US',viewport:{width:w,height:h},isMobile:vp==='mobile',hasTouch:vp==='mobile'});
  const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message.slice(0,120)));
  await p.addInitScript(()=>{window.__cls=[];const t0=performance.now();new MutationObserver(ms=>{for(const m of ms){if(m.attributeName==='class'&&m.target.nodeType===1)window.__cls.push([Math.round(performance.now()-t0),(m.target.tagName+'.'+(m.target.getAttribute('class')||'')).slice(0,60)])}}).observe(document,{subtree:true,attributes:true,attributeFilter:['class']})});
  await p.goto(URL,{waitUntil:'networkidle',timeout:60000}); await sleep(3000);
  const r={errs};
  r.page=await p.evaluate(()=>{
    const secs=[...document.querySelectorAll('body section, body footer')].filter(s=>!s.parentElement.closest('section,footer'));
    return {H:document.documentElement.scrollHeight, sections:secs.map(s=>({cls:(s.className+'').split(' ')[0]||s.tagName,id:s.id,top:Math.round(s.getBoundingClientRect().top+scrollY),h:s.offsetHeight})),
      canvases:document.querySelectorAll('canvas').length, videos:document.querySelectorAll('video').length, draggables:document.querySelectorAll('.draggable,[data-drag],[draggable]').length,
      bodyBg:getComputedStyle(document.body).backgroundColor, h1:(()=>{const e=document.querySelector('h1,.headline');if(!e)return null;const c=getComputedStyle(e);return [e.textContent.trim().slice(0,30),c.fontSize,c.fontWeight,c.letterSpacing,c.fontFamily.split(',')[0]]})(),
      idleAnims:document.getAnimations().map(a=>[a.animationName||a.transitionProperty||'waapi',Math.round(a.effect?.getTiming().duration||0)]).slice(0,30)}});
  // tokens
  r.tokens=await p.evaluate(()=>{const c={};const add=(k,v)=>{if(!v||v==='none'||v==='rgba(0, 0, 0, 0)'||v==='0px')return;(c[k]??={})[v]=(c[k][v]||0)+1};
    for(const e of document.querySelectorAll('body *')){if(!e.getClientRects().length)continue;const s=getComputedStyle(e);add('color',s.color);add('bg',s.backgroundColor);add('font',s.fontFamily.split(',')[0]);add('radius',s.borderRadius);add('shadow',s.boxShadow);add('transition',s.transitionTimingFunction==='ease'?null:s.transitionTimingFunction)}
    const o={};for(const k in c)o[k]=Object.entries(c[k]).sort((a,b)=>b[1]-a[1]).slice(0,10);return o});
  // section screenshots: scroll each section to top, settle
  for(const [i,s] of r.page.sections.entries()){ await p.evaluate(y=>scrollTo(0,y),Math.max(0,s.top-60)); await sleep(1300); await p.screenshot({path:`${OUT}/sec/${vp}-${String(i).padStart(2,'0')}.jpg`,type:'jpeg',quality:55}); }
  if(vp==='desktop'){
    // marquee probe: any element whose inline transform changes with scroll
    await p.evaluate(()=>scrollTo(0,0)); await sleep(800);
    const samples=[]; for(let y=0;y<=r.page.H;y+=300){await p.evaluate(y=>scrollTo(0,y),y);await sleep(160);
      samples.push(await p.evaluate(()=>[scrollY,...[...document.querySelectorAll('[style*="transform"],[style*="translate"]')].filter(e=>e.getBoundingClientRect().height>0).slice(0,4).map(e=>(e.className+'').split(' ')[0]+':'+(e.style.transform||e.style.translate).slice(0,40))]))}
    r.scrollLinked=samples.filter(s=>s.length>1);
    // hover probe on buttons/links
    r.hover=[]; const hs=await p.$$('a, button'); for(const el of hs.slice(0,25)){try{const vis=await el.isVisible();if(!vis)continue;await el.scrollIntoViewIfNeeded();await p.mouse.move(1,1);await sleep(200);const a=await el.evaluate(e=>{const c=getComputedStyle(e);return [c.opacity,c.transform,c.backgroundColor,c.transition.slice(0,60)]});await el.hover({timeout:1500});await sleep(400);const z=await el.evaluate(e=>{const c=getComputedStyle(e);return [c.opacity,c.transform,c.backgroundColor]});if(a[0]!==z[0]||a[1]!==z[1]||a[2]!==z[2])r.hover.push([(await el.innerText()).slice(0,20),a,z])}catch{}}
    // reduced motion check
  }
  r.classTimeline=await p.evaluate(()=>window.__cls.filter(x=>/rvg-in|revealed|asking|answering|sec-dim|glass-cheap|dimmed/.test(x[1])).slice(0,40));
  res[vp]=r; await ctx.close();
}
// reduced motion
const rc=await b.newContext({locale:'en-US',viewport:{width:1440,height:900},reducedMotion:'reduce'}); const rp=await rc.newPage(); await rp.goto(URL,{waitUntil:'networkidle'}); await sleep(2500);
res.reducedRunning=await rp.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length); await rc.close();
fs.writeFileSync(OUT+'/probe.json',JSON.stringify(res,null,1)); await b.close(); console.log('done',OUT);
