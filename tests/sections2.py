# v2.1 storefront section additions (demo mode, port 8765)
import json, sys, datetime
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
FAKE="""window.BarcodeDetector=class{async detect(){return [{rawValue:'8901234567890'}]}};
navigator.mediaDevices.getUserMedia=async()=>document.createElement('canvas').captureStream();"""
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':1200,'height':900});ctx.add_init_script(FAKE);pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(B+'index.html');pg.wait_for_selector('#all article.card')
    d=pg.evaluate("db()");d['products']=[dict(x,barcode='8901234567890') if x['id']=='P1' else x for x in d['products']]
    pg.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d);pg.reload();pg.wait_for_selector('#all article.card')
    # ---- Shop
    ok(pg.locator('#all .ppu').count()>=3,'price per unit shown on cards: '+pg.locator('#all .ppu').first.inner_text())
    pg.fill('.filters input[type=search]','napa');pg.press('.filters input[type=search]','Tab');pg.wait_for_timeout(200);pg.reload();pg.wait_for_selector('#all article.card')
    ok(pg.locator('button:has-text("napa")').count()>=1,'recent search chip is kept')
    pg.click('button:has-text("napa") >> nth=0');pg.wait_for_timeout(300);ok(pg.input_value('.filters input[type=search]')=='napa','recent search chip searches again')
    pg.click('.scanbtn');pg.wait_for_selector('dialog.qv video');pg.wait_for_function("location.hash==='#/product/P1'",timeout=6000);ok(True,'barcode scan opens the matching product')
    ok(pg.locator('dialog.qv').count()==0,'scanner closes after a match')
    # alternatives: two products with the same generic
    d=pg.evaluate("db()");pr=[x for x in d['products'] if x['id']=='P1'][0]
    d['products'].append(dict(pr,id='PX9',name='Napa Cheap',price=max(1,pr['price']-3),disc=0,pack=pr['pack']))
    pg.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d)
    for b in d['batches'][:1]: pass
    d['batches'].append({'id':'BX9','pid':'PX9','no':'BX9','qty':50,'exp':'2030-01-01','cost':1,'supplier':''});pg.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d)
    pg.goto(B+'index.html#/product/P1');pg.reload();pg.wait_for_selector('h1');t=pg.inner_text('#app')
    ok('Same ingredient, other brands' in t and 'Napa Cheap' in t,'product page lists other brands with the same ingredient')
    # ---- Wishlist
    pg.evaluate("localStorage.setItem('mc_wish',JSON.stringify(['P1','P2','PX9']))");pg.goto(B+'index.html#/wishlist');pg.reload();pg.wait_for_selector('.grid article.card')
    ok(pg.locator('.wnote input').count()==3,'each wishlist card has a note box')
    pg.fill('.wnote input >> nth=0','for Dad');pg.press('.wnote input >> nth=0','Tab');ok('for Dad' in pg.evaluate("localStorage.getItem('mc_wnote')"),'wishlist note is saved')
    pg.select_option('select[aria-label=Sort]','lo');names=pg.eval_on_selector_all('.grid article.card h3','e=>e.map(x=>x.textContent)');pr_=pg.eval_on_selector_all('.grid article.card','e=>e.length');ok(pr_==3,'sorting keeps all cards (%s)'%names)
    pg.reload();pg.wait_for_selector('.grid article.card');ok(pg.input_value('select[aria-label=Sort]')=='lo','sort choice is remembered')
    ok(pg.locator('a:has-text("WhatsApp")').count()==1 and pg.locator('button:has-text("Copy list as text")').count()==1,'copy and WhatsApp for the list')
    # ---- Orders
    now=datetime.datetime.now(datetime.timezone.utc)
    d=pg.evaluate("db()");d['orders']=[{'id':'O1','no':'INV-2001','at':(now-datetime.timedelta(days=40)).isoformat(),'customer':'Test Buyer','phone':'01712345678','addr':'Dhaka','items':[{'id':'P1','pid':'P1','qty':2,'price':12,'name':'Napa'}],'total':80,'status':'Delivered','rx':False,'note':''},
        {'id':'O2','no':'INV-2002','at':(now-datetime.timedelta(days=3)).isoformat(),'customer':'Test Buyer','phone':'01712345678','addr':'Dhaka','items':[{'id':'P2','pid':'P2','qty':1,'price':70,'name':'Seclo'}],'total':130,'status':'Pending','rx':False,'note':''}]
    pg.evaluate("(d)=>{localStorage.setItem('mc_db',JSON.stringify(d));localStorage.setItem('mc_user','Test Buyer')}",d);pg.goto(B+'index.html#/orders');pg.reload();pg.wait_for_selector('article.card .timeline')
    ok('Time to reorder?' in pg.inner_text('#app') and '40 days ago' in pg.inner_text('#app'),'reorder suggestion for a product bought 40 days ago')
    ok('Spending by month' in pg.inner_text('#app') and pg.locator('#app .hbars .br').count()==6,'six-month spending chart')
    pg.click('section:has-text("Time to reorder?") button:has-text("Add to cart")');ok(pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('mc_cart')||'{}')).includes('P1')"),'reorder suggestion adds to cart')
    # ---- Contact
    pg.goto(B+'index.html#/contact');pg.reload();pg.wait_for_selector('form input[name=n]')
    pg.click('button:has-text("Evening (5-9)")');ok('Please call me back: Evening (5-9).' in pg.input_value('textarea[name=m]'),'call-back time is added to the message')
    pg.click('button:has-text("Morning (9-12)")');v=pg.input_value('textarea[name=m]');ok(v.count('Please call me back')==1 and 'Morning' in v,'changing the call-back time replaces the line')
    pg.select_option('select[aria-label="Pick a recent order"]',index=1);ok(pg.input_value('input[name=o]').startswith('INV-200'),'recent order picked into the order field')
    # ---- Help
    pg.goto(B+'index.html#/info');pg.reload();pg.wait_for_selector('details');ok('Using this website' in pg.inner_text('#app') and 'Know your medicine' in pg.inner_text('#app'),'help has the medicine knowledge group')
    pg.fill('#app input[type=search]','expiry');pg.wait_for_timeout(200);ok(pg.locator('details:visible').count()>=1,'help search finds the new answers')
    pg.goto(B+'faq.html');pg.wait_for_selector('details');ok('Know your medicine' in pg.inner_text('#app'),'direct visit to faq.html also shows the new groups')
    # ---- Health
    pg.goto(B+'index.html#/health');pg.reload();pg.wait_for_selector('#bmi-out',state='attached')
    pg.fill('input[name=dn]','Cefixime');pg.select_option('select[name=di]','8');pg.fill('input[name=ds]','06:00');pg.click('text=Create reminders');pg.wait_for_selector('.rem-list li >> text=Cefixime')
    rem=pg.evaluate("JSON.parse(localStorage.getItem('mc_rem')).map(x=>x.time).sort()");ok(rem==['06:00','14:00','22:00'],'every 8 hours from 06:00: %s'%rem)
    pg.fill('input[name=sn]','Metformin');pg.fill('input[name=su]','60');pg.fill('input[name=sp]','2');pg.click('article:has-text("Supply calculator") button:has-text("Calculate")');ok('30 day' in pg.inner_text('#app'),'60 units at 2 a day last 30 days')
    with pg.expect_download() as dl:
        pg.click('text=Add to calendar')
    path=dl.value.path();txt=open(path).read();ok(dl.value.suggested_filename=='reorder.ics' and 'BEGIN:VEVENT' in txt and 'Metformin' in txt,'calendar file is downloaded')
    ok(not errs,'no page errors '+str(errs[:3]));br.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
sys.exit(1 if any(r.startswith('FAIL') for r in res) else 0)
