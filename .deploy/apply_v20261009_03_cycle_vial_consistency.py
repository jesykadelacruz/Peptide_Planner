from pathlib import Path

VERSION='Peptide_Planner_v20261009.03'
OLD_VERSION='Peptide_Planner_v20261009.02'
index=Path('index.html')
sw=Path('peptide-planner-sw.js')
h=index.read_text(encoding='utf-8')
s=sw.read_text(encoding='utf-8')


def rep(old,new,label,count=1):
    global h
    n=h.count(old)
    assert n==count, f'{label}: expected {count}, found {n}'
    h=h.replace(old,new,count)

rep(f'<title>{OLD_VERSION}</title>',f'<title>{VERSION}</title>','title')
rep(f'const APP_VERSION="{OLD_VERSION}";',f'const APP_VERSION="{VERSION}";','APP_VERSION')

rep('''function cycleVialPrepForDate(plan,date=new Date(),sequence=null){
  if(!plan||plan.noCycle)return null;
  const target=typeof date==="string"?parseISO(date):date;
  const position=target?protocolPositionForDate(plan,target):null;
  const resolvedSequence=Math.max(1,Math.floor(num(sequence)||num(position?.sequence)||1));
  const records=cycleVialPrepRecords(plan).filter(record=>Number(record.scheduleCycleNumber)===resolvedSequence&&num(record?.vialMg)>0&&num(record?.finalMl||record?.bacWaterMl)>0);
  const dated=records
    .map(record=>({record,date:parseISO(record.startDate||record.scheduleResolvedOpenDate||record.needDate||"")}))
    .filter(item=>item.date&&(!target||item.date<=target))
    .sort((a,b)=>a.date-b.date||Number(a.record?.scheduleRowIndex||a.record?.vialNumber||0)-Number(b.record?.scheduleRowIndex||b.record?.vialNumber||0));
  if(dated.length)return cycleVialPrepForRecord(plan,dated[dated.length-1].record);
  if(records.length)return cycleVialPrepForRecord(plan,records[0]);
  return cycleVialPrepForSequence(plan,resolvedSequence);
}''','''function cycleVialRecordHasAuthoritativeOpen(record){
  if(!record?.startDate)return false;
  if(record.openedActual===true)return true;
  if(record.openedActual===false)return false;
  const opened=parseISO(record.startDate),today=parseISO(todayISO());
  return !!(opened&&today&&opened<=today&&(record.scheduleOpenAuto===false||record.scheduleOpenAuto==null));
}
function cycleVialRecordResolvedOpenDate(record){
  if(!record)return "";
  if(cycleVialRecordHasAuthoritativeOpen(record))return String(record.startDate||"");
  return String(record.scheduleResolvedOpenDate||"");
}
function cycleVialPrepForDate(plan,date=new Date(),sequence=null){
  if(!plan||plan.noCycle)return null;
  const target=typeof date==="string"?parseISO(date):date;
  const position=target?protocolPositionForDate(plan,target):null;
  const resolvedSequence=Math.max(1,Math.floor(num(sequence)||num(position?.sequence)||1));
  const period=protocolPeriodForSequence(plan,resolvedSequence);
  const records=(state.vialRecords||[]).filter(record=>{
    if(record?.planId!==plan.id||!(num(record?.vialMg)>0&&num(record?.finalMl||record?.bacWaterMl)>0))return false;
    const mapped=Number(record.scheduleCycleNumber||0);
    if(mapped>0)return mapped===resolvedSequence;
    const resolvedOpen=parseISO(cycleVialRecordResolvedOpenDate(record));
    return !!(resolvedOpen&&period?.valid&&resolvedOpen>=period.start&&resolvedOpen<=period.activeEnd);
  });
  const dated=records
    .map(record=>({record,date:parseISO(cycleVialRecordResolvedOpenDate(record))}))
    .filter(item=>item.date&&(!target||item.date<=target))
    .sort((a,b)=>a.date-b.date||Number(a.record?.scheduleRowIndex||a.record?.vialNumber||0)-Number(b.record?.scheduleRowIndex||b.record?.vialNumber||0));
  if(dated.length)return cycleVialPrepForRecord(plan,dated[dated.length-1].record);
  const mapped=records.filter(record=>Number(record.scheduleCycleNumber)===resolvedSequence).sort((a,b)=>Number(a.scheduleRowIndex||a.vialNumber||0)-Number(b.scheduleRowIndex||b.vialNumber||0));
  if(mapped.length)return cycleVialPrepForRecord(plan,mapped[0]);
  return cycleVialPrepForSequence(plan,resolvedSequence);
}''','active vial prep resolver')

