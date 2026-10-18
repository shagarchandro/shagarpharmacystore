from playwright.sync_api import sync_playwright
B='http://localhost:8765/'
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':800,'height':900}); ctx.add_init_script("sessionStorage.setItem('mc_role','Owner')")
    pg=ctx.new_page(); pg.on('dialog',lambda d:d.accept()); pg.goto(B+'admin/pos.html'); pg.wait_for_selector('#pq'); pg.fill('#pq','890001000'); pg.press('#pq','Enter'); pg.wait_for_timeout(200)
    pg.fill('[aria-label="Cash received"]','100'); pg.click('text=Complete sale'); pg.wait_for_selector('dialog[open]')
    pg.emulate_media(media='print'); print('top hidden:',pg.evaluate("getComputedStyle(document.querySelector('.top')).display"),'| side hidden:',pg.evaluate("getComputedStyle(document.querySelector('.side')).display"),'| dialog buttons hidden:',pg.evaluate("getComputedStyle(document.querySelector('dialog button')).display"))
    pg.pdf(path='/tmp/receipt.pdf'); pg.screenshot(path='/tmp/receipt_print.png'); b.close()
