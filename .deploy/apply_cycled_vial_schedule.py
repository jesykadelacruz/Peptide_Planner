from pathlib import Path
import hashlib, re

path = Path('index.html')
html = path.read_text()
expected_before = '626109dd9fb1b2480158229f8c6e013976e24429aa69a4f2743cd5bf30b69152'
before = hashlib.sha256(html.encode()).hexdigest()
if before != expected_before:
    raise SystemExit(f'Unexpected latest index checksum: {before}')

settings_marker = '''${!plan.noCycle?`<div><label>Vial (mg)</label><input type="number" min="0" step="0.001" data-simple-field="vialMg" value="${esc(plan.vialMg||"")}"></div>
            <div><label>Water (mL)</label><input type="number" min="0" step="0.001" data-simple-field="bacWaterMl" value="${esc(plan.bacWaterMl||"")}"></div>
            <div><label>Concentration (mg/mL)</label><input type="text" data-simple-concentration readonly value="${num(plan.vialMg)>0&&num(plan.bacWaterMl)>0?esc(round(num(plan.vialMg)/num(plan.bacWaterMl),3)):""}"></div><input type="hidden" data-simple-field="finalMl" value="${esc(plan.bacWaterMl||plan.finalMl||"")}">`:""}

            <div><label>Dispose by</label><div class="dispose-by-control"><input type="number" min="1" step="1" data-simple-dispose-value value="${esc(disposeByControlValue(plan))}" aria-label="Dispose by period"><select data-simple-dispose-unit aria-label="Dispose by unit"><option value="days" ${disposeByControlUnit(plan)==="days"?"selected":""}>Days</option><option value="weeks" ${disposeByControlUnit(plan)==="weeks"?"selected":""}>Weeks</option><option value="months" ${disposeByControlUnit(plan)==="months"?"selected":""}>Months</option></select></div></div>
            ${!plan.noCycle?`<div><label>On</label><input type="number" min="1" step="1" data-plan-active-weeks value="${esc(plan.activeWeeks||1)}"></div><div><label>Off</label><input type="number" min="0" step="1" data-plan-break-weeks value="${esc(plan.breakWeeks??0)}"></div>`:""}
            <div><label>Cycles/Year</label><select data-plan-cycles-per-year>'''
if settings_marker not in html:
    raise SystemExit('Cycled Peptide Settings structure no longer matches the requested preserved layout')

cycle_pat = re.compile(r'function cycleVialScheduleComputation\(plan,cycleUsage,requestedTotal=null\)\{.*?\n\}(?=\nfunction cycleVialScheduleRows)', re.S)
if not cycle_pat.search(html):
    raise SystemExit('cycleVialScheduleComputation block not found')
