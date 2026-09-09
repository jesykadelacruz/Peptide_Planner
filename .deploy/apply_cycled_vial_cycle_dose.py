from pathlib import Path
import re

path=Path('index.html')
html=path.read_text()

cycle_pat=re.compile(r'function renderCycleConfigVialSchedule\(plan,config,sequence\)\{.*?\n\}(?=\nfunction renderPeptideVialSchedule)',re.S)
continuous_pat=re.compile(r'function renderContinuousVialSchedule\(plan\)\{.*?\n\}(?=\nfunction renderContinuousDoseSchedule)',re.S)
cycle_match=cycle_pat.search(html)
continuous_match=continuous_pat.search(html)
if not cycle_match: raise SystemExit('Cycled Vial Schedule renderer not found')
if not continuous_match: raise SystemExit('Continuous Vial Schedule renderer not found')
block=cycle_match.group(0)
continuous_before=continuous_match.group(0)

old_header='<thead><tr><th>Vial #</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Open</th><th>Finish</th><th>Status</th></tr></thead>'
new_header='<thead><tr><th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th></tr></thead>'
if block.count(old_header)!=1: raise SystemExit(f'Cycled desktop header marker count: {block.count(old_header)}')
block=block.replace(old_header,new_header,1)

old_desktop='<td><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></td><td class="cycle-vial-table-date">${dateOpenInput(row)}</td>'
new_desktop='<td><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></td><td><div class="cycle-vial-dose-box cycle-vial-cycle-dose">${Number(row.cycleDoseCount)||0}</div></td><td class="cycle-vial-table-date">${dateOpenInput(row)}</td>'
if block.count(old_desktop)!=1: raise SystemExit(f'Cycled desktop Full Dose marker count: {block.count(old_desktop)}')
block=block.replace(old_desktop,new_desktop,1)

old_mobile='<label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-date-field"><span>Date Open</span>${dateOpenInput(row)}</label>'
new_mobile='<label class="cycle-vial-dose-field cycle-vial-full-dose-field"><span>Full Dose</span><div class="cycle-vial-dose-box cycle-vial-full-dose">${Number(row.fullDoseCount)||0}</div></label><label class="cycle-vial-dose-field cycle-vial-cycle-dose-field"><span>Cycle Dose</span><div class="cycle-vial-dose-box cycle-vial-cycle-dose">${Number(row.cycleDoseCount)||0}</div></label><label class="cycle-vial-date-field"><span>Date Open</span>${dateOpenInput(row)}</label>'
if block.count(old_mobile)!=1: raise SystemExit(f'Cycled mobile Full Dose marker count: {block.count(old_mobile)}')
block=block.replace(old_mobile,new_mobile,1)

if '<th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th>' not in block:
    raise SystemExit('Requested cycled desktop column order missing')
if block.count('<span>Cycle Dose</span>')!=1:
    raise SystemExit('Requested cycled mobile Cycle Dose missing')

html=html[:cycle_match.start()]+block+html[cycle_match.end():]
continuous_after=continuous_pat.search(html).group(0)
if continuous_after!=continuous_before:
    raise SystemExit('Continuous Vial Schedule changed unexpectedly')

path.write_text(html)
print('Updated Cycled Vial Schedule only')
