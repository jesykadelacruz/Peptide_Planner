from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

def replace_once(old,new,label):
    global html
    count=html.count(old)
    assert count==1, f'{label}: expected one match, found {count}'
    html=html.replace(old,new,1)

replace_once('''function cyclePhaseStartOffset(config,week){
  const phase=cyclePhaseForWeek(config,week);return Math.max(0,(Math.max(1,Math.floor(enteredPlanNumber(phase?.startWeek)||1))-1)*7);
}
function cycleAdministrations(plan,config,week,doseMg,units,date=null,sequence=null){
  const phase=cyclePhaseForWeek(config,week),original=plan.injectionTime;plan.injectionTime=config?.injectionTime||original||"";
  const rows=administrationsForPhase(plan,phase,doseMg,units,date,sequence);plan.injectionTime=original;return rows;
}''','''function cyclePhaseStartOffset(config,week){
  const phase=cyclePhaseForWeek(config,week);return Math.max(0,(Math.max(1,Math.floor(enteredPlanNumber(phase?.startWeek)||1))-1)*7);
}
function cyclePhaseReferenceDate(plan,config,phase,sequence){
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),period=protocolPeriodForSequence(plan,resolved);
  if(!period?.valid)return null;
  const startWeek=Math.max(1,Math.floor(enteredPlanNumber(phase?.startWeek)||1)),endWeek=Math.max(startWeek,Math.floor(enteredPlanNumber(phase?.endWeek)||startWeek));
  const today=parseISO(localDateISO(new Date())),position=today?protocolPositionForDate(plan,today):null;
  if(position?.valid&&!position.beforeStart&&!position.washout&&!position.ended&&Number(position.sequence||1)===resolved){
    const activeWeek=Math.max(1,Math.floor(num(position.week)||1));
    if(activeWeek>=startWeek&&activeWeek<=endWeek)return today;
  }
  return addDays(period.start,(startWeek-1)*7);
}
function cyclePhaseDoseForDate(plan,phase,date,sequence,fallbackDose=null){
  const entered=enteredPlanNumber(phase?.doseMg)??enteredPlanNumber(fallbackDose);
  if(inferPhaseDoseEntryMode(plan,phase,date,sequence)!=="units")return entered;
  const units=enteredPlanNumber(phase?.units),calculated=units!=null?phaseDoseFromUnits(plan,units,date,sequence):null;
  return calculated!=null?calculated:entered;
}
function cycleAdministrations(plan,config,week,doseMg,units,date=null,sequence=null){
  const phase=cyclePhaseForWeek(config,week),resolvedDose=cyclePhaseDoseForDate(plan,phase,date,sequence,doseMg),effectivePhase=phase&&inferPhaseDoseEntryMode(plan,phase,date,sequence)==="units"?{...phase,doseMg:resolvedDose}:phase,original=plan.injectionTime;plan.injectionTime=config?.injectionTime||original||"";
  const rows=administrationsForPhase(plan,effectivePhase,resolvedDose,units,date,sequence);plan.injectionTime=original;return rows;
}''','active-week vial reference helpers')

replace_once('''function syncCyclePhaseCalculationsForSequence(plan,sequence){
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),config=cycleConfigForSequence(plan,resolved);if(!config)return;
  (Array.isArray(config.phases)?config.phases:[]).forEach(phase=>{
    const mode=inferPhaseDoseEntryMode(plan,phase,null,resolved);
    if(mode==="units"){
      const parts=simplePhaseSplitParts(phase),split=Array.isArray(phase.splitUnits)?phase.splitUnits.slice(0,parts):[];
      const complete=phase.splitDose&&split.length===parts&&split.every(value=>num(value)!=null&&num(value)>=0);
      if(complete)syncPhaseFromSplitUnits(plan,phase,null,resolved);else syncPhaseFromUnits(plan,phase,null,resolved);
    }else syncPhaseFromDose(plan,phase,null,resolved);
  });
}''','''function syncCyclePhaseCalculationsForSequence(plan,sequence){
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),config=cycleConfigForSequence(plan,resolved);if(!config)return;
  (Array.isArray(config.phases)?config.phases:[]).forEach(phase=>{
    const referenceDate=cyclePhaseReferenceDate(plan,config,phase,resolved),mode=inferPhaseDoseEntryMode(plan,phase,referenceDate,resolved);
    if(mode==="units"){
      const parts=simplePhaseSplitParts(phase),split=Array.isArray(phase.splitUnits)?phase.splitUnits.slice(0,parts):[];
      const complete=phase.splitDose&&split.length===parts&&split.every(value=>num(value)!=null&&num(value)>=0);
      if(complete)syncPhaseFromSplitUnits(plan,phase,referenceDate,resolved);else syncPhaseFromUnits(plan,phase,referenceDate,resolved);
    }else syncPhaseFromDose(plan,phase,referenceDate,resolved);
  });
}''','cycle phase reconciliation')

