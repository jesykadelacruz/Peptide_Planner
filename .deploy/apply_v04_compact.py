from pathlib import Path
import hashlib, re
p=Path('index.html')
h=p.read_text()
BEFORE='2f88603a130e6c0dea7953ed89d76e4716fc5f25bb2c679205ac0bbdff7a5b77'
AFTER='626109dd9fb1b2480158229f8c6e013976e24429aa69a4f2743cd5bf30b69152'
if hashlib.sha256(h.encode()).hexdigest()!=BEFORE: raise SystemExit('unexpected source checksum')
def one(old,new):
    global h
    if h.count(old)!=1: raise SystemExit('marker mismatch: '+old[:80])
    h=h.replace(old,new,1)
one('<title>Peptide Planner v2026.0909.03</title>\n','<title>Peptide Planner v2026.0909.04</title>\n<!-- v2026.0909.04: Production hardening only. Cloud writes are serialized so overlapping autosaves cannot race or clear a newer local edit; successful writes preserve the dirty state when another edit occurred in flight. Password-reset redirects resolve from the planner URL currently in use instead of a fixed Pages hostname. Treatment, dose, vial, schedule, role and layout behavior are unchanged. -->\n')
one('const APP_VERSION="v2026.0909.03";','const APP_VERSION="v2026.0909.04";')
one('const PASSWORD_RESET_REDIRECT_URL="https://peptide-planner.pages.dev/?password=1";','''const PASSWORD_RESET_REDIRECT_URL=(()=>{\n  try{const url=new URL(window.location.href);url.search="";url.hash="";url.searchParams.set("password","1");return url.toString()}\n  catch{return "?password=1"}\n})();''')
one('let cloudClient=null,cloudUser=null,cloudAccess=null,cloudSaveTimer=null,cloudApplying=false,cloudInitialised=false,cloudAuthMode="signin",cloudAccessChecking=false;','let cloudClient=null,cloudUser=null,cloudAccess=null,cloudSaveTimer=null,cloudPushInFlight=null,cloudChangeRevision=0,cloudApplying=false,cloudInitialised=false,cloudAuthMode="signin",cloudAccessChecking=false;')
one('function markLocalChanged(){if(!cloudApplying)setCloudSyncMeta({localModifiedAt:new Date().toISOString(),localDirty:true})}','function markLocalChanged(){if(!cloudApplying){cloudChangeRevision+=1;setCloudSyncMeta({localModifiedAt:new Date().toISOString(),localDirty:true})}}')
new_push='''async function pushCloudState(reason="automatic"){
  if(!cloudClient||!cloudUser||cloudApplying||cloudAccess?.status!=="active")return false;
  if(cloudPushInFlight){setCloudSyncStatus("Changes pending","syncing");return cloudPushInFlight}
  clearTimeout(cloudSaveTimer);setCloudSyncStatus("Syncing…","syncing");
  const userId=cloudUser.id,revisionAtStart=cloudChangeRevision,stamp=new Date().toISOString();
  const payload={user_id:userId,state:clone(state),app_version:APP_VERSION,client_updated_at:stamp};
  cloudPushInFlight=(async()=>{
    try{
      let data=null,error=null;
      if(reason==="first_user_upload"){
        ({data,error}=await cloudClient.from("planner_state").upsert(payload,{onConflict:"user_id"}).select("updated_at,client_updated_at").maybeSingle());
      }else{
        const meta=getCloudSyncMeta(userId),baseline=meta.lastRemoteUpdatedAt||"";
        if(!baseline){
          await pullLatestCloudAfterRejectedPush("sync_baseline_backup");
          return false;
        }
        ({data,error}=await cloudClient.from("planner_state").update(payload).eq("user_id",userId).eq("updated_at",baseline).select("updated_at,client_updated_at").maybeSingle());
        if(error)throw error;
        if(!data){
          await pullLatestCloudAfterRejectedPush("cross_device_conflict_backup");
          return false;
        }
      }
      if(error)throw error;
      const remoteStamp=data?.updated_at||data?.client_updated_at||stamp;
      const changedDuringPush=cloudChangeRevision!==revisionAtStart,currentMeta=getCloudSyncMeta(userId);
      setCloudSyncMeta({userId,lastSyncedAt:stamp,localModifiedAt:changedDuringPush?(currentMeta.localModifiedAt||stamp):stamp,localDirty:changedDuringPush,lastRemoteUpdatedAt:remoteStamp},userId);
      setCloudSyncStatus(changedDuringPush?"Changes pending":"Synced",changedDuringPush?"syncing":"synced");
      return true;
    }catch(error){console.error("Cloud sync failed",error);setCloudSyncStatus("Sync error","error");return false}
  })();
  try{return await cloudPushInFlight}
  finally{
    cloudPushInFlight=null;
    const currentUserId=cloudUser?.id||"";
    if(currentUserId&&getCloudSyncMeta(currentUserId).localDirty===true)scheduleCloudSave();
  }
}'''
pat=r'async function pushCloudState\(reason="automatic"\)\{.*?\n\}(?=\n\nasync function snapshotLocalState)'
h,n=re.subn(pat,new_push,h,count=1,flags=re.S)
if n!=1: raise SystemExit('pushCloudState block mismatch')
p.write_text(h)
out=hashlib.sha256(h.encode()).hexdigest()
if out!=AFTER: raise SystemExit('unexpected output checksum '+out)
print(out)
