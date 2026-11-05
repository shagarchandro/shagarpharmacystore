# Real-browser checks that each role still works with the role-limited data. Fresh DB:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471' --rate-scale 50
import json, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; PW = 'Fresh-Pass-7788'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def api(path, body=None, cookie=None, raw=False):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    r = urllib.request.Request(B + 'api/' + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method='POST' if body is not None else 'GET')
    try:
        x = urllib.request.urlopen(r); return x if raw else json.load(x)
    except urllib.error.HTTPError as e: return {'error': json.loads(e.read() or b'{}').get('error'), 'status': e.code}
ck = api('login', {'username': 'owner', 'password': OWNER}, raw=True).headers['Set-Cookie'].split(';')[0]
for u, r in (('cash4', 'Cashier'), ('deliv3', 'Delivery Staff'), ('pharma3', 'Pharmacist'), ('inv3', 'Inventory Manager')):
    api('staff', {'username': u, 'name': u, 'role': r, 'password': 'Temp-Password-1'}, ck); k = api('login', {'username': u, 'password': 'Temp-Password-1'}, raw=True).headers['Set-Cookie'].split(';')[0]; api('password', {'old': 'Temp-Password-1', 'new': PW}, k)
cust = {'name': 'Role Customer', 'phone': '01744444444', 'addr': 'House 1, Road 2', 'thana': 'Banani', 'district': 'Dhaka', 'division': 'Dhaka', 'post': '1213'}
o1 = api('orders', {'items': [{'id': 'P3', 'qty': 1}], 'customer': cust, 'area': 'dhaka', 'pay': 'Cash on delivery'})['order']
o2 = api('orders', {'items': [{'id': 'P5', 'qty': 1}], 'customer': cust, 'area': 'dhaka', 'pay': 'Cash on delivery', 'doc': 'Dr R BMDC 55', 'rxConfirmed': True})['order']
st = api('state', cookie=ck); orders = st['data']['orders']; orders[[o['no'] for o in orders].index(o1['no'])]['status'] = 'Packed'
api('state', {'base': {'orders': st['versions']['orders']}, 'changes': {'orders': orders}}, ck)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def staff(u):
        c = b.new_context(viewport={'width': 1280, 'height': 900}); c.add_init_script("localStorage.setItem('mc_poll','60000')"); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(u + ': ' + str(e)[:140])); pg.on('dialog', lambda d: d.accept('Rider One'))
        pg.goto(B + 'admin/login.html'); pg.fill('#lu', u); pg.fill('#lp', PW); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html'); pg.wait_for_selector('#side nav button'); return c, pg
    # delivery staff
    c, d = staff('deliv3'); tabs = d.locator('#side nav button').evaluate_all("els=>els.map(e=>e.dataset.t)"); ok(sorted(tabs) == ['account', 'delivery', 'orders'], f'delivery staff see only Orders, Delivery and My account {tabs}')
    d.click('#side nav button[data-t=orders]'); d.wait_for_selector('#app tbody select'); ok(d.locator('button:text-is("Pick list")').count() == 0 and 'Role Customer' in d.inner_text('#app'), 'delivery staff see the orders but no stock/pick-list tools')
    row = d.locator('#app tbody tr', has_text=o1['no']); row.locator('select').select_option('Shipped'); d.wait_for_timeout(900); ok(api('state', cookie=ck)['data']['orders'][[o['no'] for o in api('state', cookie=ck)['data']['orders']].index(o1['no'])]['status'] == 'Shipped', 'delivery staff can still mark an order shipped')
    row.locator('select').select_option('Cancelled'); d.wait_for_timeout(700); ok('cannot set' in d.inner_text('#toasts'), 'delivery staff cannot cancel orders'); c.close()
    # pharmacist
    c, ph = staff('pharma3'); ph.click('#side nav button[data-t=rx]'); ph.wait_for_selector('#app article.card'); ok('Dr R BMDC 55' in ph.inner_text('#app'), 'the pharmacist still sees the prescription queue'); ph.click('button:text-is("Approve")'); ph.wait_for_timeout(900)
    ok([o for o in api('state', cookie=ck)['data']['orders'] if o['no'] == o2['no']][0]['status'] == 'Confirmed', 'the pharmacist can approve it')
    ph.click('#side nav button[data-t=dash]'); ph.wait_for_selector('#app h1'); ok('profit estimate' not in ph.inner_text('#app') and ph.evaluate("db().products.every(p=>p.cost===undefined)"), 'the pharmacist screens show no profit or cost figures')
    ph.click('#side nav button[data-t=ledger]'); ph.wait_for_selector('button[role=tab]'); ok(True, 'ledger and recall open for the pharmacist'); c.close()
    # cashier
    c, ca = staff('cash4'); ca.click('#side nav button[data-t=pos]'); ca.wait_for_selector('#pq'); ca.fill('#pq', '890001000'); ca.press('#pq', 'Enter'); ca.wait_for_timeout(200); ca.fill('[aria-label="Cash received"]', '100'); ca.click('button:text-is("Complete sale")'); ca.wait_for_selector('dialog[open]'); ok(True, 'the cashier can still sell at the counter')
    ca.evaluate("document.querySelector('dialog').remove()"); ca.click('#side nav button[data-t=expenses]'); ca.wait_for_selector('#app h1'); ok('Cashbook' in ca.inner_text('#app'), 'the cashbook still works without supplier or purchase data')
    ok(ca.evaluate("db().suppliers.length===0 && db().purchases.length===0 && db().products.every(p=>p.cost===undefined)"), 'the cashier browser holds no supplier, purchase or cost data'); c.close()
    # inventory manager keeps costs and purchasing
    c, im = staff('inv3'); im.click('#side nav button[data-t=purchases]'); im.wait_for_selector('form.row'); ok(im.evaluate("db().products.every(p=>typeof p.cost==='number')"), 'the inventory manager still sees costs'); im.click('#side nav button[data-t=dash]'); im.wait_for_selector('#app h1'); ok('profit estimate' in im.inner_text('#app'), 'and the profit estimate'); c.close()
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