new_cycle = '''function cycleVialScheduleComputation(plan,cycleUsage,requestedTotal=null){
  if(!plan||plan.noCycle||!cycleUsage?.valid||cycleUsage.mode!=="cycle")return {valid:false,rows:[],required:0,reason:cycleUsage?.reason||"Complete the cycle dose and vial inputs to calculate the vial schedule."};
  const cycleNumber=Math.max(1,Math.floor(num(cycleUsage.cycleNumber)||1));
  const dosePlan=cycleVialDoseEvents(plan,cycleNumber);
  if(!dosePlan.valid)return {valid:false,rows:[],required:0,reason:dosePlan.reason};
  const requested=Math.max(0,Math.floor(num(requestedTotal)||0));
  const cycleRecords=cycleVialScheduleRecordPool(plan,cycleUsage,cycleNumber),used=new Set();
  const rows=[];let cursor=0,previousFinish=localDateISO(dosePlan.period.start),required=0,index=1,previousPrep=null;
  const unitsPerMl=Math.max(0,num(plan?.unitsPerMl)||0);
  const maxRows=Math.max(200,requested+20);
  while(index<=maxRows){
    const {record,forecastOpening}=cycleVialScheduleRecordAt(plan,cycleUsage,cycleNumber,index,used,cycleRecords);
    const prep=continuousVialPrepForRecord(plan,record,previousPrep);previousPrep=prep;
    const capacityUnits=prep.finalMl>0&&unitsPerMl>0?round(prep.finalMl*unitsPerMl,6):0;
    const rowEvents=dosePlan.events.map(event=>({...event,units:prep.vialMg>0&&prep.finalMl>0&&unitsPerMl>0?round((num(event.doseMg)||0)*prep.finalMl/prep.vialMg*unitsPerMl,6):0}));
    const previousFinishDate=index>1&&previousFinish?parseISO(previousFinish):null;
    const rowStartCursor=cursor;
    const fallbackOpenDate=previousFinishDate?localDateISO(addDays(previousFinishDate,1)):(previousFinish||"");
    const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):automaticVialOpenDateForCursor(dosePlan,rowStartCursor,fallbackOpenDate);
    const legacyManualOpen=!!(record&&record.scheduleOpenAuto==null&&record.startDate);
    const legacyManualFinish=!!(record&&record.scheduleFinishAuto==null&&record.finishDate);
    const manualOpen=!!(record&&(record.scheduleOpenAuto===false||legacyManualOpen));
    const manualFinish=!!(record&&(record.scheduleFinishAuto===false||legacyManualFinish));
    const openDate=manualOpen?String(record.startDate||""):calculatedOpenDate;
    const disposeAt=openDate?disposeDateFromOpen(plan,parseISO(openDate)):null;
    const disposeDate=disposeAt?localDateISO(disposeAt):"";
    if(!(prep.vialMg>0&&prep.finalMl>0&&capacityUnits>0)){
      const status=cycleVialScheduleStatus(openDate,record?.finishDate||"");
      rows.push({index,cycleNumber,record,forecastNumber:forecastOpening?.number||null,projectedDate:calculatedOpenDate,calculatedOpenDate,calculatedFinishDate:"",openDate,finishDate:record?.finishDate||"",disposeDate,vialMg:prep.vialMg,waterMl:prep.waterMl,concentration:prep.concentration,unitsUsed:0,fullDoseCount:0,cycleDoseCount:0,remainingUnits:capacityUnits,lastFullDoseDate:"",status,statusKey:cycleVialScheduleStatusKey(status),autoRequired:false});
      break;
    }
    const autoWindow=simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,null);
    if(autoWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};
    const finishDate=manualFinish?String(record.finishDate||""):autoWindow.finishDate;
    const effectiveWindow=manualFinish?simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,finishDate):autoWindow;
    if(effectiveWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};
    const fullDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,null);
    const cycleDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate||null);
    const hadDoseAtStart=rowStartCursor<dosePlan.events.length;
    cursor=effectiveWindow.nextCursor;
    previousFinish=finishDate||calculatedOpenDate||previousFinish;
    const rowRequired=hadDoseAtStart;
    if(rowRequired)required=index;
    const projected=forecastOpening?.date||null;
    rows.push({
      index,cycleNumber,record,forecastNumber:forecastOpening?.number||null,projectedDate:projected?localDateISO(projected):calculatedOpenDate,
      calculatedOpenDate,calculatedFinishDate:autoWindow.finishDate,openDate,finishDate,disposeDate,
      vialMg:prep.vialMg,waterMl:prep.waterMl,concentration:prep.concentration,
      unitsUsed:effectiveWindow.usedUnits,fullDoseCount,cycleDoseCount,remainingUnits:effectiveWindow.remainingUnits,lastFullDoseDate:effectiveWindow.lastFullDoseDate,
      status:cycleVialScheduleStatus(openDate,finishDate),statusKey:cycleVialScheduleStatusKey(cycleVialScheduleStatus(openDate,finishDate)),autoRequired:rowRequired
    });
    const needMoreAutomatic=cursor<dosePlan.events.length;
    const needMoreManual=index<requested;
    if(!needMoreAutomatic&&!needMoreManual)break;
    if(!previousFinish&&needMoreAutomatic)break;
    index+=1;
  }
  return {valid:true,rows,required,reason:"",dosePlan};
}'''
html, n = cycle_pat.subn(lambda m:new_cycle, html, count=1)
if n != 1:
    raise SystemExit('cycleVialScheduleComputation replacement count mismatch')

ensure_old = '''  if(requestedTotal!==null&&requestedTotal!==undefined&&requestedTotal!==""){
    record.scheduleCycleNumber=Math.max(1,Math.floor(num(row?.cycleNumber||cycleUsage?.cycleNumber)||1));
    record.scheduleRowIndex=Math.max(1,Math.floor(num(index)||1));
  }
  updateVialRecordDerived(record,plan);'''
ensure_new = '''  if(requestedTotal!==null&&requestedTotal!==undefined&&requestedTotal!==""){
    record.scheduleCycleNumber=Math.max(1,Math.floor(num(row?.cycleNumber||cycleUsage?.cycleNumber)||1));
    record.scheduleRowIndex=Math.max(1,Math.floor(num(index)||1));
  }
  record.vialMg=row?.vialMg||record.vialMg||plan.vialMg||"";
  record.bacWaterMl=row?.waterMl||record.bacWaterMl||plan.bacWaterMl||"";
  record.finalMl=record.bacWaterMl||record.finalMl||plan.finalMl||"";
  updateVialRecordDerived(record,plan);'''
