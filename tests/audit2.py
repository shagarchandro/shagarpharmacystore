# Real-browser checks for v13. Serve the project on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1280,'height':800}); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:100])); pg.on('dialog',lambda d:d.accept())
    pg.goto(B+'product-details.html?id=P1'); pg.wait_for_selector('#app h1'); t=pg.inner_text('#app'); ok('Strength' in t and '500 mg' in t,'product page shows strength')
    pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card'); ok('500 mg' in pg.inner_text('#all'),'product card shows strength')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P9:2}))"); pg.goto(B+'cart.html'); pg.fill('#cp','SAVE10'); pg.click('button:text-is("Apply")'); pg.wait_for_timeout(200)
    pg.goto(B+'checkout.html'); pg.wait_for_selector('#sum p'); s=pg.inner_text('#sum'); ok('Coupon: −৳70' in s,'coupon persists to checkout.html and shows in summary')
    ok('Delivery: ৳60' in s,'order summary shows delivery fee'); pg.select_option('select[name=area]','pickup'); pg.wait_for_timeout(150); ok('Delivery: ৳0' in pg.inner_text('#sum'),'summary updates for store pickup')
    pg.goto(B+'shipping.html'); pg.wait_for_selector('#sec-shipping'); ok(pg.evaluate("document.getElementById('sec-shipping').classList.contains('hl')&&!document.getElementById('sec-faq').classList.contains('hl')"),'shipping.html highlights the Shipping section')
    pg.goto(B+'index.html'); r=pg.evaluate("(()=>{Storage.prototype.setItem=function(){throw new DOMException('full','QuotaExceededError')};try{const d=db();return 'saved='+save(d)}catch(e){return 'threw '+e.message}})()"); ok(r=='saved=false' and 'Could not save' in pg.inner_text('#toasts'),'full storage shows a friendly message, no crash: '+r)
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
