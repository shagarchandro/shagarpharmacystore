# Offline check: after one visit the shell (page, styles, fonts, scripts) loads without a network (demo mode, port 8765)
import sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':1100,'height':800});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(B+'index.html');pg.wait_for_selector('#all');pg.evaluate("navigator.serviceWorker.ready.then(()=>1)");pg.wait_for_timeout(1500)
    pg.reload();pg.wait_for_selector('#all');pg.wait_for_timeout(800)   # now controlled by the service worker
    ok(pg.evaluate("!!navigator.serviceWorker.controller"),'service worker controls the page')
    ctx.set_offline(True)
    pg.reload();pg.wait_for_selector('#all',timeout=8000);pg.wait_for_timeout(600)
    ok(pg.locator('#all article.card').count()>=3,'offline: home page and products render')
    ok(pg.evaluate("getComputedStyle(document.querySelector('header.bar')).backgroundColor")!='rgba(0, 0, 0, 0)','offline: styles are applied (header colour)')
    ok(pg.evaluate("document.fonts.check('700 20px \"Bricolage Grotesque Variable\"')") and pg.evaluate("[...document.fonts].some(f=>f.status==='loaded')"),'offline: fonts load from the cache')
    ok(not errs,'no page errors '+str(errs[:2]));br.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
sys.exit(1 if any(r.startswith('FAIL') for r in res) else 0)
