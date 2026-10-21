# Real-browser tests of the staff login experience on the REAL server. Fresh DB:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471' --rate-scale 50
import json, hmac, hashlib, base64, struct, time, urllib.request, urllib.error, re
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800/'; OWNER = 'Sunrise-Tea-4471'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def totp(secret, counter=None):
    counter = int(time.time() // 30) if counter is None else counter
    key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8)); h = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest(); o = h[-1] & 15
    return str((struct.unpack('>I', h[o:o + 4])[0] & 0x7fffffff) % 10 ** 6).zfill(6)
def api(path, body=None, cookie=None, raw=False):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    r = urllib.request.Request(B + 'api/' + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method='POST' if body is not None else 'GET')
    try:
        x = urllib.request.urlopen(r); return x if raw else json.load(x)
    except urllib.error.HTTPError as e: return {'error': json.loads(e.read() or b'{}').get('error'), 'status': e.code}
ck = api('login', {'username': 'owner', 'password': OWNER}, raw=True).headers['Set-Cookie'].split(';')[0]
api('staff', {'username': 'twofa1', 'name': 'Two Fa', 'role': 'Pharmacist', 'password': 'Violet-Sky-2031'}, ck)
k = api('login', {'username': 'twofa1', 'password': 'Violet-Sky-2031'}, raw=True).headers['Set-Cookie'].split(';')[0]; api('password', {'old': 'Violet-Sky-2031', 'new': 'Violet-Sky-2032'}, k)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def ctx(poll=True): c = b.new_context(viewport={'width': 1280, 'height': 900}); c.add_init_script("localStorage.setItem('mc_poll','60000')") if poll else None; return c
    def login(pg, u, pw, code=None):
        pg.goto(B + 'admin/login.html'); pg.wait_for_selector('#lu'); pg.fill('#lu', u); pg.fill('#lp', pw)
        pg.click('button.btn')
        if code: pg.wait_for_selector('#lc', state='visible'); pg.fill('#lc', code); pg.click('button.btn')
    # 1 redirect back to the page the user wanted
    c = ctx(); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:150])); pg.on('dialog', lambda d: d.accept('x'))
    pg.goto(B + 'admin/pos.html'); pg.wait_for_url('**login.html?next=pos.html'); ok('next=pos.html' in pg.url, 'a closed admin page sends you to login and remembers where you were going')
    # 2 login page behaviour
    pg.fill('#lu', 'owner'); pg.fill('#lp', 'wrong-password'); pg.click('button.btn'); pg.wait_for_selector('#lmsg:not(:empty)'); ok('Wrong username or password' in pg.inner_text('#lmsg') and pg.get_attribute('#lmsg', 'role') == 'alert', 'a wrong password shows an announced error')
    pg.click('button:text-is("Show")'); ok(pg.get_attribute('#lp', 'type') == 'text', 'the Show button reveals the password'); pg.click('button:text-is("Hide")'); ok(pg.get_attribute('#lp', 'type') == 'password', 'and hides it again')
    pg.evaluate("document.getElementById('lp').dispatchEvent(new KeyboardEvent('keyup',{key:'A',modifierCapsLock:true}))"); ok(pg.is_visible('text=Caps Lock is on'), 'a Caps Lock warning appears')
    pg.click('summary:has-text("Forgot your password")'); ok('--reset-password owner' in pg.inner_text('details'), 'forgot-password help explains how the Owner recovers access')
    pg.fill('#lp', OWNER); pg.click('button.btn'); pg.wait_for_url('**/admin/pos.html'); ok('/admin/pos.html' in pg.url, 'after login you land on the page you asked for')
    pg.click('#side nav button[data-t=dash]'); pg.wait_for_selector('#app h1'); ok('Protect your account' in pg.inner_text('#app'), 'the owner is reminded to turn on two-step login'); pg.click('button:text-is("Not now")'); pg.wait_for_timeout(300); ok('Protect your account' not in pg.inner_text('#app'), 'the reminder can be dismissed')
    pg.click('button:text-is("Log out")'); pg.wait_for_url('**login.html'); pg.wait_for_selector('#lu'); ok(pg.input_value('#lu') == 'owner', 'the login page remembers the last username (never the password)')
    # 3 password change + strength meter + 2FA for twofa1
    login(pg, 'twofa1', 'Violet-Sky-2032'); pg.wait_for_url('**/admin/index.html'); pg.click('#side nav button[data-t=account]'); pg.wait_for_selector('input[name=old]')
    pg.fill('input[name=nw]', 'abc'); ok('Too weak' in pg.inner_text('p[aria-live=polite]'), 'weak passwords show “Too weak”'); pg.fill('input[name=nw]', 'Correct-Horse-Battery-9'); ok('Strong' in pg.inner_text('p[aria-live=polite]'), 'a good passphrase shows “Strong”')
    pg.fill('input[name=old]', 'not-my-password'); pg.fill('input[name=nw2]', 'Correct-Horse-Battery-9'); pg.click('button.btn:text-is("Change password")'); pg.wait_for_timeout(400); ok('current password is wrong' in pg.inner_text('#toasts'), 'a wrong current password is refused')
    pg.fill('input[name=old]', 'Violet-Sky-2032'); pg.click('button.btn:text-is("Change password")'); pg.wait_for_timeout(500); ok('Password changed' in pg.inner_text('#toasts'), 'the password can be changed from My account')
    pg.click('#side nav button[data-t=account]'); pg.click('button:text-is("Set up two-step login")'); pg.wait_for_selector('code.key'); secret = pg.inner_text('code.key').replace(' ', ''); ok(re.fullmatch(r'[A-Z2-7]{32}', secret) is not None, 'two-step setup shows an authenticator key')
    pg.fill('dialog input[name=pw], .card input[name=pw]', 'Correct-Horse-Battery-9'); pg.fill('.card input[name=code]', totp(secret)); pg.click('button.btn:text-is("Turn on")'); pg.wait_for_selector('ul.codes'); codes = pg.locator('ul.codes li').all_inner_texts(); ok(len(codes) == 10, 'ten one-time recovery codes are shown'); pg.click('button:text-is("I have saved them")')
    pg.click('button:text-is("Log out")'); pg.wait_for_url('**login.html')
    login(pg, 'twofa1', 'Correct-Horse-Battery-9'); pg.wait_for_selector('#lc', state='visible'); ok('6-digit code' in pg.inner_text('#lmsg'), 'a correct password alone now asks for the authenticator code')
    pg.fill('#lc', '000000'); pg.click('button.btn'); pg.wait_for_selector('#lmsg:has-text("not right")'); ok(True, 'a wrong code is refused')
    pg.fill('#lc', totp(secret, int(time.time() // 30) + 1)); pg.click('button.btn'); pg.wait_for_url('**/admin/index.html'); ok(pg.is_visible('#side nav'), 'password + code signs in')
    pg.click('button:text-is("Log out")'); pg.wait_for_url('**login.html'); login(pg, 'twofa1', 'Correct-Horse-Battery-9', codes[0]); pg.wait_for_url('**/admin/index.html'); ok(True, 'a recovery code signs in when the phone is lost')
    # 4 devices
    ow = ctx(); a = ow.new_page(); a.on('dialog', lambda d: d.accept('x')); login(a, 'owner', OWNER); a.wait_for_url('**/admin/index.html')
    ob = ctx(); bb = ob.new_page(); login(bb, 'owner', OWNER); bb.wait_for_url('**/admin/index.html')
    a.click('#side nav button[data-t=account]'); a.wait_for_selector('button:text-is("Sign out all other devices")'); ok(a.locator('#app table >> nth=0').inner_text().count('Chrome') >= 2 or a.locator('#app tbody tr').count() >= 2, 'My account lists every signed-in device')
    a.click('button:text-is("Sign out all other devices")'); a.wait_for_timeout(600); ok(bb.evaluate("fetch('/api/state').then(r=>r.status)") == 401, 'signing out other devices works immediately')
    # 5 staff management and security log
    a.click('#side nav button[data-t=users]'); a.wait_for_selector('tr:has-text("twofa1")'); ok('On' in a.inner_text('tr:has-text("twofa1")'), 'the staff table shows who uses two-step login')
    a.click('tr:has-text("twofa1") button:text-is("Edit")'); a.wait_for_selector('dialog[open] select[name=role]'); a.select_option('dialog select[name=role]', 'Cashier'); a.click('dialog button.btn'); a.wait_for_timeout(500); ok('Cashier' in a.inner_text('tr:has-text("twofa1")'), 'the Owner can change a role')
    for _ in range(5): api('login', {'username': 'twofa1', 'password': 'wrong-password-x'})
    a.click('#side nav button[data-t=users]'); a.wait_for_selector('tr:has-text("twofa1") button:text-is("Unlock")'); ok('Locked' in a.inner_text('tr:has-text("twofa1")'), 'a locked account is marked'); a.click('tr:has-text("twofa1") button:text-is("Unlock")'); a.wait_for_timeout(500); ok('Locked' not in a.inner_text('tr:has-text("twofa1")'), 'and can be unlocked in one click')
    a.click('tr:has-text("twofa1") button:text-is("Reset two-step")'); a.wait_for_timeout(500); ok('Off' in a.inner_text('tr:has-text("twofa1")'), 'two-step can be reset for someone who lost their phone')
    a.click('#side nav button[data-t=seclog]'); a.wait_for_selector('#app tbody tr'); t = a.inner_text('#app'); ok('Failed sign-in' in t and 'Role changed' in t and 'Two-step reset' in t, 'the security log shows failures and account changes')
    with a.expect_download() as dl: a.click('button:text-is("Export CSV")')
    ok(dl.value.suggested_filename == 'security-log.csv', 'the security log exports to CSV')
    # 6 idle warning
    a.click('#side nav button[data-t=dash]'); a.evaluate("IDLE_LAST=Date.now()-(D.settings.idleMin*60000-30000);idleCheck()"); a.wait_for_selector('dialog[open]:has-text("Still there?")'); ok(True, 'a warning appears a minute before an idle sign-out')
    a.click('button:text-is("Stay signed in")'); a.wait_for_timeout(300); ok(a.locator('dialog[open]').count() == 0 and a.evaluate("fetch('/api/state').then(r=>r.status)") == 200, 'Stay signed in keeps the session')
    ok(not errs, 'no page errors ' + str(errs)); b.close()
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
