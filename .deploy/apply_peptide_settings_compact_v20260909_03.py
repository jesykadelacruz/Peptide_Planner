from pathlib import Path

path = Path("index.html")
html = path.read_text(encoding="utf-8")
original = html

# Preserve the application/runtime version exactly. This release changes visible UI only.
original_title = '<title>Peptide Planner v2026.0909.04</title>'
original_app_version = 'const APP_VERSION="v2026.0909.04";'
assert original_title in html, "Unexpected planner title/version"
assert original_app_version in html, "Unexpected APP_VERSION"

# Remove only the visible Vial / Water / Concentration controls from Peptide Settings.
# Keep the same underlying values in hidden inputs so all existing calculations and behavior remain intact.
start_marker = '            ${!plan.noCycle?`<div><label>Vial (mg)</label>'
end_marker = '<input type="hidden" data-simple-field="finalMl" value="${esc(plan.bacWaterMl||plan.finalMl||"")}">`:""}'
assert html.count(start_marker) == 1, f"Expected one visible cycled preparation block, found {html.count(start_marker)}"
start = html.index(start_marker)
end = html.index(end_marker, start) + len(end_marker)
replacement = '            ${!plan.noCycle?`<input type="hidden" data-simple-field="vialMg" value="${esc(plan.vialMg||"")}"><input type="hidden" data-simple-field="bacWaterMl" value="${esc(plan.bacWaterMl||"")}"><input type="hidden" data-simple-field="finalMl" value="${esc(plan.bacWaterMl||plan.finalMl||"")}">`:""}'
html = html[:start] + replacement + html[end:]

# Add a class only for responsive layout targeting. No event/data attributes are changed.
dispose_old = '<div><label>Dispose by</label><div class="dispose-by-control">'
dispose_new = '<div class="peptide-settings-dispose"><label>Dispose by</label><div class="dispose-by-control">'
assert html.count(dispose_old) == 1, f"Expected one Dispose by control, found {html.count(dispose_old)}"
html = html.replace(dispose_old, dispose_new, 1)

css_marker = '/* v20260909.03 — compact Peptide Settings and cycled-treatment controls; UI dimensions only. */'
assert css_marker not in html, "Compact UI patch already present"
css = r'''

/* v20260909.03 — compact Peptide Settings and cycled-treatment controls; UI dimensions only. */
#planner .peptide-settings-grid{
  grid-template-columns:repeat(auto-fit,minmax(112px,1fr))!important;
  gap:7px!important;
  align-items:end!important;
}
#planner .peptide-settings-grid>div{
  grid-column:auto!important;
  margin-top:0!important;
  min-width:0!important;
}
#planner .peptide-settings-grid>.peptide-settings-dispose{
  grid-column:span 2!important;
}
#planner .peptide-settings-grid input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]),
#planner .peptide-settings-grid select,
#planner .cycle-config-card input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]),
#planner .cycle-config-card select,
#planner .cycle-vial-schedule-field [data-cycle-vial-row] input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]),
#planner .cycle-vial-schedule-field [data-cycle-vial-row] select,
#planner .cycle-vial-schedule-field [data-cycle-vial-row] .cycle-vial-dose-box{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  height:36px!important;
  min-height:36px!important;
  max-height:36px!important;
  block-size:36px!important;
  box-sizing:border-box!important;
  padding-top:0!important;
  padding-bottom:0!important;
  line-height:1.15!important;
  overflow:hidden!important;
}
#planner .cycle-vial-schedule-field [data-cycle-vial-row] .cycle-vial-dose-box{
  white-space:nowrap!important;
  text-overflow:ellipsis!important;
}
#planner .peptide-settings-grid label,
#planner .cycle-config-card label,
#planner .cycle-vial-schedule-field [data-cycle-vial-row] label{
  min-width:0!important;
  max-width:100%!important;
  overflow-wrap:anywhere;
}
@media(max-width:760px){
  #planner .peptide-settings-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  #planner .peptide-settings-grid>.peptide-settings-dispose{
    grid-column:1/-1!important;
  }
}
@media(max-width:420px){
  #planner .peptide-settings-grid{
    grid-template-columns:1fr!important;
  }
  #planner .peptide-settings-grid>.peptide-settings-dispose{
    grid-column:auto!important;
  }
}
'''
style_close = '</style>\n</head>'
assert html.count(style_close) == 1, f"Expected one final style close, found {html.count(style_close)}"
html = html.replace(style_close, css + '\n</style>\n</head>', 1)

# Static safety checks: visible fields removed from Peptide Settings, hidden logic state retained,
# requested cycled Vial Schedule columns retained, and runtime version left untouched.
settings_start = html.index('<details class="peptide-settings"')
settings_end = html.index('</details>', settings_start)
settings = html[settings_start:settings_end]
assert '<label>Vial (mg)</label>' not in settings
assert '<label>Water (mL)</label>' not in settings
assert '<label>Concentration (mg/mL)</label>' not in settings
assert 'type="hidden" data-simple-field="vialMg"' in settings
assert 'type="hidden" data-simple-field="bacWaterMl"' in settings
assert 'type="hidden" data-simple-field="finalMl"' in settings
expected_cycle_header = '<th>#</th><th>Vial</th><th>Water</th><th>mg/mL</th><th>Full Dose</th><th>Cycle Dose</th><th>Open</th><th>Finish</th><th>Status</th>'
assert expected_cycle_header in html, "Cycled Vial Schedule header changed unexpectedly"
assert original_title in html and original_app_version in html, "Application version changed unexpectedly"
assert html != original, "Patch made no changes"

path.write_text(html, encoding="utf-8")
print("Applied Peptide Settings visibility + compact-height UI patch")
