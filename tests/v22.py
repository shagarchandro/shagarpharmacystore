# Demo-mode (LocalStorage) checks for: store controls, alternatives, waiting list, bulk orders, create-all purchase orders. Serve on port 8765 first.
from playwright.sync_api import sync_playwright
B = 'http://localhost:8765/'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    c = b.new_context(viewport={'width': 1280, 'height': 900}); c.add_init_script("sessionStorage.setItem('mc_role','Owner')"); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:150])); pg.on('dialog', lambda d: d.accept('x'))
    pg.goto(B + 'index.html'); pg.wait_for_selector('#all article.card')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.products.push({...d.products[0],id:'PX1',name:'Alt Paracetamol 650',sku:'SKX1',barcode:'',strength:'650 mg'});d.batches.filter(b=>b.pid==='P8').forEach(b=>b.qty=0);d.settings.minOrder=100;localStorage.mc_db=JSON.stringify(d)})()")
    pg.goto(B + 'product-details.html?id=P1'); pg.wait_for_selector('#alts'); ok('Alt Paracetamol 650' in pg.inner_text('#alts'), 'alternatives with the same ingredient are listed')
    pg.goto(B + 'product-details.html?id=P8'); pg.wait_for_selector('#waitbox'); pg.fill('#waitbox input[name=ph]', '01711111111'); pg.click('#waitbox button.btn'); pg.wait_for_timeout(300); ok(pg.evaluate("JSON.parse(localStorage.mc_db).waitlist.length")==1, 'the waiting-list request is saved (demo)')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); pg.goto(B + 'checkout.html'); pg.wait_for_selector('#app form')
    for n, v in [('name', 'Demo Customer'), ('phone', '01712345678'), ('addr', 'House 5, Road 3'), ('thana', 'Dhanmondi'), ('district', 'Dhaka')]: pg.fill(f'#app input[name={n}]', v)
    pg.click('#app button[type=submit]'); pg.wait_for_timeout(300); ok('minimum order' in pg.inner_text('#toasts').lower(), 'a cart below the minimum order is refused with a message (demo)')
    ok(pg.evaluate("JSON.parse(localStorage.mc_db).orders.length")==0, 'no order was created below the minimum')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.settings.minOrder=0;localStorage.mc_db=JSON.stringify(d)})()")
    for _ in range(2):
        pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); pg.goto(B + 'checkout.html'); pg.wait_for_selector('#app form')
        for n, v in [('name', 'Demo Customer'), ('phone', '01712345678'), ('addr', 'House 5, Road 3'), ('thana', 'Dhanmondi'), ('district', 'Dhaka')]: pg.fill(f'#app input[name={n}]', v)
        pg.select_option('select[name=slot]', 'Today 5-9 pm'); pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*')
    ok(pg.evaluate("JSON.parse(localStorage.mc_db).orders.every(o=>o.slot==='Today 5-9 pm')"), 'the delivery time is stored on demo orders')
    pg.goto(B + 'admin/index.html'); pg.wait_for_selector('#side nav button'); pg.click('#side nav button[data-t=orders]'); pg.wait_for_selector('#app tbody tr')
    pg.check('input[aria-label="Select all shown orders"]'); pg.wait_for_timeout(300); pg.select_option('select[aria-label="Set selected orders to"]', 'Confirmed'); pg.click('button:text-is("Apply status")'); pg.wait_for_timeout(500)
    ok(pg.evaluate("JSON.parse(localStorage.mc_db).orders.every(o=>o.status==='Confirmed')"), 'bulk status change works in demo mode')
    pg.click('#side nav button[data-t=settings]'); pg.wait_for_selector('input[name=onlineOrders]'); pg.uncheck('input[name=onlineOrders]'); pg.fill('input[name=notice]', 'Holiday: back on Sunday'); pg.click('button:text-is("Save store controls")'); pg.wait_for_timeout(400)
    pg.goto(B + 'index.html'); pg.wait_for_selector('#all article.card'); ok('Holiday: back on Sunday' in pg.inner_text('#app') and 'paused' in pg.inner_text('#app'), 'store controls pause the demo shop and show the notice')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); pg.goto(B + 'checkout.html'); pg.wait_for_selector('#app form'); ok(pg.is_disabled('#app button[type=submit]'), 'the demo checkout button is disabled while paused')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.settings.onlineOrders=true;d.products[2].reorder=500;d.products[3].reorder=500;localStorage.mc_db=JSON.stringify(d)})()")
    pg.goto(B + 'admin/index.html'); pg.click('#side nav button[data-t=alerts]'); pg.wait_for_selector('button:has-text("Create purchase orders for all")'); ok('01711111111' in pg.inner_text('#app'), 'the waiting customer appears on the alerts screen (demo)')
    pg.click('button:has-text("Create purchase orders for all")'); pg.wait_for_timeout(500); ok(pg.evaluate("JSON.parse(localStorage.mc_db).purchases.length")>=2, 'create-all makes a purchase order per low-stock product (demo)')
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
