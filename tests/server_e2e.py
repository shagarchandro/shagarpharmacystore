# Real-browser tests against the REAL server (shared database, real login). Start it first:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471'
import json, urllib.request
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def catalog_stock(pid): return next(p['stock'] for p in json.load(urllib.request.urlopen(B + 'api/catalog'))['products'] if p['id'] == pid)
def new_ctx(b, poll=False, w=1280, h=900):
    c = b.new_context(viewport={'width': w, 'height': h})
    if poll: c.add_init_script("localStorage.setItem('mc_poll','1500')")
    return c
def staff_login(pg, u, p):
    pg.goto(B + 'admin/login.html'); pg.wait_for_selector('input[name=u]'); pg.fill('input[name=u]', u); pg.fill('input[name=p]', p); pg.click('button.btn')
def checkout(pg, doc=False):
    pg.goto(B + 'checkout.html'); pg.wait_for_selector('#app form')
    for n, v in [('name', 'Real Customer'), ('phone', '01712345678'), ('addr', 'House 5, Road 3'), ('thana', 'Dhanmondi'), ('district', 'Dhaka')]: pg.fill(f'#app input[name={n}]', v)
    if doc: pg.fill('#app input[name=doc]', 'Dr A, BMDC 1234'); pg.check('#app input[name=ok]')
    pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*')
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    # 1 customer browses the real catalog
    cu = new_ctx(b); pg = cu.new_page(); pg.on('pageerror', lambda e: errs.append((str(e)+' @'+str(getattr(e,'stack',''))[:260]))); pg.on('dialog', lambda d: d.accept('x'))
    pg.goto(B + 'index.html'); pg.wait_for_selector('#all article.card')
    ok(pg.evaluate("SERVER===true && localStorage.getItem('mc_db')===null"), 'storefront runs in server mode and holds no shop database in the browser')
    ok('Napa' in pg.inner_text('#all') and pg.evaluate("db().products.every(p=>p.cost===0)"), 'catalog comes from the server and carries no cost prices')
    s0 = catalog_stock('P1')
    pg.click('#all article.card >> nth=0 >> button.btn'); pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P1:2}))"); checkout(pg)
    ok('Order placed' in pg.inner_text('#app') and 'INV-1001' in pg.inner_text('#app'), 'order is placed on the server and numbered INV-1001')
    ok(catalog_stock('P1') == s0 - 2, 'stock is deducted in the shared database')
    # 2 admin on another "device" sees it
    ad = new_ctx(b, poll=True); a = ad.new_page(); a.on('pageerror', lambda e: errs.append((str(e)+' @'+str(getattr(e,'stack',''))[:260]))); a.on('dialog', lambda d: d.accept('x'))
    staff_login(a, 'owner', 'wrong-password'); a.wait_for_selector('#lmsg:not(:empty)'); ok('Wrong username or password' in a.inner_text('#lmsg'), 'wrong password shows an error on the login page')
    a.goto(B + 'admin/index.html'); ok('login.html' in a.url, 'admin pages redirect to login without a session')
    staff_login(a, 'owner', OWNER); a.wait_for_url('**/admin/index.html'); a.wait_for_selector('#side nav button')
    ok(a.evaluate("localStorage.getItem('mc_db')===null && !document.cookie.includes('sid')"), 'admin holds no database locally and the session cookie is hidden from scripts')
    a.click('#side nav button[data-t=orders]'); a.wait_for_selector('#app tbody tr'); ok('INV-1001' in a.inner_text('#app tbody') and 'Real Customer' in a.inner_text('#app tbody'), "the customer's order appears in the admin panel on another device")
    ok(a.is_visible('#bdg-notes'), 'staff get a notification for the new order')
    # 3 prescription workflow across devices
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P5:1}))"); checkout(pg, doc=True)
    a.click('#side nav button[data-t=rx]'); a.wait_for_selector('#app article.card', timeout=20000); ok('Dr A, BMDC 1234' in a.inner_text('#app'), 'pharmacist queue shows the order and the doctor details')
    a.click('button:text-is("Approve")'); a.wait_for_timeout(800)
    pg.goto(B + 'orders.html'); pg.wait_for_selector('#app article.card'); ok('Confirmed' in pg.inner_text('#app') and 'Prescription Review' in pg.inner_text('#app'), 'customer sees the approval on their own device')
    # 4 status change persists
    a.click('#side nav button[data-t=orders]'); a.wait_for_selector('#app tbody select'); a.locator('#app tbody select').nth(1).select_option('Packed'); a.wait_for_timeout(800); a.reload(); a.click('#side nav button[data-t=orders]'); a.wait_for_selector('#app tbody select')
    ok('Packed' in a.inner_text('#app tbody'), 'a status change survives a reload (stored on the server)')
    # 5 two staff devices stay in sync
    a2c = new_ctx(b, poll=True); a2 = a2c.new_page(); a2.on('dialog', lambda d: d.accept('x')); staff_login(a2, 'owner', OWNER); a2.wait_for_selector('#side nav button')
    a.click('#side nav button[data-t=products]'); a.wait_for_selector('#app tbody tr input'); a.locator('#app tbody tr input[aria-label^="Price"]').first.fill('13'); a.keyboard.press('Tab'); a.wait_for_timeout(600)
    a2.click('#side nav button[data-t=products]'); a2.wait_for_selector('#app tbody tr input'); a2.wait_for_timeout(4500)
    ok(a2.locator('#app tbody tr input[aria-label^="Price"]').first.input_value() == '13', 'a price change on one device appears on another within seconds')
    # 6 staff accounts, forced password change, cashier POS
    a.click('#side nav button[data-t=users]'); a.wait_for_selector('input[name=username]'); a.fill('input[name=username]', 'cash2'); a.fill('input[name=name]', 'Cash Two'); a.select_option('select[name=role]', 'Cashier'); a.fill('input[name=password]', 'Temp-Password-9'); a.click('button:text-is("Add staff")'); a.wait_for_timeout(600)
    ok('cash2' in a.inner_text('#app'), 'owner creates a staff account with a real password')
    ca = new_ctx(b, poll=True); c = ca.new_page(); c.on('dialog', lambda d: d.accept('x')); c.on('pageerror', lambda e: errs.append((str(e)+' @'+str(getattr(e,'stack',''))[:260]))); staff_login(c, 'cash2', 'Temp-Password-9'); c.wait_for_selector('dialog[open] input[name=nw]')
    ok('Choose a new password' in c.inner_text('dialog[open]'), 'a new account is forced to choose its own password')
    c.fill('dialog input[name=old]', 'Temp-Password-9'); c.fill('dialog input[name=nw]', 'Cash-Two-New-Pass'); c.fill('dialog input[name=nw2]', 'Cash-Two-New-Pass'); c.click('dialog button.btn'); c.wait_for_timeout(500)
    ok(c.locator('#side nav button').count() == 4 and c.locator('#side nav button[data-t=reports]').count() == 0, 'cashier sees only the cashier screens plus My account')
    c.click('#side nav button[data-t=pos]'); c.wait_for_selector('#pq'); c.fill('#pq', '890001000'); c.press('#pq', 'Enter'); c.wait_for_timeout(200); c.fill('[aria-label="Cash received"]', '100'); c.click('button:text-is("Complete sale")'); c.wait_for_selector('dialog[open]')
    ok('INV-POS-1' in c.inner_text('dialog[open]'), 'cashier completes a POS sale that the server accepts')
    a.click('#side nav button[data-t=dash]'); a.wait_for_timeout(4500); a.click('#side nav button[data-t=dash]'); ok('INV-POS-1' not in a.inner_text('body') and a.evaluate("db().sales.length")==1, "the owner's panel receives the cashier's sale")
    ok(c.evaluate("fetch('/api/state',{method:'POST',headers:XH,body:JSON.stringify({base:{products:VERS.products},changes:{products:db().products.map(p=>({...p,price:1}))}})}).then(r=>r.status)") == 403, 'a cashier tampering with prices from the browser is refused by the server (403)')
    # 7 customer cancel, tracking from another device, contact
    pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); checkout(pg); s1 = catalog_stock('P3'); pg.goto(B + 'orders.html'); pg.wait_for_selector('#app article.card')
    pg.locator('article.card:has-text("INV-1003") button:text-is("Cancel order")').click(); pg.wait_for_timeout(600); ok(catalog_stock('P3') == s1 + 1, 'customer cancel restores stock on the server')
    ot = new_ctx(b); o = ot.new_page(); o.goto(B + 'orders.html'); o.wait_for_selector('input[name=no]'); o.fill('input[name=no]', 'INV-1003'); o.fill('input[name=ph]', '01712345678'); o.click('button:text-is("Track")'); o.wait_for_timeout(500)
    ok('Status: Cancelled' in o.inner_text('#app').replace('\n',' ') or 'Cancelled' in o.inner_text('#app div:has(> p b)'), 'tracking works from any device with order number and mobile')
    o.fill('input[name=ph]', '01999999999'); o.click('button:text-is("Track")'); o.wait_for_timeout(400); ok('No order found' in o.inner_text('#app'), 'wrong mobile number reveals nothing')
    o.goto(B + 'contact.html'); o.wait_for_selector('#app form'); o.fill('#app input[name=n]', 'Sara Akter'); o.fill('#app input[name=ph]', '01912345678'); o.fill('#app textarea[name=m]', 'Do you stock ORS sachets?'); o.click('#app button.btn:has-text("Send message")'); o.wait_for_timeout(600)
    ok('CT-1001' in o.inner_text('#app'), 'contact message is stored on the server with a reference')
    a.click('#side nav button[data-t=notes]'); a.wait_for_timeout(4500); a.click('#side nav button[data-t=notes]'); ok('CT-1001' in a.inner_text('#app'), 'staff receive the customer message')
    # 8 logout
    a.click('button:text-is("Log out")'); a.wait_for_url('**login.html'); a.goto(B + 'admin/index.html'); ok('login.html' in a.url, 'after logout the admin is closed again')
    ok(a.evaluate("fetch('/api/state').then(r=>r.status)") == 401, 'the server no longer accepts the old session')
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
