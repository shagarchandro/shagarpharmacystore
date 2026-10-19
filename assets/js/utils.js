// utils.js: DOM helper, money/date formatting, ids, CSV (formula-safe), toasts, placeholder images
'use strict';
const $=(s,r=document)=>r.querySelector(s);
function h(t,p={},...k){const e=document.createElement(t);for(const[a,v]of Object.entries(p)){if(a==='class')e.className=v;else if(a.startsWith('on'))e.addEventListener(a.slice(2),v);else if(v!==false&&v!=null)e.setAttribute(a,v)}for(const c of k.flat())if(c!=null&&c!==false)e.append(c.nodeType?c:document.createTextNode(c));return e}
const money=n=>'৳'+Number(n||0).toLocaleString('en-BD',{maximumFractionDigits:2});
const dhaka=d=>new Date(d).toLocaleString('en-GB',{timeZone:'Asia/Dhaka',dateStyle:'medium',timeStyle:'short'});
const today=()=>new Date().toISOString().slice(0,10);
const eff=p=>Math.round(p.price*(100-(p.disc||0))/100);
const uid=p=>p+'-'+Date.now().toString(36)+Math.random().toString(36).slice(2,5);
const csvCell=v=>{let s=String(v??'');if(/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'};
function csv(name,rows){const b=new Blob([rows.map(r=>r.map(csvCell).join(',')).join('\n')],{type:'text/csv'});h('a',{href:URL.createObjectURL(b),download:name}).click()}
function toast(m,bad){let t=$('#toasts')||document.body.appendChild(h('div',{id:'toasts','aria-live':'polite'}));const e=h('div',{class:'toast'+(bad?' bad':'')},T(m));t.append(e);setTimeout(()=>e.remove(),3000)}
const pcol=(v,d)=>(getComputedStyle(document.documentElement).getPropertyValue(v)||'').trim()||d;
const ph=n=>'data:image/svg+xml,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 70"><rect width="120" height="70" fill="${pcol('--mint','#e6efe6')}"/><text x="60" y="44" text-anchor="middle" font-size="28" font-family="sans-serif" fill="${pcol('--pri','#13694b')}">${n.replace(/[^A-Za-z0-9]/g,'').slice(0,2).toUpperCase()}</text></svg>`);
const nph=x=>String(x||'').replace(/^\+?88/,'');
if('serviceWorker' in navigator&&/^https?:$/.test(location.protocol)){const base=document.currentScript?document.currentScript.src.replace(/assets\/js\/utils\.js.*$/,''):'';navigator.serviceWorker.register(base+'sw.js').catch(()=>{})}
