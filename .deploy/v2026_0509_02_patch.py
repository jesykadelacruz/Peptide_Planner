from pathlib import Path
import subprocess

path = Path('index.html')
text = path.read_text()

# Production can still be on the exact v2026.0409.04 source while the
# downloadable baseline is v2026.0509.01. Bring production through the
# already-staged v2026.0509.01 patch first, then apply this release.
if '<title>Peptide Planner v2026.0409.04</title>' in text:
    subprocess.run(['python', '.deploy/v2026_0509_01_patch.py'], check=True)
    text = path.read_text()

required = [
    '<title>Peptide Planner v2026.0509.02</title>',
    'const APP_VERSION="v2026.0509.02";',
    'data-cycle-config-field="endDate" data-cycle-sequence="0"',
    'function continuousCurrentCycleText',
    'function todayAdministrationMissed',
    'today-injection-missed',
    'signInWithPassword',
    'resetPasswordForEmail',
    'PASSWORD_RECOVERY',
    'planner_state',
    'planner_snapshots',
]

# Safe retry: if the release is already present, validate and exit without
# rewriting anything.
if '<title>Peptide Planner v2026.0509.02</title>' in text:
    missing = [m for m in required if m not in text]
    if missing:
        raise SystemExit('v2026.0509.02 detected but required markers are missing: ' + ', '.join(missing))
    print('v2026.0509.02 already applied:', len(text.encode()))
    raise SystemExit(0)

def once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    text = text.replace(old, new, 1)

once('<title>Peptide Planner v2026.0509.01</title>',
     '<title>Peptide Planner v2026.0509.02</title>\n<!-- v2026.0509.02: Continuous treatments now expose an optional end date in Cycle Settings and show Current cycle with the active continuous week; Today marks unchecked administrations as Missed in small red italic text after their scheduled date/time has passed. -->',
     'title/version')

once('const APP_VERSION="v2026.0509.01";',
     'const APP_VERSION="v2026.0509.02";',
     'APP_VERSION')

css_anchor = '''body.mobile-app .today-injection-check{
  grid-area:check!important;
  align-self:center!important;
}
'''
css_add = css_anchor + '''.today-injection-done-line{display:inline-flex;align-items:center;gap:7px}
.today-injection-check.missed{flex-direction:column;align-items:flex-start;gap:1px}
.today-injection-missed{display:block;margin-left:25px;color:var(--red);font-size:.66rem;font-style:italic;font-weight:700;line-height:1.05}
body.mobile-app .today-injection-check.missed{flex-direction:column!important;align-items:flex-end!important;gap:1px!important}
body.mobile-app .today-injection-check .today-injection-done-line{gap:5px!important}
body.mobile-app .today-injection-missed{margin-left:0!important;font-size:.62rem!important;line-height:1!important}
'''
once(css_anchor, css_add, 'Today missed CSS')

once('''function renderTodayInjections(){''', '''function todayAdministrationMissed(dateISO,time,completed,at=new Date()){
  if(completed)return false;
  const scheduledDay=parseISO(dateISO);
  if(!scheduledDay)return false;
  const today=new Date(at.getFullYear(),at.getMonth(),at.getDate());
  if(scheduledDay<today)return true;
  if(scheduledDay>today)return false;
  const match=String(time||"").match(/^(\\d{1,2}):(\\d{2})$/);
  if(!match)return false;
  const hours=Number(match[1]),minutes=Number(match[2]);
  if(!Number.isFinite(hours)||!Number.isFinite(minutes)||hours<0||hours>23||minutes<0||minutes>59)return false;
  const scheduledAt=new Date(scheduledDay.getFullYear(),scheduledDay.getMonth(),scheduledDay.getDate(),hours,minutes,0,0);
  return at>scheduledAt;
}

function renderTodayInjections(){''', 'Today missed helper')

once('''        const siteLabel=item.rotationSite
          ? `<div class="today-injection-site ${item.rotationRoute}">${item.rotationRoute==="subq"?"SubQ":"IM"} rotation · ${esc(item.rotationSite)}</div>`
          :"";
        return `<div class="today-injection-item ${item.completed?"completed":""}" style="--plan-color:${planMeta(item.plan).color}">''',
'''        const siteLabel=item.rotationSite
          ? `<div class="today-injection-site ${item.rotationRoute}">${item.rotationRoute==="subq"?"SubQ":"IM"} rotation · ${esc(item.rotationSite)}</div>`
          :"";
        const missed=todayAdministrationMissed(selectedIso,item.time,item.completed,new Date());
        return `<div class="today-injection-item ${item.completed?"completed":""}" style="--plan-color:${planMeta(item.plan).color}">''', 'Today missed calculation')

