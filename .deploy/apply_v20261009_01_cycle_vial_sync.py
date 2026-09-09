from pathlib import Path

VERSION='Peptide_Planner_v20261009.01'
OLD_VERSION='Peptide_Planner_v20260909.12'

index=Path('index.html')
sw=Path('peptide-planner-sw.js')
h=index.read_text(encoding='utf-8')
original=h

def replace_once(old,new,label):
    global h
    count=h.count(old)
    assert count==1, f'{label}: expected 1 match, found {count}'
    h=h.replace(old,new,1)

replace_once(f'<title>{OLD_VERSION}</title>',f'<title>{VERSION}</title>','browser title')
replace_once(f'const APP_VERSION="{OLD_VERSION}";',f'const APP_VERSION="{VERSION}";','app version')
replace_once('    const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):automaticVialOpenDateForCursor(dosePlan,rowStartCursor,fallbackOpenDate);','    const calculatedOpenDate=index===1?localDateISO(dosePlan.period.start):fallbackOpenDate;','cycled sequential open date')
replace_once('''    const finishDate=manualFinish?String(record.finishDate||""):autoWindow.finishDate;
    const effectiveWindow=manualFinish?simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,finishDate):autoWindow;
    if(effectiveWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};
    const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits);
    const cycleDoseCount=vialDoseCountForDisplay(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate||null);''','''    const automaticFinishDate=autoWindow.lastFullDoseDate||autoWindow.finishDate;
    const finishDate=manualFinish?String(record.finishDate||""):automaticFinishDate;
    const effectiveWindow=manualFinish?simulateCycleVialWindow(rowEvents,rowStartCursor,openDate,capacityUnits,disposeDate,finishDate):autoWindow;
    if(effectiveWindow.invalid)return {valid:false,rows,required,reason:"A scheduled full dose is larger than the prepared vial capacity."};
    const fullDoseCount=cycleFullDoseCountForDisplay(rowEvents,0,localDateISO(dosePlan.period.start),capacityUnits);
    const cycleDoseCount=effectiveWindow.fullDoseCount;''','cycled Full Dose / Cycle Dose / Finish synchronization')
replace_once('      calculatedOpenDate,calculatedFinishDate:autoWindow.finishDate,openDate,finishDate,disposeDate,','      calculatedOpenDate,calculatedFinishDate:automaticFinishDate,openDate,finishDate,disposeDate,','cycled calculated finish date')

assert h!=original
index.write_text(h,encoding='utf-8')

s=sw.read_text(encoding='utf-8')
old=f"const PEPTIDE_PLANNER_SW_VERSION='{OLD_VERSION}';"
new=f"const PEPTIDE_PLANNER_SW_VERSION='{VERSION}';"
assert s.count(old)==1, f'service worker version: expected 1 match, found {s.count(old)}'
s=s.replace(old,new,1)
sw.write_text(s,encoding='utf-8')
print(f'Applied {VERSION}')
