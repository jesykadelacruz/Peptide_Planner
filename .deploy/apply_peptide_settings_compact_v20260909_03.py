from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

TITLE='<title>Peptide Planner v2026.0909.04</title>'
APP='const APP_VERSION="v2026.0909.04";'
assert TITLE in html and APP in html, 'Unexpected application version'

def replace_once(old,new,label):
    global html
    count=html.count(old)
    assert count==1, f'{label}: expected 1 match, found {count}'
    html=html.replace(old,new,1)

def replace_block(start_marker,end_marker,replacement,label):
    global html
    assert html.count(start_marker)==1, f'{label}: start marker count {html.count(start_marker)}'
    start=html.index(start_marker)
    end=html.index(end_marker,start)
    html=html[:start]+replacement+'\n'+html[end:]

# Peptide Settings: preparation no longer lives here at all.
hidden='            ${!plan.noCycle?`<input type="hidden" data-simple-field="vialMg" value="${esc(plan.vialMg||"")}"><input type="hidden" data-simple-field="bacWaterMl" value="${esc(plan.bacWaterMl||"")}"><input type="hidden" data-simple-field="finalMl" value="${esc(plan.bacWaterMl||plan.finalMl||"")}">`:""}\n\n'
assert html.count(hidden)==1, f'Expected wrong hidden Peptide Settings prep block once, found {html.count(hidden)}'
html=html.replace(hidden,'',1)

# Rename the compact UI marker only; keep its UI-only sizing rules.
replace_once('/* v20260909.03 — compact Peptide Settings and cycled-treatment controls; UI dimensions only. */','/* v20260909.04 — compact treatment controls; UI dimensions only. */','compact CSS marker')

# Add cycled preparation resolvers alongside the proven continuous resolver.
insert_marker='function administrationConsumedMg(plan,record){'
assert html.count('function cycleVialPrepForSequence(')==0, 'Cycled preparation helper already exists'
helpers=r'''function cycleVialPrepRecords(plan){
  if(!plan||plan.noCycle)return [];
  return (state.vialRecords||[])
    .filter(record=>record?.planId===plan.id&&Number(record?.scheduleCycleNumber)>0)
    .sort((a,b)=>Number(a.scheduleCycleNumber||0)-Number(b.scheduleCycleNumber||0)||Number(a.scheduleRowIndex||a.vialNumber||0)-Number(b.scheduleRowIndex||b.vialNumber||0));
}
function cycleVialPrepForRecord(plan,record,fallback=null){
  const vialMg=num(record?.vialMg)>0?num(record.vialMg):(num(fallback?.vialMg)>0?num(fallback.vialMg):0);
  const waterMl=num(record?.finalMl||record?.bacWaterMl)>0?num(record.finalMl||record.bacWaterMl):(num(fallback?.waterMl)>0?num(fallback.waterMl):0);
  return {record:record||fallback?.record||null,vialMg:vialMg||0,waterMl:waterMl||0,finalMl:waterMl||0,concentration:vialMg>0&&waterMl>0?vialMg/waterMl:0};
}
function cycleVialPrepForSequence(plan,sequence=1){
  if(!plan||plan.noCycle)return null;
  const target=Math.max(1,Math.floor(num(sequence)||1)),records=cycleVialPrepRecords(plan);
  const valid=record=>num(record?.vialMg)>0&&num(record?.finalMl||record?.bacWaterMl)>0;
  const exact=records.filter(record=>Number(record.scheduleCycleNumber)===target&&valid(record));
  if(exact.length)return cycleVialPrepForRecord(plan,exact[0]);
  const prior=records.filter(record=>Number(record.scheduleCycleNumber)<target&&valid(record));
  if(prior.length)return cycleVialPrepForRecord(plan,prior[prior.length-1]);
  if(!records.length){
    const vialMg=num(plan?.vialMg),waterMl=num(plan?.finalMl||plan?.bacWaterMl);
    if(vialMg>0&&waterMl>0)return {record:null,vialMg,waterMl,finalMl:waterMl,concentration:vialMg/waterMl,legacy:true};
  }
  return null;
}
function cycleVialPrepForDate(plan,date=new Date(),sequence=null){
  if(!plan||plan.noCycle)return null;
  const target=typeof date==="string"?parseISO(date):date;
  const position=target?protocolPositionForDate(plan,target):null;
  const resolvedSequence=Math.max(1,Math.floor(num(sequence)||num(position?.sequence)||1));
  const records=cycleVialPrepRecords(plan).filter(record=>Number(record.scheduleCycleNumber)===resolvedSequence&&num(record?.vialMg)>0&&num(record?.finalMl||record?.bacWaterMl)>0);
  const dated=records
    .map(record=>({record,date:parseISO(record.startDate||record.needDate||"")}))
    .filter(item=>item.date&&(!target||item.date<=target))
    .sort((a,b)=>a.date-b.date||Number(a.record?.scheduleRowIndex||a.record?.vialNumber||0)-Number(b.record?.scheduleRowIndex||b.record?.vialNumber||0));
  if(dated.length)return cycleVialPrepForRecord(plan,dated[dated.length-1].record);
  if(records.length)return cycleVialPrepForRecord(plan,records[0]);
  return cycleVialPrepForSequence(plan,resolvedSequence);
}
function planVialPrepForDate(plan,date=new Date(),sequence=null){
  return plan?.noCycle?continuousVialPrepForDate(plan,date):cycleVialPrepForDate(plan,date,sequence);
}
'''
idx=html.index(insert_marker)
html=html[:idx]+helpers+html[idx:]

