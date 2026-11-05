# v1.3 add-ons test (demo mode). Serve the folder on port 8765 first: python3 -m http.server 8765
import json,sys,io,datetime
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';fails=0
def ok(c,m):
    global fails
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails+=1
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context();pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(B+'index.html');pg.wait_for_selector('article.card')
    ok(pg.locator('header nav a[href="#/health"]').count()==1,'Health link in header')
    btns=pg.locator('button[data-cmp]');ok(btns.count()>=4,'compare buttons on cards: %d'%btns.count())
    btns.nth(0).click();btns.nth(1).click()
    ok(pg.locator('.cmpbar').is_visible(),'compare bar visible')
    pg.locator('.cmpbar a').click();pg.wait_for_selector('.cmp-table')
    ok(pg.locator('.cmp-table thead th').count()==3,'compare table has 2 products + label column')
    ok('Price per unit' in pg.inner_text('.cmp-table'),'price per unit row')
    # limit of 3
    pg.goto(B+'index.html');pg.wait_for_selector('article.card');b=pg.locator('button[data-cmp]')
    ok(b.nth(0).get_attribute('aria-pressed')=='true','compare selection remembered')
    b.nth(2).click();b.nth(3).click()
    ok(pg.locator('.cmpbar b').inner_text().startswith('Compare (3/3)'),'max 3 enforced')
    # recently viewed + product extras
    pg.goto(B+'index.html#/product/P1');pg.wait_for_selector('h1');pg.reload()
    pg.goto(B+'index.html#/product/P2');pg.wait_for_selector('h1')
    ok(pg.locator('a[href^="https://wa.me/"]').count()==1,'WhatsApp link')
    ok(pg.locator('.recent').count()==1,'recently viewed on product page')
    pg.goto(B+'index.html#/');pg.wait_for_selector('article.card')
    ok(pg.locator('.recent article.card').count()>=2,'recently viewed on home')
    # health
    pg.goto(B+'index.html#/health');pg.wait_for_selector('#bmi-out',state='attached')
    pg.fill('input[name=h]','170');pg.fill('input[name=w]','70');pg.click('text=Calculate')
    t=pg.inner_text('#bmi-out');ok('BMI 24.2' in t,'BMI computed: '+t[:40])
    ok('ml' in pg.inner_text('#w-out'),'water guide shown')
    pg.fill('input[name=n]','Napa');pg.fill('input[name=t]','08:00');pg.click('text=Add reminder')
    ok('Napa' in pg.inner_text('.rem-list'),'reminder added')
    pg.click('.rem-list >> text=Taken');ok('✓' in pg.inner_text('.rem-list'),'marked taken')
    # reminder fires
    pg.evaluate("(()=>{const n=new Date(),k=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');localStorage.setItem('mc_rem',JSON.stringify([{id:'R1',name:'TestMed',time:k,note:''}]))})()")
    pg.reload();pg.wait_for_selector('.rem-list');pg.wait_for_timeout(800)
    ok('TestMed' in pg.inner_text('#toasts'),'reminder toast fired')
    pg.goto(B+'health.html');pg.wait_for_selector('h1');ok('Health tools' in pg.inner_text('h1'),'health.html page')
    pg.goto(B+'compare.html');pg.wait_for_selector('h1');ok(True,'compare.html page')
    # bangla
    pg.evaluate("localStorage.setItem('mc_lang','bn')");pg.goto(B+'index.html#/health');pg.wait_for_selector('h1')
    ok('স্বাস্থ্য' in pg.inner_text('h1'),'Bangla heading');pg.evaluate("localStorage.removeItem('mc_lang')")
    # ---- v1.4 storefront
    pg.goto(B+'index.html');pg.wait_for_selector('article.card')
    ok(pg.locator('.openb').count()==1 and ('Open now' in pg.inner_text('.openb') or 'Closed now' in pg.inner_text('.openb')),'open/closed badge')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P1:2,P2:1}))");pg.goto(B+'index.html#/cart');pg.wait_for_selector('text=Copy cart link')
    pg.evaluate("localStorage.removeItem('mc_cart')");pg.goto(B+'index.html#/sharecart/P1.2~P2.1~NOPE.3');pg.wait_for_selector('text=Shared cart')
    ok(pg.locator('main li').count()==2,'shared cart lists 2 valid items (unknown id ignored)')
    pg.click('text=Add all to my cart');pg.wait_for_selector('#cc');ok(pg.evaluate("Object.values(JSON.parse(localStorage.getItem('mc_cart'))).reduce((a,b)=>a+b,0)")==3,'shared cart added to cart')
    pg.goto(B+'index.html#/sharecart/%3Cb%3E');pg.wait_for_selector('text=no longer valid');ok(True,'bad share link handled')
    # ---- v1.6 storefront: text size + voice button
    pg.goto(B+'index.html');pg.wait_for_selector('article.card');pg.click('button[aria-label="Text size"]')
    ok(pg.evaluate("document.documentElement.style.fontSize")=='112%','larger text applies');pg.reload();pg.wait_for_selector('article.card')
    ok(pg.evaluate("document.documentElement.style.fontSize")=='112%','text size is remembered');pg.evaluate("localStorage.removeItem('mc_fs')")
    ok(pg.locator('.mic').count()==1,'voice search button shown where the browser supports it')
    # ---- admin
    now=datetime.datetime.utcnow()
    def iso(d,h=10): return (now-datetime.timedelta(days=d)).replace(hour=h).isoformat()+'Z'
    pg.goto(B+'index.html');db=pg.evaluate("db()")
    pr=db['products'][:3]
    db['sales']=[{'id':'S%d'%i,'no':'INV-%d'%i,'at':iso(d,h),'phone':ph,'items':[{'pid':pr[i%3]['id'],'name':pr[i%3]['name'],'price':pr[i%3]['price'],'qty':q,'cost':1}],'total':pr[i%3]['price']*q,'disc':0,'pay':'Cash','by':'Owner'} for i,(d,h,ph,q) in enumerate([(3,10,'01711111111',5),(35,14,'01711111111',2),(30,20,'01822222222',3),(1,9,'',4),(33,11,'01933333333',1)])]
    ctx2=br.new_context(device_scale_factor=4);a=ctx2.new_page();a.on('pageerror',lambda e:errs.append('admin:'+str(e)))
    a.add_init_script("sessionStorage.setItem('mc_role','Owner');localStorage.setItem('mc_db',%s)"%json.dumps(json.dumps(db)))
    a.goto(B+'admin/index.html');a.wait_for_selector('#side nav button')
    ok(a.locator('#side nav button[data-t=insights]').count()==1,'Insights in sidebar')
    a.click('#side nav button[data-t=insights]');a.wait_for_selector('.kpis')
    ok(a.locator('.hbars .br').count()>=24+7,'charts drawn');txt=a.inner_text('#app')
    ok('Busiest hour' in txt and 'ABC analysis' in txt and 'Dead stock' in txt,'insights sections')
    a.select_option('select[aria-label=Period]','90');a.wait_for_selector('.kpis');ok(True,'period change')
    a.click('#side nav button[data-t=refill]');a.wait_for_selector('#app table')
    rows=a.locator('#app tbody tr').count();ok(rows>=1,'refill rows: %d'%rows)
    a.locator('#app tbody tr button').first.click();a.wait_for_selector('#app table');ok('Undo' in a.inner_text('#app'),'refill mark contacted')
    a.click('#side nav button[data-t=labels]');a.wait_for_selector('#app table')
    a.click('text=Select all shown');a.click('text=Preview and print');a.wait_for_selector('dialog .lbl')
    n=a.locator('dialog .lbl').count();ok(n==len(db['products']),'labels rendered: %d'%n)
    svg=a.locator('dialog .lbl svg').first;png=svg.screenshot()
    try:
        import zxingcpp
        from PIL import Image
        im=Image.open(io.BytesIO(png));r=zxingcpp.read_barcodes(im)
        want=db['products'][0].get('barcode') or db['products'][0]['sku']
        ok(bool(r) and r[0].text==want and '128' in str(r[0].format),'barcode decodes to %s (%s)'%(want,r[0].text if r else None))
    except ImportError: print('SKIP barcode decode')
    a.evaluate("document.querySelectorAll('dialog').forEach(d=>d.remove())")
    a.click('#side nav button[data-t=dash]');a.wait_for_selector('text=Today at a glance');a.fill('input[aria-label="Daily sales target"]','1000');a.press('input[aria-label="Daily sales target"]','Enter');a.wait_for_selector('progress');ok(True,'dashboard add-on with target progress')
    for t,need in [('expiry','By month'),('margins','Average margin'),('reorder',None),('pricelist','products in')]:
        a.click('#side nav button[data-t=%s]'%t);a.wait_for_selector('#app h1');a.wait_for_timeout(200);tx=a.inner_text('#app')
        ok('Something went wrong' not in tx and len(tx)>20 and (need is None or need in tx),'screen renders: '+t)
    a.click('#side nav button[data-t=pricelist]');a.click('text=Preview and print');a.wait_for_selector('dialog table');ok(True,'price list preview');a.evaluate("document.querySelectorAll('dialog').forEach(d=>d.remove())")
    a.evaluate("document.querySelectorAll('dialog').forEach(d=>d.remove())")
    a.click('#side nav button[data-t=customer360]');a.wait_for_selector('#app input[type=search]');a.fill('#app input[type=search]','0171')
    a.wait_for_selector('#app tbody tr');a.click('#app tbody tr >> text=Open');a.wait_for_selector('text=Most bought');ok('Total spent' in a.inner_text('#app') and 'History' in a.inner_text('#app'),'customer lookup shows one customer history')
    # other roles
    for role,seen,absent in [('Cashier',['pricelist','customer360'],['insights','labels','refill','expiry','margins','reorder']),('Pharmacist',['refill','expiry','pricelist','customer360'],['insights','labels','margins','reorder']),('Inventory Manager',['labels','expiry','margins','reorder','pricelist'],['insights','refill'])]:
        c=br.new_context();q=c.new_page();q.add_init_script("sessionStorage.setItem('mc_role','%s');localStorage.setItem('mc_db',%s)"%(role,json.dumps(json.dumps(db))))
        q.goto(B+'admin/index.html');q.wait_for_selector('#side nav button')
        ok(all(q.locator('#side nav button[data-t=%s]'%t).count()==1 for t in seen) and all(q.locator('#side nav button[data-t=%s]'%t).count()==0 for t in absent),role+' sees right new tabs')
        q.goto(B+'admin/insights.html');q.wait_for_selector('#app h1')
        if 'insights' in absent: ok('Insights' not in q.inner_text('#app h1'),role+' blocked from insights deep link')
    for t in ['insights','refill','labels','pricelist','expiry','margins','reorder','customer360']:
        a.goto(B+'admin/%s.html'%t);a.wait_for_selector('#app h1');ok(True,'admin/%s.html opens'%t)
    ok(not errs,'no JS errors: '+'; '.join(errs[:3]))
    br.close()
print('FAILS',fails);sys.exit(1 if fails else 0)
