self.addEventListener('push',event=>{
  let data={};
  try{data=event.data?event.data.json():{}}catch(_){data={body:event.data?event.data.text():''}}
  const title=data.title||'Peptide Planner';
  const options={
    body:data.body||'You have a treatment reminder.',
    tag:data.tag||'peptide-planner-reminder',
    renotify:false,
    data:{url:data.url||'./'}
  };
  event.waitUntil(self.registration.showNotification(title,options));
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const target=new URL(event.notification?.data?.url||'./',self.registration.scope).href;
  event.waitUntil((async()=>{
    const list=await clients.matchAll({type:'window',includeUncontrolled:true});
    for(const client of list){
      if(client.url.startsWith(self.registration.scope)){await client.focus();return}
    }
    if(clients.openWindow)await clients.openWindow(target);
  })());
});
