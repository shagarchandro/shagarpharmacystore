# v3.2 POS against the REAL server (fresh DB, port 8800): the server must accept sales made with the new screen
import json
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8800/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b=p.chromium.launch();errs=[];dl=[];pg=b.new_context(viewport={'width':1280,'height':900}).new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(dl.append(d.type),d.accept()))
    pg.goto(B+'admin/login.html');pg.wait_for_selector('#lu');pg.fill('#lu','owner');pg.fill('#lp','Sunrise-Tea-4471');pg.click('button.btn');pg.wait_for_url('**/admin/index.html');pg.wait_for_selector('details.navgrp')
    pg.click('#side nav button[data-t=pos]');pg.wait_for_selector('.posgrid')
    pg.fill('#pq','napa');pg.wait_for_selector('.pos-results li');pg.keyboard.press('Enter');pg.wait_for_selector('.stepper');pg.click('button[aria-label^="One more"]');pg.wait_for_selector('.stepper input[value="2"]')
    pg.fill('[aria-label="Discount ৳"]','4');pg.click('.pos-chips button:has-text("৳100")');ok('Change' in pg.inner_text('.pos-change'),'live totals with the server catalog: '+pg.inner_text('.pos-total')+' / '+pg.inner_text('.pos-change'))
    pg.click('button:text-is("Complete sale")');pg.wait_for_selector('dialog.rcpt80[open]');ok('Cash received' in pg.inner_text('dialog.rcpt80'),'the server accepted the sale and the receipt shows')
    pg.evaluate("document.querySelectorAll('dialog').forEach(x=>x.remove())");pg.wait_for_timeout(1500);pg.reload();pg.wait_for_selector('.posgrid');ok('1 sale(s)' in pg.inner_text('#app'),'the sale is still there after a reload (saved on the server): '+pg.inner_text('.card:has(h2:has-text("Today at the till")) p'))
    # Rx sale: inline reference, no pop-up
    pg.fill('#pq','amlodipine');pg.wait_for_selector('.pos-results li');pg.keyboard.press('Enter');pg.wait_for_selector('.stepper');pg.fill('[aria-label="Prescription reference"]','Dr Karim BMDC 54321 2026-11-02');pg.fill('[aria-label="Cash received"]','500');dl.clear()
    pg.click('button:text-is("Complete sale")');pg.wait_for_selector('dialog.rcpt80[open]');ok('prompt' not in dl and 'Prescription: Dr Karim' in pg.inner_text('dialog.rcpt80'),'prescription sale accepted by the server with the inline reference')
    pg.evaluate("document.querySelectorAll('dialog').forEach(x=>x.remove())")
    pg.click('button:has-text("Receipt") >> nth=0');pg.wait_for_selector('dialog.rcpt80[open]');ok(True,'receipt can be reprinted')
    ok(not errs,'no page errors '+str(errs[:2]));b.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
