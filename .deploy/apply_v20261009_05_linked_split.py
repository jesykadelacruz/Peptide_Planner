from pathlib import Path
import re

OLD='Peptide_Planner_v20261009.04'
NEW='Peptide_Planner_v20261009.05'
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    n=s.count(old)
    assert n==1,f'{label}: expected 1, found {n}'
    s=s.replace(old,new,1)

def replace_function(name,new):
    global s
    m=re.search(r'function '+re.escape(name)+r'\([^\)]*\)\{',s);assert m,name
    i=m.start();k=m.end();depth=1
    while k<len(s) and depth:
        if s[k]=='{':depth+=1
        elif s[k]=='}':depth-=1
        k+=1
    s=s[:i]+new+s[k:]

def replace_line(prefix,new,label):
    global s
    pattern=re.compile(r'(?m)^'+re.escape(prefix)+r'.*$')
    matches=pattern.findall(s);assert len(matches)==1,f'{label}: {len(matches)}'
    s=pattern.sub(new,s,count=1)

rep(f'<title>{OLD}</title>',f'<title>{NEW}</title>','title')
rep(f'const APP_VERSION="{OLD}";',f'const APP_VERSION="{NEW}";','APP_VERSION')

replace_function('syncCycleDoseScheduleLinkedEdit',r'''function syncCycleDoseScheduleLinkedEdit(plan,sequence,phaseIndex,row,source,control){
  if(!plan||!control)return;
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),index=Math.max(0,Math.floor(Number(phaseIndex)||0));
  const initialConfig=cycleConfigForSequence(plan,resolved),initialPhase=initialConfig?.phases?.[index];
  if(!initialConfig||!initialPhase)return;
  const phase=clone(initialPhase),referenceDate=cyclePhaseReferenceDate(plan,initialConfig,phase,resolved),updates={};
  if(source==="dose"){
    updates.doseMg=control.value;updates.doseEntryMode="dose";
    const units=phaseUnitsFromDose(plan,control.value,referenceDate,resolved);updates.units=units==null?"":units;
    if(phase.splitDose)updates.splitUnits=distributeSplitUnits(units,simplePhaseSplitParts(phase));
  }else if(source==="units"){
    updates.doseEntryMode="units";updates.units=control.value;
    const units=enteredPlanNumber(control.value);
    if(units!=null&&units>=0){
      updates.units=round(units,2);
      const dose=phaseDoseFromUnits(plan,updates.units,referenceDate,resolved);if(dose!=null)updates.doseMg=dose;
      if(phase.splitDose)updates.splitUnits=distributeSplitUnits(updates.units,simplePhaseSplitParts(phase));
    }
  }else if(source==="split"){
    const parts=simplePhaseSplitParts(phase),splitControls=row?[...row.querySelectorAll(`[data-cycle-phase-split-unit="${resolved}"]`)]:[],existing=Array.isArray(phase.splitUnits)?phase.splitUnits:[];
    const raw=Array.from({length:parts},(_,partIndex)=>splitControls[partIndex]?splitControls[partIndex].value:(existing[partIndex]??""));
    updates.doseEntryMode="units";updates.splitUnits=raw;
    const values=raw.map(value=>num(value));
    if(values.every(value=>value!=null&&value>=0)){
      const total=round(values.reduce((sum,value)=>sum+value,0),2);updates.units=total;updates.splitUnits=values.map(value=>round(value,2));
      const dose=phaseDoseFromUnits(plan,total,referenceDate,resolved);if(dose!=null)updates.doseMg=dose;
    }
  }else return;
  const liveConfig=cycleConfigForSequence(plan,resolved),livePhase=liveConfig?.phases?.[index];if(!livePhase)return;
  Object.assign(livePhase,updates);syncLegacyPlanFromCycleConfigs(plan);
  if(!row)return;
  const doseControl=row.querySelector(`[data-cycle-phase="${resolved}"][data-cycle-phase-field="doseMg"]`),unitsControl=row.querySelector(`[data-cycle-phase-units="${resolved}"]`);
  if(source!=="dose"&&doseControl&&livePhase.doseMg!=null)doseControl.value=livePhase.doseMg;
  if(source!=="units"&&unitsControl&&livePhase.units!=null)unitsControl.value=livePhase.units;
  if(source!=="split"&&livePhase.splitDose){
    const values=Array.isArray(livePhase.splitUnits)?livePhase.splitUnits:[];
    [...row.querySelectorAll(`[data-cycle-phase-split-unit="${resolved}"]`)].forEach((input,partIndex)=>{input.value=values[partIndex]??"";});
  }
}''')

