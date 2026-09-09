from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

assert '<title>Peptide Planner v2026.0909.04</title>' in html
assert 'const APP_VERSION="v2026.0909.04";' in html

def replace_once(old,new,label):
    global html
    count=html.count(old)
    assert count==1, f'{label}: expected one match, found {count}'
    html=html.replace(old,new,1)

# Restore affected treatment-control heights to the established completed-vial Open/Finish height.
start=html.index('/* v20260909.04 — compact treatment controls; UI dimensions only. */')
end=html.index('@media(max-width:760px){',start)
segment=html[start:end]
assert segment.count('36px')==8, f'expected eight 36px compact-height values, found {segment.count("36px")}'
segment=segment.replace('36px','40px')
html=html[:start]+segment+html[end:]

# Detailed cycled Vial Schedule is authoritative for automatic vial requirements.
replace_once('''function cycleConfigVialScheduleTargetCount(config,usage){
  const forecastRequired=usage?.valid&&usage.mode==="cycle"?Math.max(0,Math.floor(num(usage.wholeVials)||0)):0;
  const stored=Math.max(0,Math.floor(num(config?.vialScheduleRowCount)||0));
  return Math.max(forecastRequired,stored);
}''','''function cycleConfigVialScheduleTargetCount(config,usage){
  const stored=Math.max(0,Math.floor(num(config?.vialScheduleRowCount)||0));
  return stored;
}''','cycled target count')

replace_once('''  const forecastRequired=usage?.valid&&usage.mode==="cycle"?Math.max(0,Math.floor(num(usage.wholeVials)||0)):0;
  const required=Math.max(computed.required,forecastRequired),rowCount=rows.length;''','''  const required=computed.required,rowCount=rows.length;''','cycled render required count')

replace_once('''      const forecastRequired=usage?.valid&&usage.mode==="cycle"?Math.max(0,Math.floor(num(usage.wholeVials)||0)):0;
      const required=Math.max(computed.required,forecastRequired),current=computed.rows.length;''','''      const required=computed.required,current=computed.rows.length;''','cycled remove required count')

replace_once('''  const forecastTotal=Math.max(0,Math.floor(num(cycleUsage.wholeVials)||0));
  const required=rows.reduce((max,row)=>row?.autoRequired?Math.max(max,Number(row.index)||0):max,0);
  const started=rows.filter(row=>row?.openDate&&row.status!=="Pending").length;
  const total=Math.max(1,forecastTotal,required,started);''','''  const required=rows.reduce((max,row)=>row?.autoRequired?Math.max(max,Number(row.index)||0):max,0);
  const started=rows.filter(row=>row?.openDate&&row.status!=="Pending").length;
  const total=Math.max(1,required,started);''','current vial total')

# Exact requested invariants.
compact=html[start:html.index('@media(max-width:760px){',start)]
assert '36px' not in compact
assert compact.count('40px')>=12
assert '<th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th>' in html
assert '<th>Vial #</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Open</th><th>Finish</th><th>Status</th>' in html
assert 'const required=computed.required,rowCount=rows.length;' in html
assert 'const required=computed.required,current=computed.rows.length;' in html
assert 'const total=Math.max(1,required,started);' in html
assert html!=original

path.write_text(html,encoding='utf-8')
print('Applied v20260909.06 height and cycled zero-dose-vial correction')
