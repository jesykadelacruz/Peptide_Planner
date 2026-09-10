const PEPTIDE_PLANNER_SW_VERSION='Peptide_Planner_v20261009.07';
self.addEventListener('install',event=>{self.skipWaiting();});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.map(key=>caches.delete(key)));
    await self.clients.claim();
    const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    await Promise.all(clients.map(client=>{
      try{
        const url=new URL(client.url);
        url.searchParams.set('_ppv',PEPTIDE_PLANNER_SW_VERSION);
        return client.navigate(url.href);
      }catch{return Promise.resolve();}
    }));
  })());
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  event.respondWith(fetch(event.request,{cache:'no-store'}).catch(()=>fetch(event.request)));
});