replace_function('syncCyclePhaseCalculationsForSequence',r'''function syncCyclePhaseCalculationsForSequence(plan,sequence){
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),firstConfig=cycleConfigForSequence(plan,resolved);if(!firstConfig)return;
  const count=Array.isArray(firstConfig.phases)?firstConfig.phases.length:0;
  for(let index=0;index<count;index+=1){
    const config=cycleConfigForSequence(plan,resolved),stored=config?.phases?.[index];if(!config||!stored)continue;
    const phase=clone(stored),referenceDate=cyclePhaseReferenceDate(plan,config,phase,resolved),mode=inferPhaseDoseEntryMode(plan,phase,referenceDate,resolved),updates={doseEntryMode:mode};
    if(mode==="units"){
      const parts=simplePhaseSplitParts(phase),split=Array.isArray(phase.splitUnits)?phase.splitUnits.slice(0,parts):[],complete=phase.splitDose&&split.length===parts&&split.every(value=>num(value)!=null&&num(value)>=0);
      if(complete){
        const values=split.map(value=>round(num(value),2)),total=round(values.reduce((sum,value)=>sum+value,0),2);updates.splitUnits=values;updates.units=total;
        const dose=phaseDoseFromUnits(plan,total,referenceDate,resolved);if(dose!=null)updates.doseMg=dose;
      }else{
        const units=enteredPlanNumber(phase.units);updates.units=phase.units;
        if(units!=null&&units>=0){updates.units=round(units,2);const dose=phaseDoseFromUnits(plan,updates.units,referenceDate,resolved);if(dose!=null)updates.doseMg=dose;if(phase.splitDose)updates.splitUnits=distributeSplitUnits(updates.units,parts);}
      }
    }else{
      updates.doseMg=phase.doseMg;
      const units=phaseUnitsFromDose(plan,phase.doseMg,referenceDate,resolved);updates.units=units==null?"":units;
      if(phase.splitDose)updates.splitUnits=distributeSplitUnits(units,simplePhaseSplitParts(phase));
    }
    const liveConfig=cycleConfigForSequence(plan,resolved),livePhase=liveConfig?.phases?.[index];if(livePhase)Object.assign(livePhase,updates);
  }
  syncLegacyPlanFromCycleConfigs(plan);
}''')

rep('syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"dose",control)','syncCycleDoseScheduleLinkedEdit(plan,sequence,index,control.closest("tr"),"dose",control)','dose handler')
rep('syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"units",control)','syncCycleDoseScheduleLinkedEdit(plan,sequence,index,control.closest("tr"),"units",control)','units handler')
rep('syncCycleDoseScheduleLinkedEdit(plan,config,phase,sequence,control.closest("tr"),"split",control)','syncCycleDoseScheduleLinkedEdit(plan,sequence,index,control.closest("tr"),"split",control)','split handler')
rep('syncCycleDoseScheduleLinkedEdit(plan,config,config.phases[index],sequence,control.closest("tr"),source,control);plan.confirmed=false;','syncCycleDoseScheduleLinkedEdit(plan,sequence,index,control.closest("tr"),source,control);plan.confirmed=false;save();','input persistence')

replace_line('    card.querySelectorAll("[data-cycle-phase-split]")',r'''    card.querySelectorAll("[data-cycle-phase-split]").forEach(control=>control.addEventListener("change",()=>{const sequence=Number(control.dataset.cyclePhaseSplit),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index];if(!control.checked){phase.splitDose=false;syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll();return;}const parts=Math.max(2,Math.min(10,Math.floor(num(phase.splitParts)||2))),existing=Array.isArray(phase.splitTimes)?phase.splitTimes:[],times=Array.from({length:parts},(_,i)=>existing[i]||(i===0?config.injectionTime||"":"")),snapshot={...clone(phase),splitDose:true,splitParts:parts,splitTimes:times},referenceDate=cyclePhaseReferenceDate(plan,config,snapshot,sequence),splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,snapshot,referenceDate,sequence),parts),liveConfig=cycleConfigForSequence(plan,sequence),livePhase=liveConfig?.phases?.[index];if(!livePhase)return;livePhase.splitDose=true;livePhase.splitParts=parts;livePhase.splitTimes=times;livePhase.splitUnits=splitUnits;syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll()}));''','split toggle')
replace_line('    card.querySelectorAll("[data-cycle-phase-split-parts]")',r'''    card.querySelectorAll("[data-cycle-phase-split-parts]").forEach(control=>control.addEventListener("change",()=>{const sequence=Number(control.dataset.cyclePhaseSplitParts),index=Number(control.dataset.cyclePhaseIndex),config=cycleConfigForSequence(plan,sequence);if(!config||!config.phases[index])return;const phase=config.phases[index],parts=Math.max(2,Math.min(10,Math.floor(num(control.value)||2))),existing=Array.isArray(phase.splitTimes)?phase.splitTimes:[],times=Array.from({length:parts},(_,i)=>existing[i]||(i===0?config.injectionTime||"":"")),snapshot={...clone(phase),splitDose:true,splitParts:parts,splitTimes:times},referenceDate=cyclePhaseReferenceDate(plan,config,snapshot,sequence),splitUnits=distributeSplitUnits(phaseResolvedUnits(plan,snapshot,referenceDate,sequence),parts),liveConfig=cycleConfigForSequence(plan,sequence),livePhase=liveConfig?.phases?.[index];if(!livePhase)return;livePhase.splitParts=parts;livePhase.splitDose=true;livePhase.splitTimes=times;livePhase.splitUnits=splitUnits;syncLegacyPlanFromCycleConfigs(plan);plan.confirmed=false;save();renderAll()}));''','split parts')

p.write_text(s,encoding='utf-8')
sw=Path('peptide-planner-sw.js');t=sw.read_text(encoding='utf-8')
old=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD}';";new=f"const PEPTIDE_PLANNER_SW_VERSION='{NEW}';"
assert t.count(old)==1,'service worker version'
sw.write_text(t.replace(old,new,1),encoding='utf-8')
print('Applied',NEW)
