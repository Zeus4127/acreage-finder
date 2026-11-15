// Release check for the built page: run before every publish. Exits 1 (and prints why) if anything is broken.
//   node checks/check_page.js path/to/acreage-finder.html
// Checks at phone size (Pixel 5) and desktop: no script errors, every screen shows, nothing runs off the side,
// lists have rows, a block page opens with its sections and Back returns, Home stays short.
const {chromium,devices}=require('playwright');
const file=process.argv[2]; if(!file){console.error('usage: node check_page.js page.html');process.exit(2)}
const fails=[];const ok=(c,msg)=>{if(!c)fails.push(msg)};
(async()=>{
  const b=await chromium.launch();
  for(const [label,ctx] of [['phone',{...devices['Pixel 5']}],['desktop',{viewport:{width:1280,height:900}}]]){
    const c=await b.newContext(ctx);const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
    await p.goto('file://'+require('path').resolve(file));
    try{await p.waitForFunction(()=>document.querySelectorAll('.ri').length>0,{timeout:30000})}catch(e){fails.push(label+': no blocks showed within 30 s')}
    const info=await p.evaluate(()=>({n:(window.ACREAGE_DATA||{}).listings?.length||0,stars:document.querySelectorAll('#hStars .ri').length,h:document.documentElement.scrollHeight}));
    ok(info.n>=2000,`${label}: only ${info.n} listings in the data (expected 2,000+)`);
    ok(info.stars>=1,`${label}: no top picks on Home`);
    if(label==='phone')ok(info.h<6000,`${label}: Home is ${info.h}px tall (should stay under 6,000)`);
    for(const v of ['home','search','saved','insights','more']){
      await p.evaluate(v=>{location.hash=v},v);await p.waitForTimeout(250);
      const r=await p.evaluate(v=>{const s=document.getElementById('v-'+v);return{shown:s&&!s.hidden,wide:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,rows:s?s.querySelectorAll('.ri').length:0}},v);
      ok(r.shown,`${label}: the ${v} screen didn't show`);ok(!r.wide,`${label}: the ${v} screen runs off the side of the screen`);
      if(v==='search')ok(r.rows>=10,`${label}: Search shows only ${r.rows} rows`);
    }
    await p.evaluate(()=>{location.hash='home'});await p.waitForTimeout(250);
    await p.click('#hStars .ri');await p.waitForTimeout(400);
    const bp=await p.evaluate(()=>({hash:location.hash,secs:document.querySelectorAll('#bp .bsec').length,wide:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,link:!!document.querySelector('#bp .actbar a.go[href^="http"]')}));
    ok(bp.hash.startsWith('#block-'),`${label}: tapping a top pick didn't open its page`);ok(bp.secs>=8,`${label}: block page has only ${bp.secs} sections`);
    ok(!bp.wide,`${label}: block page runs off the side`);ok(bp.link,`${label}: block page has no "Open the listing" link`);
    await p.goBack();await p.waitForTimeout(300);ok((await p.evaluate(()=>location.hash))==='#home',`${label}: Back didn't return to Home`);
    ok(errs.length===0,`${label}: script errors: ${errs.slice(0,3).join(' | ')}`);
    await c.close();
  }
  await b.close();
  if(fails.length){console.log('PAGE CHECK FAILED:\n - '+fails.join('\n - '));process.exit(1)}
  console.log('PAGE CHECK PASSED');
})().catch(e=>{console.log('PAGE CHECK FAILED: '+e.message);process.exit(1)});
