from pathlib import Path

OLD='Peptide_Planner_v20261009.05'
NEW='Peptide_Planner_v20261009.06'
index=Path('index.html')
s=index.read_text(encoding='utf-8')

assert s.count(f'<title>{OLD}</title>')==1
s=s.replace(f'<title>{OLD}</title>',f'<title>{NEW}</title>',1)
assert s.count(f'const APP_VERSION="{OLD}";')==1
s=s.replace(f'const APP_VERSION="{OLD}";',f'const APP_VERSION="{NEW}";',1)

helper='''function syncCycleVialScheduleAfterDoseEdit(plan,sequence,card=null){
  if(!plan||plan.noCycle)return null;
  const resolved=Math.max(1,Math.floor(num(sequence)||1)),config=cycleConfigForSequence(plan,resolved);if(!config)return null;
  const computed=cycleConfigVialScheduleComputation(plan,config,resolved);
  if(!card||!computed?.valid)return computed;
  const cycleCard=card.querySelector(`details[data-cycle-config="${resolved}"]`),detail=cycleCard?.querySelector("details.cycle-vial-schedule-field");if(!detail)return computed;
  const count=detail.querySelector(".cycle-subsection-count");if(count)count.textContent=String(computed.rows.length);
  const rows=new Map((computed.rows||[]).map(row=>[Number(row.index),row]));
  detail.querySelectorAll("[data-cycle-vial-row]").forEach(rowElement=>{
    const row=rows.get(Number(rowElement.dataset.cycleVialRow));if(!row)return;
    const full=rowElement.querySelector(".cycle-vial-full-dose"),cycle=rowElement.querySelector(".cycle-vial-cycle-dose"),status=rowElement.querySelector(".cycle-vial-status");
    if(full)full.textContent=String(Number(row.fullDoseCount)||0);
    if(cycle)cycle.textContent=String(Number(row.cycleDoseCount)||0);
    rowElement.querySelectorAll("[data-cycle-vial-open-date]").forEach(input=>{input.value=row.openDate||"";});
    rowElement.querySelectorAll("[data-cycle-vial-finish-date]").forEach(input=>{input.value=row.finishDate||"";});
    if(status){status.textContent=row.status||"";status.className=`cycle-vial-status cycle-vial-status-${row.statusKey||"pending"}`;}
  });
  return computed;
}
'''
needle='function syncCyclePhaseCalculationsForSequence(plan,sequence){'
assert s.count(needle)==1
s=s.replace(needle,helper+needle,1)

def insert_before(marker,needle,text,occ=1):
    global s
    pos=s.index(marker); search=pos
    for _ in range(occ):
        hit=s.index(needle,search); search=hit+len(needle)
    s=s[:hit]+text+s[hit:]

def insert_after(marker,needle,text,occ=1):
    global s
    pos=s.index(marker); search=pos
    for _ in range(occ):
        hit=s.index(needle,search); search=hit+len(needle)
    hit+=len(needle)
    s=s[:hit]+text+s[hit:]

insert_before('card.querySelectorAll("[data-cycle-phase]")','plan.confirmed=false;save();renderAll();','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_before('card.querySelectorAll("[data-cycle-phase-units]")','plan.confirmed=false;save();renderAll();','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_before('card.querySelectorAll("[data-cycle-phase-weekday]")','plan.confirmed=false;save();renderAll();','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_before('card.querySelectorAll("[data-cycle-add-phase]")','plan.confirmed=false;save();renderAll()','syncCycleVialScheduleAfterDoseEdit(plan,Number(button.dataset.cycleAddPhase));')
insert_before('card.querySelectorAll("[data-cycle-remove-phase]")','plan.confirmed=false;save();renderAll()','syncCycleVialScheduleAfterDoseEdit(plan,Number(button.dataset.cycleRemovePhase));')
marker='card.querySelectorAll("[data-cycle-phase-split]")'
insert_after(marker,'phase.splitDose=false;syncLegacyPlanFromCycleConfigs(plan);','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_after(marker,'syncLegacyPlanFromCycleConfigs(plan);','syncCycleVialScheduleAfterDoseEdit(plan,sequence);',occ=2)
insert_before('card.querySelectorAll("[data-cycle-phase-split-parts]")','plan.confirmed=false;save();renderAll()','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_before('card.querySelectorAll("[data-cycle-phase-split-unit]")','plan.confirmed=false;save();renderAll()','syncCycleVialScheduleAfterDoseEdit(plan,sequence);')
insert_before("card.querySelectorAll('[data-cycle-phase][data-cycle-phase-field=\"doseMg\"], [data-cycle-phase-units], [data-cycle-phase-split-unit]')",'plan.confirmed=false;save();','syncCycleVialScheduleAfterDoseEdit(plan,sequence,card);')

index.write_text(s,encoding='utf-8')

sw=Path('peptide-planner-sw.js')
t=sw.read_text(encoding='utf-8')
old=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD}';"
new=f"const PEPTIDE_PLANNER_SW_VERSION='{NEW}';"
assert t.count(old)==1
sw.write_text(t.replace(old,new,1),encoding='utf-8')
print(f'Applied {NEW}')