# Dose/unit conversion reads Vial Schedule preparation for cycled treatment.
replace_block('function calcUnits(plan,doseMg,date=null){','function phaseUnitCalculation',r'''function calcUnits(plan,doseMg,date=null,sequence=null){
  const prep=planVialPrepForDate(plan,date||new Date(),sequence);
  const vial=num(prep?.vialMg),ml=num(prep?.waterMl),upm=num(plan.unitsPerMl);
  if(!plan.confirmed||!doseMg||!vial||!ml||!upm)return {valid:false};
  const concentration=vial/ml,volume=doseMg/concentration,units=volume*upm;
  const warnings=[];
  if(num(plan.syringeCapacity)&&units>Number(plan.syringeCapacity))warnings.push(`Calculated ${round(units,2)} units exceeds the entered syringe capacity.`);
  if(volume>1)warnings.push(`Calculated volume is ${round(volume,3)} mL; confirm the product, route and concentration.`);
  return {valid:true,concentration,volume,units,warnings};
}''','calcUnits')
replace_block('function phaseUnitCalculation(plan,doseMg,date=null){','function simplePhaseSplitParts',r'''function phaseUnitCalculation(plan,doseMg,date=null,sequence=null){
  const prep=planVialPrepForDate(plan,date||new Date(),sequence);
  const dose=num(doseMg),vial=num(prep?.vialMg),ml=num(prep?.waterMl),upm=num(plan.unitsPerMl);
  if(dose==null||dose<0||vial==null||vial<=0||ml==null||ml<=0||upm==null||upm<=0)return {valid:false};
  const concentration=vial/ml,volume=dose/concentration,units=volume*upm;
  return {valid:true,concentration,volume,units};
}''','phaseUnitCalculation')
replace_once('function phaseUnitsFromDose(plan,doseMg){\n  const calc=phaseUnitCalculation(plan,doseMg);','function phaseUnitsFromDose(plan,doseMg,date=null,sequence=null){\n  const calc=phaseUnitCalculation(plan,doseMg,date,sequence);','phaseUnitsFromDose')
replace_block('function phaseDoseFromUnits(plan,units,date=null){','function inferPhaseDoseEntryMode',r'''function phaseDoseFromUnits(plan,units,date=null,sequence=null){
  const prep=planVialPrepForDate(plan,date||new Date(),sequence);
  const totalUnits=num(units),vial=num(prep?.vialMg),ml=num(prep?.waterMl),upm=num(plan?.unitsPerMl);
  if(totalUnits==null||totalUnits<0||vial==null||vial<=0||ml==null||ml<=0||upm==null||upm<=0)return null;
  return round((totalUnits*vial)/(ml*upm),6);
}''','phaseDoseFromUnits')
replace_once('function inferPhaseDoseEntryMode(plan,phase){','function inferPhaseDoseEntryMode(plan,phase,date=null,sequence=null){','inferPhaseDoseEntryMode signature')
replace_once('const entered=enteredPlanNumber(phase?.units),calculated=phaseUnitsFromDose(plan,phase?.doseMg);','const entered=enteredPlanNumber(phase?.units),calculated=phaseUnitsFromDose(plan,phase?.doseMg,date,sequence);','inferPhaseDoseEntryMode calculation')
replace_block('function phaseResolvedUnits(plan,phase){','function distributeSplitUnits',r'''function phaseResolvedUnits(plan,phase,date=null,sequence=null){
  const mode=inferPhaseDoseEntryMode(plan,phase,date,sequence),entered=enteredPlanNumber(phase?.units);
  if(mode==="units"&&entered!=null&&entered>=0)return round(entered,2);
  const calculated=phaseUnitsFromDose(plan,phase?.doseMg,date,sequence);
  if(calculated!=null)return calculated;
  return entered!=null&&entered>=0?round(entered,2):null;
}''','phaseResolvedUnits')
replace_block('function phaseSplitUnitValues(plan,phase){','function syncPhaseFromDose',r'''function phaseSplitUnitValues(plan,phase,date=null,sequence=null){
  const parts=simplePhaseSplitParts(phase),total=phaseResolvedUnits(plan,phase,date,sequence),existing=Array.isArray(phase?.splitUnits)?phase.splitUnits:[];
  const values=existing.slice(0,parts).map(value=>num(value));
  const complete=values.length===parts&&values.every(value=>value!=null&&value>=0);
  if(complete&&total!=null&&Math.abs(round(values.reduce((sum,value)=>sum+value,0),2)-round(total,2))<0.005)return values.map(value=>round(value,2));
  return distributeSplitUnits(total,parts);
}''','phaseSplitUnitValues')
replace_block('function syncPhaseFromDose(plan,phase){','function syncPhaseFromUnits',r'''function syncPhaseFromDose(plan,phase,date=null,sequence=null){
  phase.doseEntryMode="dose";
  const units=phaseUnitsFromDose(plan,phase?.doseMg,date,sequence);
  phase.units=units==null?"":units;
  if(phase?.splitDose)phase.splitUnits=distributeSplitUnits(units,simplePhaseSplitParts(phase));
}''','syncPhaseFromDose')
replace_block('function syncPhaseFromUnits(plan,phase){','function syncPhaseFromSplitUnits',r'''function syncPhaseFromUnits(plan,phase,date=null,sequence=null){
  phase.doseEntryMode="units";
  const units=enteredPlanNumber(phase?.units);
  if(units==null||units<0)return;
  phase.units=round(units,2);
  const dose=phaseDoseFromUnits(plan,phase.units,date,sequence);if(dose!=null)phase.doseMg=dose;
  if(phase?.splitDose)phase.splitUnits=distributeSplitUnits(phase.units,simplePhaseSplitParts(phase));
}''','syncPhaseFromUnits')
replace_block('function syncPhaseFromSplitUnits(plan,phase){','function syncPlanPhaseCalculations',r'''function syncPhaseFromSplitUnits(plan,phase,date=null,sequence=null){
  phase.doseEntryMode="units";
  const parts=simplePhaseSplitParts(phase),existing=Array.isArray(phase?.splitUnits)?phase.splitUnits:[],values=Array.from({length:parts},(_,index)=>num(existing[index]));
  if(values.some(value=>value==null||value<0))return;
  const total=round(values.reduce((sum,value)=>sum+value,0),2);phase.units=total;
  const dose=phaseDoseFromUnits(plan,total,date,sequence);if(dose!=null)phase.doseMg=dose;
}
function syncCyclePhaseCalculationsForSequence(plan,sequence){
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),config=cycleConfigForSequence(plan,resolved);if(!config)return;
  (Array.isArray(config.phases)?config.phases:[]).forEach(phase=>{
    const mode=inferPhaseDoseEntryMode(plan,phase,null,resolved);
    if(mode==="units"){
      const parts=simplePhaseSplitParts(phase),split=Array.isArray(phase.splitUnits)?phase.splitUnits.slice(0,parts):[];
      const complete=phase.splitDose&&split.length===parts&&split.every(value=>num(value)!=null&&num(value)>=0);
      if(complete)syncPhaseFromSplitUnits(plan,phase,null,resolved);else syncPhaseFromUnits(plan,phase,null,resolved);
    }else syncPhaseFromDose(plan,phase,null,resolved);
  });
}''','syncPhaseFromSplitUnits')

