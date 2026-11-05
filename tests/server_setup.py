# v1.9: real first-run setup (own server on port 8803, fresh data dir, NO --owner-password)
import json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8803/';D='/tmp/shagar_setup';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
shutil.rmtree(D,ignore_errors=True)
root=os.path.dirname(os.path.abspath(__file__))+'/../server/server.py'
log=open('/tmp/setup_srv.log','w');srv=subprocess.Popen([sys.executable,'-u',root,'--port','8803','--data',D,'--rate-scale','50'],stdout=log,stderr=subprocess.STDOUT)
def api(p,b=None):
    r=urllib.request.Request(B+'api/'+p,data=json.dumps(b).encode() if b is not None else None,headers={'X-Requested-With':'XMLHttpRequest','Content-Type':'application/json'},method='POST' if b is not None else 'GET')
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e: d=json.loads(e.read() or b'{}');d['status']=e.code;return d
try:
    for _ in range(50):
        try: urllib.request.urlopen(B+'api/health');break
        except Exception: time.sleep(.2)
    out=open('/tmp/setup_srv.log').read();m=re.search(r'Setup code[^:]*: (\S+)',out);code=m.group(1) if m else ''
    ok(bool(code) and 'password:' not in out,'server prints a setup code and no default password')
    ok(api('setup')['needed'] is True,'setup is reported as needed')
    ok(api('login',{'username':'owner','password':'anything-at-all'}).get('status') in (401,403),'no default account exists')
    ok(api('setup',{'code':'wrong','name':'A B','username':'boss','password':'Sunrise-Tea-4471'}).get('status')==403,'wrong setup code is refused')
    ok(api('setup',{'code':code,'name':'A B','username':'boss','password':'short'}).get('status')==400,'weak password is refused')
    ok(api('setup',{'code':code,'name':'A B','username':'B!','password':'Sunrise-Tea-4471'}).get('status')==400,'bad username is refused')
    with sync_playwright() as p:
        b=p.chromium.launch();errs=[];pg=b.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(B+'admin/login.html');pg.wait_for_selector('#sc');ok('Set up your shop' in pg.inner_text('h1'),'login page shows the first-run form')
        pg.fill('#sc',code);pg.fill('#sn','Rahim Uddin');pg.fill('#su','boss');pg.fill('#sp','Sunrise-Tea-4471');pg.fill('#sp2','different-Pass-1');pg.click('button.btn')
        pg.wait_for_selector('#lmsg:not(:empty)');ok('different' in pg.inner_text('#lmsg'),'mismatching passwords are caught in the browser')
        pg.fill('#sp2','Sunrise-Tea-4471');pg.click('button.btn');pg.wait_for_url('**/admin/index.html');pg.wait_for_selector('#side nav button')
        ok(pg.evaluate("ME.role")=='Owner' and pg.evaluate("ME.username")=='boss','owner is created and signed in');ok(not errs,'no page errors '+str(errs[:2]));b.close()
    ok(api('setup')['needed'] is False,'setup closes once the owner exists')
    ok(api('setup',{'code':code,'name':'X Y','username':'second','password':'Sunrise-Tea-4471x'}).get('status')==409,'a second owner cannot be created')
    ok(api('login',{'username':'boss','password':'Sunrise-Tea-4471'}).get('user',{}).get('role')=='Owner','normal login works afterwards')
finally:
    srv.terminate();srv.wait(5)
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
