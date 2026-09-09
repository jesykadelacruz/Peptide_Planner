from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

assert '<title>Peptide Planner v2026.0909.04</title>' in html
assert 'const APP_VERSION="v2026.0909.04";' in html

base='''function vialDoseCountForDisplay(events,startCursor,openDate,unitsPerVial,throughDate=null){
  const open=parseISO(openDate),through=throughDate?parseISO(throughDate):null;
  if(!open||!unitsPerVial||unitsPerVial<=0)return 0;
  let cursor=Math.max(0,startCursor),remaining=unitsPerVial,count=0;
  while(cursor<events.length&&events[cursor].date<open)cursor+=1;
  while(cursor<events.length){
    const event=events[cursor];
    if(through&&event.date>through)break;
    if(event.units>remaining+0.000001)break;
    remaining=round(remaining-event.units,6);
    count+=1;
    cursor+=1;
    if(remaining<=0.000001)break;
  }
  return count;
}
'''
assert html.count(base)==1
helper='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
  const open=parseISO(openDate);
  if(!open||!unitsPerVial||unitsPerVial<=0)return 0;
  let cursor=Math.max(0,startCursor),remaining=unitsPerVial,count=0,continuationUnits=0;
  while(cursor<events.length&&events[cursor].date<open)cursor+=1;
  while(cursor<events.length){
    const event=events[cursor],eventUnits=num(event?.units);
    if(!(eventUnits>0))break;
    if(eventUnits>remaining+0.000001)break;
    remaining=round(remaining-eventUnits,6);count+=1;continuationUnits=eventUnits;cursor+=1;
    if(remaining<=0.000001)break;
  }
  if(remaining>0.000001&&!(continuationUnits>0)){
    for(let index=Math.min(events.length-1,Math.max(0,cursor-1));index>=0;index-=1){
      const eventUnits=num(events[index]?.units);if(eventUnits>0){continuationUnits=eventUnits;break;}
    }
  }
  if(remaining>0.000001&&continuationUnits>0)count+=Math.max(0,Math.floor((remaining+0.000001)/continuationUnits));
  return count;
}
'''
html=html.replace(base,base+helper,1)
old='const fullDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,null);'
new='const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits);'
assert html.count(old)==1
html=html.replace(old,new,1)

assert html.count('cycleFullDoseCountForDisplay(')==2
assert 'const cycleDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate||null);' in html
assert '<th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th>' in html
assert html!=original
path.write_text(html,encoding='utf-8')
print('Corrected cycled Full Dose to ignore disposal and cycle-end cutoffs')