# Split-dose administration conversion also receives the cycled vial context.
replace_block('function administrationsForPhase(plan,phase,doseMg,units){','function scheduleAdministrations',r'''function administrationsForPhase(plan,phase,doseMg,units,date=null,sequence=null){
  const resolvedDose=num(phase?.doseMg)!=null?num(phase.doseMg):num(doseMg);
  const resolvedUnits=phaseResolvedUnits(plan,phase,date,sequence)??(num(units)!=null?round(Number(units),2):null);
  if(!phase?.splitDose){
    return [{partKey:"",partNumber:1,partCount:1,doseMg:resolvedDose,units:resolvedUnits,time:plan.injectionTime||""}];
  }
  const parts=simplePhaseSplitParts(phase),times=Array.isArray(phase.splitTimes)?phase.splitTimes:[],splitUnits=phaseSplitUnitValues(plan,phase,date,sequence);
  return Array.from({length:parts},(_,index)=>{
    const partUnits=num(splitUnits[index]),partDose=partUnits!=null?phaseDoseFromUnits(plan,partUnits,date,sequence):(resolvedDose!=null?round(Number(resolvedDose)/parts,6):null);
    return {partKey:`split-${index+1}`,partNumber:index+1,partCount:parts,doseMg:partDose,units:partUnits,time:times[index]||""};
  });
}''','administrationsForPhase')
replace_block('function cycleAdministrations(plan,config,week,doseMg,units){','function cycleScheduleLabel',r'''function cycleAdministrations(plan,config,week,doseMg,units,date=null,sequence=null){
  const phase=cyclePhaseForWeek(config,week),original=plan.injectionTime;plan.injectionTime=config?.injectionTime||original||"";
  const rows=administrationsForPhase(plan,phase,doseMg,units,date,sequence);plan.injectionTime=original;return rows;
}''','cycleAdministrations')

