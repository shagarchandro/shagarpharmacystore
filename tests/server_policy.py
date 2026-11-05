# v1.7 sign-in policy on the REAL server (fresh DB, port 8800)
import json, sqlite3, urllib.request, urllib.error, datetime
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8800/';OWN='Sunrise-Tea-4471';DB='/tmp/shagar_t/shop.db';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
def api(p,b=None,ck=None,raw=False):
    h={'X-Requested-With':'XMLHttpRequest','Content-Type':'application/json'}
    if ck:h['Cookie']=ck
    r=urllib.request.Request(B+'api/'+p,data=json.dumps(b).encode() if b is not None else None,headers=h,method='POST' if b is not None else 'GET')
    try:
        x=urllib.request.urlopen(r);return x if raw else json.load(x)
    except urllib.error.HTTPError as e:
        d=json.loads(e.read() or b'{}');d['status']=e.code;return d
def login(u,p):
    x=api('login',{'username':u,'password':p},raw=True)
    if isinstance(x,dict):return None,x
    return x.headers['Set-Cookie'].split(';')[0],json.load(x)
def setpol(ck,**kw):
    st=api('state',ck=ck);s=st['data']['settings'];v=st['versions']['settings'];s.update(kw)
    return api('state',{'base':{'settings':v},'changes':{'settings':s}},ck)
ck,_=login('owner',OWN)
for nm,role in (('cash','Cashier'),('pharm','Pharmacist')):
    api('staff',{'username':nm,'name':nm,'role':role,'password':'Violet-Sky-2031'},ck)
    k,_=login(nm,'Violet-Sky-2031');api('password',{'old':'Violet-Sky-2031','new':'Violet-Sky-2032'},k)
# defaults: everything off
st=api('state',ck=ck)['data']['settings'];ok(st.get('req2fa')=='' and not st.get('hoursOn') and st.get('maxSessions')==0 and st.get('pwMaxDays')==0,'policy is off by default')
# validation
r=setpol(ck,req2fa='bogus');ok(r.get('status') in (400,422),'unknown two-step policy value is refused')
r=setpol(ck,pwMaxDays=10);ok(r.get('status') in (400,422),'password max age below 30 days is refused')
r=setpol(ck,hoursOn=True,hoursFrom=9,hoursTo=9);ok(r.get('status') in (400,422),'empty sign-in window is refused')
ok('req2fa' not in api('catalog')['settings'],'policy is not exposed to the public shop')
# hours window: Owner exempt, staff blocked outside it
h=(datetime.datetime.utcnow()+datetime.timedelta(hours=6)).hour
out_from,out_to=(h+2)%24,(h+4)%24 or 24
r=setpol(ck,hoursOn=True,hoursFrom=out_from,hoursTo=out_to);ok(not r.get('error'),'owner saves a sign-in window')
k,r=login('cash','Violet-Sky-2032');ok(k is None and r.get('status')==403 and 'Dhaka time' in r.get('error',''),'cashier is blocked outside the window')
k,r=login('owner',OWN);ok(k is not None,'owner is never blocked by the hours rule');ck=k
ev=[e['event'] for e in api('security-log?limit=50',ck=ck)['events']]
ok('login_outside_hours' in ev,'blocked sign-in is written to the security log')
c=sqlite3.connect(DB);ok(c.execute("SELECT failed FROM staff WHERE username='cash'").fetchone()[0]==0,'a blocked sign-in does not count as a wrong password')
r=setpol(ck,hoursOn=True,hoursFrom=h,hoursTo=(h+1)%24 or 24);k,r=login('cash','Violet-Sky-2032');ok(k is not None,'cashier can sign in inside the window')
setpol(ck,hoursOn=False)
# device limit
setpol(ck,maxSessions=1)
k1,_=login('cash','Violet-Sky-2032');k2,_=login('cash','Violet-Sky-2032')
ok(api('me',ck=k2).get('user') and not api('me',ck=k1).get('user'),'second sign-in closes the older device when the limit is 1')
setpol(ck,maxSessions=0)
# password expiry
setpol(ck,pwMaxDays=30);c.execute("UPDATE staff SET pw_changed='2020-01-01T00:00:00.000Z' WHERE username='pharm'");c.commit()
k,r=login('pharm','Violet-Sky-2032');ok(r['user']['must_change'] is True,'an expired password must be changed at sign-in')
setpol(ck,pwMaxDays=0)
# required two-step: locked to My account until enrolled
r=setpol(ck,req2fa='owner_pharmacist');ok(r.get('status')==400 and 'your own two-step' in r.get('error','').lower(),'cannot require two-step before turning it on yourself')
c.execute("UPDATE staff SET totp_enabled=1 WHERE username='owner'");c.commit()
r=setpol(ck,req2fa='owner_pharmacist');ok(not r.get('error'),'owner with two-step on can require it')
k,r=login('cash','Violet-Sky-2032');ok(r['user']['must_2fa'] is False,'cashier is not affected when only owner and pharmacist are required')
c.execute("UPDATE staff SET must_change=0 WHERE username='pharm'");c.commit();k,r=login('pharm','Violet-Sky-2032')
ok(r['user']['must_2fa'] is True,'pharmacist is told two-step is required')
ok(api('state',ck=k).get('status')==403 and 'two-step' in api('state',ck=k).get('error','').lower(),'data is locked until two-step is on')
ok(api('account',ck=k).get('user') is not None,'My account stays open so they can set it up')
ok(api('me',ck=k)['user']['must_2fa'] is True,'/api/me reports must_2fa')
with sync_playwright() as p:
    b=p.chromium.launch();errs=[];pg=b.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(B+'admin/login.html');pg.fill('#lu','pharm');pg.fill('#lp','Violet-Sky-2032');pg.click('button.btn');pg.wait_for_url('**/admin/index.html');pg.wait_for_selector('#side nav button')
    pg.wait_for_selector('text=Two-step login is required',timeout=8000);ok(pg.locator('#side nav button').count()==1,'required-two-step account sees only My account, with a notice')
    r=setpol(ck,req2fa='');c.execute("UPDATE staff SET totp_enabled=0 WHERE username='owner'");c.commit();ok(not r.get('error'),'owner turns the requirement off again')
    q=b.new_page();q.on('pageerror',lambda e:errs.append(str(e)));q.goto(B+'admin/login.html');q.fill('#lu','owner');q.fill('#lp',OWN);q.click('button.btn');q.wait_for_url('**/admin/index.html');q.wait_for_selector('#side nav button')
    q.click('#side nav button[data-t=settings]');q.wait_for_selector('text=Sign-in policy');q.fill('input[name=maxSessions]','3');q.click('text=Save sign-in policy');q.wait_for_timeout(1000)
    k3,_=login('owner',OWN);ok(api('state',ck=k3)['data']['settings']['maxSessions']==3,'policy card saves to the server')
    ok(not errs,'no page errors '+str(errs[:2]));b.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