replace_once('''  const phase=cyclePhaseForWeek(config,week),dose=cyclePhaseDose(config,week);out.administration=true;out.doseMg=dose;out.units=phaseResolvedUnits(plan,phase,date,position.sequence);if(out.units==null){const c=calcUnits(plan,dose,date,position.sequence);out.units=c.valid?round(c.units,2):(num(plan.fixedUnits)!=null?round(Number(plan.fixedUnits),2):null);}out.administrations=cycleAdministrations(plan,config,week,out.doseMg,out.units,date,position.sequence);return out;''','''  const phase=cyclePhaseForWeek(config,week),storedDose=cyclePhaseDose(config,week),dose=cyclePhaseDoseForDate(plan,phase,date,position.sequence,storedDose);out.administration=true;out.doseMg=dose;out.units=phaseResolvedUnits(plan,phase,date,position.sequence);if(out.units==null){const c=calcUnits(plan,dose,date,position.sequence);out.units=c.valid?round(c.units,2):(num(plan.fixedUnits)!=null?round(Number(plan.fixedUnits),2):null);}out.administrations=cycleAdministrations(plan,config,week,out.doseMg,out.units,date,position.sequence);return out;''','scheduled cycled dose reconciliation')

replace_once('''  return phases.map((ph,i)=>{
    const parts=simplePhaseSplitParts(ph),splitTimes=Array.isArray(ph.splitTimes)?ph.splitTimes:[],splitUnits=phaseSplitUnitValues(plan,ph,null,sequence),phaseDays=(Array.isArray(ph.weekdays)?ph.weekdays:[]).map(Number),phaseInterval=phaseDays.length?null:(enteredPlanNumber(ph.intervalDays)??(config.scheduleMode==="interval"?enteredPlanNumber(config.intervalDays):null)),totalUnits=phaseResolvedUnits(plan,ph,null,sequence);
    return `<tr><td><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="startWeek" value="${esc(ph.startWeek)}"></td><td><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="endWeek" value="${esc(ph.endWeek)}"></td><td class="phase-interval-col"><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="intervalDays" value="${esc(phaseInterval??"")}" ${phaseDays.length?'disabled aria-label="Manual weekday selection active"':''}></td><td><input type="number" min="0" step="0.001" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="doseMg" value="${esc(ph.doseMg??"")}"></td><td><input type="number" min="0" step="0.01" data-cycle-phase-units="${sequence}" data-cycle-phase-index="${i}" value="${esc(totalUnits??"")}" aria-label="Total units"></td>''','''  return phases.map((ph,i)=>{
    const referenceDate=sequence>0?cyclePhaseReferenceDate(plan,config,ph,sequence):null,parts=simplePhaseSplitParts(ph),splitTimes=Array.isArray(ph.splitTimes)?ph.splitTimes:[],splitUnits=phaseSplitUnitValues(plan,ph,referenceDate,sequence),phaseDays=(Array.isArray(ph.weekdays)?ph.weekdays:[]).map(Number),phaseInterval=phaseDays.length?null:(enteredPlanNumber(ph.intervalDays)??(config.scheduleMode==="interval"?enteredPlanNumber(config.intervalDays):null)),totalUnits=phaseResolvedUnits(plan,ph,referenceDate,sequence),displayDose=sequence>0?cyclePhaseDoseForDate(plan,ph,referenceDate,sequence,ph.doseMg):ph.doseMg;
    return `<tr><td><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="startWeek" value="${esc(ph.startWeek)}"></td><td><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="endWeek" value="${esc(ph.endWeek)}"></td><td class="phase-interval-col"><input type="number" min="1" step="1" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="intervalDays" value="${esc(phaseInterval??"")}" ${phaseDays.length?'disabled aria-label="Manual weekday selection active"':''}></td><td><input type="number" min="0" step="0.001" data-cycle-phase="${sequence}" data-cycle-phase-index="${i}" data-cycle-phase-field="doseMg" value="${esc(displayDose??"")}"></td><td><input type="number" min="0" step="0.01" data-cycle-phase-units="${sequence}" data-cycle-phase-index="${i}" value="${esc(totalUnits??"")}" aria-label="Total units"></td>''','cycle dose schedule display')

