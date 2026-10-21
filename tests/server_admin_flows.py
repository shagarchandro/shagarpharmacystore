# Exercises the other admin screens against the REAL server's validation. Start via tests/run_server_tests.sh style (fresh DB).
import json, urllib.request
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
COOKIE = ''
def api(path, body=None, raw=False):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if COOKIE: h['Cookie'] = COOKIE
    r = urllib.request.Request(B + 'api/' + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method='POST' if body is not None else 'GET')
    try:
        x = urllib.request.urlopen(r)
        return x if raw else json.load(x)
    except urllib.error.HTTPError as e: return {'error': json.loads(e.read() or b'{}').get('error'), 'status': e.code}
def dlg(d):
    m = d.message
    v = ('LOT1' if 'Batch number' in m else '2030-01-01' if 'Expiry' in m else '10' if 'Quantity received' in m else '50' if 'Counted cash' in m else 'Rider One' if 'Assign delivery' in m
         else 'Wrong item' if 'Reason' in m or 'reason' in m else 'VIP Name' if 'Customer name' in m else 'Internal note' if 'Internal note' in m else '1' if 'Units to return' in m else 'x')
    d.accept(v)
COOKIE = api('login', {'username': 'owner', 'password': OWNER}, raw=True).headers['Set-Cookie'].split(';')[0]
with sync_playwright() as p:
    b = p.chromium.launch(); c = b.new_context(viewport={'width': 1280, 'height': 900}); c.add_init_script("localStorage.setItem('mc_poll','60000')"); pg = c.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150])); pg.on('dialog', dlg)
    pg.goto(B + 'admin/login.html'); pg.fill('input[name=u]', 'owner'); pg.fill('input[name=p]', OWNER); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html'); pg.wait_for_selector('#side nav button')
    def tab(t): pg.click(f'#side nav button[data-t={t}]'); pg.wait_for_selector('#app h1'); pg.wait_for_timeout(250)
    def clean(label):  # no server rejection toast after the step, and the server really has the change
        pg.wait_for_timeout(900); bad = pg.evaluate("[...document.querySelectorAll('.toast.bad')].map(t=>t.textContent)"); pg.evaluate("document.getElementById('toasts')&&(document.getElementById('toasts').textContent='')")
        ok(not bad, f'{label} accepted by the server' + (f' – {bad}' if bad else ''))
    def server(): return api('state')['data']
    # purchase order + receiving (partial then full) + purchase return
    tab('purchases'); pg.wait_for_selector('form.row'); pg.fill('input[name=qty]', '10'); pg.fill('input[name=cost]', '10'); pg.click('button:text-is("Create PO")'); clean('create purchase order')
    pg.click('button:text-is("Receive")'); clean('receive purchase order'); S = server(); ok(any(b['no'] == 'LOT1' and b['qty'] == 10 for b in S['batches']) and any(l['why'] == 'PO received' for l in S['log']), 'received stock is in the server database and stock log')
    pg.click('button:text-is("Purchase return")'); clean('purchase return')
    # supplier + customer admin
    tab('suppliers'); pg.fill('input[name=n]', 'New Supplier'); pg.fill('input[name=ph]', '01711111111'); pg.click('button:text-is("Add supplier")'); clean('add supplier')
    # inventory: adjustment, write-off of the expired demo batch, receive-form
    tab('inv'); pg.wait_for_selector('button:text-is("Write off")'); pg.click('button:text-is("Write off")'); clean('write off expired stock')
    pg.select_option('select[name=bid]', index=2); pg.fill('input[name=delta]', '-2'); pg.select_option('select[name=why]', 'Damaged'); pg.click('button:text-is("Adjust stock")'); clean('damaged-stock adjustment')
    pg.fill('input[name=no]', 'LOT2'); pg.fill('input[name=exp]', '2030-05-05'); pg.fill('input[name=qty]', '5'); pg.fill('input[name=cost]', '8'); pg.click('button:text-is("Receive batch")'); clean('direct batch receiving')
    # stocktake
    tab('stk'); pg.wait_for_selector('#app tbody tr input'); q = int(pg.inner_text('#app tbody tr >> nth=0 >> td >> nth=3')); pg.locator('#app tbody tr input').first.fill(str(q - 1)); pg.click('button:text-is("Apply variances")'); clean('stocktake')
    # POS sale and refund
    tab('pos'); pg.fill('#pq', '890001001'); pg.press('#pq', 'Enter'); pg.wait_for_timeout(200); pg.fill('[aria-label="Cash received"]', '500'); pg.click('button:text-is("Complete sale")'); pg.wait_for_selector('dialog[open]'); pg.evaluate("document.querySelector('dialog').remove()"); clean('POS sale')
    tab('returns'); pg.click('button:text-is("Refund sale")'); clean('POS refund')
    # online order through the public API, then the full workflow
    cust = {'name': 'Flow Customer', 'phone': '01733333333', 'addr': 'House 9, Road 4', 'thana': 'Gulshan', 'district': 'Dhaka', 'division': 'Dhaka', 'post': '1212'}
    no = api('orders', {'items': [{'id': 'P3', 'qty': 1}], 'customer': cust, 'area': 'dhaka', 'pay': 'Cash on delivery'})['order']['no']
    pg.wait_for_timeout(200); pg.evaluate("refreshState().then(()=>go())"); pg.wait_for_timeout(500); tab('orders'); pg.wait_for_selector('#app tbody select')
    for st in ('Confirmed', 'Processing', 'Packed'):
        pg.locator('#app tbody select').first.select_option(st); clean('order status ' + st)
    tab('delivery'); pg.wait_for_selector('button:text-is("Mark shipped")'); pg.click('button:text-is("Mark shipped")'); clean('assign rider and ship'); pg.click('button:text-is("Mark delivered")'); clean('mark delivered')
    ok(api('orders/return', {'no': no, 'phone': '01733333333', 'reason': 'Wrong item'}).get('order', {}).get('status') == 'Return Requested', 'customer return request reaches the server')
    pg.evaluate("refreshState().then(()=>go())"); pg.wait_for_timeout(500); tab('returns'); pg.wait_for_selector('button:text-is("Accept return")'); pg.click('button:text-is("Accept return")'); clean('accept return and restock'); pg.click('button:text-is("Refund")'); clean('refund order')
    S = server(); o = next(x for x in S['orders'] if x['no'] == no); ok(o['status'] == 'Refunded' and [h['s'] for h in o['hist']][-4:] == ['Delivered', 'Return Requested', 'Returned', 'Refunded'] and any(r['no'] == no for r in S['refunds']), 'full order life-cycle recorded by the server with who/when history')
    # money screens
    tab('expenses'); pg.fill('input[name=what]', 'Electricity'); pg.fill('input[name=amt]', '500'); pg.click('button:text-is("Add expense")'); clean('add expense'); pg.click('button:text-is("Close shift")'); clean('close shift')
    # catalogue management
    tab('products'); pg.click('button:text-is("Add product (full form)")'); pg.wait_for_selector('dialog[open] form')
    for n, v in [('name', 'Flow Syrup'), ('price', '55'), ('cost', '40'), ('disc', '5'), ('sku', 'SKU-FLOW'), ('barcode', '8900555')]: pg.fill(f'dialog input[name={n}]', v)
    pg.click('dialog button.btn'); clean('add product'); pg.locator('#app tbody tr:has-text("Flow Syrup") button:text-is("Edit")').click(); pg.wait_for_selector('dialog[open] form'); pg.fill('dialog input[name=price]', '60'); pg.click('dialog button.btn'); clean('edit product')
    pg.locator('#app tbody tr:has-text("Flow Syrup") button:text-is("Delete")').click(); clean('delete product')
    tab('cats'); pg.click('button:text-is("Rename") >> nth=0'); clean('rename category')
    tab('customers'); pg.wait_for_selector('#app tbody tr'); pg.click('button:text-is("Edit") >> nth=0'); clean('edit customer'); pg.click('button:text-is("Block") >> nth=0'); clean('block customer')
    r = api('orders', {'items': [{'id': 'P3', 'qty': 1}], 'customer': cust, 'area': 'dhaka', 'pay': 'Cash on delivery'}); ok(r.get('status') == 403, 'a blocked customer cannot order (enforced by the server)')
    tab('settings'); pg.wait_for_selector('input[name=phone]'); pg.fill('input[name=phone]', '01800-111222'); pg.click('button:text-is("Save settings")'); clean('save settings')
    pg.fill('input[name=code]', 'EID20'); pg.fill('input[name=pct]', '20'); pg.fill('input[name=min]', '300'); pg.click('button:text-is("Add coupon")'); clean('add coupon')
    S = server(); ok(S['settings']['phone'] == '01800-111222' and any(k['code'] == 'EID20' for k in S['coupons']) and 'Flow Syrup' not in [p['name'] for p in S['products']], 'settings, coupon and product deletion are stored')
    ok(api('catalog')['settings']['phone'] == '01800-111222', 'the public site shows the new phone number at once')
    tab('ledger'); pg.wait_for_selector('button[role=tab]'); ok(pg.locator('#app tbody tr').count() > 5, 'ledger reads server data')
    tab('data'); pg.wait_for_selector('button:text-is("Export JSON")'); ok('Resetting is disabled' in pg.inner_text('#app'), 'demo reset is disabled on the real server')
    pg.reload(); pg.wait_for_selector('#side nav button'); ok(pg.evaluate("db().orders.some(o=>o.status==='Refunded')&&db().sales.some(s=>s.refunded)"), 'after a reload everything is still there')
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