# Cycled schedule date calculation must use the vial preparation for that date/cycle.
old='const phase=cyclePhaseForWeek(config,week),dose=cyclePhaseDose(config,week);out.administration=true;out.doseMg=dose;out.units=phaseResolvedUnits(plan,phase);if(out.units==null){const c=calcUnits(plan,dose);out.units=c.valid?round(c.units,2):(num(plan.fixedUnits)!=null?round(Number(plan.fixedUnits),2):null);}out.administrations=cycleAdministrations(plan,config,week,out.doseMg,out.units);return out;'
new='const phase=cyclePhaseForWeek(config,week),dose=cyclePhaseDose(config,week);out.administration=true;out.doseMg=dose;out.units=phaseResolvedUnits(plan,phase,date,position.sequence);if(out.units==null){const c=calcUnits(plan,dose,date,position.sequence);out.units=c.valid?round(c.units,2):(num(plan.fixedUnits)!=null?round(Number(plan.fixedUnits),2):null);}out.administrations=cycleAdministrations(plan,config,week,out.doseMg,out.units,date,position.sequence);return out;'
replace_once(old,new,'scheduleForDate cycled conversion')

# Verification checks preparation from Vial Schedule rather than Peptide Settings for cycled plans.
old='''  if(injectable){\n    if(!(num(plan?.vialMg)>0))missing.push("vial strength");\n    if(!(num(plan?.finalMl)>0))missing.push("final prepared volume");\n    if(!(num(plan?.unitsPerMl)>0))missing.push("syringe calibration");\n    if(!(num(plan?.syringeCapacity)>0))missing.push("syringe/device capacity");\n  }'''
new='''  if(injectable){\n    const verificationSequence=plan?.noCycle?null:(isSeparateCycleStack(plan)?planCycleNumber(plan):1),verificationPrep=planVialPrepForDate(plan,new Date(),verificationSequence);\n    if(!(num(verificationPrep?.vialMg)>0))missing.push("vial strength");\n    if(!(num(verificationPrep?.finalMl)>0))missing.push("final prepared volume");\n    if(!(num(plan?.unitsPerMl)>0))missing.push("syringe calibration");\n    if(!(num(plan?.syringeCapacity)>0))missing.push("syringe/device capacity");\n  }'''
replace_once(old,new,'verification prep source')

