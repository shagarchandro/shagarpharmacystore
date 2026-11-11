# v3.2 POS upgrades (demo mode, port 8765)
import sys, json, datetime
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
def sale(pid,qty,days,pay='Cash',n=1):
    return {'id':'S%d'%n,'no':'INV-POS-%d'%n,'rx':'','phone':'','loy':0,'at':(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=days)).isoformat(),'items':[{'pid':pid,'name':pid,'price':50,'qty':qty,'cost':10}],'total':50*qty,'disc':0,'pay':pay,'change':0,'by':'Owner'}
with sync_playwright() as p:
    br=p.chromium.launch();errs=[];dialogs=[]
    ctx=br.new_context(viewport={'width':1280,'height':900});pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(dialogs.append(d.type),d.accept('x')))
    pg.add_init_script("sessionStorage.setItem('mc_role','Owner')");pg.goto(B+'admin/index.html');pg.wait_for_selector('#side nav button')
    d=pg.evaluate("db()");d['sales']=[sale('P2',9,3,'bKash (demo)',1),sale('P3',4,5,'Cash',2)]
    d['orders']=[{'id':'O1','no':'INV-4001','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'customer':'Rahim Uddin','phone':'01712345678','addr':'x','items':[{'id':'P1','pid':'P1','qty':1,'price':12,'name':'Napa'}],'total':1000,'status':'Delivered','rx':False,'note':''}]
    pg.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d);pg.goto(B+'admin/pos.html');pg.reload();pg.wait_for_selector('#pq');pg.wait_for_selector('.posgrid')
    ok(pg.locator('.posleft').count()==1 and pg.locator('.posright').count()==1,'two-column POS layout')
    first=pg.eval_on_selector('[aria-label="Quick add"] button:nth-of-type(1)','e=>e.textContent');ok(first.startswith('Seclo'),'frequent items first (P2 sold most): '+first)
    pg.fill('#pq','napa');pg.wait_for_selector('.pos-results li');ok('Napa' in pg.inner_text('.pos-results'),'typing shows live matches')
    pg.keyboard.press('Enter');pg.wait_for_selector('.stepper');ok(pg.locator('.stepper').count()==1 and pg.locator('text=Not found').count()==0,'Enter on a partial name adds the top match')
    pg.click('button[aria-label^="One more"]');pg.wait_for_selector('.stepper input[value="2"]');pg.fill('.stepper input','3');pg.press('.stepper input','Tab');pg.wait_for_selector('.stepper input[value="3"]');ok(pg.input_value('.stepper input')=='3','quantity stepper and typed quantity')
    pg.click('button[aria-label^="One less"]');pg.wait_for_selector('.stepper input[value="2"]')
    ok('৳24' in pg.inner_text('.pos-sum'),'total shows ৳24: '+pg.inner_text('.pos-total'))
    pg.fill('[aria-label="Cash received"]','10');ok('Short by' in pg.inner_text('.pos-change'),'short cash is shown: '+pg.inner_text('.pos-change'))
    pg.click('.pos-chips button:has-text("৳100")');ok('Change ৳76' in pg.inner_text('.pos-change'),'change due: '+pg.inner_text('.pos-change'))
    pg.fill('[aria-label="Discount ৳"]','4');ok('৳20' in pg.inner_text('.pos-total') and 'Change ৳80' in pg.inner_text('.pos-change'),'discount updates total and change live: %s / %s'%(pg.inner_text('.pos-total'),pg.inner_text('.pos-change')))
    pg.click('[aria-label="Quick add"] button >> nth=0');pg.wait_for_timeout(300);ok(pg.input_value('[aria-label="Discount ৳"]')=='4' and pg.input_value('[aria-label="Cash received"]')=='100','fields survive adding another item')
    pg.fill('[aria-label="Customer mobile (optional)"]','01712345678');ok('Rahim Uddin' in pg.inner_text('.posright') and 'points available' in pg.inner_text('.posright'),'customer name and points are shown: '+pg.inner_text('.posright small'))
    pg.click('button:has-text("Hold cart")');pg.wait_for_selector('.pos-held');ok(pg.locator('.stepper').count()==0 and 'item(s)' in pg.inner_text('.pos-held'),'cart held')
    pg.click('button:has-text("Resume")');pg.wait_for_selector('.stepper');ok(pg.locator('.stepper').count()==2,'held cart resumed with its two lines')
    pg.click('button:has-text("Clear cart")');pg.wait_for_timeout(200);ok(pg.locator('.stepper').count()==0,'clear cart')
    # prescription item with an inline reference, no pop-up
    pg.fill('#pq','amlodipine');pg.wait_for_selector('.pos-results li');pg.keyboard.press('Enter');pg.wait_for_selector('.stepper');ok('prescription items' in pg.inner_text('.posright'),'Rx notice appears for prescription items')
    pg.fill('[aria-label="Prescription reference"]','Dr Rahman BMDC 12345 2026-11-01');pg.fill('[aria-label="Cash received"]','500');dialogs.clear();pg.click('button:text-is("Complete sale")');pg.wait_for_selector('dialog[open]')
    ok('prompt' not in dialogs,'no pop-up asked for the prescription reference')
    rt=pg.inner_text('dialog[open]');ok('Amlodipine' in rt and 'Cash received' in rt and 'Change' in rt and 'Prescription: Dr Rahman' in rt and 'Served by: Owner' in rt,'receipt has items, payment, change, Rx reference and cashier')
    pg.screenshot(path='/tmp/receipt_new.png')
    sl=pg.evaluate("db().sales.at(-1)");ok(sl['rx'].startswith('Dr Rahman') and sl['change']>0,'sale saved with the prescription reference and change: %s / %s'%(sl['rx'],sl['change']))
    pg.evaluate("document.querySelectorAll('dialog').forEach(x=>x.remove())");pg.reload();pg.wait_for_selector('.posgrid')
    ok('Today at the till' in pg.inner_text('#app') and 'sale(s)' in pg.inner_text('#app'),'till summary: '+pg.inner_text('.card:has(h2:has-text("Today at the till")) p'))
    pg.click('#app table >> nth=-1 >> tbody tr >> nth=0 >> button:has-text("Receipt")');pg.wait_for_selector('dialog[open]');ok(True,'receipt can be reprinted from the history');pg.evaluate("document.querySelectorAll('dialog').forEach(x=>x.remove())")
    pg.keyboard.press('F2');ok(pg.evaluate("document.activeElement.id")=='pq','F2 still focuses the search')
    # cashier cannot complete Rx sale
    c2=br.new_context(viewport={'width':1280,'height':900});q=c2.new_page();q.on('pageerror',lambda e:errs.append(str(e)))
    q.add_init_script("sessionStorage.setItem('mc_role','Cashier')");q.goto(B+'admin/index.html');q.wait_for_selector('#side nav button');q.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d);q.goto(B+'admin/pos.html');q.reload();q.wait_for_selector('.posgrid')
    q.fill('#pq','amlodipine');q.wait_for_selector('.pos-results li');q.keyboard.press('Enter');q.wait_for_selector('.stepper');ok('Only a pharmacist' in q.inner_text('.posright') and q.locator('[aria-label="Prescription reference"]').count()==0,'cashier is told to ask a pharmacist')
    ok(not errs,'no page errors '+str(errs[:3]));br.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
sys.exit(1 if any(r.startswith('FAIL') for r in res) else 0)
