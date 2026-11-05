# Real-browser tests of the new storefront/admin features against the REAL server. Fresh DB:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471' --rate-scale 50
import base64, json, os, struct, zlib, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def api(path, body=None, cookie=None, raw=False):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    r = urllib.request.Request(B + 'api/' + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method='POST' if body is not None else 'GET')
    try:
        x = urllib.request.urlopen(r); return x if raw else json.load(x)
    except urllib.error.HTTPError as e: return {'error': json.loads(e.read() or b'{}').get('error'), 'status': e.code}
ck = api('login', {'username': 'owner', 'password': OWNER}, raw=True).headers['Set-Cookie'].split(';')[0]
def change(**colls):
    st = api('state', cookie=ck); return api('state', {'base': {k: st['versions'][k] for k in colls}, 'changes': colls}, ck)
def settings(**kw):
    st = api('state', cookie=ck); s = dict(st['data']['settings']); s.update(kw); return change(settings=s)
def png(w=60, h=60):
    raw = b''.join(b'\x00' + os.urandom(3 * w) for _ in range(h))
    def ch(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b'')
open('/tmp/rx.png', 'wb').write(png()); open('/tmp/notimage.png', 'wb').write(b'GIF89a' + b'0' * 400)
products = api('state', cookie=ck)['data']['products']
products.append({'id': 'PX1', 'name': 'Alt Paracetamol 650', 'generic': 'Paracetamol', 'strength': '650 mg', 'maker': 'Testco', 'form': 'Tablet', 'pack': '10 tabs', 'price': 20, 'cost': 10, 'disc': 0, 'reorder': 20, 'rx': False, 'cat': 'Pain & Fever', 'sku': 'SKX1', 'barcode': '', 'warn': 'x'}); change(products=products)
def cust(pg, doc=False, consent=False, file=None):
    pg.goto(B + 'checkout.html'); pg.wait_for_selector('#app form')
    for n, v in [('name', 'UI Customer'), ('phone', '01766666666'), ('addr', 'House 5, Road 3'), ('thana', 'Dhanmondi'), ('district', 'Dhaka')]: pg.fill(f'#app input[name={n}]', v)
    if doc: pg.fill('#app input[name=doc]', 'Dr U BMDC 21'); pg.check('#app input[name=ok]')
    if file: pg.set_input_files('#app input[name=rxfile]', file)
    if consent: pg.check('#app input[name=rxconsent]')
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    shop = b.new_context(viewport={'width': 1280, 'height': 900}); pg = shop.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:150])); pg.on('dialog', lambda d: d.accept('x'))
    # store controls on the storefront
    settings(notice='Eid hours: 10 am - 6 pm', onlineOrders=False)
    pg.goto(B + 'index.html'); pg.wait_for_selector('#all article.card'); t = pg.inner_text('#app'); ok('Eid hours' in t and 'paused' in t, 'the shop shows the owner\'s notice and a paused-ordering banner')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); cust(pg); ok(pg.is_disabled('#app button[type=submit]'), 'checkout cannot be submitted while ordering is paused')
    settings(onlineOrders=True, notice='', freeDeliveryMin=500, minOrder=100)
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); cust(pg); pg.wait_for_selector('#sum p'); ok('Minimum order' in pg.inner_text('#sum'), 'the summary warns when the cart is below the minimum order')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P9:1}))"); cust(pg); pg.wait_for_selector('#sum p'); ok('more for free delivery' in pg.inner_text('#sum') and pg.locator('select[name=slot] option').count() == 4, 'the summary shows how much more earns free delivery, and delivery times can be chosen')
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P9:2}))"); cust(pg); pg.wait_for_selector('#sum p'); ok('Delivery: ৳0' in pg.inner_text('#sum'), 'delivery becomes free above the level')
    pg.select_option('select[name=slot]', 'Tomorrow 9 am-1 pm'); pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*'); no1 = pg.url.split('/')[-1]
    ok(next(o for o in api('state', cookie=ck)['data']['orders'] if o['no'] == no1)['slot'] == 'Tomorrow 9 am-1 pm', 'the chosen delivery time reaches the pharmacy')
    settings(freeDeliveryMin=0, minOrder=0)
    # alternatives + waiting list
    pg.goto(B + 'product-details.html?id=P1'); pg.wait_for_selector('#alts'); ok('Alt Paracetamol 650' in pg.inner_text('#alts') and 'ask the pharmacist' in pg.inner_text('#alts'), 'a product page lists other brands with the same ingredient')
    pg.goto(B + 'product-details.html?id=PX1'); pg.wait_for_selector('#waitbox'); pg.fill('#waitbox input[name=nm]', 'Waiting Wendy'); pg.fill('#waitbox input[name=ph]', '12'); pg.click('#waitbox button.btn'); pg.wait_for_timeout(300); ok('valid Bangladesh mobile' in pg.inner_text('#toasts'), 'the waiting-list form checks the number')
    pg.fill('#waitbox input[name=ph]', '01788888888'); pg.click('#waitbox button.btn'); pg.wait_for_timeout(500); ok(len(api('state', cookie=ck)['data']['waitlist']) == 1, 'a request is saved on the server')
    pg.goto(B + 'product-details.html?id=P3'); pg.wait_for_selector('#app h1'); ok(pg.locator('#waitbox').count() == 0, 'products in stock show no waiting-list box')
    # prescription upload
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P5:1}))"); cust(pg, doc=True, file='/tmp/rx.png'); pg.click('#app button[type=submit]'); pg.wait_for_timeout(600); ok('tick the box' in pg.inner_text('#toasts') and '#/success' not in pg.url, 'an image without consent is not sent')
    cust(pg, doc=True, file='/tmp/notimage.png', consent=True); pg.click('#app button[type=submit]'); pg.wait_for_timeout(700); ok('JPG, PNG' in pg.inner_text('#toasts') and '#/success' not in pg.url, 'a fake image is refused with a clear message')
    cust(pg, doc=True, file='/tmp/rx.png', consent=True); pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*'); no2 = pg.url.split('/')[-1]; ok('prescription' in pg.inner_text('#app').lower(), 'an order with a prescription image is placed')
    # admin
    ad = b.new_context(viewport={'width': 1280, 'height': 900}); a = ad.new_page(); a.on('pageerror', lambda e: errs.append(str(e)[:150])); a.on('dialog', lambda d: d.accept('x'))
    a.goto(B + 'admin/login.html'); a.fill('#lu', 'owner'); a.fill('#lp', OWNER); a.click('button.btn'); a.wait_for_url('**/admin/index.html'); a.wait_for_selector('#side nav button')
    a.click('#side nav button[data-t=rx]'); a.wait_for_selector('#app article.card'); a.click('button:text-is("View prescription image")'); a.wait_for_selector('dialog[open] img'); a.wait_for_timeout(400)
    ok(a.evaluate("document.querySelector('dialog[open] img').naturalWidth")==60, 'the pharmacist screen shows the uploaded prescription image'); a.click('dialog button:text-is("Close")')
    a.click('#side nav button[data-t=alerts]'); a.wait_for_selector('text=Customers waiting for stock'); ok('Waiting Wendy' in a.inner_text('#app') and 'Still out of stock' in a.inner_text('#app'), 'staff see the waiting customer on the alerts screen')
    st = api('state', cookie=ck); prods = st['data']['products']; prods[2]['reorder'] = 500; prods[3]['reorder'] = 500; change(products=prods); a.reload(); a.click('#side nav button[data-t=alerts]'); a.wait_for_selector('button:has-text("Create purchase orders for all")')
    a.click('button:has-text("Create purchase orders for all")'); a.wait_for_timeout(900); ok(len(api('state', cookie=ck)['data']['purchases']) >= 2, 'one click creates purchase orders for every low-stock product')
    a.click('button:text-is("Contacted")'); a.wait_for_timeout(700); ok(api('state', cookie=ck)['data']['waitlist'][0]['contacted'] is True, 'a staff member can mark a waiting customer as contacted')
    # bulk orders
    nos = [api('orders', {'items': [{'id': 'P3', 'qty': 1}], 'customer': {'name': 'Bulk %d' % i, 'phone': '0177000000%d' % i, 'addr': 'House 9, Road 4', 'thana': 'Gulshan', 'district': 'Dhaka', 'division': 'Dhaka'}, 'area': 'dhaka', 'pay': 'Cash on delivery'})['order']['no'] for i in range(1, 4)]
    a.click('#side nav button[data-t=orders]'); a.wait_for_selector('#app tbody tr'); a.evaluate("refreshState().then(()=>go())"); a.wait_for_timeout(600)
    for n in (nos[0], nos[1], no2): a.locator('tr', has_text=n).locator('input[type=checkbox]').check()
    a.select_option('select[aria-label="Set selected orders to"]', 'Processing'); a.click('button:text-is("Apply status")'); a.wait_for_timeout(900)
    S = {o['no']: o['status'] for o in api('state', cookie=ck)['data']['orders']}; ok(S[nos[0]] == 'Processing' and S[nos[1]] == 'Processing' and S[nos[2]] == 'Pending', 'bulk status change updates only the selected orders')
    ok(S[no2] == 'Prescription Review' and 'skipped' in a.inner_text('#toasts'), 'prescription orders are skipped by the bulk action and the staff are told')
    for n in (nos[0], nos[1]): a.locator('tr', has_text=n).locator('input[type=checkbox]').check()
    a.click('button:text-is("Print pick lists")'); a.wait_for_selector('dialog[open]'); t = a.inner_text('dialog[open]'); ok(nos[0] in t and nos[1] in t and nos[2] not in t, 'pick lists print for the selected orders together'); a.evaluate("document.querySelector('dialog').remove()")
    # settings UI
    a.click('#side nav button[data-t=settings]'); a.wait_for_selector('input[name=onlineOrders]'); a.uncheck('input[name=onlineOrders]'); a.fill('input[name=notice]', 'Closed for a family event'); a.click('button:text-is("Save store controls")'); a.wait_for_timeout(900)
    pg.goto(B + 'index.html'); pg.wait_for_selector('#all article.card'); ok('Closed for a family event' in pg.inner_text('#app') and 'paused' in pg.inner_text('#app'), 'the owner pauses the shop and posts a notice from Settings, and customers see it at once')
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
