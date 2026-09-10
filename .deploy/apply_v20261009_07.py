from pathlib import Path

OLD='Peptide_Planner_v20261009.06'
NEW='Peptide_Planner_v20261009.07'
index=Path('index.html')
s=index.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    assert n==1, f'{label}: expected 1 match, found {n}'
    s=s.replace(old,new,1)

once(f'<title>{OLD}</title>',f'<title>{NEW}</title>','browser title')
once(f'const APP_VERSION="{OLD}";',f'const APP_VERSION="{NEW}";','app version')

old_full='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
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
new_full='''function cycleFullDoseCountForDisplay(events,startCursor,openDate,unitsPerVial){
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
once(old_full,new_full,'Full Dose current-vial dose-pattern calculation')

once('const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,0,localDateISO(dosePlan.period.start),capacityUnits);',
     'const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits);',
     'Full Dose row reference')

once('if(current&&current.discardDate&&date>=current.discardDate)closeCurrent("Final planned dose before the entered disposal limit");',
     'if(current&&current.discardDate&&date>current.discardDate)closeCurrent("Final planned dose on or before the entered disposal limit");',
     'cycled disposal-date inclusion')

starting_helper='''function copyStartingPhaseToCycle(plan,sequence){
  const configs=ensurePlanCycleConfigs(plan),index=Math.max(2,Math.floor(Number(sequence)||2))-1;
  const first=configs[0],target=configs[index];if(!first||!target)return;
  const keepStart=target.startDate,keepAuto=target.startAuto;
  target.injectionTime=first.injectionTime;
  target.scheduleMode=first.scheduleMode;target.intervalDays=first.intervalDays;target.weekdays=clone(first.weekdays||[]);target.phases=clone(first.phases||[]);
  target.startDate=keepStart;target.startAuto=keepAuto;
  syncLegacyPlanFromCycleConfigs(plan);recalculateConfiguredCycleStarts(plan);
}
'''
copy_previous='''function copyPreviousCycleToCycle(plan,sequence){
  const configs=ensurePlanCycleConfigs(plan),targetSequence=Math.max(2,Math.floor(Number(sequence)||2)),targetIndex=targetSequence-1;
  const previous=configs[targetIndex-1],target=configs[targetIndex];if(!previous||!target)return false;
  const keepStart=target.startDate,keepAuto=target.startAuto;
  target.injectionTime=previous.injectionTime;
  target.scheduleMode=previous.scheduleMode;target.intervalDays=previous.intervalDays;target.weekdays=clone(previous.weekdays||[]);target.phases=clone(previous.phases||[]);
  target.startDate=keepStart;target.startAuto=keepAuto;
  const sourceSequence=targetSequence-1,sourceComputed=cycleConfigVialScheduleComputation(plan,previous,sourceSequence);
  const sourceRows=(sourceComputed?.rows||[]).filter(row=>num(row?.vialMg)>0&&num(row?.waterMl)>0);
  if(sourceRows.length){
    const targetUsage=cycleConfigVialScheduleUsage(plan,targetSequence),targetComputed=cycleConfigVialScheduleComputation(plan,target,targetSequence);
    const targetCount=Math.max(1,(targetComputed?.rows||[]).length);
    for(let rowIndex=1;rowIndex<=targetCount;rowIndex+=1){
      const source=sourceRows[Math.min(rowIndex-1,sourceRows.length-1)];
      let record=(state.vialRecords||[]).find(item=>item?.planId===plan.id&&Number(item.scheduleCycleNumber)===targetSequence&&Number(item.scheduleRowIndex)===rowIndex)||null;
      if(!record)record=ensureCycleVialScheduleRecord(plan,targetUsage,rowIndex,targetCount);
      if(!record)continue;
      record.scheduleCycleNumber=targetSequence;record.scheduleRowIndex=rowIndex;record.vialNumber=rowIndex;
      record.vialMg=source.vialMg;record.bacWaterMl=source.waterMl;record.finalMl=source.waterMl;
      updateVialRecordDerived(record,plan);
    }
  }
  syncCyclePhaseCalculationsForSequence(plan,targetSequence);
  syncLegacyPlanFromCycleConfigs(plan);
  syncCycleVialScheduleAfterDoseEdit(plan,targetSequence);
  return true;
}
'''
once(starting_helper,starting_helper+copy_previous,'Copy Previous Cycle helper')

old_actions='''              <div class="actions no-print"><button class="btn small" type="button" data-cycle-add-phase="${sequence}">Add dose phase</button></div>
            </div>
          </details>
          ${sequence>1?`<div class="cycle-config-actions no-print"><button class="btn small" type="button" data-copy-starting-cycle="${sequence}">Copy from Starting Phase</button></div>`:""}
'''
new_actions='''              <div class="actions no-print"><button class="btn small" type="button" data-cycle-add-phase="${sequence}">Add Dose Phase</button>${sequence>1?`<button class="btn small" type="button" data-copy-starting-cycle="${sequence}">Copy Starting Phase</button><button class="btn small" type="button" data-copy-previous-cycle="${sequence}">Copy Previous Cycle</button>`:""}</div>
            </div>
          </details>
