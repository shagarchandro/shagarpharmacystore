# Accessibility audit with axe-core (demo mode, serve the folder on 8765; needs: npm i axe-core in /tmp/axe)
import json, sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';AXE=open('/tmp/axe/node_modules/axe-core/axe.min.js').read();bad={}
PAGES=[('index.html#/','shop'),('index.html#/wishlist','wishlist'),('index.html#/orders','orders'),('index.html#/info','help'),('index.html#/contact','contact'),('index.html#/health','health'),('index.html#/compare','compare'),('index.html#/product/P1','product'),('index.html#/cart','cart'),('admin/login.html','login')]
ADMIN=['dash','products','inv','pos','orders','reports','insights','refill','labels','pricelist','expiry','margins','reorder','customer360','account']
def run(pg,name):
    pg.evaluate(AXE);r=pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']})")
    for v in r['violations']:
        if v['impact'] in('serious','critical') or v['id'] in('label','button-name','link-name','color-contrast'):
            bad.setdefault(v['id']+' ['+v['impact']+'] '+v['help'],[]).append(name+': '+', '.join(n['target'][-1] if isinstance(n['target'][-1],str) else str(n['target'][-1]) for n in v['nodes'][:3]))
with sync_playwright() as p:
    br=p.chromium.launch()
    for dark in (False,True):
        ctx=br.new_context(viewport={'width':1100,'height':800},color_scheme='dark' if dark else 'light');pg=ctx.new_page()
        pg.add_init_script("localStorage.setItem('mc_wish',JSON.stringify(['P1']));localStorage.setItem('mc_cart',JSON.stringify({P1:1}))")
        for u,n in PAGES:
            pg.goto(B+u);pg.reload();pg.wait_for_timeout(500);run(pg,('dark ' if dark else '')+n)
        a=ctx.new_page();a.add_init_script("sessionStorage.setItem('mc_role','Owner')");a.goto(B+'admin/index.html');a.wait_for_selector('#side nav button')
        for t in ADMIN:
            b=a.locator('#side nav button[data-t=%s]'%t)
            if b.count():
                b.click();a.wait_for_timeout(350);run(a,('dark ' if dark else '')+'admin-'+t)
    br.close()
for k,v in sorted(bad.items()):print(k,'\n    ',' | '.join(sorted(set(v))[:6]))
print('RULES WITH PROBLEMS:',len(bad))