if html.count(ensure_old) != 1:
    raise SystemExit('ensureCycleVialScheduleRecord marker mismatch')
html = html.replace(ensure_old, ensure_new, 1)

render_pat = re.compile(r'function renderCycleConfigVialSchedule\(plan,config,sequence\)\{.*?\n\}(?=\nfunction renderPeptideVialSchedule)', re.S)
if not render_pat.search(html):
    raise SystemExit('renderCycleConfigVialSchedule block not found')
new_render = '''function renderCycleConfigVialSchedule(plan,config,sequence){
  const usage=cycleConfigVialScheduleUsage(plan,sequence);
  const computed=cycleConfigVialScheduleComputation(plan,config,sequence);
  const rows=computed.rows;
  const forecastRequired=usage?.valid&&usage.mode==="cycle"?Math.max(0,Math.floor(num(usage.wholeVials)||0)):0;
  const required=Math.max(computed.required,forecastRequired),rowCount=rows.length;
  const key=`${plan.id}:cycle-config:${sequence}:vial-schedule`;
  const dateOpenInput=row=>`<input type="date" aria-label="Vial ${row.index} date open" data-cycle-vial-open-date="${row.index}" data-cycle-vial-cycle="${sequence}" data-cycle-vial-config="${sequence}" value="${esc(row.openDate||"")}">`;
  const dateFinishInput=row=>`<input type="date" aria-label="Vial ${row.index} date finish" data-cycle-vial-finish-date="${row.index}" data-cycle-vial-cycle="${sequence}" data-cycle-vial-config="${sequence}" value="${esc(row.finishDate||"")}">`;
  const prepInput=(row,field,value,step="0.001")=>`<input type="number" min="0" step="${step}" data-cycle-vial-field="${field}" data-cycle-vial-index="${row.index}" data-cycle-vial-cycle="${sequence}" data-cycle-vial-config="${sequence}" value="${esc(value??"")}">`;
  const removeButton=row=>row.index>required?`<button class="btn small danger cycle-vial-remove" type="button" data-cycle-remove-vial="${sequence}" data-cycle-vial-index="${row.index}">Remove vial</button>`:"";
  const desktopRows=groupRows=>`<div class="cycle-vial-desktop-table-wrap"><table class="cycle-vial-desktop-table continuous-vial-prep-table"><thead><tr><th>Vial #</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Open</th><th>Finish</th><th>Status</th></tr></thead><tbody>${groupRows.map(row=>`<tr data-cycle-vial-row="${row.index}"><td><strong class="cycle-vial-table-number">${row.index}</strong></td><td>${prepInput(row,"vialMg",row.vialMg)}</td><td>${prepInput(row,"bacWaterMl",row.waterMl)}</td><td><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></td><td><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></td><td class="cycle-vial-table-date">${dateOpenInput(row)}</td><td class="cycle-vial-table-date">${dateFinishInput(row)}</td><td><div class="cycle-vial-table-status"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span>${removeButton(row)}</div></td></tr>`).join("")}</tbody></table></div>`;
  const mobileRows=groupRows=>`<div class="cycle-vial-schedule cycle-vial-mobile-cards">${groupRows.map(row=>`<div class="cycle-vial-schedule-row" data-cycle-vial-row="${row.index}"><div class="cycle-vial-line"><strong class="cycle-vial-number">${row.index}</strong><label class="cycle-vial-dose-field"><span>Vial (mg)</span>${prepInput(row,"vialMg",row.vialMg)}</label><label class="cycle-vial-dose-field"><span>Water (mL)</span>${prepInput(row,"bacWaterMl",row.waterMl)}</label><label class="cycle-vial-dose-field"><span>mg/mL</span><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></label><label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-date-field"><span>Date Open</span>${dateOpenInput(row)}</label><label class="cycle-vial-date-field"><span>Date Finish</span>${dateFinishInput(row)}</label><div class="cycle-vial-status-wrap"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span></div></div>${row.index>required?`<div class="cycle-vial-row-actions no-print">${removeButton(row)}</div>`:""}</div>`).join("")}</div>`;
  const renderGroup=(title,groupRows,emptyText)=>`<section class="continuous-vial-group"><div class="continuous-vial-group-heading"><strong>${esc(title)}</strong><span class="continuous-vial-group-count">${groupRows.length}</span></div>${groupRows.length?`${desktopRows(groupRows)}${mobileRows(groupRows)}`:`<div class="continuous-vial-group-empty">${esc(emptyText)}</div>`}</section>`;
  const activePendingRows=rows.filter(row=>row.status!=="Completed"),completedRows=rows.filter(row=>row.status==="Completed");
  return `<details class="span-2 cycle-vial-schedule-field cycle-subsection continuous-vial-schedule-field" data-cycle-subsection="vial-schedule" data-collapse-key="${esc(key)}"${detailOpenAttr(key,true)}>
    <summary class="cycle-subsection-summary"><strong>Vial Schedule</strong><span class="cycle-subsection-count">${rowCount}</span></summary>
    <div class="cycle-vial-schedule-body">
      ${rows.length?`${renderGroup("Active & Pending Vials",activePendingRows,"No active or pending vials.")}<div class="actions cycle-vial-schedule-actions no-print"><button class="btn small" type="button" data-cycle-add-vial="${sequence}">Add vial</button></div>${renderGroup("Completed Vials",completedRows,"No completed vials yet.")}`:`<div class="helper">${esc(computed.reason||"Complete the cycle dose and vial inputs to calculate the vial schedule.")}</div><div class="actions cycle-vial-schedule-actions no-print"><button class="btn small" type="button" data-cycle-add-vial="${sequence}">Add vial</button></div>`}
    </div>
  </details>`;
}'''
html, n = render_pat.subn(lambda m:new_render, html, count=1)
if n != 1:
    raise SystemExit('renderCycleConfigVialSchedule replacement count mismatch')

