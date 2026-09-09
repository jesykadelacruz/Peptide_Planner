from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

old='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
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
}'''

new='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
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

assert html.count(old)==1, f'Expected one cycled Full Dose helper, found {html.count(old)}'
html=html.replace(old,new,1)
assert html!=original
path.write_text(html,encoding='utf-8')
print('Corrected cycled Full Dose to continue through the repeating dose schedule')
