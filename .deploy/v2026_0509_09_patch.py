from pathlib import Path
import hashlib

PATH=Path("index.html")
SOURCE_SHA="c01d27c9c8c0b09f403de09b0d5664e28af176669ac803855760495681a95f3d"
TARGET_SHA="f9805dd4fbfc4a9222aeb19fb2a785194ae4c30818e09505f0ce5fd3ba56028a"

def sha256_bytes(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()

data=PATH.read_bytes()
actual=sha256_bytes(data)
if actual==TARGET_SHA:
    print("index.html is already v2026.0509.09")
    raise SystemExit(0)
if actual!=SOURCE_SHA:
    raise SystemExit(f"Refusing patch: unexpected source SHA {actual}")

s=data.decode("utf-8")
s=s.replace('<title>Peptide Planner v2026.0509.08</title>','<title>Peptide Planner v2026.0509.09</title>',1)
s=s.replace('const APP_VERSION="v2026.0509.08";','const APP_VERSION="v2026.0509.09";',1)
release='<!-- v2026.0509.09: Continuous Vial Schedule is visually separated into Active & Pending Vials and Completed Vials; vial calculations, dates, statuses, editing, and dose-counting logic are unchanged. -->\n'
release_anchor='<!-- v2026.0509.08: Continuous Open next vial promotes the next scheduled future vial to the actual opened vial; future-dated openings no longer derive an In use status before their open date. -->\n'
if release not in s:
    if release_anchor not in s: raise SystemExit("Release-note anchor not found")
    s=s.replace(release_anchor,release_anchor+release,1)
css='/* v2026.0509.09 — continuous Vial Schedule grouping only; no vial logic changes. */\n#planner .continuous-vial-group{margin-top:10px}\n#planner .continuous-vial-group:first-child{margin-top:2px}\n#planner .continuous-vial-group-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 6px;padding:0 2px;color:var(--ink)}\n#planner .continuous-vial-group-heading strong{font-size:.82rem;font-weight:850}\n#planner .continuous-vial-group-count{min-width:24px;padding:2px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:.68rem;font-weight:850;text-align:center;box-sizing:border-box}\n#planner .continuous-vial-group-empty{padding:9px 10px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);font-size:.78rem;background:#fff}\n\n'
css_anchor='/* v2026.0209.018 desktop vial table; v017 mobile vial cards remain unchanged */'
if css not in s:
    if css_anchor not in s: raise SystemExit("CSS anchor not found")
    s=s.replace(css_anchor,css+css_anchor,1)
start=s.find('function renderContinuousVialSchedule(plan){')
end=s.find('\nfunction renderContinuousDoseSchedule(plan){',start)
if start<0 or end<0: raise SystemExit("Continuous vial renderer boundary not found")
s=s[:start]+'function renderContinuousVialSchedule(plan){\n  const computed=continuousVialScheduleComputation(plan),rows=computed.rows,required=computed.required,rowCount=rows.length,key=`${plan.id}:continuous:vial-schedule`;\n  const dateOpenInput=row=>`<input type="date" aria-label="Vial ${row.index} date open" data-continuous-vial-open-date="${row.index}" value="${esc(row.openDate||"")}">`;\n  const dateFinishInput=row=>`<input type="date" aria-label="Vial ${row.index} date finish" data-continuous-vial-finish-date="${row.index}" value="${esc(row.finishDate||"")}">`;\n  const prepInput=(row,field,value,step="0.001")=>`<input type="number" min="0" step="${step}" data-continuous-vial-field="${field}" data-continuous-vial-index="${row.index}" value="${esc(value??"")}">`;\n  const removeButton=row=>row.index>required?`<button class="btn small danger cycle-vial-remove" type="button" data-continuous-remove-vial="${row.index}">Remove vial</button>`:"";\n  const desktopRows=groupRows=>`<div class="cycle-vial-desktop-table-wrap"><table class="cycle-vial-desktop-table continuous-vial-prep-table"><thead><tr><th>Vial #</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Open</th><th>Finish</th><th>Status</th></tr></thead><tbody>${groupRows.map(row=>`<tr data-continuous-vial-row="${row.index}"><td><strong class="cycle-vial-table-number">${row.index}</strong></td><td>${prepInput(row,"vialMg",row.vialMg)}</td><td>${prepInput(row,"bacWaterMl",row.waterMl)}</td><td><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></td><td><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></td><td class="cycle-vial-table-date">${dateOpenInput(row)}</td><td class="cycle-vial-table-date">${dateFinishInput(row)}</td><td><div class="cycle-vial-table-status"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span>${removeButton(row)}</div></td></tr>`).join("")}</tbody></table></div>`;\n  const mobileRows=groupRows=>`<div class="cycle-vial-schedule cycle-vial-mobile-cards">${groupRows.map(row=>`<div class="cycle-vial-schedule-row" data-continuous-vial-row="${row.index}"><div class="cycle-vial-line"><strong class="cycle-vial-number">${row.index}</strong><label class="cycle-vial-dose-field"><span>Vial (mg)</span>${prepInput(row,"vialMg",row.vialMg)}</label><label class="cycle-vial-dose-field"><span>Water (mL)</span>${prepInput(row,"bacWaterMl",row.waterMl)}</label><label class="cycle-vial-dose-field"><span>mg/mL</span><div class="cycle-vial-dose-box">${row.concentration>0?round(row.concentration,3):"—"}</div></label><label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-date-field"><span>Date Open</span>${dateOpenInput(row)}</label><label class="cycle-vial-date-field"><span>Date Finish</span>${dateFinishInput(row)}</label><div class="cycle-vial-status-wrap"><span class="cycle-vial-status cycle-vial-status-${row.statusKey}">${esc(row.status)}</span></div></div>${row.index>required?`<div class="cycle-vial-row-actions no-print">${removeButton(row)}</div>`:""}</div>`).join("")}</div>`;\n  const renderGroup=(title,groupRows,emptyText)=>`<section class="continuous-vial-group"><div class="continuous-vial-group-heading"><strong>${esc(title)}</strong><span class="continuous-vial-group-count">${groupRows.length}</span></div>${groupRows.length?`${desktopRows(groupRows)}${mobileRows(groupRows)}`:`<div class="continuous-vial-group-empty">${esc(emptyText)}</div>`}</section>`;\n  const activePendingRows=rows.filter(row=>row.status!=="Completed"),completedRows=rows.filter(row=>row.status==="Completed");\n  return `<details class="span-2 cycle-vial-schedule-field cycle-subsection continuous-vial-schedule-field" data-cycle-subsection="vial-schedule" data-collapse-key="${esc(key)}"${detailOpenAttr(key,true)}>\n    <summary class="cycle-subsection-summary"><strong>Vial Schedule</strong><span class="cycle-subsection-count">${rowCount}</span></summary>\n    <div class="cycle-vial-schedule-body">\n      ${rows.length?`${renderGroup("Active & Pending Vials",activePendingRows,"No active or pending vials.")}<div class="actions cycle-vial-schedule-actions no-print"><button class="btn small" type="button" data-continuous-add-vial>Add vial</button></div>${renderGroup("Completed Vials",completedRows,"No completed vials yet.")}`:`<div class="helper">${esc(computed.reason||"Add Vial (mg) and Water (mL) to calculate the continuous vial schedule.")}</div><div class="actions cycle-vial-schedule-actions no-print"><button class="btn small" type="button" data-continuous-add-vial>Add vial</button></div>`}\n    </div>\n  </details>`;\n}'+s[end:]
out=s.encode("utf-8")
result=sha256_bytes(out)
if result!=TARGET_SHA:
    raise SystemExit(f"Refusing write: target SHA mismatch {result}")
PATH.write_bytes(out)
print(f"Patched index.html to v2026.0509.09 {result}")
