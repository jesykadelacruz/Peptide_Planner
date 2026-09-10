from pathlib import Path
import re, subprocess, json
src=Path('index.html').read_text()

def fn(name):
    marker=f'function {name}('
    start=src.index(marker)
    brace=src.index('{',start)
    depth=0; quote=None; esc=False; i=brace
    while i<len(src):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
        else:
            if ch in "'\"`": quote=ch
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return src[start:i+1]
        i+=1
    raise ValueError(name)

names=['cycleVialRecordHasAuthoritativeOpen','cycleVialRecordResolvedOpenDate','cycleVialScheduleRecordPool','cycleVialScheduleRecordAt','cycleFullDoseCountForDisplay','simulateCycleVialWindow','cycleVialScheduleComputation']
blocks='\n'.join(fn(n) for n in names)
js=r'''"use strict";
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null}
function round(v,d=2){const p=10**d;return Math.round((Number(v)+Number.EPSILON)*p)/p}
function parseISO(s){if(!s)return null;const m=String(s).match(/^(\d{4})-(\d{2})-(\d{2})$/);if(!m)return null;return new Date(Number(m[1]),Number(m[2])-1,Number(m[3]))}
function localDateISO(d){return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x}
function todayISO(){return '2026-09-10'}
function enteredPlanNumber(v){return num(v)}
function recordHasActualActivity(r){return !!(r.purchaseDate||r.receivedDate||r.startDate||r.expiryDate||r.notes||['Purchased','Received','In use','Finished','Discarded','On hold'].includes(r.status))}
let state={vialRecords:[]};
let TEST_PERIOD={valid:true,start:parseISO('2026-08-01'),activeEnd:parseISO('2026-11-01'),fullEnd:parseISO('2026-11-28')};
function protocolPeriodForSequence(plan,seq){return TEST_PERIOD}
let TEST_EVENTS=[];
function cycleVialDoseEvents(plan,cycleNumber){return {valid:true,cycleNumber,period:TEST_PERIOD,events:TEST_EVENTS}}
function cycleVialPrepForSequence(plan,seq){return {vialMg:100,waterMl:5,finalMl:5,concentration:20}}
function cycleVialPrepForRecord(plan,record,fallback){const vialMg=num(record?.vialMg)>0?num(record.vialMg):num(fallback?.vialMg);const waterMl=num(record?.finalMl||record?.bacWaterMl)>0?num(record.finalMl||record.bacWaterMl):num(fallback?.waterMl);return {record:record||fallback?.record||null,vialMg:vialMg||0,waterMl:waterMl||0,finalMl:waterMl||0,concentration:vialMg>0&&waterMl>0?vialMg/waterMl:0}}
function disposeDateFromOpen(plan,opened){return addDays(opened,Number(plan.discardAfterDays||42))}
function cycleVialScheduleStatus(open,finish){return 'Pending'}
function cycleVialScheduleStatusKey(x){return 'pending'}
''' + blocks + r'''
function event(date,dose){return {date:parseISO(date),dateISO:date,doseMg:dose,units:dose*5,week:1,entryMode:'dose',enteredUnits:null}}
function assert(cond,msg){if(!cond)throw new Error(msg)}
TEST_PERIOD={valid:true,start:parseISO('2026-08-01'),activeEnd:parseISO('2026-10-31'),fullEnd:parseISO('2026-11-28')};
TEST_EVENTS=[];for(let d=parseISO('2026-08-01');d<=TEST_PERIOD.activeEnd;d=addDays(d,2))TEST_EVENTS.push(event(localDateISO(d),10));
state.vialRecords=[];
let plan={id:'p',noCycle:false,unitsPerMl:100,discardAfterDays:42};
let usage={valid:true,mode:'cycle',cycleNumber:1,openings:[]};
let c=cycleVialScheduleComputation(plan,usage,0);
assert(c.rows.length>=2,'constant schedule should require multiple vials');
assert(c.rows[0].fullDoseCount===10&&c.rows[1].fullDoseCount===10,'Full Dose must be identical for identical prep');
assert(c.rows[0].cycleDoseCount===10&&c.rows[1].cycleDoseCount===10,'Cycle Dose must be identical under identical dose/window conditions');
assert(c.rows[1].openDate===localDateISO(addDays(parseISO(c.rows[0].finishDate),1)),'next Open must equal prior Finish + 1 day');
TEST_PERIOD={valid:true,start:parseISO('2026-08-01'),activeEnd:parseISO('2026-10-31'),fullEnd:parseISO('2026-11-28')};
TEST_EVENTS=[];let i=0;for(let d=parseISO('2026-08-01');d<=TEST_PERIOD.activeEnd;d=addDays(d,3)){TEST_EVENTS.push(event(localDateISO(d),i<8?5:20));i++}
state.vialRecords=[];c=cycleVialScheduleComputation(plan,usage,0);
assert(c.rows[0].fullDoseCount===c.rows[1].fullDoseCount,'Full Dose must not rotate with vial row');
assert(c.rows[0].cycleDoseCount!==c.rows[1].cycleDoseCount,'Cycle Dose should reflect actual changed prescribed dose sizes');
assert(c.rows[1].openDate===localDateISO(addDays(parseISO(c.rows[0].finishDate),1)),'escalating schedule must still chain dates');
TEST_EVENTS=[];for(let d=parseISO('2026-08-01');d<=TEST_PERIOD.activeEnd;d=addDays(d,2))TEST_EVENTS.push(event(localDateISO(d),10));
state.vialRecords=[
 {id:'r1',planId:'p',source:'forecast',forecastActive:true,vialNumber:1,vialMg:100,bacWaterMl:5,finalMl:5,startDate:'2026-08-01',scheduleOpenAuto:false,openedActual:true,finishDate:'',scheduleFinishAuto:true,status:'In use'},
 {id:'r2',planId:'p',source:'forecast',forecastActive:true,vialNumber:2,vialMg:100,bacWaterMl:5,finalMl:5,startDate:'2026-10-10',scheduleOpenAuto:false,finishDate:'',scheduleFinishAuto:true,status:'Received',needDate:'2026-08-10'},
];
c=cycleVialScheduleComputation(plan,usage,0);
assert(c.rows[0].openDate==='2026-08-01','historical actual open must be retained');
assert(c.rows[1].openDate!== '2026-10-10','future stale open must not break automatic sequence');
assert(c.rows[1].openDate===localDateISO(addDays(parseISO(c.rows[0].finishDate),1)),'future row must remain synchronized');
state.vialRecords=[
 {id:'actual-a',planId:'p',source:'forecast',forecastActive:true,forecastNumber:3,vialNumber:3,vialMg:100,bacWaterMl:5,finalMl:5,startDate:'2026-08-01',scheduleOpenAuto:false,openedActual:true,status:'In use'},
 {id:'planned-old',planId:'p',source:'forecast',forecastActive:true,forecastNumber:1,vialNumber:1,vialMg:100,bacWaterMl:5,finalMl:5,startDate:'',needDate:'2026-08-02',scheduleOpenAuto:true,status:'Received'},
];
usage={valid:true,mode:'cycle',cycleNumber:1,openings:[{number:1,date:parseISO('2026-08-02')},{number:3,date:parseISO('2026-08-01')}]};
c=cycleVialScheduleComputation(plan,usage,0);
assert(c.rows[0].record?.id==='actual-a','actual chronological vial must beat coarse forecast number mapping');
TEST_PERIOD={valid:true,start:parseISO('2026-07-31'),activeEnd:parseISO('2026-10-21'),fullEnd:parseISO('2026-11-18')};
TEST_EVENTS=[];
for(let d=parseISO('2026-07-31'),off=0;d<=TEST_PERIOD.activeEnd;d=addDays(d,1),off++){
  const jsDay=d.getDay(); if(![1,3,5].includes(jsDay))continue;
  const week=Math.floor(off/7)+1; const dose=week<=2?25:week<=4?50:week===5?100:50;
  TEST_EVENTS.push(event(localDateISO(d),dose));
}
state.vialRecords=[
 {id:'nad1',planId:'nad',source:'forecast',forecastActive:true,forecastNumber:1,vialNumber:1,vialMg:500,bacWaterMl:5,finalMl:5,startDate:'2026-07-31',scheduleOpenAuto:null,finishDate:'2026-08-28',scheduleFinishAuto:false,status:'In use',needDate:'2026-07-30'},
 {id:'nad2stock',planId:'nad',source:'forecast',forecastActive:true,forecastNumber:3,vialNumber:2,vialMg:500,bacWaterMl:5,finalMl:5,startDate:'',scheduleOpenAuto:true,finishDate:'',scheduleFinishAuto:true,status:'Received',needDate:'2026-08-13'},
 {id:'nad2actual',planId:'nad',source:'forecast',forecastActive:true,forecastNumber:2,vialNumber:3,vialMg:500,bacWaterMl:5,finalMl:5,startDate:'2026-08-29',scheduleOpenAuto:false,finishDate:'',scheduleFinishAuto:true,status:'In use',needDate:'2026-09-17'},
 {id:'nadfuture',planId:'nad',source:'forecast',forecastActive:true,forecastNumber:4,vialNumber:4,vialMg:500,bacWaterMl:5,finalMl:5,startDate:'2026-10-10',scheduleOpenAuto:false,finishDate:'',scheduleFinishAuto:true,status:'Received',needDate:'2026-10-01'},
];
plan={id:'nad',noCycle:false,unitsPerMl:100,discardAfterDays:42}; usage={valid:true,mode:'cycle',cycleNumber:1,openings:[{number:1},{number:2},{number:3},{number:4}]};
c=cycleVialScheduleComputation(plan,usage,4);
const nadRows=c.rows.filter(r=>r.cycleDoseCount>0);
assert(nadRows.length===4,'NAD should resolve four usable vials');
assert(nadRows[0].finishDate==='2026-08-26','manual finish must display last counted Cycle Dose date');
assert(nadRows[1].openDate==='2026-08-29'&&nadRows[1].finishDate==='2026-09-16'&&nadRows[1].cycleDoseCount===8,'NAD actual second vial sequence mismatch');
assert(nadRows[2].openDate==='2026-09-17'&&nadRows[2].finishDate==='2026-10-09'&&nadRows[2].cycleDoseCount===10,'NAD automatic third vial sequence mismatch');
assert(nadRows[3].openDate==='2026-10-10'&&nadRows[3].finishDate==='2026-10-21'&&nadRows[3].cycleDoseCount===5,'NAD final vial cycle-boundary mismatch');
assert(new Set(nadRows.map(r=>r.fullDoseCount)).size===1&&nadRows[0].fullDoseCount===12,'NAD Full Dose must remain 12 across identical prep');
console.log(JSON.stringify({ok:true,nad:nadRows.map(r=>({open:r.openDate,finish:r.finishDate,full:r.fullDoseCount,cycle:r.cycleDoseCount}))}));
'''
Path('/tmp/v03_core_test.js').write_text(js)
subprocess.run(['node','--check','/tmp/v03_core_test.js'],check=True)
r=subprocess.run(['node','/tmp/v03_core_test.js'],capture_output=True,text=True)
print(r.stdout);print(r.stderr)
raise SystemExit(r.returncode)
