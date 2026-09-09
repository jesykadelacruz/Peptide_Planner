from pathlib import Path

path=Path('index.html')
html=path.read_text(encoding='utf-8')
original=html

assert '<title>Peptide Planner v2026.0909.04</title>' in html
assert 'const APP_VERSION="v2026.0909.04";' in html

marker='''#planner .peptide-settings-grid label,\n#planner .cycle-config-card label,\n#planner .cycle-vial-schedule-field [data-cycle-vial-row] label{\n  min-width:0!important;\n  max-width:100%!important;\n  overflow-wrap:anywhere;\n}\n@media(max-width:760px){'''
replacement='''#planner .peptide-settings-grid label,\n#planner .cycle-config-card label,\n#planner .cycle-vial-schedule-field [data-cycle-vial-row] label{\n  min-width:0!important;\n  max-width:100%!important;\n  overflow-wrap:anywhere;\n}\n/* Keep enhanced date wrappers exactly the same height as their visible date fields. */\n#planner .cycle-config-card .date-control,\n#planner .cycle-vial-schedule-field [data-cycle-vial-row] .date-control{\n  height:36px!important;\n  min-height:36px!important;\n  max-height:36px!important;\n  block-size:36px!important;\n  box-sizing:border-box!important;\n}\n#planner .continuous-vial-schedule-field [data-continuous-vial-row] .date-control,\n#planner .continuous-vial-schedule-field [data-continuous-vial-row] .date-display{\n  height:40px!important;\n  min-height:40px!important;\n  max-height:40px!important;\n  block-size:40px!important;\n  box-sizing:border-box!important;\n}\n@media(max-width:760px){'''

assert html.count(marker)==1, f'Expected one date-control insertion marker, found {html.count(marker)}'
html=html.replace(marker,replacement,1)

assert html!=original
path.write_text(html,encoding='utf-8')
print('Aligned treatment date-control wrapper heights')
