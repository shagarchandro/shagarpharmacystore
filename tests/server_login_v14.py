# v1.4 staff-login updates on the REAL server. Fresh DB:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471' --rate-scale 50
import json, sqlite3, subprocess, sys, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; DB = '/tmp/shagar_t/shop.db'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def api(path, body=None, cookie=None, raw=False):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    r = urllib.request.Request(B + 'api/' + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method='POST' if body is not None else 'GET')
    try:
        x = urllib.request.urlopen(r); return x if raw else json.load(x)
    except urllib.error.HTTPError as e: return {'error': json.loads(e.read() or b'{}').get('error'), 'status': e.code}
x = api('login', {'username': 'owner', 'password': OWNER}, raw=True); ck = x.headers['Set-Cookie'].split(';')[0]; j = json.load(x)['user']
ok('pw_age_days' in j and j['new_address'] is False, 'login reports password age and no new address on the first sign-in')
api('login', {'username': 'owner', 'password': OWNER})
c = sqlite3.connect(DB); c.execute("UPDATE staff SET last_ip='203.0.113.9' WHERE username='owner'"); c.commit()
j = api('login', {'username': 'owner', 'password': OWNER})['user']
ok(j['new_address'] is True and j['prev_ip'] == '203.0.113.9', 'a different address than last time is flagged')
ev = [e['event'] for e in api('security-log?limit=50', cookie=ck)['events']]
ok('login_new_address' in ev, 'the new-address sign-in is written to the security log')
c.execute("UPDATE staff SET pw_changed='2020-01-01T00:00:00.000Z' WHERE username='owner'"); c.commit()
ok(api('account', cookie=ck)['pw_age_days'] > 1000, 'account reports the real password age')
st = api('staff', cookie=ck)['staff'][0]
ok('sessions' in st and 'pw_age_days' in st, 'staff list has session count and password age')
r = api('password', {'old': OWNER, 'new': OWNER + 'x9'}, ck); ok(r.get('ok'), 'password change works')
ok(api('account', cookie=ck).get('pw_age_days') == 0 or api('login', {'username': 'owner', 'password': OWNER + 'x9'}).get('user', {}).get('pw_age_days') == 0, 'password age resets after a change')
OWNER2 = OWNER + 'x9'
out = subprocess.run([sys.executable, 'server/server.py', '--data', '/tmp/shagar_t', '--list-staff'], capture_output=True, text=True).stdout
ok('owner' in out and 'Owner' in out and 'pw age' in out, '--list-staff prints accounts without secrets')
ok('salt' not in out.lower() and 'sha' not in out.lower(), '--list-staff shows no password data')
c.execute("UPDATE staff SET last_ip='203.0.113.9', pw_changed='2020-01-01T00:00:00.000Z' WHERE username='owner'"); c.commit()
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_context(viewport={'width': 1280, 'height': 900}).new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + 'admin/login.html'); pg.wait_for_selector('#lu')
    ok(pg.locator('#lrem').is_checked() and pg.locator('main.login button[aria-label="Toggle theme"]').count() == 1, 'login page has Remember username and the display buttons')
    pg.uncheck('#lrem'); pg.fill('#lu', 'owner'); pg.fill('#lp', OWNER2); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html'); pg.wait_for_selector('#side nav button')
    ok(pg.evaluate("localStorage.getItem('mc_lastuser')") is None, 'unchecked Remember does not store the username')
    pg.wait_for_selector('.signin-notices .card', timeout=5000); t = pg.inner_text('.signin-notices')
    ok('New sign-in address' in t and '203.0.113.9' in t and 'Time to refresh your password' in t, 'banner warns about the new address and the old password')
    pg.click('.signin-notices >> text=Dismiss >> nth=0'); ok(pg.locator('.signin-notices .card').count() == 1, 'a notice can be dismissed')
    pg.click('#side nav button[data-t=users]'); pg.wait_for_selector('text=Staff security overview'); ok('Using two-step login' in pg.inner_text('#app') and 'Password age' in pg.inner_text('#app'), 'Users shows the staff security overview')
    pg.click('#side nav button[data-t=account]'); pg.wait_for_selector('text=Need a strong password?'); pg.click('text=Suggest a password')
    pw = pg.inner_text('code'); import re
    ok(len(pw) == 16 and re.search('[a-z]', pw) and re.search('[A-Z]', pw) and re.search(r'\d', pw) and re.search(r'[^A-Za-z0-9]', pw), 'password suggestion has 16 characters and all four kinds')
    pg.goto(B + 'admin/login.html'); pg.wait_for_selector('#lu'); pg.check('#lrem'); pg.fill('#lu', 'owner'); pg.fill('#lp', OWNER2); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html')
    pg.goto(B + 'admin/login.html'); pg.wait_for_selector('#lu'); ok(pg.input_value('#lu') == 'owner', 'a remembered username is pre-filled')
    ok(not errs, 'no page errors ' + str(errs[:2]))
    b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
