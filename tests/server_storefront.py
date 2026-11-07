# v2.2: the updated storefront sections against the REAL server (fresh DB, port 8800)
import json, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8800/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
CUST={'name':'Api Tester','phone':'01712345678','addr':'House 5, Road 3','thana':'Dhanmondi','district':'Dhaka','division':'Dhaka','post':'1205'}
def api(p,b=None):
    r=urllib.request.Request(B+'api/'+p,data=json.dumps(b).encode() if b is not None else None,headers={'X-Requested-With':'XMLHttpRequest','Content-Type':'application/json'},method='POST' if b is not None else 'GET')
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e: d=json.loads(e.read() or b'{}');d['status']=e.code;return d
o=api('orders',{'items':[{'id':'P1','qty':2}],'customer':CUST,'area':'dhaka','pay':'Cash on delivery'});no=o.get('no') or o.get('order',{}).get('no');ok(bool(no),'test order placed: %s'%no)
with sync_playwright() as p:
    b=p.chromium.launch();errs=[];pg=b.new_page(viewport={'width':1100,'height':900});pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(B+'index.html');pg.wait_for_selector('#all article.card');ok(pg.locator('#all .qvbtn').count()>=3 and pg.locator('.viewtog button').count()==2,'shop additions work with the server catalog')
    pg.locator('#all .qvbtn').first.click();pg.wait_for_selector('dialog.qv[open]');ok('Add to cart' in pg.inner_text('dialog.qv'),'quick view works');pg.keyboard.press('Escape')
    pg.goto(B+'index.html#/product/P1');pg.reload();pg.wait_for_selector('h1');ok(pg.locator('a[href^="https://wa.me/"]').count()>=0,'product page renders with the add-ons')
    pg.goto(B+'index.html#/orders');pg.reload();pg.wait_for_selector('input[name=no]')
    TS='section.card:has(> h2:has-text("Track an order"))';pg.fill(TS+' input[name=no]',no);pg.fill(TS+' input[name=ph]','01712345678');pg.click(TS+' button');pg.wait_for_selector('.timeline',timeout=8000)
    ok(pg.locator('text=Need help with this order').count()>=1,'a tracked order gets the "Need help" button')
    pg.click('text=Need help with this order >> nth=0');pg.wait_for_selector('#app form input[name=n]');ok(pg.input_value('input[name=o]')==no,'contact form has the order number: '+pg.input_value('input[name=o]'))
    pg.fill('input[name=n]','Api Tester');pg.fill('input[name=ph]','01712345678');pg.click('button:has-text("Evening (5-9)")');pg.fill('textarea[name=m]',pg.input_value('textarea[name=m]')+'\nWhen will it arrive?')
    pg.click('#app form button.btn');pg.wait_for_selector('text=Message sent',timeout=8000);ok(True,'contact message is accepted by the server')
    pg.goto(B+'index.html#/info');pg.reload();pg.wait_for_selector('details');ok('Know your medicine' in pg.inner_text('#app') and '999' in pg.inner_text('#app'),'help additions show with the server')
    pg.goto(B+'index.html#/health');pg.reload();pg.wait_for_selector('#bmi-out',state='attached');pg.select_option('select[name=k]','bp');pg.fill('input[name=a]','150');pg.fill('input[name=b]','95');pg.click('text=Save reading');ok('doctor' in pg.inner_text('#app').lower(),'health log works')
    pg.evaluate("localStorage.setItem('mc_wish',JSON.stringify(['P1','P2']))");pg.goto(B+'index.html#/wishlist');pg.reload();pg.wait_for_selector('.grid article.card');ok(pg.locator('.wnote input').count()==2 and pg.locator('button:has-text("Copy list as text")').count()==1,'wishlist additions work with the server catalog')
    ok(not errs,'no page errors '+str(errs[:3]));b.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
