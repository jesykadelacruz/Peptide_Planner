from pathlib import Path

index=Path('index.html')
h=index.read_text(encoding='utf-8')
old_h=h
replacements=[
    ('<title>Peptide Planner v2026.0909.11</title>','<title>Peptide_Planner_v20260909.12</title>'),
    ('const APP_VERSION="v2026.0909.11";','const APP_VERSION="Peptide_Planner_v20260909.12";'),
]
for old,new in replacements:
    assert h.count(old)==1, f'Expected one match for {old!r}, found {h.count(old)}'
    h=h.replace(old,new,1)
assert h!=old_h
index.write_text(h,encoding='utf-8')

sw=Path('peptide-planner-sw.js')
s=sw.read_text(encoding='utf-8')
old="const PEPTIDE_PLANNER_SW_VERSION='v2026.0909.04';"
new="const PEPTIDE_PLANNER_SW_VERSION='Peptide_Planner_v20260909.12';"
assert s.count(old)==1, f'Expected one service-worker version match, found {s.count(old)}'
s=s.replace(old,new,1)
sw.write_text(s,encoding='utf-8')
print('Synchronized release naming to Peptide_Planner_v20260909.12')
