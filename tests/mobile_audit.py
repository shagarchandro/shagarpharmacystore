# Phone-width layout audit (demo mode, 8765): no sideways scrolling, nothing wider than the screen, tap targets not tiny
import sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
PAGES=['index.html#/','index.html#/wishlist','index.html#/orders','index.html#/info','index.html#/contact','index.html#/health','index.html#/compare','index.html#/product/P1','index.html#/cart','index.html#/checkout','admin/login.html']
ADMIN=['dash','products','inv','pos','orders','reports','insights','refill','labels','pricelist','expiry','margins','reorder','customer360','account','settings','users']
JS="""()=>{const W=document.documentElement.clientWidth,out=[];document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();if(r.width&&r.right>W+1&&getComputedStyle(e).position!=='fixed'){let p=e.parentElement,scroll=false;while(p&&p!==document.body){const o=getComputedStyle(p).overflowX;if(o==='auto'||o==='scroll'||o==='hidden'){scroll=true;break}p=p.parentElement}if(!scroll)out.push((e.tagName+'.'+(e.className||'')).slice(0,50)+' right='+Math.round(r.right))}});return {sw:document.documentElement.scrollWidth,W,over:[...new Set(out)].slice(0,4)}}"""
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':390,'height':800},has_touch=True,is_mobile=True);pg=ctx.new_page()
    pg.add_init_script("localStorage.setItem('mc_wish',JSON.stringify(['P1','P2']));localStorage.setItem('mc_cart',JSON.stringify({P1:1}));localStorage.setItem('mc_hlog',JSON.stringify([{id:'a',t:'bp',at:'2026-11-01T08:00:00Z',a:132,b:84},{id:'b',t:'bp',at:'2026-11-02T08:00:00Z',a:118,b:76}]))")
    for u in PAGES:
        pg.goto(B+u);pg.reload();pg.wait_for_timeout(500);r=pg.evaluate(JS);ok=r['sw']<=r['W']+1 and not r['over']
        res.append(('PASS ' if ok else 'FAIL ')+u+(' '+str(r) if not ok else ''))
    a=ctx.new_page();a.add_init_script("sessionStorage.setItem('mc_role','Owner')");a.goto(B+'admin/index.html');a.wait_for_selector('.burger')
    for t in ADMIN:
        a.evaluate("document.body.classList.add('open')")
        b=a.locator('#side nav button[data-t=%s]'%t)
        if not b.count(): continue
        b.click();a.evaluate("document.body.classList.remove('open')");a.wait_for_timeout(300);r=a.evaluate(JS);ok=r['sw']<=r['W']+1 and not r['over']
        res.append(('PASS ' if ok else 'FAIL ')+'admin '+t+(' '+str(r) if not ok else ''))
    br.close()
print('\n'.join(r for r in res if r.startswith('FAIL')) or 'no layout problems');print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
