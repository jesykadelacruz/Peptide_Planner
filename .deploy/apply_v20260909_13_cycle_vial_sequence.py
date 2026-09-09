from pathlib import Path

index=Path('index.html')
sw=Path('peptide-planner-sw.js')
html=index.read_text(encoding='utf-8')
service=sw.read_text(encoding='utf-8')
original_html=html
original_service=service

def replace_once(text,old,new,label):
    count=text.count(old)
    assert count==1, f'{label}: expected 1 match, found {count}'
    return text.replace(old,new,1)

html=replace_once(html,'<title>Peptide_Planner_v20260909.12</title>','<title>Peptide_Planner_v20260909.13</title>','browser title')
html=replace_once(html,'const APP_VERSION="Peptide_Planner_v20260909.12";','const APP_VERSION="Peptide_Planner_v20260909.13";','APP_VERSION')
service=replace_once(service,"const PEPTIDE_PLANNER_SW_VERSION='Peptide_Planner_v20260909.12';","const PEPTIDE_PLANNER_SW_VERSION='Peptide_Planner_v20260909.13';",'service worker version')

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
html=replace_once(html,old_full,new_full,'canonical Full Dose sequence')

html=replace_once(html,'if(!manualFinish&&dispose&&event.date>=dispose){reason="Disposal limit";break;}','if(!manualFinish&&dispose&&event.date>dispose){reason="Disposal limit";break;}','dispose date inclusive')
html=replace_once(html,'if(reason==="Disposal limit")return {nextCursor:cursor,finishDate:disposeDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason};','if(reason==="Disposal limit")return {nextCursor:cursor,finishDate:lastFullDoseDate||openDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason};','finish on last Cycle Dose date')

old_open='''    const fallbackOpenDate=previousFinishDate?localDateISO(addDays(previousFinishDate,1)):(previousFinish||"");
    const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):automaticVialOpenDateForCursor(dosePlan,rowStartCursor,fallbackOpenDate);'''
new_open='''    const fallbackOpenDate=previousFinishDate?localDateISO(addDays(previousFinishDate,1)):(previousFinish||"");
    const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):fallbackOpenDate;'''
html=replace_once(html,old_open,new_open,'sequential next-day vial open')

html=replace_once(html,'const cycleDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate||null);','const cycleDoseCount=effectiveWindow.fullDoseCount;','Cycle Dose from assigned vial window')

assert html!=original_html
assert service!=original_service
index.write_text(html,encoding='utf-8')
sw.write_text(service,encoding='utf-8')
print('Applied Peptide_Planner_v20260909.13 cycled vial sequence correction')