# The live unit helper no longer queries removed Peptide Settings fields.
old='''  const vial=num(card.querySelector('[data-simple-field="vialMg"]')?.value??plan.vialMg);\n  const ml=num(card.querySelector('[data-simple-field="finalMl"]')?.value??plan.finalMl);\n  const upm=num(card.querySelector('[data-simple-field="unitsPerMl"]')?.value??plan.unitsPerMl);'''
new='''  const prep=planVialPrepForDate(plan,new Date(),plan?.noCycle?null:(isSeparateCycleStack(plan)?planCycleNumber(plan):1));\n  const vial=num(prep?.vialMg),ml=num(prep?.finalMl),upm=num(plan.unitsPerMl);'''
replace_once(old,new,'live phase unit source')

# Vial Schedule can be created before preparation exists; its dose events are mg-first.
replace_block('function cycleVialDoseEvents(plan,cycleNumber=1){','function cycleVialScheduleRecordPool',r'''function cycleVialDoseEvents(plan,cycleNumber=1){
  const unitsPerMl=num(plan?.unitsPerMl);
  if(!unitsPerMl||unitsPerMl<=0)return {valid:false,reason:"Enter syringe calibration"};
  const requestedCycle=isSeparateCycleStack(plan)?planCycleNumber(plan):Math.max(1,Math.floor(num(cycleNumber)||1));
  const period=protocolPeriodForSequence(plan,requestedCycle);
  if(!period?.valid)return {valid:false,reason:requestedCycle>1?"Enter maintenance weeks":"Enter active weeks"};
  const usageSchedule={...plan};
  if(usageSchedule.scheduleMode==="weekdays"&&!(usageSchedule.weekdays||[]).length){
    const selectedProtocol=(usageSchedule.kbProtocolOptions||[]).find(option=>option?.id===usageSchedule.cyclePreset);
    if(selectedProtocol?.scheduleMode==="weekdays"&&Array.isArray(selectedProtocol.weekdays)&&selectedProtocol.weekdays.length)usageSchedule.weekdays=clone(selectedProtocol.weekdays);
  }
  const simulation={...usageSchedule,enabled:true},cycleStart=new Date(period.start),activeEnd=new Date(period.activeEnd),activeDays=Math.max(1,dayDiff(cycleStart,activeEnd)+1),events=[];
  for(let offset=0;offset<activeDays;offset++){
    const date=addDays(cycleStart,offset),scheduled=scheduleForDate(simulation,date);
    if(!scheduled.administration)continue;
    const doseMg=num(scheduled.doseMg);
    if(doseMg==null||doseMg<=0)return {valid:false,reason:"Complete the dose/units for every active week"};
    const phaseCalc=phaseUnitCalculation(plan,doseMg,date,requestedCycle),units=phaseCalc.valid?phaseCalc.units:0;
    events.push({date:new Date(date.getFullYear(),date.getMonth(),date.getDate()),dateISO:localDateISO(date),units:round(units,4),doseMg,week:scheduled.week||1});
  }
  if(!events.length)return {valid:false,reason:"Complete the cycle schedule and dose/units"};
  const prep=cycleVialPrepForSequence(plan,requestedCycle),unitsPerVial=prep?.finalMl>0?round(prep.finalMl*unitsPerMl,6):0;
  return {valid:true,cycleNumber:requestedCycle,period,cycleStart,activeEnd,events,unitsPerVial};
}''','cycleVialDoseEvents')