rep('''      if(!record.startDate&&state.usedVials[oldUseKey]){
        record.startDate=needDate;
        changed=true;
      }''','''      if(!record.startDate&&state.usedVials[oldUseKey]){
        record.startDate=needDate;
        if(!plan.noCycle){record.openedActual=true;record.scheduleOpenAuto=false;}
        changed=true;
      }''','legacy actual vial migration')

rep('''  }else{
    record=records.find(item=>!item.startDate&&!closed.has(String(item.status||"")));
  }''','''  }else{
    record=records.find(item=>!cycleVialRecordHasAuthoritativeOpen(item)&&!closed.has(String(item.status||"")));
  }''','open-next vial selection')

rep('''  record.startDate=localDateISO(opened);
  if(plan.noCycle){
    record.scheduleOpenAuto=false;
    record.finishDate="";
    record.scheduleFinishAuto=true;
  }
  record.statusAuto=true;''','''  record.startDate=localDateISO(opened);
  record.openedActual=true;
  record.scheduleOpenAuto=false;
  record.finishDate="";
  record.scheduleFinishAuto=true;
  record.statusAuto=true;''','actual open authority')

rep('''    const phaseCalc=phaseUnitCalculation(plan,doseMg,date,requestedCycle),units=phaseCalc.valid?phaseCalc.units:0;
    events.push({date:new Date(date.getFullYear(),date.getMonth(),date.getDate()),dateISO:localDateISO(date),units:round(units,4),doseMg,week:scheduled.week||1});''','''    const week=scheduled.week||1,config=cycleConfigForSequence(plan,requestedCycle),phase=cyclePhaseForWeek(config,week),entryMode=inferPhaseDoseEntryMode(plan,phase,date,requestedCycle);
    const enteredUnits=entryMode==="units"?enteredPlanNumber(phase?.units):null;
    const phaseCalc=phaseUnitCalculation(plan,doseMg,date,requestedCycle),units=enteredUnits!=null?enteredUnits:(phaseCalc.valid?phaseCalc.units:0);
    events.push({date:new Date(date.getFullYear(),date.getMonth(),date.getDate()),dateISO:localDateISO(date),units:round(units,4),doseMg,week,entryMode,enteredUnits});''','units-led event authority')