'''
once(old_actions,new_actions,'aligned Dose Schedule action buttons')

starting_handler='''    card.querySelectorAll("[data-copy-starting-cycle]").forEach(button=>button.addEventListener("click",()=>{copyStartingPhaseToCycle(plan,button.dataset.copyStartingCycle);plan.confirmed=false;save();renderAll()}));
'''
previous_handler='''    card.querySelectorAll("[data-copy-previous-cycle]").forEach(button=>button.addEventListener("click",()=>{if(copyPreviousCycleToCycle(plan,button.dataset.copyPreviousCycle)){plan.confirmed=false;save();renderAll()}}));
'''
once(starting_handler,starting_handler+previous_handler,'Copy Previous Cycle handler')

old_mobile='''  const mobileRows=groupRows=>`<div class="cycle-vial-schedule cycle-vial-mobile-cards">${groupRows.map(row=>`<div class="cycle-vial-schedule-row" data-cycle-vial-row="${row.index}"><div class="cycle-vial-line"><strong class="cycle-vial-number">${row.index}</strong><label class="cycle-vial-dose-field"><span>Vial (mg)</span>${prepInput(row,"vialMg",row.vialMg)}</label><label class="cycle-vial-dose-field"><span>Water (mL)</span>${prepInput(row,"bacWaterMl",row.waterMl)}</label><label class="cycle-vial-dose-field"><span>mg/mL</span><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></label><label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-dose-field cycle-vial-cycle-dose-field"><span>Cycle Dose</span><div class="cycle-vial-dose-box cycle-vial-cycle-dose">${Number(row.cycleDoseCount)||0}</div></label><label class="cycle-vial-date-field"><span>Date Open</span>${dateOpenInput(row)}</label><label class="cycle-vial-date-field"><span>Date Finish</span>${dateFinishInput(row)}</label><div class="cycle-vial-status-wrap"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span></div></div>${row.index>required?`<div class="cycle-vial-row-actions no-print">${removeButton(row)}</div>`:""}</div>`).join("")}</div>`;
'''
new_mobile='''  const mobileRows=groupRows=>`<div class="cycle-vial-schedule cycle-vial-mobile-cards cycle-vial-cycled-mobile-cards">${groupRows.map(row=>`<div class="cycle-vial-schedule-row" data-cycle-vial-row="${row.index}"><div class="cycle-vial-line cycle-vial-cycled-line"><strong class="cycle-vial-number">${row.index}</strong><label class="cycle-vial-dose-field cycle-vial-prep-vial"><span>Vial (mg)</span>${prepInput(row,"vialMg",row.vialMg)}</label><label class="cycle-vial-dose-field cycle-vial-prep-water"><span>Water (mL)</span>${prepInput(row,"bacWaterMl",row.waterMl)}</label><label class="cycle-vial-dose-field cycle-vial-prep-concentration"><span>mg/mL</span><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></label><label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-dose-field cycle-vial-cycle-dose-field"><span>Cycle Dose</span><div class="cycle-vial-dose-box cycle-vial-cycle-dose">${Number(row.cycleDoseCount)||0}</div></label><label class="cycle-vial-date-field cycle-vial-open-field"><span>Date Open</span>${dateOpenInput(row)}</label><label class="cycle-vial-date-field cycle-vial-finish-field"><span>Date Finish</span>${dateFinishInput(row)}</label><div class="cycle-vial-status-wrap"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span></div></div>${row.index>required?`<div class="cycle-vial-row-actions no-print">${removeButton(row)}</div>`:""}</div>`).join("")}</div>`;
'''
once(old_mobile,new_mobile,'cycled mobile Vial Schedule markup')

mobile_css='''
/* v20261009.07 — cycled Vial Schedule mobile field order only. */
@media(max-width:760px){
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-cycled-line{
    grid-template-columns:repeat(6,minmax(0,1fr))!important;
    grid-template-areas:none!important;
    gap:7px 8px!important;
  }
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-prep-vial{grid-column:1/3!important;grid-row:1!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-prep-water{grid-column:3/5!important;grid-row:1!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-prep-concentration{grid-column:5/7!important;grid-row:1!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-full-dose-field{grid-column:1/4!important;grid-row:2!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-cycle-dose-field{grid-column:4/7!important;grid-row:2!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-open-field{grid-column:1/4!important;grid-row:3!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-finish-field{grid-column:4/7!important;grid-row:3!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-number{grid-column:1/4!important;grid-row:4!important}
  body.mobile-app #planner .cycle-vial-cycled-mobile-cards .cycle-vial-status-wrap{grid-column:4/7!important;grid-row:4!important}
}
'''
style_end=s.rfind('</style>')
assert style_end>=0
s=s[:style_end]+mobile_css+s[style_end:]
index.write_text(s,encoding='utf-8')

sw=Path('peptide-planner-sw.js')
t=sw.read_text(encoding='utf-8')
old=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD}';"
new=f"const PEPTIDE_PLANNER_SW_VERSION='{NEW}';"
assert t.count(old)==1, f'SW version match count {t.count(old)}'
sw.write_text(t.replace(old,new,1),encoding='utf-8')
print(f'Applied {NEW}')