# High-level cycled vial usage takes its preparation from Vial Schedule. Continuous branch is retained.
replace_block('function cycleVialUsage(plan,cycleNumber=1){','function currentVialPerCycle',r'''function cycleVialUsage(plan,cycleNumber=1){
  const unitsPerMl=num(plan.unitsPerMl);
  if(!unitsPerMl||unitsPerMl<=0)return {valid:false,reason:"Enter syringe calibration"};
  if(plan.noCycle){
    const finalMl=num(plan.finalMl);if(!finalMl||finalMl<=0)return {valid:false,reason:"Enter final prepared volume and syringe calibration"};
    const unitsPerVial=finalMl*unitsPerMl;
    let week=1;const start=parseISO(plan.startDate);
    if(start){const now=new Date(),today=new Date(now.getFullYear(),now.getMonth(),now.getDate());const elapsed=dayDiff(start,today);if(elapsed>=0)week=Math.floor(elapsed/7)+1;}
    let injectionsPerWeek=0;
    const phaseDays=phaseWeekdaysForWeek(plan,week);
    if(phaseDays!==null){if(!phaseDays.length)return {valid:false,reason:"Choose treatment days"};injectionsPerWeek=phaseDays.length;}
    else if(plan.scheduleMode==="interval"){const interval=num(plan.intervalDays);if(!interval||interval<=0)return {valid:false,reason:"Enter the treatment interval"};injectionsPerWeek=7/interval;}
    else{const days=[...new Set((plan.weekdays||[]).map(Number).filter(day=>day>=0&&day<=6))];if(!days.length)return {valid:false,reason:"Choose treatment days"};injectionsPerWeek=days.length;}
    const dose=phaseDose(plan,week),phase=phaseUnitCalculation(plan,dose),units=phase.valid?phase.units:num(plan.fixedUnits);
    if(units==null||units<=0)return {valid:false,reason:"Complete the current dose/units"};
    const injectionsPerVial=unitsPerVial/units,capacityWeeksPerVial=injectionsPerVial/injectionsPerWeek;
    let weeksPerVial=capacityWeeksPerVial;const basisDate=start||parseISO(todayISO()),disposeDate=basisDate?disposeDateFromOpen(plan,basisDate):null;
    if(basisDate&&disposeDate)weeksPerVial=Math.min(weeksPerVial,Math.max(0,dayDiff(basisDate,disposeDate)/7));
    return {valid:true,mode:"ongoing",week,unitsPerInjection:round(units,2),volumePerInjection:round(units/unitsPerMl,4),injectionsPerWeek:round(injectionsPerWeek,2),injectionsPerVial:round(injectionsPerVial,2),weeksPerVial:round(weeksPerVial,2),capacityWeeksPerVial:round(capacityWeeksPerVial,2),frequency:cycleFrequencyText(plan)};
  }
  const requestedCycle=isSeparateCycleStack(plan)?planCycleNumber(plan):Math.max(1,Math.floor(num(cycleNumber)||1));
  const period=protocolPeriodForSequence(plan,requestedCycle);
  if(!period.valid)return {valid:false,reason:requestedCycle>1?"Enter maintenance weeks":"Enter active weeks"};
  const prep=cycleVialPrepForSequence(plan,requestedCycle),finalMl=num(prep?.finalMl),unitsPerVial=finalMl>0?finalMl*unitsPerMl:0;
  if(!(finalMl>0))return {valid:true,mode:"cycle",cycleNumber:requestedCycle,cycleStart:new Date(period.start),injections:0,totalUnits:0,volumeUsed:0,vialsUsed:0,capacityWholeVials:0,wholeVials:0,discardDrivenExtraVials:0,openings:[],lastDoses:[],frequency:"Vial preparation not set",reason:"Enter Vial and Water in Vial Schedule"};
  const baseStart=parseISO(plan.startDate)||parseISO(todayISO());if(!baseStart)return {valid:false,reason:"Enter the treatment start date"};
  const usageSchedule={...plan};
  if(usageSchedule.scheduleMode==="weekdays"&&!(usageSchedule.weekdays||[]).length){const selectedProtocol=(usageSchedule.kbProtocolOptions||[]).find(option=>option?.id===usageSchedule.cyclePreset);if(selectedProtocol?.scheduleMode==="weekdays"&&Array.isArray(selectedProtocol.weekdays)&&selectedProtocol.weekdays.length)usageSchedule.weekdays=clone(selectedProtocol.weekdays);}
  const simulation={...usageSchedule,enabled:true},cycleStart=new Date(period.start),activeDays=Math.max(1,dayDiff(period.start,period.activeEnd)+1);
  let totalUnits=0,injections=0,missingDose=false,remaining=0,current=null,openedCount=0;const openings=[],lastDoses=[];
  const closeCurrent=reason=>{if(!current)return;if(current.lastDoseDate)lastDoses.push({vialNumber:current.number,date:new Date(current.lastDoseDate),doseMg:current.lastDoseMg,units:current.lastDoseUnits,cycle:requestedCycle,cycleWeek:current.lastCycleWeek,reason});current=null;remaining=0;};
  const openCurrent=(date,week,reason,isFirst)=>{openedCount+=1;const openedDate=isFirst?new Date(cycleStart.getFullYear(),cycleStart.getMonth(),cycleStart.getDate()):new Date(date.getFullYear(),date.getMonth(),date.getDate());const discardDate=disposeDateFromOpen(plan,openedDate);current={number:openedCount,openedDate,discardDate,lastDoseDate:null,lastDoseMg:null,lastDoseUnits:null,lastCycleWeek:week};remaining=unitsPerVial;openings.push({number:openedCount,date:openedDate,discardDate,cycle:requestedCycle,cycleWeek:week,reason});};
  let firstVial=true;
  for(let offset=0;offset<activeDays;offset++){
    const date=addDays(cycleStart,offset),scheduled=scheduleForDate(simulation,date);if(!scheduled.administration)continue;const phaseCalc=phaseUnitCalculation(plan,scheduled.doseMg,date,requestedCycle),units=phaseCalc.valid?phaseCalc.units:num(plan.fixedUnits);if(units==null||units<0){missingDose=true;continue}if(units===0)continue;totalUnits+=units;injections+=1;
    if(current&&current.discardDate&&date>=current.discardDate)closeCurrent("Final planned dose before the entered disposal limit");
    let need=units,safety=0;while(need>0.0000001&&safety<100){safety+=1;if(!current||remaining<=0.0000001){if(current)closeCurrent("Final planned dose before opening the next vial");openCurrent(date,scheduled.week||1,firstVial?"First planned vial for this period":"Previous vial was disposed or does not contain enough for the next planned dose",firstVial);firstVial=false;}const used=Math.min(remaining,need);remaining=round(remaining-used,6);need=round(need-used,6);current.lastDoseDate=new Date(date.getFullYear(),date.getMonth(),date.getDate());current.lastDoseMg=scheduled.doseMg;current.lastDoseUnits=round(units,2);current.lastCycleWeek=scheduled.week||1;if(remaining<=0.0000001&&need>0.0000001)closeCurrent("Vial exhausted during a planned dose");}
  }
  if(current)closeCurrent("Last planned dose in this period");if(missingDose||!injections)return {valid:false,reason:"Complete the dose/units for every active week"};
  const volumeUsed=totalUnits/unitsPerMl,vialsUsed=volumeUsed/finalMl,capacityWholeVials=vialsUsed>0?Math.ceil(vialsUsed-1e-9):0;
  return {valid:true,mode:"cycle",phase:period.kind,maintenanceCycle:period.maintenanceCycle,cycleNumber:requestedCycle,cycleStart,injections,totalUnits:round(totalUnits,2),volumeUsed:round(volumeUsed,3),vialsUsed:round(vialsUsed,2),capacityWholeVials,wholeVials:openedCount,discardDrivenExtraVials:Math.max(0,openedCount-capacityWholeVials),openings,lastDoses,frequency:cycleFrequencyText(usageSchedule)};
}''','cycleVialUsage')

