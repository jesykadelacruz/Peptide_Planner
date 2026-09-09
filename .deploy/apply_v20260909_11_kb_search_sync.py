from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

def replace_once(old,new,label):
    global html
    count=html.count(old)
    assert count==1, f'{label}: expected one match, found {count}'
    html=html.replace(old,new,1)

replace_once('<title>Peptide Planner v2026.0909.04</title>','<title>Peptide Planner v2026.0909.11</title>','browser title')
replace_once('const APP_VERSION="v2026.0909.04";','const APP_VERSION="v2026.0909.11";','app version')

replace_once('''function renderProtocolLibrary(){
  const root=document.getElementById("protocolLibraryCards");if(!root)return;
  const normalizeKbSearch=value=>String(value||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim().replace(/\s+/g," ");
  const search=normalizeKbSearch(state.ui.protocolLibrarySearch||"");''','''function renderProtocolLibrary(){
  const root=document.getElementById("protocolLibraryCards");if(!root)return;
  const normalizeKbSearch=value=>String(value||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim().replace(/\s+/g," ");
  const searchInput=document.getElementById("protocolLibrarySearch");
  const search=normalizeKbSearch(searchInput?searchInput.value:(state.ui.protocolLibrarySearch||""));''','Knowledge Base visible search source')

replace_once('''if(protocolSearch){
  protocolSearch.value=state.ui.protocolLibrarySearch||"";
  const runProtocolSearch=()=>{state.ui.protocolLibrarySearch=protocolSearch.value;renderProtocolLibrary()};''','''if(protocolSearch){
  state.ui.protocolLibrarySearch=protocolSearch.value||"";
  const runProtocolSearch=()=>{state.ui.protocolLibrarySearch=protocolSearch.value;renderProtocolLibrary()};''','Knowledge Base initial search reset')

replace_once('''function applyCloudPlannerState(remoteState,remoteStamp){
  if(!remoteState||typeof remoteState!=="object"||!cloudUser?.id)return false;
  let reconciledFreshPreparation=false;
  cloudApplying=true;
  try{
    state={...defaultState(),...remoteState};reconciledFreshPreparation=!!normaliseState();plannerStateUserId=cloudUser.id;
    const key=plannerUserStorageKey(cloudUser.id);if(key)localStorage.setItem(key,JSON.stringify(state));''','''function applyCloudPlannerState(remoteState,remoteStamp){
  if(!remoteState||typeof remoteState!=="object"||!cloudUser?.id)return false;
  let reconciledFreshPreparation=false;
  const visibleProtocolSearch=document.getElementById("protocolLibrarySearch")?.value;
  cloudApplying=true;
  try{
    state={...defaultState(),...remoteState};reconciledFreshPreparation=!!normaliseState();plannerStateUserId=cloudUser.id;
    if(visibleProtocolSearch!=null)state.ui.protocolLibrarySearch=visibleProtocolSearch;
    const key=plannerUserStorageKey(cloudUser.id);if(key)localStorage.setItem(key,JSON.stringify(state));''','cloud restore visible search preservation')

assert html!=original
path.write_text(html,encoding='utf-8')
print('Applied v20260909.11 Knowledge Base search synchronization and release identifiers')