rep('''function cycleVialScheduleRecordPool(plan,cycleUsage,cycleNumber){
  const period=protocolPeriodForSequence(plan,cycleNumber);
  const periodStart=period?.valid?localDateISO(period.start):"";
  const periodEnd=period?.valid?localDateISO(period.fullEnd||period.activeEnd):"";
  return (state.vialRecords||[])
    .filter(record=>record?.planId===plan.id&&(record.source==="manual"||record.forecastActive||recordHasActualActivity(record)))
    .filter(record=>{
      const date=String(record.startDate||record.needDate||"");
      return date&&(!periodStart||date>=periodStart)&&(!periodEnd||date<=periodEnd);
    })
    .sort((a,b)=>String(a.needDate||a.startDate||"9999-12-31").localeCompare(String(b.needDate||b.startDate||"9999-12-31"))||Number(a.vialNumber||9999)-Number(b.vialNumber||9999));
}
function cycleVialScheduleRecordAt(plan,cycleUsage,cycleNumber,index,used,cycleRecords){
  let record=(state.vialRecords||[]).find(item=>item?.planId===plan.id&&Number(item.scheduleCycleNumber)===cycleNumber&&Number(item.scheduleRowIndex)===index)||null;
  const forecastOpening=cycleUsage?.openings?.[index-1]||null;
  if(!record&&forecastOpening){
    record=(cycleRecords||[]).find(item=>!used.has(item.id)&&item.source==="forecast"&&Number(item.forecastNumber)===Number(forecastOpening.number))||null;
  }
  if(record)used.add(record.id);
  if(!record){
    record=(cycleRecords||[]).find(item=>!used.has(item.id)&&!(Number(item.scheduleCycleNumber)>0||Number(item.scheduleRowIndex)>0))||null;
    if(record)used.add(record.id);
  }
  return {record,forecastOpening};
}''','''function cycleVialScheduleRecordPool(plan,cycleUsage,cycleNumber){
  const period=protocolPeriodForSequence(plan,cycleNumber);
  const periodStart=period?.valid?localDateISO(period.start):"";
  const periodEnd=period?.valid?localDateISO(period.fullEnd||period.activeEnd):"";
  const recordDate=record=>cycleVialRecordResolvedOpenDate(record)||String(record?.needDate||"");
  return (state.vialRecords||[])
    .filter(record=>record?.planId===plan.id&&(record.source==="manual"||record.forecastActive||recordHasActualActivity(record)))
    .filter(record=>{
      if(Number(record.scheduleCycleNumber)===cycleNumber)return true;
      if(Number(record.scheduleCycleNumber)>0)return false;
      const date=recordDate(record);
      return date&&(!periodStart||date>=periodStart)&&(!periodEnd||date<=periodEnd);
    })
    .sort((a,b)=>String(recordDate(a)||"9999-12-31").localeCompare(String(recordDate(b)||"9999-12-31"))||Number(a.vialNumber||9999)-Number(b.vialNumber||9999));
}
function cycleVialScheduleRecordAt(plan,cycleUsage,cycleNumber,index,used,cycleRecords){
  let record=(state.vialRecords||[]).find(item=>item?.planId===plan.id&&Number(item.scheduleCycleNumber)===cycleNumber&&Number(item.scheduleRowIndex)===index)||null;
  if(record)used.add(record.id);
  if(!record){
    record=(cycleRecords||[]).find(item=>!used.has(item.id)&&!(Number(item.scheduleCycleNumber)>0||Number(item.scheduleRowIndex)>0)&&cycleVialRecordHasAuthoritativeOpen(item))||null;
    if(record)used.add(record.id);
  }
  if(!record){
    record=(cycleRecords||[]).find(item=>!used.has(item.id)&&!(Number(item.scheduleCycleNumber)>0||Number(item.scheduleRowIndex)>0))||null;
    if(record)used.add(record.id);
  }
  return {record,forecastOpening:null};
}''','detailed vial record ordering')

rep('''  if(manualFinish)return {nextCursor:cursor,finishDate:manualFinishDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason:reason||"Manual finish"};''','''  if(manualFinish)return {nextCursor:cursor,finishDate:lastFullDoseDate||manualFinishDate,lastFullDoseDate,usedUnits,fullDoseCount,remainingUnits:remaining,reason:reason||"Manual finish"};''','finish follows counted dose')