# Detailed cycled Vial Schedule uses only row/prior-Vial-Schedule preparation once records exist.
replace_once('const rows=[];let cursor=0,previousFinish=localDateISO(dosePlan.period.start),required=0,index=1,previousPrep=null;','const rows=[];let cursor=0,previousFinish=localDateISO(dosePlan.period.start),required=0,index=1,previousPrep=cycleVialPrepForSequence(plan,cycleNumber);','cycle schedule initial prep')
replace_once('const prep=continuousVialPrepForRecord(plan,record,previousPrep);previousPrep=prep;','const prep=cycleVialPrepForRecord(plan,record,previousPrep);previousPrep=prep;','cycle schedule row prep')

# Newly created cycled records get their visible preparation from the computed Vial Schedule row, not Peptide Settings.
replace_once('''      vialMg:plan.vialMg||"",\n      bacWaterMl:plan.bacWaterMl||"",\n      finalMl:plan.finalMl||"",''','''      vialMg:row?.vialMg||"",\n      bacWaterMl:row?.waterMl||"",\n      finalMl:row?.waterMl||"",''','forecast record prep')
replace_once('''  record.vialMg=row?.vialMg||record.vialMg||plan.vialMg||"";\n  record.bacWaterMl=row?.waterMl||record.bacWaterMl||plan.bacWaterMl||"";\n  record.finalMl=record.bacWaterMl||record.finalMl||plan.finalMl||"";''','''  record.vialMg=row?.vialMg||record.vialMg||"";\n  record.bacWaterMl=row?.waterMl||record.bacWaterMl||"";\n  record.finalMl=record.bacWaterMl||record.finalMl||"";''','ensure cycled record prep')

