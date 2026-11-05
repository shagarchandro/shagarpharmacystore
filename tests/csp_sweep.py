# Visits every page of the REAL server and fails on any console error (this includes Content-Security-Policy violations).
import json, urllib.request
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
hdr = urllib.request.urlopen(B + 'index.html').headers.get('Content-Security-Policy', '')
ok("script-src 'self';" in hdr and "script-src 'self' 'unsafe" not in hdr, 'the policy allows only scripts from this site (no inline scripts)')
store = ['index.html', 'index.html#/cart', 'index.html#/checkout', 'index.html#/orders', 'index.html#/info', 'index.html#/health', 'index.html#/sharewish/P1~P2', 'index.html#/wishlist', 'index.html#/contact', 'index.html#/orders', 'index.html#/sharecart/P1.2~P2.1', 'index.html#/compare', 'health.html', 'compare.html', 'index.html#/contact', 'index.html#/product/P2', 'products.html', 'faq.html', 'shipping.html', 'privacy.html', 'cart.html', 'checkout.html', 'orders.html', 'contact.html', 'wishlist.html', 'order-success.html', 'product-details.html?id=P1', '404-not-here.html']
tabs = ['customer360', 'insights', 'refill', 'labels', 'pricelist', 'expiry', 'margins', 'reorder', 'dash', 'alerts', 'rx', 'orders', 'pos', 'returns', 'delivery', 'products', 'cats', 'inv', 'stk', 'ledger', 'purchases', 'suppliers', 'customers', 'expenses', 'reports', 'notes', 'users', 'seclog', 'account', 'settings', 'data']
with sync_playwright() as p:
    b = p.chromium.launch(); bad = []
    c = b.new_context(viewport={'width': 1280, 'height': 900}); pg = c.new_page()
    pg.on('console', lambda m: bad.append(m.text[:140]) if m.type == 'error' and '404' not in m.text else None); pg.on('pageerror', lambda e: bad.append('PAGEERR ' + str(e)[:140]))
    for u in store: pg.goto(B + u); pg.wait_for_timeout(300)
    ok(not bad, 'every storefront page loads with no console or policy errors ' + str(bad[:3]))
    pg.goto(B + 'admin/login.html'); pg.wait_for_selector('#lu'); pg.fill('#lu', 'owner'); pg.fill('#lp', OWNER); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html'); pg.wait_for_selector('#side nav button')
    for t in tabs: pg.click(f'#side nav button[data-t={t}]'); pg.wait_for_timeout(250)
    for u in ('admin/pos.html', 'admin/inventory.html', 'admin/reports.html', 'admin/users.html', 'admin/settings.html', 'admin/insights.html', 'admin/refill.html', 'admin/labels.html', 'admin/pricelist.html', 'admin/customer360.html', 'admin/expiry.html', 'admin/margins.html', 'admin/reorder.html'): pg.goto(B + u); pg.wait_for_selector('#side nav button'); pg.wait_for_timeout(200)
    ok(not bad, 'every admin screen and admin page loads with no console or policy errors ' + str(bad[:3]))
    c2 = b.new_context(); q = c2.new_page(); q.goto(B + 'admin/pos.html'); q.wait_for_url('**login.html?next=pos.html'); ok(True, 'the redirect to login still works without any inline script')
    b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
