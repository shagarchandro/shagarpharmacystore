# Real-browser test: loyalty redemption. Serve the project on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
def order(pg,cart,redeem=None):
    pg.evaluate("c=>localStorage.setItem('mc_cart',JSON.stringify(c))",cart); pg.goto(B+'checkout.html'); pg.wait_for_selector('#app form')
    for n,v in [('name','Loyal Customer'),('phone','01712345678'),('addr','House 5, Road 3'),('thana','Dhanmondi'),('district','Dhaka')]: pg.fill(f'#app input[name={n}]',v)
    if redeem is not None: pg.fill('#app input[name=redeem]',str(redeem))
    pg.click('#app button[type=submit]'); pg.wait_for_timeout(300)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(); pg=ctx.new_page(); pg.on('dialog',lambda d:d.accept()); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(B+'index.html'); order(pg,{'P8':2}); ok('#/success/' in pg.url,'first order placed (৳300 + ৳60 delivery)')
    av=lambda: pg.evaluate("loyAvail(db(),'01712345678')"); ok(av()==3,f'earns 1 point per ৳100: {av()}')
    order(pg,{'P1':1},redeem=9); ok('#/success/' not in pg.url,'cannot redeem more points than available')
    order(pg,{'P8':1},redeem=2); ok('#/success/' in pg.url,'redeem 2 points at checkout')
    o=pg.evaluate("db().orders.at(-1)"); ok(o['loy']==2 and o['total']==150-2+60,f"total reduced by redeemed points: {o['total']}")
    ok(pg.evaluate("db().loyalty['01712345678'].redeemed")==2,'redeemed points recorded')
    pg.goto(B+'orders.html'); pg.click('text=Cancel order >> nth=0'); pg.wait_for_timeout(300)
    ok(pg.evaluate("db().loyalty['01712345678'].redeemed")==0,'cancelling restores redeemed points')
    ctx.add_init_script("sessionStorage.setItem('mc_role','Owner')"); order(pg,{'P8':2}); pg.goto(B+'admin/pos.html'); pg.wait_for_selector('#pq')
    pg.fill('#pq','890001007'); pg.press('#pq','Enter'); pg.wait_for_timeout(200); pg.fill('[aria-label="Customer mobile (optional)"]','01712345678'); pg.fill('[aria-label="Redeem points"]','50'); pg.fill('[aria-label="Cash received"]','500'); pg.click('button:text-is("Complete sale")'); pg.wait_for_timeout(300)
    ok(pg.evaluate("db().sales.length")==0,'POS blocks redeeming more points than available')
    pg.fill('[aria-label="Redeem points"]','2'); pg.click('button:text-is("Complete sale")'); pg.wait_for_selector('dialog[open]')
    s=pg.evaluate("db().sales[0]"); ok(s['loy']==2 and s['total']==148,f"POS redemption reduces total: {s['total']}"); ok('Points redeemed 2' in pg.inner_text('dialog[open]'),'receipt shows points redeemed')
    pg.evaluate("document.querySelector('dialog').remove()"); pg.goto(B+'admin/returns.html'); pg.click('text=Refund sale >> nth=0'); pg.wait_for_timeout(300)
    ok(pg.evaluate("db().loyalty['01712345678'].redeemed")==0 and pg.evaluate("db().sales[0].refunded"),'POS refund returns the points')
    pg.goto(B+'index.html'); pg.wait_for_timeout(300); ok(pg.evaluate("document.querySelectorAll('#sg option').length")>12,'search suggestions include generic names')
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
