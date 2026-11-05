# v2.0 storefront sections: Shop, Wishlist, Orders, Help, Contact, Health (demo mode, port 8765)
import json, sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':1200,'height':900});pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    # ---- Shop
    pg.goto(B+'index.html');pg.wait_for_selector('#all article.card')
    ok(pg.locator('.viewtog button').count()==2,'grid/list toggle')
    pg.click('.viewtog button >> nth=1');ok(pg.evaluate("document.getElementById('all').classList.contains('listview')"),'list view applies');pg.reload();pg.wait_for_selector('#all article.card')
    ok(pg.evaluate("document.getElementById('all').classList.contains('listview')"),'list view is remembered');pg.click('.viewtog button >> nth=0');ok(not pg.evaluate("document.getElementById('all').classList.contains('listview')"),'back to grid')
    pg.locator('#all .qvbtn').first.click();pg.wait_for_selector('dialog.qv[open]');ok('Add to cart' in pg.inner_text('dialog.qv'),'quick view opens')
    pg.click('dialog.qv >> text=Add to cart');pg.wait_for_selector('dialog.qv',state='detached');ok(pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('mc_cart')||'{}')).length")>=1,'quick view adds to cart')
    pg.fill('.filters input[type=search]','Napaa');pg.wait_for_selector('text=Did you mean');ok(pg.locator('.card button.btn2:has-text("Napa")').count()>=1,'misspelling suggests a real product')
    pg.click('.card button.btn2 >> nth=0');pg.wait_for_selector('#all article.card');ok(True,'suggestion searches again')
    pg.evaluate("window.scrollTo(0,2000)");pg.wait_for_timeout(300);ok(pg.is_visible('.totop'),'back-to-top button appears after scrolling')
    # ---- Wishlist
    pg.evaluate("localStorage.setItem('mc_wish',JSON.stringify(['P1','P2']));localStorage.removeItem('mc_wishp')");pg.goto(B+'index.html#/wishlist');pg.wait_for_selector('.grid article.card')
    ok('saved' in pg.inner_text('main,#app'),'wishlist shows a total line')
    db=pg.evaluate("db()");pr=[x for x in db['products'] if x['id']=='P1'][0];db['products']=[dict(x,price=x['price']+50) if x['id']=='P1' else x for x in db['products']]
    pg.evaluate("(d)=>{localStorage.setItem('mc_wishp',JSON.stringify({P1:"+str(round(pr['price']*(1-pr.get('disc',0)/100)+50+40))+",P2:1}));}",None);pg.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",db);pg.reload();pg.wait_for_selector('.grid article.card')
    ok('Price dropped' in pg.inner_text('#app'),'a lower price than when saved is flagged')
    pg.goto(B+'index.html#/sharewish/P1~P2~BAD!');pg.wait_for_selector('text=Shared wishlist');ok(pg.locator('#app article.card').count()==2,'shared wishlist lists 2 valid products')
    pg.evaluate("localStorage.setItem('mc_wish','[]')");pg.click('text=Save all to my wishlist');pg.wait_for_selector('h1');ok(len(pg.evaluate("JSON.parse(localStorage.getItem('mc_wish'))"))==2,'shared wishlist can be saved')
    pg.evaluate("localStorage.setItem('mc_wish','[]')");pg.goto(B+'index.html#/wishlist');pg.reload();pg.wait_for_selector('text=Popular picks');ok(True,'empty wishlist suggests popular products')
    # ---- Orders (demo orders exist for the logged-in demo customer)
    d=pg.evaluate("db()");import datetime
    d['orders']=[{'id':'O%d'%i,'no':'INV-%d'%(1001+i),'at':(datetime.datetime.utcnow()-datetime.timedelta(days=i)).isoformat()+'Z','customer':'Test Buyer','phone':'01712345678','addr':'Dhaka','items':[{'id':'P1','pid':'P1','qty':1,'price':12,'name':'Napa'}],'total':72,'status':st,'rx':False,'note':''} for i,st in enumerate(['Pending','Delivered','Cancelled','Delivered'])]
    pg.evaluate("(d)=>{localStorage.setItem('mc_db',JSON.stringify(d));localStorage.setItem('mc_user','Test Buyer')}",d);pg.goto(B+'index.html#/orders');pg.reload();pg.wait_for_selector('article.card .timeline')
    n=pg.locator('article.card .timeline').count();ok(n>=1,'orders listed: %d'%n)
    ok(pg.locator('text=Need help with this order').count()==n,'each order has a help button')
    ok(pg.locator('details:has-text("What do the statuses mean")').count()==1,'status legend present')
    pg.click('text=Need help with this order >> nth=0');pg.wait_for_selector('form input[name=o]');ok(pg.input_value('input[name=o]').startswith('INV-'),'contact form opens with the order number filled in: '+pg.input_value('input[name=o]'))
    # ---- Contact
    pg.evaluate("localStorage.setItem('mc_prof',JSON.stringify({name:'Rahim Uddin',phone:'01712345678'}))");pg.evaluate("sessionStorage.clear()");pg.goto(B+'index.html#/contact');pg.reload();pg.wait_for_selector('form input[name=n]')
    ok(pg.input_value('input[name=n]')=='Rahim Uddin' and pg.input_value('input[name=ph]')=='01712345678','contact form is prefilled from saved details')
    ok(pg.locator('.openb').count()>=1 and pg.locator('a:has-text("Show on map")').count()==1,'contact card has open status and map link')
    pg.fill('textarea[name=m]','Is Napa 500 available today?');pg.reload();pg.wait_for_selector('form input[name=n]');ok(pg.input_value('textarea[name=m]')=='Is Napa 500 available today?','message draft survives a reload')
    pg.fill('textarea[name=m]','Is Napa 500 available today?');pg.click('#app form button.btn');pg.wait_for_selector('text=Message sent');ok(pg.input_value('textarea[name=m]')=='','draft cleared after sending');ok(pg.evaluate("localStorage.getItem('mc_cdraft')")is None,'saved draft removed after sending')
    # ---- Help
    pg.goto(B+'index.html#/info');pg.wait_for_selector('details');t=pg.inner_text('#app')
    ok('999' in t and 'Using this website' in t,'help has the emergency box and the new FAQ group')
    pg.fill('#app input[type=search]','reminder');pg.wait_for_timeout(200);vis=pg.locator('details:visible').count();ok(vis>=1 and vis<=3,'FAQ search also filters the new answers: %d visible'%vis)
    # ---- Health
    pg.goto(B+'index.html#/health');pg.wait_for_selector('#bmi-out',state='attached')
    ok('999' in pg.inner_text('#app'),'health page shows the emergency number')
    pg.select_option('select[name=k]','bp');pg.fill('input[name=a]','150');pg.fill('input[name=b]','95');pg.click('text=Save reading');pg.wait_for_selector('.health-none, td.bad',timeout=3000);ok('doctor' in pg.inner_text('#app').lower(),'high blood pressure is flagged with advice')
    pg.fill('input[name=a]','118');pg.fill('input[name=b]','76');pg.click('text=Save reading');pg.wait_for_selector('svg.spark');ok(True,'trend chart appears after two readings')
    pg.fill('input[name=a]','200');pg.fill('input[name=b]','250');pg.click('text=Save reading');ok(pg.evaluate("JSON.parse(localStorage.getItem('mc_hlog')).length")==2,'impossible values are refused')
    pg.select_option('select[name=k]','bg');pg.fill('input[name=a]','6.2');pg.select_option('select[name=x]','fasting');pg.click('text=Save reading');pg.wait_for_selector('text=Above the usual fasting');ok(True,'blood sugar classified')
    with pg.expect_download() as dl:
        pg.click('text=Export CSV')
    ok(dl.value.suggested_filename=='health-log.csv','CSV export downloads')
    pg.click('text=+ 1 cup');pg.click('text=+ 1 cup');ok('2 / 8' in pg.inner_text('#app'),'water tracker counts')
    pg.evaluate("localStorage.setItem('mc_rem',JSON.stringify([{id:'R1',name:'Napa',time:'08:00',note:'after food'}]))");pg.reload();pg.wait_for_selector('#bmi-out',state='attached');pg.click('text=Print my schedule >> nth=1');pg.wait_for_selector('dialog.rcpt[open]');ok('Napa' in pg.inner_text('dialog.rcpt'),'printable medicine schedule')
    ok(not errs,'no page errors '+str(errs[:3]));br.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
sys.exit(1 if any(r.startswith('FAIL') for r in res) else 0)