replace_once('''      if(!config.phases[index])config.phases[index]={startWeek:1,endWeek:1,doseMg:""};const phase=config.phases[index];phase[field]=control.value;
      if(field==="doseMg")syncPhaseFromDose(plan,phase,null,sequence);
      const start=Math.max(1,Math.floor(num(phase.startWeek)||1)),end=Math.max(start,Math.floor(num(phase.endWeek)||start));phase.startWeek=start;phase.endWeek=end;config.phases.sort((a,b)=>Number(a.startWeek||1)-Number(b.startWeek||1));syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();''','''      if(!config.phases[index])config.phases[index]={startWeek:1,endWeek:1,doseMg:""};const phase=config.phases[index];phase[field]=control.value;
      const start=Math.max(1,Math.floor(num(phase.startWeek)||1)),end=Math.max(start,Math.floor(num(phase.endWeek)||start));phase.startWeek=start;phase.endWeek=end;
      const referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);
      if(field==="doseMg")syncPhaseFromDose(plan,phase,referenceDate,sequence);
      else if(field==="startWeek"||field==="endWeek"){const mode=inferPhaseDoseEntryMode(plan,phase,referenceDate,sequence);if(mode==="units")syncPhaseFromUnits(plan,phase,referenceDate,sequence);else syncPhaseFromDose(plan,phase,referenceDate,sequence);}
      config.phases.sort((a,b)=>Number(a.startWeek||1)-Number(b.startWeek||1));syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();''','cycle dose field edit')

replace_once('''      const sequence=Number(control.dataset.cyclePhaseUnits),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index];phase.units=control.value;syncPhaseFromUnits(plan,phase,null,sequence);syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();''','''      const sequence=Number(control.dataset.cyclePhaseUnits),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index],referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);phase.units=control.value;syncPhaseFromUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();''','cycle units edit')

replace_once('phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,null,Number(control.dataset.cyclePhaseSplit)),parts);','const sequence=Number(control.dataset.cyclePhaseSplit),referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,referenceDate,sequence),parts);','split toggle reconciliation')
replace_once('phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,null,Number(control.dataset.cyclePhaseSplitParts)),parts);syncLegacyPlanFromCycleConfigs','const sequence=Number(control.dataset.cyclePhaseSplitParts),referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);phase.splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,phase,referenceDate,sequence),parts);syncLegacyPlanFromCycleConfigs','split parts reconciliation')
replace_once('const phase=config.phases[index],parts=simplePhaseSplitParts(phase),sequence=Number(control.dataset.cyclePhaseSplitUnit),values=phaseSplitUnitValues(plan,phase,null,sequence);','const phase=config.phases[index],parts=simplePhaseSplitParts(phase),sequence=Number(control.dataset.cyclePhaseSplitUnit),referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence),values=phaseSplitUnitValues(plan,phase,referenceDate,sequence);','split unit display reconciliation')
replace_once('syncPhaseFromSplitUnits(plan,phase,null,sequence);syncLegacyPlanFromCycleConfigs','syncPhaseFromSplitUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs','split unit edit reconciliation')

replace_once('''        record.statusAuto=true;
        updateVialRecordDerived(record,plan);
      }
      save();renderAll();
    }));
    card.querySelectorAll("[data-cycle-vial-finish-date]")''','''        record.statusAuto=true;
        updateVialRecordDerived(record,plan);
        syncCyclePhaseCalculationsForSequence(plan,record.scheduleCycleNumber||cycleNumber);
      }
      save();renderAll();
    }));
    card.querySelectorAll("[data-cycle-vial-finish-date]")''','vial open date reconciliation')

replace_once('''        record.startDate=control.checked?(dateControl?.value||record.startDate||todayISO()):"";
        record.statusAuto=true;updateVialRecordDerived(record,plan);
      }
      save();renderAll();
    }));
    card.querySelectorAll("[data-cycle-add-vial]")''','''        record.startDate=control.checked?(dateControl?.value||record.startDate||todayISO()):"";
        record.statusAuto=true;updateVialRecordDerived(record,plan);syncCyclePhaseCalculationsForSequence(plan,record.scheduleCycleNumber||cycleNumber);
      }
      save();renderAll();
    }));
    card.querySelectorAll("[data-cycle-add-vial]")''','vial opened reconciliation')

assert html!=original
path.write_text(html,encoding='utf-8')
print('Applied active-week vial Dose Schedule reconciliation')
