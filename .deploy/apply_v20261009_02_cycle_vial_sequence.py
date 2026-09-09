from pathlib import Path

VERSION='Peptide_Planner_v20261009.02'
OLD_VERSION='Peptide_Planner_v20261009.01'
index=Path('index.html')
sw=Path('peptide-planner-sw.js')
h=index.read_text(encoding='utf-8')
s=sw.read_text(encoding='utf-8')
base_h=h
base_s=s

def rep(text,old,new,label):
    n=text.count(old)
    assert n==1, f'{label}: expected one match, found {n}'
    return text.replace(old,new,1)

h=rep(h,f'<title>{OLD_VERSION}</title>',f'<title>{VERSION}</title>','title')
h=rep(h,f'const APP_VERSION="{OLD_VERSION}";',f'const APP_VERSION="{VERSION}";','APP_VERSION')
s=rep(s,f"const PEPTIDE_PLANNER_SW_VERSION='{OLD_VERSION}';",f"const PEPTIDE_PLANNER_SW_VERSION='{VERSION}';",'service worker version')

old_full='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
  const open=parseISO(openDate);
  if(!open||!unitsPerVial||unitsPerVial<=0||!Array.isArray(events)||!events.length)return 0;
  let cursor=Math.max(0,startCursor);
  while(cursor<events.length&&events[cursor].date<open)cursor+=1;
  const ordered=[];
  for(let index=cursor;index<events.length;index+=1){const eventUnits=num(events[index]?.units);if(eventUnits>0)ordered.push(eventUnits);}
  for(let index=0;index<Math.min(cursor,events.length);index+=1){const eventUnits=num(events[index]?.units);if(eventUnits>0)ordered.push(eventUnits);}
  if(!ordered.length)return 0;
  let remaining=unitsPerVial,count=0,index=0,safety=0;
  while(remaining>0.000001&&safety<100000){
    safety+=1;
    const eventUnits=ordered[index%ordered.length];
    if(eventUnits>remaining+0.000001)break;
    remaining=round(remaining-eventUnits,6);count+=1;index+=1;
  }
  return count;
}'''
new_full='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
  if(!unitsPerVial||unitsPerVial<=0||!Array.isArray(events)||!events.length)return 0;
  const ordered=events.map(event=>num(event?.units)).filter(eventUnits=>eventUnits>0);
  if(!ordered.length)return 0;
  let remaining=unitsPerVial,count=0,index=0,safety=0;
  while(remaining>0.000001&&safety<100000){
    safety+=1;
    const eventUnits=ordered[index%ordered.length];
    if(eventUnits>remaining+0.000001)break;
    remaining=round(remaining-eventUnits,6);count+=1;index+=1;
  }
  return count;
}'''
h=rep(h,old_full,new_full,'Full Dose canonical schedule')

h=rep(h,'if(!manualFinish&&dispose&&event.date>=dispose){reason="Disposal limit";break;}','if(!manualFinish&&dispose&&event.date>dispose){reason="Disposal limit";break;}','inclusive disposal date')
h=rep(h,'if(reason==="Disposal limit")return {nextCursor:cursor,finishDate:disposeDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason};','if(reason==="Disposal limit")return {nextCursor:cursor,finishDate:lastFullDoseDate||openDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason};','finish date from Cycle Dose')

# v20261009.01 already made the vial rows sequential and synchronized. Verify those invariants rather than changing them again.
assert 'const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):fallbackOpenDate;' in h
assert 'const automaticFinishDate=autoWindow.lastFullDoseDate||autoWindow.finishDate;' in h
assert 'const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,0,localDateISO(dosePlan.period.start),capacityUnits);' in h
assert 'const cycleDoseCount=effectiveWindow.fullDoseCount;' in h
assert 'calculatedFinishDate:automaticFinishDate' in h

assert h!=base_h and s!=base_s
index.write_text(h,encoding='utf-8')
sw.write_text(s,encoding='utf-8')
print(f'Applied {VERSION}')
