from pathlib import Path

OLD='Peptide_Planner_v20261009.03'
NEW='Peptide_Planner_v20261009.04'
index=Path('index.html')
s=index.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global s
    c=s.count(old)
    assert c==1, f'{label}: expected 1 match, found {c}'
    s=s.replace(old,new,1)

replace_once(f'<title>{OLD}</title>',f'<title>{NEW}</title>','browser title')
replace_once(f'const APP_VERSION="{OLD}";',f'const APP_VERSION="{NEW}";','app version')
replace_once('''function syncPhaseFromSplitUnits(plan,phase,date=null,sequence=null){
  phase.doseEntryMode="units";
  const parts=simplePhaseSplitParts(phase),existing=Array.isArray(phase?.splitUnits)?phase.splitUnits:[],values=Array.from({length:parts},(_,index)=>num(existing[index]));
  if(values.some(value=>value==null||value<0))return;
  const total=round(values.reduce((sum,value)=>sum+value,0),2);phase.units=total;
  const dose=phaseDoseFromUnits(plan,total,date,sequence);if(dose!=null)phase.doseMg=dose;
}
''','''function syncPhaseFromSplitUnits(plan,phase,date=null,sequence=null){
  phase.doseEntryMode="units";
  const parts=simplePhaseSplitParts(phase),existing=Array.isArray(phase?.splitUnits)?phase.splitUnits:[],values=Array.from({length:parts},(_,index)=>num(existing[index]));
  if(values.some(value=>value==null||value<0))return;
  const total=round(values.reduce((sum,value)=>sum+value,0),2);phase.units=total;
  const dose=phaseDoseFromUnits(plan,total,date,sequence);if(dose!=null)phase.doseMg=dose;
}
function syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,row,source,control){
  if(!plan||!config||!phase||!control)return;
  const referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);
  if(source==="dose"){
    phase.doseMg=control.value;
    syncPhaseFromDose(plan,phase,referenceDate,sequence);
  }else if(source==="units"){
    phase.units=control.value;
    syncPhaseFromUnits(plan,phase,referenceDate,sequence);
  }else if(source==="split"){
    const parts=simplePhaseSplitParts(phase),splitControls=row?[...row.querySelectorAll(`[data-cycle-phase-split-unit="${sequence}"]`)]:[];
    phase.splitUnits=Array.from({length:parts},(_,index)=>splitControls[index]?splitControls[index].value:(Array.isArray(phase.splitUnits)?phase.splitUnits[index]??"":""));
    syncPhaseFromSplitUnits(plan,phase,referenceDate,sequence);
  }
  syncLegacyPlanFromCycleConfigs(plan);
  if(!row)return;
  const doseControl=row.querySelector(`[data-cycle-phase="${sequence}"][data-cycle-phase-field="doseMg"]`),unitsControl=row.querySelector(`[data-cycle-phase-units="${sequence}"]`);
  if(source!=="dose"&&doseControl&&phase.doseMg!=null)doseControl.value=phase.doseMg;
  if(source!=="units"&&unitsControl&&phase.units!=null)unitsControl.value=phase.units;
  if(source!=="split"&&phase.splitDose){
    const values=Array.isArray(phase.splitUnits)?phase.splitUnits:[];
    [...row.querySelectorAll(`[data-cycle-phase-split-unit="${sequence}"]`)].forEach((input,index)=>{input.value=values[index]??"";});
  }
}
''','linked cycled dose helper')
replace_once('''      const referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);
      if(field==="doseMg")syncPhaseFromDose(plan,phase,referenceDate,sequence);
      else if(field==="startWeek"||field==="endWeek"){const mode=inferPhaseDoseEntryMode(plan,phase,referenceDate,sequence);if(mode==="units")syncPhaseFromUnits(plan,phase,referenceDate,sequence);else syncPhaseFromDose(plan,phase,referenceDate,sequence);}
      config.phases.sort((a,b)=>Number(a.startWeek||1)-Number(b.startWeek||1));syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();
''','''      const referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);
      if(field==="doseMg"&&sequence>0)syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"dose",control);
      else if(field==="doseMg")syncPhaseFromDose(plan,phase,referenceDate,sequence);
      else if(field==="startWeek"||field==="endWeek"){const mode=inferPhaseDoseEntryMode(plan,phase,referenceDate,sequence);if(mode==="units")syncPhaseFromUnits(plan,phase,referenceDate,sequence);else syncPhaseFromDose(plan,phase,referenceDate,sequence);}
      config.phases.sort((a,b)=>Number(a.startWeek||1)-Number(b.startWeek||1));syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();
''','dose change handler')
replace_once('''    card.querySelectorAll("[data-cycle-phase-units]").forEach(control=>control.addEventListener("change",()=>{
      const sequence=Number(control.dataset.cyclePhaseUnits),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index],referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);phase.units=control.value;syncPhaseFromUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();
    }));
''','''    card.querySelectorAll("[data-cycle-phase-units]").forEach(control=>control.addEventListener("change",()=>{
      const sequence=Number(control.dataset.cyclePhaseUnits),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index],referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);
      if(sequence>0)syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"units",control);else{phase.units=control.value;syncPhaseFromUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs(plan);}
      plan.confirmed=false;save();renderAll();
    }));
''','units change handler')
replace_once('''    card.querySelectorAll("[data-cycle-phase-split-unit]").forEach(control=>control.addEventListener("change",()=>{const config=cycleConfigForSequence(plan,control.dataset.cyclePhaseSplitUnit),index=Number(control.dataset.cyclePhaseIndex),unitIndex=Number(control.dataset.cycleSplitUnitIndex);if(!config)return;const phase=config.phases[index],parts=simplePhaseSplitParts(phase),sequence=Number(control.dataset.cyclePhaseSplitUnit),referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence),values=phaseSplitUnitValues(plan,phase,referenceDate,sequence);phase.splitUnits=Array.from({length:parts},(_,i)=>values[i]??"");phase.splitUnits[unitIndex]=control.value;syncPhaseFromSplitUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll()}));
''','''    card.querySelectorAll("[data-cycle-phase-split-unit]").forEach(control=>control.addEventListener("change",()=>{const config=cycleConfigForSequence(plan,control.dataset.cyclePhaseSplitUnit),index=Number(control.dataset.cyclePhaseIndex),unitIndex=Number(control.dataset.cycleSplitUnitIndex);if(!config)return;const phase=config.phases[index],parts=simplePhaseSplitParts(phase),sequence=Number(control.dataset.cyclePhaseSplitUnit),referenceDate=cyclePhaseReferenceDate(plan,config,phase,sequence);if(sequence>0)syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"split",control);else{const values=phaseSplitUnitValues(plan,phase,referenceDate,sequence);phase.splitUnits=Array.from({length:parts},(_,i)=>values[i]??"");phase.splitUnits[unitIndex]=control.value;syncPhaseFromSplitUnits(plan,phase,referenceDate,sequence);syncLegacyPlanFromCycleConfigs(plan);}plan.confirmed=false;save();renderAll()}));
    card.querySelectorAll('[data-cycle-phase][data-cycle-phase-field="doseMg"], [data-cycle-phase-units], [data-cycle-phase-split-unit]').forEach(control=>control.addEventListener("input",()=>{
      const sequence=Number(control.dataset.cyclePhase??control.dataset.cyclePhaseUnits??control.dataset.cyclePhaseSplitUnit);if(!(sequence>0))return;const index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const source=control.dataset.cyclePhaseField==="doseMg"?"dose":control.dataset.cyclePhaseUnits!=null?"units":"split";syncCycleDoseScheduleLinkedEdit(plan,config,config.phases[index],sequence,control.closest("tr"),source,control);plan.confirmed=false;
    }));
''','split handler and live linkage')
index.write_text(s,encoding='utf-8')

sw=Path('peptide-planner-sw.js')
t=sw.read_text(encoding='utf-8')
old=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD}';"
new=f"const PEPTIDE_PLANNER_SW_VERSION='{NEW}';"
assert t.count(old)==1, f'service worker version matches: {t.count(old)}'
t=t.replace(old,new,1)
sw.write_text(t,encoding='utf-8')
print(f'Applied {NEW}')