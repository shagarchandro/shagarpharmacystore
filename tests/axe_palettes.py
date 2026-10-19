import os,sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';AX=open('/tmp/t/node_modules/axe-core/axe.min.js').read();PAL=sys.argv[1]
pages=[('s','index.html'),('s','index.html#/cart'),('s','index.html#/checkout'),('s','index.html#/orders'),('s','index.html#/info'),('s','index.html#/contact'),('s','index.html#/wishlist'),('s','index.html#/product/P2'),('l','admin/login.html')]+[('a','admin/index.html#'+t) for t in ['dash','alerts','products','inv','pos','orders','settings','data','reports','stk','rx']]
out={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for theme in ['light','dark']:
        ctx=b.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script(f"sessionStorage.setItem('mc_role','Owner');localStorage.setItem('mc_theme','{theme}');localStorage.setItem('mc_palette','{PAL}');localStorage.setItem('mc_cart',JSON.stringify({{P1:1,P5:1}}));localStorage.setItem('mc_wish',JSON.stringify(['P1','P2']));")
        pg=ctx.new_page()
        for k,u in pages:
            pg.goto(B+u); pg.wait_for_timeout(200); pg.evaluate(AX)
            r=pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','best-practice']}).then(r=>r.violations.map(v=>({id:v.id,n:v.nodes.length,ex:v.nodes[0].target.join(' ').slice(0,60),sum:(v.nodes[0].any[0]||{}).message||''})))")
            for v in r: out.setdefault(v['id'],[]).append(f"{theme}:{u}:{v['n']}x {v['ex']} | {v['sum'][:110]}")
        ctx.close()
    b.close()
print(PAL,'RULES',len(out))
for k,v in out.items(): print(' ',k,len(v),v[0])