handler_anchor = '''    card.querySelectorAll("[data-cycle-vial-open-date]").forEach(control=>control.addEventListener("change",()=>{'''
if html.count(handler_anchor) != 1:
    raise SystemExit('cycle vial handler anchor mismatch')
field_handler = '''    card.querySelectorAll("[data-cycle-vial-field]").forEach(control=>control.addEventListener("change",()=>{
      const cycleNumber=Math.max(1,Number(control.dataset.cycleVialCycle)||1),index=Math.max(1,Number(control.dataset.cycleVialIndex)||1),field=String(control.dataset.cycleVialField||"");
      const configSequence=control.dataset.cycleVialConfig?Math.max(1,Number(control.dataset.cycleVialConfig)||cycleNumber):null;
      const config=configSequence?cycleConfigForSequence(plan,configSequence):null;
      const calculatedUsage=cycleVialUsage(plan,cycleNumber),usage=configSequence?cycleConfigVialScheduleUsage(plan,cycleNumber):calculatedUsage;
      if(!usage.valid)return;
      const rowCount=config?cycleConfigVialScheduleCount(config,calculatedUsage):null;
      const row=cycleVialScheduleRows(plan,usage,rowCount).find(item=>item.index===index)||null;
      let record=row?.record||null;if(!record)record=ensureCycleVialScheduleRecord(plan,usage,index,rowCount);
      if(record&&["vialMg","bacWaterMl"].includes(field)){
        record.scheduleCycleNumber=Math.max(1,Number(row?.cycleNumber||usage.cycleNumber||cycleNumber)||1);record.scheduleRowIndex=index;record.vialNumber=index;record[field]=control.value||"";
        if(field==="bacWaterMl")record.finalMl=record.bacWaterMl||"";
        updateVialRecordDerived(record,plan);
      }
      plan.confirmed=false;save();renderAll();
    }));
'''
html = html.replace(handler_anchor, field_handler + handler_anchor, 1)

header = '<th>Vial #</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Open</th><th>Finish</th><th>Status</th>'
if html.count(header) < 2:
    raise SystemExit('Continuous/cycled 8-column table parity not present')
render_block = render_pat.search(html).group(0)
if '<th>Cycle Dose</th>' in render_block or '<span>Cycle Dose</span>' in render_block:
    raise SystemExit('Legacy Cycle Dose column remains in cycled renderer')
for marker in ['data-cycle-vial-field="${field}"','<span>Vial (mg)</span>','<span>Water (mL)</span>','<span>mg/mL</span>','Active & Pending Vials','Completed Vials']:
    if marker not in render_block:
        raise SystemExit('Missing cycled continuous-parity marker: '+marker)
if settings_marker not in html:
    raise SystemExit('Peptide Settings changed unexpectedly')

path.write_text(html)
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, flags=re.I|re.S)
Path('/tmp/peptide-planner-inline.js').write_text('\n'.join(s for s in scripts if s.strip()))
print('before_sha256', before)
print('after_sha256', hashlib.sha256(html.encode()).hexdigest())
