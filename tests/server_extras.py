# v1.3 add-ons in REAL server mode: new screens render for the Owner, new pages are served, version is 3.1.0
import json, urllib.request
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8800/';OWNER='Sunrise-Tea-4471';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
h=json.load(urllib.request.urlopen(B+'api/health'));ok(h.get('version')=='3.1.0','health reports version 3.1.0: '+str(h.get('version')))
for u in ('assets/css/design.css','assets/fonts/bricolage-grotesque-latin-wght-normal.woff2','assets/fonts/hind-siliguri-bengali-400-normal.woff2','assets/fonts/hind-siliguri-latin-700-normal.woff2','assets/js/extras.js','assets/js/admin-extras.js','health.html','compare.html','admin/insights.html','admin/refill.html','admin/labels.html','admin/pricelist.html','admin/customer360.html','admin/expiry.html','admin/margins.html','admin/reorder.html'):
    r=urllib.request.urlopen(B+u);ok(r.status==200,'served: '+u)
with sync_playwright() as p:
    b=p.chromium.launch();bad=[];c=b.new_context();pg=c.new_page()
    pg.on('console',lambda m:bad.append(m.text[:140]) if m.type=='error' and '404' not in m.text else None);pg.on('pageerror',lambda e:bad.append('PAGEERR '+str(e)[:140]))
    pg.goto(B+'index.html');pg.wait_for_selector('article.card');pg.locator('button[data-cmp]').nth(0).click();pg.locator('button[data-cmp]').nth(1).click();pg.click('.cmpbar a');pg.wait_for_selector('.cmp-table')
    ok(pg.locator('.cmp-table thead th').count()==3,'compare works with the server catalog')
    pg.goto(B+'index.html#/health');pg.wait_for_selector('#bmi-out',state='attached');ok(True,'health page')
    pg.goto(B+'admin/login.html');pg.wait_for_selector('#lu');pg.fill('#lu','owner');pg.fill('#lp',OWNER);pg.click('button.btn');pg.wait_for_url('**/admin/index.html');pg.wait_for_selector('#side nav button')
    for t in ('customer360','insights','refill','labels','pricelist','expiry','margins','reorder'):
        pg.click(f'#side nav button[data-t={t}]');pg.wait_for_selector('#app h1');pg.wait_for_timeout(300)
        ok(len(pg.inner_text('#app'))>40 and 'Something went wrong' not in pg.inner_text('#app'),'owner screen renders: '+t)
    pg.goto(B+'index.html#/sharecart/P1.2');pg.wait_for_selector('text=Shared cart');ok(True,'share cart page')
    pg.goto(B+'admin/index.html');pg.wait_for_selector('#side nav button');pg.click('#side nav button[data-t=dash]');pg.wait_for_selector('text=Today at a glance');ok(True,'dashboard add-on (server)')
    pg.click('#side nav button[data-t=labels]');pg.click('text=Select all shown');pg.click('text=Preview and print');pg.wait_for_selector('dialog .lbl');ok(pg.locator('dialog .lbl svg').count()>=1,'labels preview with barcodes')
    ok(not bad,'no console or policy errors '+str(bad[:3]))
    b.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
