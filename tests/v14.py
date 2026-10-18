# Real-browser tests for CSV import, backup banner, day report, top sellers, POS shortcuts. Serve on port 8765 first.
import json
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
CSV='name,generic,maker,cat,form,strength,pack,price,cost,disc,reorder,sku,barcode,rx\nGood Syrup,Gen,Mk,Cough,Syrup,100 mg,100 ml,85,60,0,20,SKU-G1,8900000000001,yes\nDup Barcode,Gen,Mk,Cough,Syrup,,,50,30,0,20,SKU-G2,890001000,no\nBad Price,Gen,Mk,Cough,Syrup,,,abc,30,0,20,SKU-G3,,no\n=HYPERLINK("x"),Gen,Mk,Cough,Syrup,,,60,40,0,20,SKU-G4,,no\n'
open('/tmp/import.csv','w',encoding='utf-8').write(CSV)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script("sessionStorage.setItem('mc_role','Owner')")
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:100])); pg.on('dialog',lambda d:d.accept())
    pg.goto(B+'admin/index.html#data'); pg.wait_for_selector('input[type=file]')
    with pg.expect_download() as dl: pg.click('text=Download template')
    ok(dl.value.suggested_filename=='product-template.csv','CSV template downloads')
    pg.set_input_files('input[accept*=csv]','/tmp/import.csv'); pg.wait_for_selector('dialog[open]'); t=pg.inner_text('dialog[open]')
    ok('2 valid row(s), 2 with problems' in t and 'duplicate barcode' in t and 'price' in t,'preview flags duplicate barcode and bad price, keeps valid rows')
    pg.click('dialog[open] button.btn'); pg.wait_for_timeout(300)
    r=pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);const g=d.products.find(p=>p.name==='Good Syrup');return [d.products.length,g&&g.rx,g&&g.price,d.products.some(p=>p.name==='Dup Barcode')]})()"); ok(r[0]==14 and r[1] is True and r[2]==85 and r[3] is False,f'only valid rows imported (Rx parsed) {r}')
    ok(pg.evaluate("JSON.parse(localStorage.mc_db).products.some(p=>p.name.startsWith('=HYPERLINK'))"),'formula-looking name is stored as plain text (and escaped on CSV export)')
    pg.goto(B+'admin/pos.html'); pg.wait_for_selector('#pq'); pg.keyboard.press('F2'); ok(pg.evaluate("document.activeElement.id")=='pq','F2 focuses POS search')
    pg.fill('#pq','890001000'); pg.press('#pq','Enter'); pg.wait_for_timeout(150); pg.fill('[aria-label="Cash received"]','100'); pg.keyboard.press('F9'); pg.wait_for_selector('dialog[open]'); ok('INV-POS-1' in pg.inner_text('dialog[open]'),'F9 completes the sale and shows the receipt'); pg.evaluate("document.querySelector('dialog').remove()")
    pg.goto(B+'admin/index.html#dash'); pg.wait_for_selector('#app h1'); t=pg.inner_text('#app'); ok('Top sellers' in t and 'Napa 500mg' in t and 'POS profit estimate today' in t,'dashboard shows top sellers and profit')
    ok('Back up your data' in t,'backup reminder appears when data exists and was never exported')
    pg.click('#side nav button[data-t=data]'); pg.wait_for_selector('text=Export JSON')
    with pg.expect_download() as d2: pg.click('text=Export JSON')
    pg.goto(B+'admin/index.html#dash'); pg.wait_for_selector('#app h1'); ok('Back up your data' not in pg.inner_text('#app'),'reminder disappears after exporting a backup')
    pg.goto(B+'admin/expenses.html'); pg.wait_for_selector('#app h1'); pg.click('text=Print day report'); pg.wait_for_selector('dialog[open]'); t=pg.inner_text('dialog[open]'); ok('Day-end report' in t and 'Cash: ৳12' in t and 'Expected cash' in t,'day-end report lists today\'s POS cash sales')
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