rep('''    const {record,forecastOpening}=cycleVialScheduleRecordAt(plan,cycleUsage,cycleNumber,index,used,cycleRecords);
    const prep=cycleVialPrepForRecord(plan,record,previousPrep);previousPrep=prep;
    const capacityUnits=prep.finalMl>0&&unitsPerMl>0?round(prep.finalMl*unitsPerMl,6):0;
    const rowEvents=dosePlan.events.map(event=>({...event,units:prep.vialMg>0&&prep.finalMl>0&&unitsPerMl>0?round((num(event.doseMg)||0)*prep.finalMl/prep.vialMg*unitsPerMl,6):0}));''','''    const {record,forecastOpening}=cycleVialScheduleRecordAt(plan,cycleUsage,cycleNumber,index,used,cycleRecords);
    if(record){
      if(!(Number(record.scheduleCycleNumber)>0))record.scheduleCycleNumber=cycleNumber;
      if(!(Number(record.scheduleRowIndex)>0))record.scheduleRowIndex=index;
      if(record.scheduleOpenAuto==null&&!record.startDate)record.scheduleOpenAuto=true;
      if(record.scheduleFinishAuto==null&&!record.finishDate)record.scheduleFinishAuto=true;
    }
    const prep=cycleVialPrepForRecord(plan,record,previousPrep);previousPrep=prep;
    const capacityUnits=prep.finalMl>0&&unitsPerMl>0?round(prep.finalMl*unitsPerMl,6):0;
    const rowEvents=dosePlan.events.map(event=>{
      const enteredUnits=event.entryMode==="units"?enteredPlanNumber(event.enteredUnits):null;
      const units=enteredUnits!=null?enteredUnits:(prep.vialMg>0&&prep.finalMl>0&&unitsPerMl>0?round((num(event.doseMg)||0)*prep.finalMl/prep.vialMg*unitsPerMl,6):0);
      const doseMg=enteredUnits!=null&&prep.vialMg>0&&prep.finalMl>0&&unitsPerMl>0?round((enteredUnits/unitsPerMl)*(prep.vialMg/prep.finalMl),6):event.doseMg;
      return {...event,units,doseMg};
    });''','per-vial event preparation')

rep('''    const legacyManualOpen=!!(record&&record.scheduleOpenAuto==null&&record.startDate);
    const legacyManualFinish=!!(record&&record.scheduleFinishAuto==null&&record.finishDate);
    const manualOpen=!!(record&&(record.scheduleOpenAuto===false||legacyManualOpen));
    const manualFinish=!!(record&&(record.scheduleFinishAuto===false||legacyManualFinish));
    const openDate=manualOpen?String(record.startDate||""):calculatedOpenDate;''','''    const manualOpen=cycleVialRecordHasAuthoritativeOpen(record);
    const manualFinish=!!(record&&record.finishDate&&(record.scheduleFinishAuto===false||record.scheduleFinishAuto==null));
    const openDate=manualOpen?String(record.startDate||""):calculatedOpenDate;''','authoritative open rule')

rep('''      rows.push({index,cycleNumber,record,forecastNumber:forecastOpening?.number||null,projectedDate:calculatedOpenDate,calculatedOpenDate,calculatedFinishDate:"",openDate,finishDate:record?.finishDate||"",disposeDate,vialMg:prep.vialMg,waterMl:prep.waterMl,concentration:prep.concentration,unitsUsed:0,fullDoseCount:0,cycleDoseCount:0,remainingUnits:capacityUnits,lastFullDoseDate:"",status,statusKey:cycleVialScheduleStatusKey(status),autoRequired:false});''','''      rows.push({index,cycleNumber,record,forecastNumber:record?.forecastNumber||null,projectedDate:calculatedOpenDate,calculatedOpenDate,calculatedFinishDate:"",openDate,finishDate:record?.finishDate||"",disposeDate,vialMg:prep.vialMg,waterMl:prep.waterMl,concentration:prep.concentration,unitsUsed:0,fullDoseCount:0,cycleDoseCount:0,remainingUnits:capacityUnits,lastFullDoseDate:"",status,statusKey:cycleVialScheduleStatusKey(status),autoRequired:false});''','zero-use row identity')

rep('''    const automaticFinishDate=autoWindow.lastFullDoseDate||autoWindow.finishDate;
    const finishDate=manualFinish?String(record.finishDate||""):automaticFinishDate;
    const effectiveWindow=manualFinish?simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,finishDate):autoWindow;
    if(effectiveWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};''','''    const automaticFinishDate=autoWindow.lastFullDoseDate||autoWindow.finishDate;
    const requestedFinishDate=manualFinish?String(record.finishDate||""):"";
    const effectiveWindow=manualFinish?simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,requestedFinishDate):autoWindow;
    if(effectiveWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};
    const finishDate=effectiveWindow.lastFullDoseDate||effectiveWindow.finishDate||automaticFinishDate;''','effective finish date')

