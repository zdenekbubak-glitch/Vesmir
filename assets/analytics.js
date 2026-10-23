/* One page-load event; no cookies, browser storage or visitor identifiers. */
(() => {
 if (window.__kosmoAnalytics || navigator.webdriver || !['kosmonovinky.cz','www.kosmonovinky.cz','zdenekbubak-glitch.github.io'].includes(location.hostname) || (location.hostname==='zdenekbubak-glitch.github.io'&&!location.pathname.startsWith('/Vesmir/'))) return;
 window.__kosmoAnalytics=true;
 const q=new URL(location.href).searchParams;
 const aliases={x:'x',twitter:'x',facebook:'facebook',fb:'facebook',bluesky:'bluesky',bsky:'bluesky',linkedin:'linkedin'};
 let source=aliases[(q.get('utm_source')||'').toLowerCase()],method='utm',external=true;
 let ref='';try {ref=new URL(document.referrer).hostname.toLowerCase();external=!['kosmonovinky.cz','www.kosmonovinky.cz','zdenekbubak-glitch.github.io'].includes(ref);}catch{}
 if (!source && ref && external) {
  const domains={x:['x.com','twitter.com','t.co'],facebook:['facebook.com','fb.com','fb.me'],bluesky:['bsky.app','bsky.social'],linkedin:['linkedin.com','lnkd.in']};
  for(const [name,hosts] of Object.entries(domains))if(hosts.some(h=>ref===h||ref.endsWith('.'+h)))source=name;
  method='referrer';
 }
 const token=(value,max)=>new RegExp('^[a-zA-Z0-9_-]{1,'+max+'}$').test(value||'')?value:'';
 const data={site:'vesmir',id:crypto.randomUUID(),path:location.pathname};
 if(source && external)data.social={source,method,post:method==='utm'?token(q.get('utm_content'),100):'',kind:method==='utm'?token(q.get('utm_term'),24)||'unknown':'unknown'};
 const body=JSON.stringify(data);
 async function send(){try{return (await fetch('https://ai-robotika-radar.zdenek-bubak.chatgpt.site/api/analytics/collect',{method:'POST',mode:'cors',credentials:'omit',headers:{'Content-Type':'application/json'},body,keepalive:true})).ok;}catch{return false;}}
 send().then(ok=>{if(!ok)setTimeout(send,1500);});
})();
