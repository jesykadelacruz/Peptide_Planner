from pathlib import Path
import subprocess
src=Path('index.html').read_text()
def fn(name):
    start=src.index(f'function {name}('); brace=src.index('{',start); depth=0; quote=None; esc=False
    for i in range(brace,len(src)):
        ch=src[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in "'\"`":quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return src[start:i+1]
    raise RuntimeError(name)
blocks='\n'.join(fn(n) for n in ['cycleVialPrepForRecord','cycleVialPrepRecords','cycleVialPrepForSequence','cycleVialRecordHasAuthoritativeOpen','cycleVialRecordResolvedOpenDate','cycleVialPrepForDate'])
js=r'''function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null}
function parseISO(s){if(!s)return null;const [y,m,d]=String(s).split('-').map(Number);return new Date(y,m-1,d)}
function todayISO(){return '2026-09-10'}
function protocolPositionForDate(plan,d){return {sequence:1}}
function protocolPeriodForSequence(plan,s){return {valid:true,start:parseISO('2026-07-01'),activeEnd:parseISO('2026-10-31')}}
let state={vialRecords:[]};
'''+blocks+r'''
function assert(c,m){if(!c)throw new Error(m)}
let plan={id:'p',noCycle:false,vialMg:50,finalMl:5};
state.vialRecords=[
 {id:'r1',planId:'p',scheduleCycleNumber:1,scheduleRowIndex:1,vialMg:100,finalMl:5,startDate:'2026-07-01',scheduleOpenAuto:false,openedActual:true,scheduleResolvedOpenDate:'2026-07-01'},
 {id:'r2',planId:'p',scheduleCycleNumber:1,scheduleRowIndex:2,vialMg:200,finalMl:5,startDate:'2026-07-15',scheduleOpenAuto:true,scheduleResolvedOpenDate:'2026-09-01'},
];
let prep=cycleVialPrepForDate(plan,'2026-08-15',1);assert(prep.record.id==='r1','auto row stale startDate must not become active early');
prep=cycleVialPrepForDate(plan,'2026-09-05',1);assert(prep.record.id==='r2','resolved automatic Open must activate the new vial');
state.vialRecords[1].startDate='2026-08-20';state.vialRecords[1].scheduleOpenAuto=false;state.vialRecords[1].openedActual=true;
prep=cycleVialPrepForDate(plan,'2026-08-25',1);assert(prep.record.id==='r2','actual opened vial must immediately become active');
console.log('active-vial prep resolver OK');
'''
Path('/tmp/v03_prep_test.js').write_text(js)
subprocess.run(['node','--check','/tmp/v03_prep_test.js'],check=True)
r=subprocess.run(['node','/tmp/v03_prep_test.js'],capture_output=True,text=True)
print(r.stdout,r.stderr);raise SystemExit(r.returncode)
