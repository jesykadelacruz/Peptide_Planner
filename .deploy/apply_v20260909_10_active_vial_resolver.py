from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

# Only change the cycled preparation resolver.
a=html.index('function cycleVialPrepForDate(')
b=html.index('function planVialPrepForDate(',a)
segment=html[a:b]
old='.map(record=>({record,date:parseISO(record.startDate||record.needDate||"")}))'
new='.map(record=>({record,date:parseISO(record.startDate||record.scheduleResolvedOpenDate||record.needDate||"")}))'
assert segment.count(old)==1, f'cycle resolver match count: {segment.count(old)}'
segment=segment.replace(old,new,1)
html=html[:a]+segment+html[b:]

# Record the calculated automatic Vial Schedule Open date as derived runtime state.
a=html.index('function cycleVialScheduleComputation(')
b=html.index('function cycleVialScheduleRows(',a)
segment=html[a:b]
old='''    const openDate=manualOpen?String(record.startDate||""):calculatedOpenDate;\n    const disposeAt=openDate?disposeDateFromOpen(plan,parseISO(openDate)):null;'''
new='''    const openDate=manualOpen?String(record.startDate||""):calculatedOpenDate;\n    if(record)record.scheduleResolvedOpenDate=openDate||"";\n    const disposeAt=openDate?disposeDateFromOpen(plan,parseISO(openDate)):null;'''
assert segment.count(old)==1, f'cycle open-date match count: {segment.count(old)}'
segment=segment.replace(old,new,1)
html=html[:a]+segment+html[b:]

assert html!=original
path.write_text(html,encoding='utf-8')
print('Aligned cycled Dose Schedule resolver with calculated active vial Open date')
