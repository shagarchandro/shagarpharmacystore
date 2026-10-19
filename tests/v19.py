# Real-browser tests: shop name. Serve on port 8765 first.
import json
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';N='Shagar Medical Store';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    c=b.new_context(viewport={'width':1280,'height':900}); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)[:100])); pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card')
    ok(N in pg.title() and N in pg.inner_text('header .brand') and N in pg.inner_text('footer.foot'),'title, header and footer show the new name')
    pg.evaluate("window.scrollTo(0,0)")
    bad=[]
    for u in ['index.html','index.html#/cart','index.html#/info','index.html#/contact','index.html#/orders','index.html#/wishlist','faq.html','privacy.html']:
        pg.goto(B+u); pg.wait_for_timeout(200); t=pg.inner_text('body')
        if 'medicare' in t.lower(): bad.append(u)
    ok(not bad,'no visible trace of the old name on storefront pages '+str(bad))
    m=json.loads(pg.evaluate("fetch('manifest.webmanifest').then(r=>r.text())")); ok(m['name']==N,'web app manifest uses the new name')
    c.close()
    # migration of an older saved database
    c=b.new_context(viewport={'width':1280,'height':900}); pg=c.new_page(); pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.settings.store='MediCare Pharmacy';d.settings.logoText='MediCare';localStorage.mc_db=JSON.stringify(d)})()"); pg.reload(); pg.wait_for_selector('#all article.card'); ok(N in pg.inner_text('header .brand'),'older saved data (old name) is migrated to the new name')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.settings.store='My Own Name';d.settings.logoText='My Own Name';localStorage.mc_db=JSON.stringify(d)})()"); pg.reload(); pg.wait_for_selector('#all article.card'); ok('My Own Name' in pg.inner_text('header .brand'),'a name the owner chose in Settings is never overwritten')
    c.close()
    c=b.new_context(viewport={'width':1280,'height':900}); c.add_init_script("sessionStorage.setItem('mc_role','Owner')"); pg=c.new_page(); pg.on('dialog',lambda d:d.accept()); pg.goto(B+'admin/pos.html'); pg.wait_for_selector('#pq')
    ok(N in pg.inner_text('#side .brand') and N in pg.title(),'admin sidebar and title show the new name')
    pg.fill('#pq','890001000'); pg.press('#pq','Enter'); pg.wait_for_timeout(150); pg.fill('[aria-label="Cash received"]','100'); pg.click('button:text-is("Complete sale")'); pg.wait_for_selector('dialog[open]'); ok(N in pg.inner_text('dialog[open]'),'POS receipt shows the new name'); pg.screenshot(path='/tmp/brand_admin.png')
    pg.goto(B+'admin/login.html'); pg.wait_for_selector('h1'); ok(N in pg.inner_text('h1'),'admin login shows the new name'); c.close()
    c=b.new_context(viewport={'width':360,'height':740}); pg=c.new_page(); pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card'); pg.screenshot(path='/tmp/brand_mobile.png'); ok(pg.evaluate("document.documentElement.scrollWidth-innerWidth")<=1,'long name does not overflow a 360 px phone')
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
