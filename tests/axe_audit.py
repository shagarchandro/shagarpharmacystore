import json
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';AX=open('/tmp/t/node_modules/axe-core/axe.min.js').read()
pages=[('store','index.html'),('store','index.html#/cart'),('store','index.html#/checkout'),('store','index.html#/orders'),('store','index.html#/info'),('store','index.html#/contact'),('store','index.html#/product/P2'),('login','admin/login.html')]+[('admin','admin/index.html#'+t) for t in ['dash','alerts','products','inv','pos','orders','returns','purchases','suppliers','customers','expenses','reports','users','notes','settings','data','cats','delivery','rx','stk']]
out={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for theme in ['light','dark']:
        ctx=b.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script(f"sessionStorage.setItem('mc_role','Owner');localStorage.setItem('mc_theme','{theme}');localStorage.setItem('mc_cart',JSON.stringify({{P1:1}}))")
        pg=ctx.new_page()
        for kind,u in pages:
            pg.goto(B+u); pg.wait_for_timeout(250); pg.evaluate(AX)
            r=pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','best-practice']}).then(r=>r.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,ex:v.nodes[0].target.join(' ').slice(0,70)})))")
            for v in r: out.setdefault(v['id']+' ['+str(v['impact'])+']',[]).append(f"{theme}:{u}:{v['n']}x {v['ex']}")
        ctx.close()
    b.close()
for k,v in out.items(): print(k,len(v)); print('   ',v[0]); 
print('TOTAL RULES',len(out))
