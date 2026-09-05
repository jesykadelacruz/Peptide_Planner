from pathlib import Path

path = Path('index.html')
text = path.read_text()

def once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    text = text.replace(old, new, 1)

if '<title>Peptide Planner v2026.0509.03</title>' in text:
    required = [
        'const APP_VERSION="v2026.0509.03";',
        'data-cycle-config-field="endDate" data-cycle-sequence="0"',
    ]
    missing = [m for m in required if m not in text]
    if missing or 'Leave blank for continuous treatment.' in text:
        raise SystemExit('v2026.0509.03 detected but validation failed')
    print('v2026.0509.03 already applied')
    raise SystemExit(0)

once('<title>Peptide Planner v2026.0509.02</title>', '<title>Peptide Planner v2026.0509.03</title>', 'title/version')
once('const APP_VERSION="v2026.0509.02";', 'const APP_VERSION="v2026.0509.03";', 'APP_VERSION')
once('<div class="helper">Leave blank for continuous treatment.</div>', '', 'continuous end-date helper text')

required = [
    '<title>Peptide Planner v2026.0509.03</title>',
    'const APP_VERSION="v2026.0509.03";',
    'data-cycle-config-field="endDate" data-cycle-sequence="0"',
    'function continuousCurrentCycleText',
    'function todayAdministrationMissed',
    'signInWithPassword',
    'resetPasswordForEmail',
    'PASSWORD_RECOVERY',
    'planner_state',
    'planner_snapshots',
]
missing = [m for m in required if m not in text]
if missing:
    raise SystemExit('missing required markers after patch: ' + ', '.join(missing))
if 'Leave blank for continuous treatment.' in text:
    raise SystemExit('continuous helper text was not removed')

path.write_text(text)
print('Patched index.html:', len(text.encode()))
