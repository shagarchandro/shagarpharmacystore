// admin-extras.js (v1.3): extra admin screens, registered before admin.js runs.
// Insights (sales by hour/weekday, stock cover forecast, dead stock, ABC, top customers),
// Refill follow-ups (who may be due to buy again) and Shelf labels (Code 128 barcodes).
// The view functions only run later, when admin.js has defined D, h, tbl, act, nm, money ...
(()=>{
'use strict';
try{const v=+localStorage.getItem('mc_fs');if([112,125,140].includes(v))document.documentElement.style.fontSize=v+'%'}catch(e){}
if(typeof I18!=='undefined')Object.assign(I18.bn,{Insights:'ইনসাইট','Refill follow-ups':'রিফিল ফলো-আপ','Shelf labels':'শেলফ লেবেল','Expiry planner':'মেয়াদ পরিকল্পনা','Margin analysis':'মার্জিন বিশ্লেষণ','Supplier orders':'সরবরাহকারী অর্ডার','Price list':'দামের তালিকা','Customer lookup':'গ্রাহক খুঁজুন','Staff security overview':'স্টাফ নিরাপত্তা ওভারভিউ','Sign-in policy':'সাইন-ইন নীতি','Save sign-in policy':'নীতি সংরক্ষণ করুন','Need a strong password?':'শক্তিশালী পাসওয়ার্ড দরকার?','Suggest a password':'পাসওয়ার্ড প্রস্তাব করুন'});
const C128='11011001100,11001101100,11001100110,10010011000,10010001100,10001001100,10011001000,10011000100,10001100100,11001001000,11001000100,11000100100,10110011100,10011011100,10011001110,10111001100,10011101100,10011100110,11001110010,11001011100,11001001110,11011100100,11001110100,11101101110,11101001100,11100101100,11100100110,11101100100,11100110100,11100110010,11011011000,11011000110,11000110110,10100011000,10001011000,10001000110,10110001000,10001101000,10001100010,11010001000,11000101000,11000100010,10110111000,10110001110,10001101110,10111011000,10111000110,10001110110,11101110110,11010001110,11000101110,11011101000,11011100010,11011101110,11101011000,11101000110,11100010110,11101101000,11101100010,11100011010,11101111010,11001000010,11110001010,10100110000,10100001100,10010110000,10010000110,10000101100,10000100110,10110010000,10110000100,10011010000,10011000010,10000110100,10000110010,11000010010,11001010000,11110111010,11000010100,10001111010,10100111100,10010111100,10010011110,10111100100,10011110100,10011110010,11110100100,11110010100,11110010010,11011011110,11011110110,11110110110,10101111000,10100011110,10001011110,10111101000,10111100010,11110101000,11110100010,10111011110,10111101110,11101011110,11110101110,11010000100,11010010000,11010011100'.split(',');
const STOP='1100011101011';
// Code 128 set B (printable ASCII 32-126); returns a string of 0/1 modules
const code128=s=>{s=String(s).replace(/[^\x20-\x7e]/g,'');if(!s)return '';let sum=104,out=C128[104];
 for(let i=0;i<s.length;i++){const v=s.charCodeAt(i)-32;sum+=v*(i+1);out+=C128[v]}
 return out+C128[sum%103]+STOP};
const barSvg=(s)=>{const m=code128(s),q=10;if(!m)return h('span',{},'—');
 let d='',i=0;while(i<m.length){if(m[i]==='1'){let j=i;while(m[j]==='1')j++;d+='M'+(i+q)+' 0h'+(j-i)+'v40h-'+(j-i)+'z';i=j}else i++}
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 '+(m.length+2*q)+' 40');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('role','img');svg.setAttribute('aria-label','Barcode '+s);
 const bg=document.createElementNS(ns,'rect');bg.setAttribute('width',m.length+2*q);bg.setAttribute('height',40);bg.setAttribute('fill','#fff');svg.append(bg);
 const p=document.createElementNS(ns,'path');p.setAttribute('d',d);p.setAttribute('fill','#000');svg.append(p);return svg};
window.__code128=code128;

const dayMs=864e5;
const itemsOf=()=>{const L=[];(D.sales||[]).filter(s=>!s.refunded).forEach(s=>(s.items||[]).forEach(i=>L.push({pid:i.pid||i.id,qty:i.qty||0,price:i.price||0,at:s.at,phone:s.phone||'',name:'',cust:''})));
 (D.orders||[]).filter(o=>o.status==='Delivered').forEach(o=>(o.items||[]).forEach(i=>L.push({pid:i.pid||i.id,qty:i.qty||0,price:i.price||0,at:o.at,phone:o.phone||'',name:o.customer||'',cust:o.customer||''})));return L};
const txns=()=>{const L=[];(D.sales||[]).filter(s=>!s.refunded).forEach(s=>L.push({at:s.at,total:s.total||0,phone:s.phone||'',name:''}));
 (D.orders||[]).filter(o=>o.status==='Delivered').forEach(o=>L.push({at:o.at,total:o.total||0,phone:o.phone||'',name:o.customer||''}));return L};
const dparts=at=>{const f=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Dhaka',hour:'2-digit',hour12:false,weekday:'short'}).formatToParts(new Date(at));
 return{h:(+f.find(x=>x.type==='hour').value)%24,w:f.find(x=>x.type==='weekday').value}};
const barsOf=(rows,fmt)=>{const mx=Math.max(1,...rows.map(r=>r[1]));return h('div',{class:'hbars',role:'list'},rows.map(([k,v])=>h('div',{class:'br',role:'listitem'},h('span',{},k),h('i',{style:'width:'+Math.round(v/mx*100)+'%'}),h('span',{},fmt(v)))))};
const kpi=(a,b)=>h('div',{class:'card'},h('span',{class:'muted'},a),h('b',{},b));
let IP=30;
const costOf=pid=>{const p=D.products.find(x=>x.id===pid);return p&&typeof p.cost==='number'?p.cost:null};

const insights=()=>{const now=Date.now(),from=now-IP*dayMs,T0=txns().filter(t=>new Date(t.at)>=from),I0=itemsOf();
 const rev=T0.reduce((a,t)=>a+t.total,0),hrs=Array.from({length:24},(_,i)=>[String(i).padStart(2,'0')+':00',0]),wk={Sat:0,Sun:0,Mon:0,Tue:0,Wed:0,Thu:0,Fri:0};
 T0.forEach(t=>{const p=dparts(t.at);hrs[p.h][1]+=t.total;if(p.w in wk)wk[p.w]+=t.total});
 const peak=hrs.reduce((a,b)=>b[1]>a[1]?b:a,hrs[0]);
 const sel=h('select',{'aria-label':'Period',onchange(e){IP=+e.target.value;go()}},[[7,'Last 7 days'],[30,'Last 30 days'],[90,'Last 90 days']].map(([v,l])=>h('option',{value:v,selected:v===IP},l)));
 // stock cover (velocity over the chosen period)
 const sold={};I0.filter(i=>new Date(i.at)>=from).forEach(i=>{sold[i.pid]=(sold[i.pid]||0)+i.qty});
 const cover=D.products.map(p=>{const s=stock(D,p.id),v=(sold[p.id]||0)/IP;return{p,s,v,days:v>0?s/v:Infinity,need:Math.max(0,Math.ceil(v*30-s))}}).filter(x=>x.v>0&&x.days<21).sort((a,b)=>a.days-b.days);
 // dead stock: stock on hand and no sale in 60 days
 const last={};I0.forEach(i=>{const t=new Date(i.at).getTime();if(!last[i.pid]||t>last[i.pid])last[i.pid]=t});
 const dead=D.products.filter(p=>stock(D,p.id)>0&&!(last[p.id]>now-60*dayMs));
 const deadVal=dead.reduce((a,p)=>a+D.batches.filter(b=>b.pid===p.id&&b.qty>0).reduce((s,b)=>s+b.qty*(b.cost??costOf(p.id)??0),0),0);
 // ABC by revenue
 const revBy={};I0.filter(i=>new Date(i.at)>=from).forEach(i=>{revBy[i.pid]=(revBy[i.pid]||0)+i.qty*i.price});
 const ranked=Object.entries(revBy).sort((a,b)=>b[1]-a[1]),tot=ranked.reduce((a,x)=>a+x[1],0);let cum=0;
 const abc=ranked.map(([pid,v])=>{const before=cum/tot;cum+=v;return{pid,v,c:before<0.8?'A':before<0.95?'B':'C'}});
 // customers
 const cm={};T0.filter(t=>t.phone).forEach(t=>{const c=cm[t.phone]||(cm[t.phone]={ph:t.phone,n:t.name,t:0,c:0,l:0});c.t+=t.total;c.c++;c.n=c.n||t.name;c.l=Math.max(c.l,new Date(t.at).getTime())});
 const top=Object.values(cm).sort((a,b)=>b.t-a.t).slice(0,10);
 // expiry risk
 const lim=new Date(now+(+D.settings.expiryDays||60)*dayMs).toISOString().slice(0,10);
 const valB=L=>L.reduce((a,b)=>a+b.qty*(b.cost??costOf(b.pid)??0),0);
 const nearV=valB(D.batches.filter(b=>b.qty>0&&b.exp>=today()&&b.exp<=lim)),expV=valB(D.batches.filter(b=>b.qty>0&&b.exp<today()));
 return h('div',{},h('div',{class:'row'},h('label',{},'Period ',sel),act('Export stock cover CSV',()=>csv('stock-cover.csv',[['Product','In stock','Sold per day','Days of cover','Suggested order for 30 days'],...cover.map(x=>[x.p.name,x.s,x.v.toFixed(2),x.days.toFixed(1),x.need])]))),
  h('div',{class:'kpis'},kpi('Revenue ('+IP+' days)',money(rev)),kpi('Transactions',T0.length),kpi('Average basket',money(T0.length?rev/T0.length:0)),kpi('Busiest hour',rev?peak[0]:'—'),kpi('Dead stock value (at cost)',money(deadVal)),kpi('Near-expiry stock (at cost)',money(nearV)),kpi('Expired stock (at cost)',money(expV))),
  h('h2',{},'Sales by hour (Dhaka time)'),barsOf(hrs,money),
  h('h2',{},'Sales by weekday'),barsOf(Object.entries(wk),money),
  h('h2',{},'Running out soon (under 21 days of cover)'),h('p',{class:'muted'},'Based on average daily sales over the chosen period. A guide only: seasons, offers and supplier delays change real needs.'),
  tbl(['Product','In stock','Sold/day','Days of cover','Suggested order (30 days)'],cover.map(x=>h('tr',{},h('td',{},x.p.name),h('td',{},x.s),h('td',{},x.v.toFixed(2)),h('td',{},x.days.toFixed(1)),h('td',{},x.need)))),
  h('h2',{},'Dead stock (in stock, no sale in 60 days)'),
  tbl(['Product','In stock','Last sold'],dead.map(p=>h('tr',{},h('td',{},p.name),h('td',{},stock(D,p.id)),h('td',{},last[p.id]?new Date(last[p.id]).toLocaleDateString('en-CA',{timeZone:'Asia/Dhaka'}):'never')))),
  h('h2',{},'ABC analysis by revenue'),h('p',{class:'muted'},'A = products making the first 80% of revenue, B = the next 15%, C = the rest. Keep A items well stocked; review C items.'),
  tbl(['Class','Product','Revenue','Share'],abc.map(x=>h('tr',{},h('td',{},x.c),h('td',{},nm(x.pid)),h('td',{},money(x.v)),h('td',{},(x.v/tot*100).toFixed(1)+'%')))),
  h('h2',{},'Top customers'),
  tbl(['Customer','Phone','Orders','Spent','Last purchase'],top.map(c=>h('tr',{},h('td',{},c.n||'Walk-in'),h('td',{},c.ph),h('td',{},c.c),h('td',{},money(c.t)),h('td',{},new Date(c.l).toLocaleDateString('en-CA',{timeZone:'Asia/Dhaka'}))))))};

// ---- refill follow-ups: customers who bought a product N days ago and have not bought it since ----
let RF={min:25,max:45};
const doneKey='mc_refill_done';
const doneSet=()=>{try{return JSON.parse(localStorage.getItem(doneKey)||'{}')}catch(e){return{}}};
const refill=()=>{const now=Date.now(),L={};
 itemsOf().filter(i=>i.phone).forEach(i=>{const k=i.phone+'|'+i.pid,t=new Date(i.at).getTime(),x=L[k]||(L[k]={ph:i.phone,pid:i.pid,name:i.name,last:0,qty:0});if(t>x.last){x.last=t;x.qty=i.qty}if(!x.name)x.name=i.name});
 const dn=doneSet(),rows=Object.values(L).map(x=>({...x,age:(now-x.last)/dayMs})).filter(x=>x.age>=RF.min&&x.age<=RF.max).sort((a,b)=>b.age-a.age);
 const num=(k,l)=>h('label',{},l,h('input',{type:'number',min:1,max:365,value:RF[k],onchange(e){RF[k]=Math.max(1,+e.target.value||RF[k]);if(RF.max<RF.min)RF.max=RF.min;go()}}));
 return h('div',{},h('p',{class:'muted'},'Customers who bought a product and have not bought it again since. Useful for regular medicines. Call them; nothing is sent automatically. "Done" marks are saved in this browser only.'),
  h('div',{class:'row'},num('min','From (days ago) '),num('max','To (days ago) ')),
  tbl(['Customer','Phone','Product','Bought','Days ago',''],rows.map(x=>{const k=x.ph+'|'+x.pid+'|'+x.last,d=!!dn[k];
   return h('tr',{},h('td',{},x.name||'—'),h('td',{},h('a',{href:'tel:'+x.ph.replace(/[^\d+]/g,'')},x.ph)),h('td',{},nm(x.pid)),h('td',{},x.qty),h('td',{},Math.round(x.age)),
    h('td',{},act(d?'Undo':'Mark contacted',()=>{const m=doneSet();if(d)delete m[k];else m[k]=Date.now();localStorage.setItem(doneKey,JSON.stringify(m));go()})))})))};

// ---- shelf labels ----
let LB={q:'',pick:{},copies:1,exp:false};
const labels=()=>{const q=LB.q.toLowerCase(),L=D.products.filter(p=>!q||(p.name+' '+p.generic+' '+p.sku+' '+(p.barcode||'')).toLowerCase().includes(q));
 const chosen=()=>D.products.filter(p=>LB.pick[p.id]);
 const preview=()=>{const P=chosen();if(!P.length)return toast('Tick at least one product',1);
  const sheet=h('div',{class:'lbl-sheet'});
  P.forEach(p=>{const b=D.batches.filter(x=>x.pid===p.id&&x.qty>0&&x.exp>=today()).sort((a,c)=>a.exp.localeCompare(c.exp))[0],code=p.barcode||p.sku||p.id;
   for(let i=0;i<LB.copies;i++)sheet.append(h('div',{class:'lbl'},h('div',{class:'n'},p.name),h('div',{class:'s'},[p.generic,p.strength&&p.strength!=='—'?p.strength:'',p.pack].filter(Boolean).join(' · ')),barSvg(code),h('div',{class:'s'},code),h('div',{class:'p'},money(eff(p))),LB.exp&&b?h('div',{class:'s'},'Exp '+b.exp):null))});
  const w=h('dialog',{},h('h2',{},T('Shelf labels')),sheet,h('button',{onclick:()=>print()},T('Print')),h('button',{onclick(){w.close();w.remove()}},T('Close')));document.body.append(w);w.showModal()};
 return h('div',{},h('p',{class:'muted'},'Print shelf or bin labels with name, price and a Code 128 barcode (uses the product barcode, or the SKU if there is none). Check one printed label with your scanner before printing a full sheet.'),
  h('div',{class:'row'},h('label',{},'Find ',h('input',{type:'search',value:LB.q,oninput(e){LB.q=e.target.value;const p=e.target.selectionStart;go();const i=$('#app input[type=search]');if(i){i.focus();i.setSelectionRange(p,p)}}})),
   h('label',{},'Copies ',h('input',{type:'number',min:1,max:20,value:LB.copies,onchange(e){LB.copies=Math.min(20,Math.max(1,+e.target.value||1))}})),
   h('label',{},h('input',{type:'checkbox',checked:LB.exp,onchange(e){LB.exp=e.target.checked}}),' Show next expiry'),
   act('Select all shown',()=>{L.forEach(p=>LB.pick[p.id]=true);go()}),act('Clear',()=>{LB.pick={};go()}),h('button',{class:'btn',onclick:preview},'Preview and print')),
  tbl(['','Product','Price','Barcode'],L.map(p=>h('tr',{},h('td',{},h('input',{type:'checkbox','aria-label':'Select '+p.name,checked:!!LB.pick[p.id],onchange(e){LB.pick[p.id]=e.target.checked}})),h('td',{},p.name),h('td',{},money(eff(p))),h('td',{},p.barcode||p.sku||'—')))))};

// ---- expiry planner: stock grouped by expiry month ----
let EP=6;
const expiry=()=>{const now=today(),lim=new Date(Date.now()+EP*30.5*dayMs).toISOString().slice(0,10),sup=id=>(D.suppliers||[]).find(x=>x.id===id)?.name||'—';
 const val=b=>{const c=b.cost??costOf(b.pid);return c==null?null:b.qty*c},fm=v=>v==null?'—':money(v);
 const all=D.batches.filter(b=>b.qty>0),expd=all.filter(b=>b.exp<now),soon=all.filter(b=>b.exp>=now&&b.exp<=lim).sort((a,c)=>a.exp.localeCompare(c.exp));
 const sum=L=>L.reduce((a,b)=>a+(val(b)||0),0),mon={};soon.forEach(b=>{const k=b.exp.slice(0,7);(mon[k]=mon[k]||[]).push(b)});
 const days=e=>Math.round((new Date(e)-new Date(now))/dayMs);
 const sel=h('select',{'aria-label':'Window',onchange(e){EP=+e.target.value;go()}},[[1,'Next month'],[3,'Next 3 months'],[6,'Next 6 months'],[12,'Next 12 months']].map(([v,l])=>h('option',{value:v,selected:v===EP},l)));
 const row=b=>h('tr',{},h('td',{},nm(b.pid)),h('td',{},b.no),h('td',{},b.exp),h('td',{},days(b.exp)),h('td',{},b.qty),h('td',{},sup(b.supplier)),h('td',{},fm(val(b))));
 return h('div',{},h('p',{class:'muted'},'Plan ahead: sell near-expiry batches first (the system already uses the earliest expiry first), discount them, or ask the supplier about returns. Values are at cost and show a dash when costs are hidden for your role.'),
  h('div',{class:'row'},h('label',{},'Window ',sel),act('Export CSV',()=>csv('expiry-plan.csv',[['Product','Batch','Expiry','Days left','Qty','Supplier','Value at cost'],...[...expd,...soon].map(b=>[nm(b.pid),b.no,b.exp,days(b.exp),b.qty,sup(b.supplier),val(b)==null?'':val(b)])]))),
  h('div',{class:'kpis'},kpi('Already expired (batches)',expd.length),kpi('Expired value (cost)',fm(expd.length?sum(expd):0)),kpi('Expiring in window (batches)',soon.length),kpi('Expiring value (cost)',fm(soon.length?sum(soon):0))),
  h('h2',{},'By month'),tbl(['Month','Batches','Units','Value at cost'],Object.entries(mon).map(([k,L])=>h('tr',{},h('td',{},k),h('td',{},L.length),h('td',{},L.reduce((a,b)=>a+b.qty,0)),h('td',{},fm(sum(L)))))),
  expd.length?h('div',{},h('h2',{},'Already expired (remove from shelf)'),tbl(['Product','Batch','Expiry','Days left','Qty','Supplier','Value at cost'],expd.map(row))):null,
  h('h2',{},'Batches expiring in the window'),tbl(['Product','Batch','Expiry','Days left','Qty','Supplier','Value at cost'],soon.map(row)))};

// ---- margin analysis ----
let MG=10;
const margins=()=>{const L=D.products.filter(p=>typeof p.cost==='number'),rows=L.map(p=>{const pr=eff(p),m=pr-p.cost;return{p,pr,m,pct:pr?m/pr*100:0,st:stock(D,p.id)}}).sort((a,b)=>a.pct-b.pct);
 if(!L.length)return h('p',{class:'empty'},'Cost prices are not available to your role.');
 const low=rows.filter(r=>r.pct<MG),neg=rows.filter(r=>r.m<0),avg=rows.reduce((a,r)=>a+r.pct,0)/rows.length,pot=rows.reduce((a,r)=>a+r.st*r.m,0),stv=rows.reduce((a,r)=>a+r.st*r.p.cost,0);
 return h('div',{},h('p',{class:'muted'},'Margin = selling price after discount minus cost price, as a share of the selling price. Cost is the product cost price, not each batch cost.'),
  h('div',{class:'row'},h('label',{},'Flag margins below (%) ',h('input',{type:'number',min:0,max:100,value:MG,onchange(e){MG=Math.max(0,+e.target.value||0);go()}})),act('Export CSV',()=>csv('margins.csv',[['Product','Price','Cost','Margin','Margin %','In stock'],...rows.map(r=>[r.p.name,r.pr,r.p.cost,r.m,r.pct.toFixed(1),r.st])]))),
  h('div',{class:'kpis'},kpi('Average margin',avg.toFixed(1)+'%'),kpi('Below '+MG+'%',low.length),kpi('Selling below cost',neg.length),kpi('Stock value (cost)',money(stv)),kpi('Profit if all stock sells',money(pot))),
  tbl(['Product','Price','Cost','Margin','Margin %','In stock'],rows.map(r=>h('tr',{class:r.m<0?'bad':''},h('td',{},r.p.name),h('td',{},money(r.pr)),h('td',{},money(r.p.cost)),h('td',{},money(r.m)),h('td',{},r.pct.toFixed(1)+'%'+(r.m<0?' ⚠':r.pct<MG?' ▼':'')),h('td',{},r.st)))))};

// ---- supplier order messages for low-stock items ----
const reorder=()=>{const by={};D.products.filter(p=>stock(D,p.id)<p.reorder).forEach(p=>{const b=D.batches.filter(x=>x.pid===p.id).slice(-1)[0],sid=b?.supplier||'';const need=Math.max(p.reorder,p.reorder*2-stock(D,p.id));(by[sid]=by[sid]||[]).push([p,need])});
 const ids=Object.keys(by);if(!ids.length)return h('p',{class:'empty'},'Nothing is below its reorder level.');
 return h('div',{},h('p',{class:'muted'},'Ready-to-send order messages for low-stock items, grouped by the supplier of the latest batch. Quantities aim for twice the reorder level; edit the text before sending. This tool only prepares the text: it does not send anything or create a purchase order (use Alerts for that).'),
  ids.map(sid=>{const sp=(D.suppliers||[]).find(x=>x.id===sid),name=sp?.name||'Supplier not known',lines=by[sid].map(([p,q])=>'- '+p.name+(p.strength&&p.strength!=='—'?' '+p.strength:'')+' ('+p.pack+') x '+q);
   const ta=h('textarea',{rows:Math.min(14,lines.length+4),'aria-label':'Message to '+name},'Hello '+name+',\nPlease supply the following for '+D.settings.store+':\n'+lines.join('\n')+'\nThank you.');
   const dg=String(sp?.phone||'').replace(/\D/g,''),wa=dg?'https://wa.me/'+(dg.startsWith('88')?dg:dg.startsWith('0')?'88'+dg:dg):'';
   return h('article',{class:'card'},h('h3',{},name+' ('+by[sid].length+' items)'),ta,h('div',{class:'row'},
    h('button',{class:'btn',type:'button',onclick:async()=>{try{await navigator.clipboard.writeText(ta.value);toast('Message copied')}catch(e){ta.select();toast('Press Ctrl+C to copy',1)}}},'Copy message'),
    wa?h('a',{class:'btn2',href:wa+'?text='+encodeURIComponent(ta.value),target:'_blank',rel:'noopener noreferrer',onclick(e){e.currentTarget.href=wa+'?text='+encodeURIComponent(ta.value)}},'Open WhatsApp'):h('span',{class:'muted'},'No phone saved for this supplier')))}))};

// ---- printable price list ----
let PL={oos:false,rx:true};
const pricelist=()=>{const L=D.products.filter(p=>(PL.oos||stock(D,p.id)>0)&&(PL.rx||!p.rx)).sort((a,b)=>a.cat.localeCompare(b.cat)||a.name.localeCompare(b.name));
 const cats=[...new Set(L.map(p=>p.cat))];
 const tables=()=>cats.map(c=>h('div',{},h('h3',{},c),h('table',{},h('thead',{},h('tr',{},['Product','Strength','Pack','Price'].map(x=>h('th',{},x)))),h('tbody',{},L.filter(p=>p.cat===c).map(p=>h('tr',{},h('td',{},p.name+(p.rx?' (Rx)':'')),h('td',{},p.strength&&p.strength!=='—'?p.strength:''),h('td',{},p.pack),h('td',{},money(eff(p)))))))));
 const dlg=()=>{const w=h('dialog',{},h('h2',{},D.settings.store+' – '+T('Price list')),h('p',{class:'muted'},'Prices on '+dhaka(new Date())+'. Prices can change.'),...tables(),h('button',{onclick:()=>print()},T('Print')),h('button',{onclick(){w.close();w.remove()}},T('Close')));document.body.append(w);w.showModal()};
 return h('div',{},h('div',{class:'row'},h('label',{},h('input',{type:'checkbox',checked:PL.oos,onchange(e){PL.oos=e.target.checked;go()}}),' Include out-of-stock items'),h('label',{},h('input',{type:'checkbox',checked:PL.rx,onchange(e){PL.rx=e.target.checked;go()}}),' Include prescription items'),
  h('button',{class:'btn',onclick:dlg},'Preview and print'),act('Export CSV',()=>csv('price-list.csv',[['Category','Product','Strength','Pack','Price'],...L.map(p=>[p.cat,p.name,p.strength||'',p.pack,eff(p)])]))),
  h('p',{class:'muted'},L.length+' products in '+cats.length+' categories.'),...tables())};

// ---- dashboard add-on: today at a glance, copy summary, daily sales target (this browser) ----
const dashAdd=r=>{try{const k=x=>new Date(x).toLocaleDateString('en-CA',{timeZone:'Asia/Dhaka'}),td=k(Date.now());
 const sl=(D.sales||[]).filter(s=>!s.refunded&&k(s.at)===td),od=(D.orders||[]).filter(o=>k(o.at)===td),dv=od.filter(o=>o.status==='Delivered');
 const total=sl.reduce((a,s)=>a+s.total,0)+dv.reduce((a,o)=>a+o.total,0),pend=(D.orders||[]).filter(o=>['Pending','Prescription Review'].includes(o.status)).length,low=D.products.filter(p=>stock(D,p.id)<p.reorder).length;
 const tg=+localStorage.getItem('mc_target')||0,pct=tg?Math.min(100,Math.round(total/tg*100)):0;
 const text=D.settings.store+' – '+td+'\nCounter sales: '+sl.length+' ('+money(sl.reduce((a,s)=>a+s.total,0))+')\nOnline orders today: '+od.length+', delivered: '+dv.length+' ('+money(dv.reduce((a,o)=>a+o.total,0))+')\nTotal: '+money(total)+'\nWaiting orders: '+pend+'\nLow-stock products: '+low;
 const tin=h('input',{type:'number',min:0,step:100,value:tg||'','aria-label':'Daily sales target',onchange(e){localStorage.setItem('mc_target',String(Math.max(0,+e.target.value||0)));go()}});
 r.append(h('article',{class:'card'},h('h2',{},'Today at a glance'),h('div',{class:'kpis'},kpi('Total today',money(total)),kpi('Waiting orders',pend),kpi('Low-stock products',low)),
  h('div',{class:'row'},h('label',{},'Daily target (৳, this browser) ',tin),tg?h('span',{},pct+'% of target'):null),tg?h('progress',{max:100,value:pct,'aria-label':'Progress to daily target'}):null,
  h('div',{class:'row'},h('button',{class:'btn2',type:'button',onclick:async()=>{try{await navigator.clipboard.writeText(text);toast('Summary copied')}catch(e){toast('Could not copy',1)}}},'Copy day summary'))))}catch(e){console.error(e)}return r};

// ---- sign-in notices (server mode): new address, old password ----
const dh=at=>at?new Date(at).toLocaleString('en-GB',{timeZone:'Asia/Dhaka',dateStyle:'medium',timeStyle:'short'}):'never';
const bootNotices=()=>{let raw=null;try{raw=sessionStorage.getItem('mc_loginfo');sessionStorage.removeItem('mc_loginfo')}catch(e){}
 if(!raw)return;let i;try{i=JSON.parse(raw)}catch(e){return}if(!i||typeof i!=='object')return;
 const msgs=[];
 if(i.new_address)msgs.push(['New sign-in address. ','Your previous sign-in was on '+dh(i.prev_login)+' from '+(i.prev_ip||'an unknown address')+'. This sign-in came from a different address. If it was not you, change your password and sign out other devices.']);
 if(+i.pw_age_days>=90)msgs.push(['Time to refresh your password. ','It was last set '+(+i.pw_age_days)+' days ago. Changing it every few months is a good habit.']);
 if(!msgs.length)return;
 let n=0;const t=setInterval(()=>{const top=document.querySelector('.top');if(++n>50)clearInterval(t);if(!top)return;clearInterval(t);
  const box=h('div',{class:'signin-notices'},msgs.map(([b,m])=>{const c=h('div',{class:'card warn',role:'status'},h('b',{},b),m+' ',h('button',{type:'button',class:'btn2',onclick(){document.querySelector('#side nav button[data-t=account]')?.click()}},'Open My account'),h('button',{type:'button',class:'btn2',onclick(){c.remove()}},'Dismiss'));return c}));
  top.after(box)},100)};
if(typeof SERVER!=='undefined'&&SERVER)bootNotices();

// ---- My account add-on: strong password suggestion (generated in this browser, never sent anywhere) ----
const GEN={low:'abcdefghijkmnpqrstuvwxyz',up:'ABCDEFGHJKLMNPQRSTUVWXYZ',dig:'23456789',sym:'!@#$%^&*-_=+?'};
const rnd=n=>{const a=new Uint32Array(1),lim=Math.floor(4294967296/n)*n;let x;do{crypto.getRandomValues(a);x=a[0]}while(x>=lim);return x%n};
const gen=(len=16)=>{const all=Object.values(GEN).join(''),out=Object.values(GEN).map(g=>g[rnd(g.length)]);while(out.length<len)out.push(all[rnd(all.length)]);for(let i=out.length-1;i>0;i--){const j=rnd(i+1);[out[i],out[j]]=[out[j],out[i]]}return out.join('')};
const accountAdd=r=>{try{if(typeof ME!=='undefined'&&ME&&ME.must_2fa)r.prepend(h('div',{class:'card warn',role:'alert'},h('b',{},'Two-step login is required. '),'Your shop requires two-step login for your role. Turn it on below (you need an authenticator app); other screens stay locked until you do.'));const code=h('code',{'aria-live':'polite'},'—'),mk=()=>{code.textContent=gen(16)};
 r.append(h('article',{class:'card'},h('h2',{},'Need a strong password?'),h('p',{class:'muted'},'Suggestions are made in this browser and are not saved or sent anywhere. Copy one into your password manager first, then use it in Change password. Do not reuse it on other sites.'),
  h('p',{},code),h('div',{class:'row'},h('button',{class:'btn2',type:'button',onclick:mk},'Suggest a password'),h('button',{class:'btn2',type:'button',onclick:async()=>{if(code.textContent==='—')return toast('Press Suggest first',1);try{await navigator.clipboard.writeText(code.textContent);toast('Copied')}catch(e){toast('Could not copy',1)}}},'Copy'))))}catch(e){console.error(e)}return r};

// ---- Users add-on (Owner, server mode): staff security overview ----
const usersAdd=r=>{try{if(!(typeof SERVER!=='undefined'&&SERVER)||R!=='Owner')return r;const x=apiSync('GET','/api/staff');if(!x.ok||!Array.isArray(x.staff))return r;
 const S=x.staff,act_=S.filter(s=>s.active),two=act_.filter(s=>s.totp_enabled).length,old=act_.filter(s=>s.pw_age_days>=90).length,never=act_.filter(s=>!s.last_login).length,locked=S.filter(s=>s.locked).length;
 r.append(h('article',{class:'card'},h('h2',{},'Staff security overview'),
  h('div',{class:'kpis'},kpi('Active staff',act_.length),kpi('Using two-step login',two+' of '+act_.length),kpi('Passwords 90+ days old',old),kpi('Never signed in',never),kpi('Locked now',locked)),
  two<act_.length?h('p',{class:'muted'},'Ask staff without two-step login to turn it on in My account, starting with the Owner and Pharmacists.'):null,
  tbl(['Name','Username','Role','Two-step','Password age','Last sign-in','Last address','Signed in now','Status'],S.map(s=>h('tr',{},h('td',{},s.name),h('td',{},s.username),h('td',{},s.role),h('td',{},s.totp_enabled?'✓ On':'Off'),h('td',{},s.pw_age_days+' days'+(s.pw_age_days>=90?' ⚠':'')),h('td',{},dh(s.last_login)),h('td',{},s.last_ip||'—'),h('td',{},s.sessions||0),h('td',{},!s.active?'Inactive':s.locked?'Locked':s.must_change?'Must change password':'OK'))))))}catch(e){console.error(e)}return r};

// ---- customer lookup: one customer's whole history (orders + counter sales), found by phone or name ----
let CL={q:'',sel:''};
const custAll=()=>{const m={};const add=(ph,n,rec)=>{if(!ph)return;const c=m[ph]||(m[ph]={ph,n:'',rec:[]});if(n&&!c.n)c.n=n;c.rec.push(rec)};
 (D.orders||[]).forEach(o=>add(o.phone,o.customer,{at:o.at,kind:'Online order',ref:o.id,total:o.status==='Refunded'||o.status==='Cancelled'?0:o.total,status:o.status,items:o.items||[]}));
 (D.sales||[]).forEach(x=>add(x.phone,x.customer||'',{at:x.at,kind:'Counter sale',ref:x.no||x.id,total:x.refunded?0:x.total,status:x.refunded?'Refunded':'Paid',items:x.items||[]}));
 return Object.values(m)};
const customer=()=>{const all=custAll(),q=CL.q.trim().toLowerCase(),hit=q?all.filter(c=>c.ph.toLowerCase().includes(q)||(c.n||'').toLowerCase().includes(q)).slice(0,20):[];
 const sel=all.find(c=>c.ph===CL.sel);
 const box=h('div',{},h('p',{class:'muted'},'Look up a customer by phone number or name. This shows personal information: use it only to serve the customer, and do not share it.'),
  h('div',{class:'row'},h('label',{},'Phone or name ',h('input',{type:'search',value:CL.q,oninput(e){CL.q=e.target.value;CL.sel='';const p=e.target.selectionStart;go();const i=document.querySelector('#app input[type=search]');if(i){i.focus();i.setSelectionRange(p,p)}}}))));
 if(!sel){if(q)box.append(hit.length?tbl(['Customer','Phone','Records',''],hit.map(c=>h('tr',{},h('td',{},c.n||'—'),h('td',{},c.ph),h('td',{},c.rec.length),h('td',{},act('Open',()=>{CL.sel=c.ph;go()}))))):h('p',{class:'empty'},'No customer found.'));return box}
 const rec=sel.rec.slice().sort((a,b)=>String(b.at).localeCompare(String(a.at))),spent=rec.reduce((a,r)=>a+r.total,0),n=rec.filter(r=>r.total>0).length;
 const fav={};rec.filter(r=>r.total>0).forEach(r=>r.items.forEach(i=>{const k=i.pid||i.id;fav[k]=(fav[k]||0)+(i.qty||0)}));
 const favL=Object.entries(fav).sort((a,b)=>b[1]-a[1]).slice(0,5);
 box.append(h('div',{class:'row'},act('← All results',()=>{CL.sel='';go()}),h('a',{class:'btn2',href:'tel:'+sel.ph.replace(/[^\d+]/g,'')},'Call '+sel.ph)),
  h('h2',{},sel.n||'Customer'),
  h('div',{class:'kpis'},kpi('Completed purchases',n),kpi('Total spent',money(spent)),kpi('Average basket',money(n?spent/n:0)),kpi('Last purchase',dh(rec[0]?.at)),kpi('Loyalty points (1 per ৳100)',Math.floor(spent/100))),
  h('h3',{},'Most bought'),favL.length?tbl(['Product','Units'],favL.map(([pid,q])=>h('tr',{},h('td',{},nm(pid)),h('td',{},q)))):h('p',{class:'empty'},'Nothing yet.'),
  h('h3',{},'History'),tbl(['Date','Type','Reference','Items','Total','Status'],rec.slice(0,50).map(r=>h('tr',{},h('td',{},dh(r.at)),h('td',{},r.kind),h('td',{},r.ref),h('td',{},r.items.map(i=>nm(i.pid||i.id)+' × '+(i.qty||0)).join(', ')),h('td',{},money(r.total)),h('td',{},r.status)))));
 return box};


// ---- Settings add-on (Owner, server mode): sign-in policy. All options are off until the Owner turns them on. ----
const policyAdd=r=>{try{if(!(typeof SERVER!=='undefined'&&SERVER)||R!=='Owner')return r;const st=D.settings,v=(k,d)=>st[k]===undefined?d:st[k];
 const sel=h('select',{name:'req2fa','aria-label':'Who must use two-step login'},[['','Nobody (optional for everyone)'],['owner','Owner only'],['owner_pharmacist','Owner and Pharmacists'],['all','Everyone']].map(([k,l])=>h('option',{value:k,selected:v('req2fa','')===k},l)));
 const on=h('input',{type:'checkbox',name:'hoursOn',checked:!!v('hoursOn',false)}),
  a=h('input',{type:'number',name:'hoursFrom',min:0,max:23,value:v('hoursFrom',8),'aria-label':'Sign-in allowed from hour'}),b=h('input',{type:'number',name:'hoursTo',min:1,max:24,value:v('hoursTo',22),'aria-label':'Sign-in allowed until hour'}),
  ms=h('input',{type:'number',name:'maxSessions',min:0,max:10,value:v('maxSessions',0),'aria-label':'Devices per person'}),pm=h('input',{type:'number',name:'pwMaxDays',min:0,max:365,value:v('pwMaxDays',0),'aria-label':'Password maximum age in days'});
 r.append(h('article',{class:'card'},h('h2',{},'Sign-in policy'),
  h('p',{class:'muted'},'Optional rules for staff sign-in. Everything is off until you turn it on. Test with a second account first. The Owner is never blocked by the hours rule, and the server console can always reset a password or two-step login.'),
  h('div',{class:'hgrid'},
   h('label',{},'Require two-step login for ',sel),
   h('label',{},on,' Allow staff sign-in only between (Dhaka time, Owner exempt)'),h('div',{class:'row'},h('label',{},'From hour ',a),h('label',{},'Until hour ',b)),
   h('label',{},'Devices signed in at once per person (0 = no limit) ',ms),
   h('label',{},'Ask for a new password after this many days (0 = never, otherwise 30 to 365) ',pm)),
  h('button',{class:'btn',type:'button',onclick(){const n=x=>Math.max(0,Math.round(+x.value||0));
   if(on.checked&&+a.value===+b.value)return toast('Start and end hours must differ',1);
   if(n(pm)&&n(pm)<30)return toast('Password maximum age must be 0 or at least 30 days',1);
   Object.assign(D.settings,{req2fa:sel.value,hoursOn:on.checked,hoursFrom:Math.min(23,n(a)),hoursTo:Math.min(24,Math.max(1,n(b))),maxSessions:Math.min(10,n(ms)),pwMaxDays:Math.min(365,n(pm))});save(D);toast('Sign-in policy saved')}},'Save sign-in policy')))}catch(e){console.error(e)}return r};

// ---- admin top bar: current screen, Dhaka clock, connection dot, signed-in name ----
{let n=0;const t=setInterval(()=>{const top=document.querySelector('.top');if(++n>60)clearInterval(t);if(!top||top.querySelector('.crumb'))return;clearInterval(t);
 const title=top.querySelector('b'),tl=top.querySelector('.tools'),crumb=h('span',{class:'crumb','aria-live':'polite'}),clock=h('span',{class:'clock',title:'Dhaka time'}),dot=h('span',{class:'conn',role:'status'});
 if(title)title.after(crumb);
 const upd=()=>{const hh=document.querySelector('#app h1');crumb.textContent=hh?'› '+hh.textContent:''};
 const app=document.getElementById('app');if(app)new MutationObserver(upd).observe(app,{childList:true});upd();
 const tick=()=>{clock.textContent=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Dhaka',hour:'2-digit',minute:'2-digit',hour12:true}).format(new Date())};tick();setInterval(tick,30000);
 const cn=()=>{const on=navigator.onLine;dot.textContent=on?'● Online':'○ Offline';dot.classList.toggle('off',!on)};cn();addEventListener('online',cn);addEventListener('offline',cn);
 const who=(typeof SERVER!=='undefined'&&SERVER&&typeof ME!=='undefined'&&ME&&ME.name)?h('span',{class:'chip'},'👤 '+ME.name):null;
 if(tl)tl.prepend(...[who,clock,dot].filter(Boolean))},100)}

// ---- v3.1 admin upgrades: grouped sidebar, "needs attention" strip, new-order alerts, shortcuts, compact tables ----
if(typeof I18!=='undefined')Object.assign(I18.bn,{'Overview':'ওভারভিউ','Orders and sales':'অর্ডার ও বিক্রি','Products and stock':'পণ্য ও স্টক','Money and reports':'হিসাব ও রিপোর্ট','People and system':'মানুষ ও সিস্টেম','Needs attention':'যেগুলো দেখা দরকার','All clear':'সব ঠিক আছে','Keyboard shortcuts':'কিবোর্ড শর্টকাট','Compact tables':'ঘন টেবিল','New order alerts':'নতুন অর্ডারের সতর্কতা'});
const GROUPS=[['Overview',['dash','alerts']],['Orders and sales',['rx','orders','pos','returns','delivery','customer360','refill','customers']],['Products and stock',['products','labels','pricelist','cats','inv','stk','expiry','ledger','purchases','reorder','suppliers']],['Money and reports',['expenses','reports','insights','margins']],['People and system',['notes','users','seclog','account','settings','data']]];
const groupNav=()=>{const nav=document.querySelector('#side nav');if(!nav||nav.dataset.grouped)return false;const btns=[...nav.querySelectorAll(':scope>button[data-t]')];if(btns.length<6)return false;
 const by=Object.fromEntries(btns.map(b=>[b.dataset.t,b])),used=new Set(),saved=(()=>{try{return JSON.parse(localStorage.getItem('mc_navc')||'{}')}catch(e){return{}}})();
 const frag=document.createDocumentFragment();
 const mk=(title,tabs)=>{const list=tabs.filter(t=>by[t]);if(!list.length)return;list.forEach(t=>used.add(t));
  const d=h('details',{class:'navgrp'},h('summary',{},T(title)),...list.map(t=>by[t]));d.open=saved[title]!==false;d.addEventListener('toggle',()=>{const m=(()=>{try{return JSON.parse(localStorage.getItem('mc_navc')||'{}')}catch(e){return{}}})();m[title]=d.open;try{localStorage.setItem('mc_navc',JSON.stringify(m))}catch(e){}});frag.append(d)};
 GROUPS.forEach(([t,l])=>mk(t,l));const rest=btns.filter(b=>!used.has(b.dataset.t));if(rest.length)mk('More',rest.map(b=>b.dataset.t));
 nav.dataset.grouped='1';nav.append(frag);
 // keep the group of the current screen open
 new MutationObserver(()=>{const on=nav.querySelector('button.on');const g=on&&on.closest('details');if(g&&!g.open)g.open=true}).observe(nav,{attributes:true,subtree:true,attributeFilter:['class']});return true};
{let n=0;const t=setInterval(()=>{if(groupNav()||++n>60)clearInterval(t)},100)}

// compact tables + alerts toggle + shortcuts help in the top bar
{let n=0;const t=setInterval(()=>{const tl=document.querySelector('.top .tools');if(++n>60)clearInterval(t);if(!tl||tl.querySelector('.dens'))return;clearInterval(t);
 const pref=k=>localStorage.getItem(k)==='1';document.body.classList.toggle('compact',pref('mc_dense'));
 const dens=h('button',{type:'button',class:'dens','aria-pressed':String(pref('mc_dense')),title:T('Compact tables'),'aria-label':T('Compact tables'),onclick(){const on=!document.body.classList.contains('compact');document.body.classList.toggle('compact',on);dens.setAttribute('aria-pressed',String(on));try{localStorage.setItem('mc_dense',on?'1':'0')}catch(e){}}},'☷');
 const al=h('button',{type:'button',class:'alrt','aria-pressed':String(pref('mc_alert')),title:T('New order alerts'),'aria-label':T('New order alerts'),onclick(){const on=!pref('mc_alert');try{localStorage.setItem('mc_alert',on?'1':'0')}catch(e){}al.setAttribute('aria-pressed',String(on));al.textContent=on?'🔔':'🔕';
  if(on){beep();if('Notification' in window&&Notification.permission==='default')Notification.requestPermission().catch(()=>{});toast('New order alerts are on')}else toast('New order alerts are off')}},pref('mc_alert')?'🔔':'🔕');
 const kb=h('button',{type:'button',title:T('Keyboard shortcuts'),'aria-label':T('Keyboard shortcuts'),onclick:()=>shortcuts()},'?');
 tl.prepend(dens,al,kb)},100)}
let AC=null;const beep=()=>{try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=880;g.gain.value=.08;o.connect(g);g.connect(AC.destination);o.start();o.stop(AC.currentTime+.18)}catch(e){}};
const baseTitle=document.title;let last={orders:null,rx:null};
const alertCheck=()=>{const o=document.getElementById('bdg-orders'),r=document.getElementById('bdg-rx');if(!o&&!r)return;const no=+(o&&o.textContent)||0,nr=+(r&&r.textContent)||0,tot=no+nr;document.title=(tot?'('+tot+') ':'')+baseTitle.replace(/^\(\d+\)\s*/,'');
 const rxUp=last.rx!==null&&nr>last.rx,grew=(last.orders!==null&&no>last.orders)||rxUp;last={orders:no,rx:nr};
 if(grew&&localStorage.getItem('mc_alert')==='1'){beep();try{if('Notification' in window&&Notification.permission==='granted')new Notification(rxUp?'New prescription to review':'New order waiting',{body:tot+' waiting'})}catch(e){}}};
{let n=0;const t=setInterval(()=>{const o=document.getElementById('bdg-orders');if(++n>80)clearInterval(t);if(!o)return;clearInterval(t);const mo=new MutationObserver(alertCheck);['bdg-orders','bdg-rx'].forEach(id=>{const e=document.getElementById(id);if(e)mo.observe(e,{childList:true,characterData:true,subtree:true})});alertCheck()},150)}

// shortcuts: "?" lists them, "g" then a letter jumps to a screen (only screens you may open)
const KEYS={d:'dash',a:'alerts',r:'rx',o:'orders',p:'pos',i:'inv',s:'products',c:'customers',e:'expenses',t:'reports',u:'users'};
const shortcuts=()=>{if(document.querySelector('dialog.kbd'))return;const rows=[['Ctrl+K','Search orders, products, customers'],['?','This list'],...Object.entries(KEYS).filter(([k,t])=>document.querySelector('#side nav button[data-t='+t+']')).map(([k,t])=>['g then '+k,'Go to '+(NAMES[t]||t)])];
 const w=h('dialog',{class:'kbd','aria-label':T('Keyboard shortcuts')},h('h2',{},T('Keyboard shortcuts')),h('dl',{},rows.flatMap(([a,b])=>[h('dt',{},h('kbd',{},a)),h('dd',{},b)])),h('p',{},h('button',{type:'button',onclick(){w.close();w.remove()}},T('Close'))));w.addEventListener('close',()=>w.remove());document.body.append(w);w.showModal()};
let gWait=0;document.addEventListener('keydown',e=>{const t=e.target,typing=t&&(/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||t.isContentEditable);if(typing||e.ctrlKey||e.metaKey||e.altKey||!document.querySelector('#side'))return;
 if(e.key==='?'){e.preventDefault();shortcuts();return}
 if(gWait&&Date.now()-gWait<1200){gWait=0;const tab=KEYS[e.key.toLowerCase()],b=tab&&document.querySelector('#side nav button[data-t='+tab+']');if(b){e.preventDefault();b.click()}return}
 if(e.key==='g')gWait=Date.now()});

// dashboard: what needs attention, with links
const attnAdd=r=>{try{const can=t=>(typeof ACC!=='undefined'&&ACC[R]||[]).includes(t),lim=new Date(Date.now()+(+D.settings.expiryDays||60)*864e5).toISOString().slice(0,10),go2=t=>{const b=document.querySelector('#side nav button[data-t='+t+']');if(b)b.click()};
 const items=[['rx','Prescriptions to review',(D.orders||[]).filter(o=>o.status==='Prescription Review').length],['orders','Orders waiting',(D.orders||[]).filter(o=>o.status==='Pending').length],['alerts','Low stock',D.products.filter(p=>stock(D,p.id)<p.reorder).length],['alerts','Expiring soon',D.batches.filter(b=>b.qty>0&&b.exp>=today()&&b.exp<=lim).length],['alerts','Expired, to write off',D.batches.filter(b=>b.qty>0&&b.exp<today()).length]].filter(([t,l,n])=>n>0&&can(t));
 r.prepend(h('section',{class:'attn','aria-label':T('Needs attention')},h('h2',{},T('Needs attention')),items.length?h('div',{class:'row'},items.map(([t,l,n])=>h('button',{type:'button',class:'btn2 attn-chip',onclick:()=>go2(t)},h('b',{},n),' '+l))):h('p',{class:'ok'},'✓ '+T('All clear'))))}catch(e){console.error(e)}return r};

// ---- v3.2 POS: live search, quantity steppers, totals with change due, Rx notice, held carts, till summary ----
if(typeof I18!=='undefined')Object.assign(I18.bn,{'Total':'মোট','Change':'ফেরত','Short by':'কম আছে','Exact':'ঠিক টাকা','Hold cart':'কার্ট ধরে রাখুন','Held carts':'ধরে রাখা কার্ট','Clear cart':'কার্ট খালি করুন','Today at the till':'আজকের কাউন্টার','Receipt':'রসিদ','Frequent items':'ঘন ঘন বিক্রি','Use max points':'সর্বোচ্চ পয়েন্ট','Prescription reference':'প্রেসক্রিপশন রেফারেন্স'});
let POSF={disc:'',pay:'Cash',cash:'',ph:'',rd:'',rx:''},posSalesLen=-1;
const HOLDS='mc_holds',holds=()=>{try{return JSON.parse(localStorage.getItem(HOLDS)||'[]')}catch(e){return[]}},setHolds=L=>{try{localStorage.setItem(HOLDS,JSON.stringify(L.slice(-12)))}catch(e){}};
const PHRE=/^(\+?88)?01[3-9]\d{8}$/;
const posAdd=r=>{try{
 if(typeof receipt==='function'&&receipt!==receipt2)receipt=receipt2;
 if(posSalesLen>=0&&D.sales.length>posSalesLen)POSF={disc:'',pay:'Cash',cash:'',ph:'',rd:'',rx:''};posSalesLen=D.sales.length;
 const q=r.querySelector('#pq'),tables=r.querySelectorAll('table'),cartTbl=tables[0],histTbl=tables[1],quick=r.querySelector('[aria-label="Quick add"]'),rowIn=[...r.querySelectorAll(':scope>.row')].find(x=>x.querySelector('[aria-label="Cash received"]')),sumP=r.querySelector(':scope>p.price');
 if(!q||!cartTbl||!rowIn)return r;
 const I={disc:rowIn.querySelector('[aria-label="Discount ৳"]'),pay:rowIn.querySelector('select'),cash:rowIn.querySelector('[aria-label="Cash received"]'),ph:rowIn.querySelector('[aria-label="Customer mobile (optional)"]'),rd:rowIn.querySelector('[aria-label="Redeem points"]')};
 const done=[...r.querySelectorAll(':scope>button')].find(b=>b.textContent==='Complete sale');
 const pid2p=id=>D.products.find(p=>p.id===id),isRx=l=>!!(pid2p(l.pid)&&pid2p(l.pid).rx);
 const add=p=>{const l=cartPOS.find(x=>x.pid===p.id)||(cartPOS.push({pid:p.id,name:p.name,price:eff(p),qty:0}),cartPOS.at(-1));if(l.qty+1>stock(D,p.id)){if(!l.qty)cartPOS.pop();return toast('Insufficient unexpired stock',1)}l.qty++;POSF.q='';go();setTimeout(()=>{const n=document.getElementById('pq');if(n)n.focus()},0)};
 // remembered field values
 Object.keys(I).forEach(k=>{if(I[k]&&POSF[k]!==''&&POSF[k]!==undefined)I[k].value=POSF[k]});
 // totals
 const calc=()=>{const sub=cartPOS.reduce((a,l)=>a+l.price*l.qty,0),d=Math.min(Math.max(+I.disc.value||0,0),sub),rd=Math.max(+I.rd.value||0,0),tot=Math.max(0,sub-d-rd),cash=+I.cash.value||0,isCash=I.pay.value==='Cash';return{sub,d,rd,tot,cash,isCash,change:isCash?Math.max(0,cash-tot):0,short:isCash&&I.cash.value!==''&&cash<tot?tot-cash:0}};
 const lSub=h('span',{}),lDisc=h('span',{}),lPts=h('span',{}),lTot=h('b',{class:'pos-total'}),lChg=h('div',{class:'pos-change',role:'status','aria-live':'polite'});
 const upd=()=>{const c=calc();lSub.textContent=money(c.sub);lDisc.textContent=c.d?'−'+money(c.d):'—';lPts.textContent=c.rd?'−'+money(c.rd):'—';lTot.textContent=money(c.tot);
  lChg.className='pos-change'+(c.short?' bad':c.change?' ok':'');lChg.textContent=!c.isCash?T('Total')+': '+money(c.tot):c.short?T('Short by')+' '+money(c.short):c.cash?T('Change')+' '+money(c.change):''};
 Object.entries(I).forEach(([k,el])=>{if(!el)return;const ev=el.tagName==='SELECT'?'change':'input';el.addEventListener(ev,()=>{POSF[k]=el.value;upd()})});
 const chips=h('div',{class:'row pos-chips',role:'group','aria-label':'Cash received quick buttons'},h('button',{type:'button',class:'btn2',onclick(){const c=calc();I.cash.value=c.tot;POSF.cash=String(c.tot);I.pay.value='Cash';POSF.pay='Cash';upd()}},T('Exact')),...[100,200,500,1000].map(v=>h('button',{type:'button',class:'btn2',onclick(){I.cash.value=v;POSF.cash=String(v);I.pay.value='Cash';POSF.pay='Cash';upd()}},'৳'+v)));
 const panel=h('div',{class:'pos-sum'},h('div',{class:'pos-line'},h('span',{},'Subtotal'),lSub),h('div',{class:'pos-line'},h('span',{},'Discount'),lDisc),h('div',{class:'pos-line'},h('span',{},'Points redeemed'),lPts),h('div',{class:'pos-line pos-big'},h('span',{},T('Total')),lTot),chips,lChg);
 // customer info
 const cinfo=h('small',{class:'muted','aria-live':'polite'});
 const showC=()=>{const ph=I.ph.value.trim();cinfo.replaceChildren();if(!PHRE.test(ph))return;const np=typeof nph==='function'?nph(ph):ph,o=(D.orders||[]).find(x=>nph(x.phone)===np),nmx=(D.cust&&D.cust[ph]&&D.cust[ph].name)||(o&&o.customer)||'',pts=loyAvail(D,ph);
  cinfo.append(...[ (nmx?nmx+' · ':'')+pts+' points available ',pts>0?h('button',{type:'button',class:'linkbtn',onclick(){const c=calc(),mx=Math.min(pts,Math.floor((c.sub-c.d)/2));I.rd.value=mx;POSF.rd=String(mx);upd()}},T('Use max points')):null ].filter(x=>x!=null&&x!==false))};
 I.ph.addEventListener('input',showC);showC();
 // Rx notice with an inline reference (used instead of the pop-up prompt)
 const rxL=cartPOS.filter(isRx),canRx=['Owner','Pharmacist'].includes(R);let rxBox=null,rxIn=null;
 if(rxL.length){rxIn=h('input',{'aria-label':T('Prescription reference'),placeholder:'Doctor, registration no., date',value:POSF.rx||'',maxlength:160,oninput(e){POSF.rx=e.target.value}});
  rxBox=h('div',{class:'card warn',role:'note'},h('b',{},'Rx '),'This sale has prescription items ('+rxL.map(l=>l.name).join(', ')+'). '+(canRx?'Enter the prescription reference (at least 6 characters) before completing.':'Only a pharmacist or the owner can complete it. Ask one to finish this sale.'),canRx?h('label',{},T('Prescription reference'),rxIn):null)}
 if(done)done.addEventListener('click',()=>{if(!rxL.length||!canRx)return;const old=window.prompt;window.prompt=()=>(rxIn&&rxIn.value||'');setTimeout(()=>{window.prompt=old},0)},true);
 // search with live results
 q.removeAttribute('list');const dl=r.querySelector('datalist');if(dl)dl.remove();
 const list=h('ul',{class:'pos-results',role:'listbox','aria-label':'Matching products',hidden:true});let cur=0,hits=[];
 const draw=()=>{const v=q.value.trim().toLowerCase();hits=v.length<2?[]:D.products.filter(p=>(p.name+' '+(p.generic||'')+' '+(p.sku||'')+' '+(p.barcode||'')).toLowerCase().includes(v)).sort((a,b)=>(stock(D,b.id)>0)-(stock(D,a.id)>0)||a.name.localeCompare(b.name)).slice(0,8);cur=0;
  list.hidden=!hits.length;list.replaceChildren(...hits.map((p,i)=>{const st=stock(D,p.id);return h('li',{role:'option','aria-selected':String(i===0)},h('button',{type:'button',class:i===0?'on':'',disabled:!st,onclick:()=>add(p)},h('b',{},p.name),' ',h('span',{class:'muted'},[p.strength&&p.strength!=='—'?p.strength:'',p.pack].filter(Boolean).join(' · ')),p.rx?h('span',{class:'tag rx'},'Rx'):null,h('span',{class:'pos-r'},st?money(eff(p))+' · '+st+' in stock':'Out of stock')))}))};
 const mark=()=>[...list.children].forEach((li,i)=>{const on=i===cur;li.setAttribute('aria-selected',String(on));li.firstChild.classList.toggle('on',on)});
 q.addEventListener('input',draw);
 q.addEventListener('keydown',e=>{if(e.key==='ArrowDown'&&hits.length){e.preventDefault();cur=Math.min(hits.length-1,cur+1);mark()}else if(e.key==='ArrowUp'&&hits.length){e.preventDefault();cur=Math.max(0,cur-1);mark()}else if(e.key==='Escape'){q.value='';draw()}
  else if(e.key==='Enter'){const v=q.value.trim().toLowerCase(),exact=D.products.find(x=>x.barcode===v||x.name.toLowerCase()===v||(x.sku||'').toLowerCase()===v);if(!exact&&hits.length){e.preventDefault();e.stopImmediatePropagation();const p=hits[cur];if(stock(D,p.id)>0)add(p);else toast('Out of stock',1)}}},true);
 // frequent items
 if(quick){const cnt={},cut=Date.now()-60*864e5;(D.sales||[]).filter(x=>!x.refunded&&new Date(x.at)>=cut).forEach(x=>x.items.forEach(i=>{cnt[i.pid]=(cnt[i.pid]||0)+i.qty}));
  const top=D.products.filter(p=>stock(D,p.id)>0).sort((a,b)=>(cnt[b.id]||0)-(cnt[a.id]||0)).slice(0,8);quick.replaceChildren(h('small',{class:'muted'},T('Frequent items')+':'),...top.map(p=>h('button',{type:'button',onclick:()=>add(p)},p.name+' '+money(eff(p)))))}
 // cart table: steppers, Rx stamps, stock hint
 [...cartTbl.querySelectorAll('tbody tr')].forEach((tr,i)=>{const l=cartPOS[i];if(!l)return;const p=pid2p(l.pid),st=p?stock(D,l.pid):0,tds=tr.children;
  tds[0].replaceChildren(...[ l.name,p&&p.rx?h('span',{class:'tag rx'},'Rx'):null,h('small',{class:'muted'},' '+money(l.price)+' each') ].filter(x=>x!=null&&x!==false));
  const set=n=>{n=Math.floor(+n);if(!(n>=1)){cartPOS=cartPOS.filter(x=>x!==l);return go()}if(n>st){toast('Only '+st+' in stock',1);n=st}l.qty=n;go()};
  tds[1].replaceChildren(h('div',{class:'stepper'},h('button',{type:'button','aria-label':'One less '+l.name,onclick:()=>set(l.qty-1)},'−'),h('input',{type:'number',min:1,max:st,value:l.qty,'aria-label':'Quantity of '+l.name,onchange:e=>set(e.target.value)}),h('button',{type:'button','aria-label':'One more '+l.name,onclick:()=>set(l.qty+1)},'+')))});
 const clear=h('button',{type:'button',class:'btn2',onclick(){if(!cartPOS.length)return toast('Cart empty',1);cartPOS=[];POSF={disc:'',pay:'Cash',cash:'',ph:'',rd:'',rx:''};go()}},T('Clear cart'));
 const hold=h('button',{type:'button',class:'btn2',onclick(){if(!cartPOS.length)return toast('Cart empty',1);const L=holds();L.push({id:uid('H'),at:Date.now(),cart:cartPOS,f:POSF});setHolds(L);cartPOS=[];POSF={disc:'',pay:'Cash',cash:'',ph:'',rd:'',rx:''};toast('Cart held');go()}},T('Hold cart'));
 const HL=holds(),heldBox=HL.length?h('div',{class:'pos-held'},h('b',{},T('Held carts')),...HL.map(x=>{const t=x.cart.reduce((a,l)=>a+l.price*l.qty,0);return h('span',{class:'pos-hold'},new Date(x.at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'})+' · '+x.cart.length+' item(s) · '+money(t)+' ',
  h('button',{type:'button',class:'btn2',onclick(){if(cartPOS.length)return toast('Hold or clear the current cart first',1);cartPOS=x.cart.filter(l=>pid2p(l.pid));POSF=Object.assign({disc:'',pay:'Cash',cash:'',ph:'',rd:'',rx:''},x.f||{});setHolds(holds().filter(y=>y.id!==x.id));go()}},'Resume'),
  h('button',{type:'button',class:'btn2','aria-label':'Delete held cart',onclick(){setHolds(holds().filter(y=>y.id!==x.id));go()}},'×'))})):null;
 // remove the old single-slot Suspend/Resume buttons (replaced by held carts)
 [...r.querySelectorAll(':scope>button')].forEach(b=>{if(b.textContent==='Suspend'||b.textContent==='Resume')b.remove()});
 if(sumP)sumP.remove();
 // today at the till
 const td=new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Dhaka'}),ts=(D.sales||[]).filter(x=>!x.refunded&&new Date(x.at).toLocaleDateString('en-CA',{timeZone:'Asia/Dhaka'})===td),by={};ts.forEach(x=>{const m=String(x.pay||'Cash').replace(/\s*\(demo\)/,'');by[m]=(by[m]||0)+x.total});
 const till=h('div',{class:'card'},h('h2',{},T('Today at the till')),h('p',{},ts.length+' sale(s) · '+money(ts.reduce((a,x)=>a+x.total,0))+(Object.keys(by).length?' ('+Object.entries(by).map(([k,v])=>k+' '+money(v)).join(' · ')+')':'')));
 // sales history: receipt reprint
 if(histTbl){const L=D.sales.slice(-10).reverse(),hr=histTbl.querySelector('thead tr');if(hr&&L.length){hr.append(h('th',{scope:'col'},''));[...histTbl.querySelectorAll('tbody tr')].forEach((tr,i)=>{const sale=L[i];if(sale)tr.append(h('td',{},h('button',{type:'button',class:'btn2',onclick:()=>receipt(sale)},T('Receipt'))))})}}
 // layout: left = search and cart, right = customer, totals and the complete button
 const left=h('div',{class:'posleft'}),right=h('div',{class:'posright'});
 left.append(q,list);if(quick)left.append(quick);left.append(cartTbl,h('div',{class:'row'},hold,clear));if(heldBox)left.append(heldBox);
 right.append(rowIn,cinfo);if(rxBox)right.append(rxBox);right.append(panel);if(done)right.append(done);
 const hint=r.querySelector(':scope>p.muted'),grid=h('div',{class:'posgrid'},left,right);
 [...r.children].forEach(c=>{if(c!==hint&&c!==histTbl&&!(c.tagName==='H2'))c.remove?.()});
 const hh=[...r.querySelectorAll(':scope>h2')];
 r.replaceChildren(...[hint,grid,till,...hh,histTbl].filter(Boolean));
 upd()}catch(e){console.error(e)}return r};

// ---- v3.2 receipt: a proper counter receipt (store, phone, items table, totals, payment, Rx reference) ----
const receipt2=s=>{const st=D.settings||{},sub=s.items.reduce((a,i)=>a+i.qty*i.price,0),cashIn=s.pay==='Cash'?s.total+(s.change||0):null;
 const row=(a,b,cls)=>h('tr',{class:cls||''},h('td',{},a),h('td',{class:'rn'},b));
 const w=h('dialog',{class:'rcpt80','aria-label':'Receipt '+s.no},h('h2',{},st.store),st.phone?h('p',{class:'muted'},[st.address,st.phone].filter(Boolean).join(' · ')):null,
  h('p',{},s.no+' · '+dhaka(s.at)),
  h('table',{class:'rc-items'},h('thead',{},h('tr',{},['Item','Qty','Amount'].map((x,i)=>h('th',{scope:'col',class:i?'rn':''},x)))),h('tbody',{},s.items.map(i=>h('tr',{},h('td',{},i.name),h('td',{class:'rn'},i.qty+' × '+money(i.price)),h('td',{class:'rn'},money(i.qty*i.price)))))),
  h('table',{class:'rc-tot'},h('tbody',{},row('Subtotal',money(sub)),s.disc?row('Discount','−'+money(s.disc)):null,s.loy?row('Points redeemed '+s.loy,'−'+money(s.loy)):null,row('Total',money(s.total),'rc-big'),row('Paid by',String(s.pay||'Cash').replace(/\s*\(demo\)/,'')),cashIn!==null?row('Cash received',money(cashIn)):null,row('Change',money(s.change||0)))),
  s.rx?h('p',{class:'muted'},'Prescription: '+s.rx):null,s.by?h('p',{class:'muted'},'Served by: '+s.by):null,
  h('p',{},st.receiptFooter),h('button',{type:'button',onclick:()=>print()},'Print'),h('button',{type:'button',onclick(){w.close();w.remove()}},'Close'));
 w.addEventListener('close',()=>w.remove());document.body.append(w);w.showModal()};

window.ADMIN_WRAPS=[{id:'dash',fn:dashAdd},{id:'dash',fn:attnAdd},{id:'pos',fn:posAdd},{id:'account',fn:accountAdd},{id:'users',fn:usersAdd},{id:'settings',fn:policyAdd}];

window.ADMIN_EXTRAS=[
 {id:'insights',name:'Insights',icon:'🔍',roles:['Owner'],after:'reports',view:insights},
 {id:'refill',name:'Refill follow-ups',icon:'📞',roles:['Owner','Pharmacist'],after:'customers',view:refill},
 {id:'labels',name:'Shelf labels',icon:'🏷️',roles:['Owner','Inventory Manager'],after:'products',view:labels},
 {id:'customer360',name:'Customer lookup',icon:'🧑',roles:['Owner','Pharmacist','Cashier'],after:'orders',view:customer},
 {id:'pricelist',name:'Price list',icon:'💲',roles:['Owner','Pharmacist','Cashier','Inventory Manager'],after:'products',view:pricelist},
 {id:'expiry',name:'Expiry planner',icon:'⏳',roles:['Owner','Pharmacist','Inventory Manager'],after:'inv',view:expiry},
 {id:'margins',name:'Margin analysis',icon:'💹',roles:['Owner','Inventory Manager'],after:'reports',view:margins},
 {id:'reorder',name:'Supplier orders',icon:'📨',roles:['Owner','Inventory Manager'],after:'purchases',view:reorder}];
})();