rep('''    const rowRequired=hadDoseAtStart;''','''    const rowRequired=cycleDoseCount>0;''','zero-use automatic vial')

rep('''    const projected=forecastOpening?.date||null;
    rows.push({
      index,cycleNumber,record,forecastNumber:forecastOpening?.number||null,projectedDate:projected?localDateISO(projected):calculatedOpenDate,''','''    rows.push({
      index,cycleNumber,record,forecastNumber:record?.forecastNumber||null,projectedDate:calculatedOpenDate,''','detailed projected opening')

rep('''function cycleConfigVialScheduleUsage(plan,sequence){
  const usage=cycleVialUsage(plan,sequence);
  if(usage?.valid&&usage.mode==="cycle")return usage;
  return {valid:true,mode:"cycle",cycleNumber:Math.max(1,Math.floor(num(sequence)||1)),wholeVials:0,openings:[],lastDoses:[]};
}''','''function cycleConfigVialScheduleUsage(plan,sequence){
  const cycleNumber=Math.max(1,Math.floor(num(sequence)||1));
  return {valid:true,mode:"cycle",cycleNumber,wholeVials:0,openings:[],lastDoses:[]};
}''','decouple coarse vial forecast')

rep('''        record.startDate=control.value||"";
        record.scheduleOpenAuto=!control.value;
        record.finishDate="";
        record.scheduleFinishAuto=true;''','''        record.startDate=control.value||"";
        const selectedOpen=parseISO(record.startDate),today=parseISO(todayISO()),actualOpen=!!(selectedOpen&&today&&selectedOpen<=today);
        record.openedActual=actualOpen;
        record.scheduleOpenAuto=!actualOpen;
        record.finishDate="";
        record.scheduleFinishAuto=true;''','open date handler')

rep('''        record.finishDate=control.value||"";
        record.scheduleFinishAuto=!control.value;''','''        record.finishDate=control.value||"";
        const selectedFinish=parseISO(record.finishDate),today=parseISO(todayISO()),actualFinish=!!(selectedFinish&&today&&selectedFinish<=today);
        record.scheduleFinishAuto=!actualFinish;''','finish date handler')

rep('''        const row=control.closest("[data-cycle-vial-row]"),dateControl=row?.querySelector("[data-cycle-vial-open-date]");
        record.startDate=control.checked?(dateControl?.value||record.startDate||todayISO()):"";
        record.statusAuto=true;updateVialRecordDerived(record,plan);syncCyclePhaseCalculationsForSequence(plan,record.scheduleCycleNumber||cycleNumber);''','''        const row=control.closest("[data-cycle-vial-row]"),dateControl=row?.querySelector("[data-cycle-vial-open-date]"),today=todayISO(),candidate=dateControl?.value||record.startDate||today,candidateDate=parseISO(candidate),todayDate=parseISO(today);
        record.startDate=control.checked&&candidateDate&&todayDate&&candidateDate<=todayDate?candidate:(control.checked?today:"");
        record.openedActual=control.checked;
        record.scheduleOpenAuto=!control.checked;
        record.finishDate="";
        record.scheduleFinishAuto=true;
        record.statusAuto=true;updateVialRecordDerived(record,plan);syncCyclePhaseCalculationsForSequence(plan,record.scheduleCycleNumber||cycleNumber);''','opened checkbox handler')

old_sw=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD_VERSION}';"
assert s.count(old_sw)==1, 'service-worker version mismatch'
s=s.replace(old_sw,f"const PEPTIDE_PLANNER_SW_VERSION='{VERSION}';",1)

index.write_text(h,encoding='utf-8')
sw.write_text(s,encoding='utf-8')
print(f'Applied {VERSION}')
