# Visible-text audit: no "null", "undefined", "NaN" or "[object" on any storefront page or admin screen (demo mode, port 8765)
import re, sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';bad=[]
PAGES=['index.html#/','index.html#/product/P1','index.html#/cart','index.html#/checkout','index.html#/wishlist','index.html#/orders','index.html#/info','index.html#/contact','index.html#/health','index.html#/compare','admin/login.html']
ADMIN=['dash','alerts','rx','orders','pos','returns','delivery','customer360','refill','customers','products','labels','pricelist','cats','inv','stk','expiry','ledger','purchases','reorder','suppliers','expenses','reports','insights','margins','notes','users','seclog','account','settings','data']
PAT=re.compile(r'\b(null|undefined|NaN)\b|\[object')
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':1280,'height':900});pg=ctx.new_page()
    pg.add_init_script("localStorage.setItem('mc_wish',JSON.stringify(['P1','P2']));localStorage.setItem('mc_cart',JSON.stringify({P1:2}))")
    for u in PAGES:
        pg.goto(B+u);pg.reload();pg.wait_for_timeout(450);t=pg.inner_text('body');m=PAT.search(t)
        if m:bad.append('%s: ...%s...'%(u,t[max(0,m.start()-30):m.end()+20].replace('\n',' ')))
    a=ctx.new_page();a.add_init_script("sessionStorage.setItem('mc_role','Owner')");a.goto(B+'admin/index.html');a.wait_for_selector('#side nav button')
    for t in ADMIN:
        b=a.locator('#side nav button[data-t=%s]'%t)
        if not b.count():continue
        a.evaluate("document.querySelectorAll('details.navgrp').forEach(d=>d.open=true)");b.click();a.wait_for_timeout(350);txt=a.inner_text('#app');m=PAT.search(txt)
        if m:bad.append('admin %s: ...%s...'%(t,txt[max(0,m.start()-30):m.end()+20].replace('\n',' ')))
    br.close()
print('\n'.join(bad) or 'no stray null/undefined/NaN text found');print('PROBLEMS:',len(bad))
sys.exit(1 if bad else 0)
