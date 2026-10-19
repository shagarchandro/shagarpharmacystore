from playwright.sync_api import sync_playwright
B='http://localhost:8765/'
store=['index.html','index.html#/cart','index.html#/checkout','index.html#/orders','index.html#/wishlist','index.html#/info','index.html#/contact','index.html#/product/P2','products.html','faq.html','cart.html']
tabs=['ledger','stk','alerts','dash','rx','products','cats','inv','pos','orders','returns','purchases','suppliers','customers','expenses','delivery','reports','users','notes','settings','data']
issues=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,h in [(360,740),(768,1024),(1280,800)]:
        ctx=b.new_context(viewport={'width':w,'height':h}); ctx.add_init_script("sessionStorage.setItem('mc_role','Owner')")
        pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e)[:120])); pg.on('console',lambda m:errs.append('CONSOLE '+m.text[:120]) if m.type=='error' else None)
        def chk(url,label):
            pg.goto(B+url); pg.wait_for_timeout(250)
            ov=pg.evaluate("document.documentElement.scrollWidth-innerWidth")
            if ov>1: 
                bad=pg.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,3).map(e=>e.tagName+'.'+e.className)")
                issues.append(f'{w}px OVERFLOW {ov}px {label} {bad}')
        for u in store: chk(u,u)
        for t in tabs: chk('admin/index.html#'+t,'admin#'+t)
        for e in sorted(set(errs)): issues.append(f'{w}px {e}')
        ctx.close()
    b.close()
print('\n'.join(issues) if issues else 'NO ISSUES')