once('''          <label class="today-injection-check no-print">
            <input type="checkbox" data-dashboard-injection="${esc(item.key)}" ${item.completed?"checked":""}>
            Done
          </label>''',
'''          <label class="today-injection-check no-print ${missed?"missed":""}">
            <span class="today-injection-done-line"><input type="checkbox" data-dashboard-injection="${esc(item.key)}" ${item.completed?"checked":""}> Done</span>
            ${missed?`<small class="today-injection-missed">Missed</small>`:""}
          </label>''', 'Today missed label')

once('''              <div><label>Start date</label><input type="date" data-cycle-config-field="startDate" data-cycle-sequence="0" value="${esc(plan.startDate||"")}"></div>
              <div><label>Time</label><input type="time" data-cycle-config-field="injectionTime" data-cycle-sequence="0" value="${esc(plan.injectionTime||"")}"></div>''',
'''              <div><label>Start date</label><input type="date" data-cycle-config-field="startDate" data-cycle-sequence="0" value="${esc(plan.startDate||"")}"></div>
              <div><label>End date <span class="helper">(optional)</span></label><input type="date" data-cycle-config-field="endDate" data-cycle-sequence="0" min="${esc(plan.startDate||"")}" value="${esc(plan.endDate||"")}"><div class="helper">Leave blank for continuous treatment.</div></div>
              <div><label>Time</label><input type="time" data-cycle-config-field="injectionTime" data-cycle-sequence="0" value="${esc(plan.injectionTime||"")}"></div>''', 'Continuous end date')

once('''function renderSimplePlanner(){''', '''function continuousCurrentCycleText(plan,at=new Date()){
  const start=parseISO(plan?.startDate);
  if(!start)return "Not started";
  const day=new Date(at.getFullYear(),at.getMonth(),at.getDate());
  if(day<start)return "Not started";
  const end=plan?.endDate?parseISO(plan.endDate):null;
  if(end&&day>end)return "Ended";
  const week=Math.max(1,Math.floor(dayDiff(start,day)/7)+1);
  return `Continuous . Week ${week}`;
}

function renderSimplePlanner(){''', 'Continuous current cycle helper')

once('''              ${plan.noCycle?"":`<div class="simple-mini"><span>Vials per cycle</span><strong>${vialPerCycle.valid?`${vialPerCycle.current} of ${vialPerCycle.total}`:(cycleUsage.valid?`0 of ${Math.max(1,cycleUsage.wholeVials)}`:"Needs cycle inputs")}</strong></div>
              <div class="simple-mini"><span>Cycle count</span><strong>${annualCycleCount?`${annualCycleCount.current} of ${annualCycleCount.total}`:`0 of ${planCyclesPerYear(plan)}`}</strong></div>
              <div class="simple-mini"><span>Current cycle</span><strong>${currentPosition?.beforeStart?"Not started":currentPosition?.annualLimit?"Yearly cycle limit reached":currentPosition?.washout?"Break":(currentPosition?.sequence===1?`Starting Phase . Week ${currentPosition?.week||"—"}`:`Cycle ${currentPosition?.sequence||"—"} . Week ${currentPosition?.week||"—"}`)}</strong></div>`}''',
'''              ${plan.noCycle?`<div class="simple-mini"><span>Current cycle</span><strong>${continuousCurrentCycleText(plan,new Date())}</strong></div>`:`<div class="simple-mini"><span>Vials per cycle</span><strong>${vialPerCycle.valid?`${vialPerCycle.current} of ${vialPerCycle.total}`:(cycleUsage.valid?`0 of ${Math.max(1,cycleUsage.wholeVials)}`:"Needs cycle inputs")}</strong></div>
              <div class="simple-mini"><span>Cycle count</span><strong>${annualCycleCount?`${annualCycleCount.current} of ${annualCycleCount.total}`:`0 of ${planCyclesPerYear(plan)}`}</strong></div>
              <div class="simple-mini"><span>Current cycle</span><strong>${currentPosition?.beforeStart?"Not started":currentPosition?.annualLimit?"Yearly cycle limit reached":currentPosition?.washout?"Break":(currentPosition?.sequence===1?`Starting Phase . Week ${currentPosition?.week||"—"}`:`Cycle ${currentPosition?.sequence||"—"} . Week ${currentPosition?.week||"—"}`)}</strong></div>`}''', 'Continuous Current cycle summary')

missing = [m for m in required if m not in text]
if missing:
    raise SystemExit('missing required markers after patch: ' + ', '.join(missing))

path.write_text(text)
print('Patched index.html:', len(text.encode()))