# Cycle dose table and edit handlers use the cycle's Vial Schedule preparation.
replace_once('splitUnits=phaseSplitUnitValues(plan,ph),phaseDays=','splitUnits=phaseSplitUnitValues(plan,ph,null,sequence),phaseDays=','render split units sequence')
replace_once('totalUnits=phaseResolvedUnits(plan,ph);','totalUnits=phaseResolvedUnits(plan,ph,null,sequence);','render total units sequence')
replace_once('if(field==="doseMg")syncPhaseFromDose(plan,phase);','if(field==="doseMg")syncPhaseFromDose(plan,phase,null,sequence);','dose edit sequence')
replace_once('phase.units=control.value;syncPhaseFromUnits(plan,phase);','phase.units=control.value;syncPhaseFromUnits(plan,phase,null,sequence);','units edit sequence')
replace_once('phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase),parts);','phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,null,Number(control.dataset.cyclePhaseSplit)),parts);','split toggle sequence')
replace_once('phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase),parts);syncLegacyPlanFromCycleConfigs','phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,null,Number(control.dataset.cyclePhaseSplitParts)),parts);syncLegacyPlanFromCycleConfigs','split parts sequence')
replace_once('const phase=config.phases[index],parts=simplePhaseSplitParts(phase),values=phaseSplitUnitValues(plan,phase);','const phase=config.phases[index],parts=simplePhaseSplitParts(phase),sequence=Number(control.dataset.cyclePhaseSplitUnit),values=phaseSplitUnitValues(plan,phase,null,sequence);','split unit values sequence')
replace_once('syncPhaseFromSplitUnits(plan,phase);syncLegacyPlanFromCycleConfigs','syncPhaseFromSplitUnits(plan,phase,null,sequence);syncLegacyPlanFromCycleConfigs','split unit sync sequence')

# A Vial/Water edit recalculates dose-authority or units-authority values for that cycle before rerendering.
old='''        if(field==="bacWaterMl")record.finalMl=record.bacWaterMl||"";\n        updateVialRecordDerived(record,plan);\n      }\n      plan.confirmed=false;save();renderAll();'''
new='''        if(field==="bacWaterMl")record.finalMl=record.bacWaterMl||"";\n        updateVialRecordDerived(record,plan);\n        syncCyclePhaseCalculationsForSequence(plan,record.scheduleCycleNumber);\n      }\n      plan.confirmed=false;save();renderAll();'''
replace_once(old,new,'cycled vial change recalculation')

# Static requirements.
settings_start=html.index('<details class="peptide-settings"')
settings_end=html.index('</details>',settings_start)
settings=html[settings_start:settings_end]
for forbidden in ['<label>Vial (mg)</label>','<label>Water (mL)</label>','<label>Concentration (mg/mL)</label>','data-simple-field="vialMg"','data-simple-field="bacWaterMl"','data-simple-field="finalMl"']:
    assert forbidden not in settings, f'Peptide Settings still contains {forbidden}'
expected='<th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th>'
assert expected in html, 'Cycled Vial Schedule columns changed'
assert 'data-cycle-vial-field="${field}"' in html, 'Cycled Vial Schedule prep inputs missing'
assert 'function cycleVialPrepForDate(' in html and 'function syncCyclePhaseCalculationsForSequence(' in html
assert TITLE in html and APP in html, 'Runtime version changed'
assert html!=original
path.write_text(html,encoding='utf-8')
print('Corrected cycled Vial Schedule preparation source of truth')
