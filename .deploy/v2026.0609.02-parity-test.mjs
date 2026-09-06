import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const url = process.env.TEST_URL || 'http://127.0.0.1:4173/index.html';
const browser = await chromium.launch({headless:true});

async function runViewport(name, viewport) {
  const page = await browser.newPage({ viewport });
  page.on('pageerror', err => console.error(`[${name}] pageerror`, err.message));
  await page.goto(url, { waitUntil:'domcontentloaded', timeout:120000 });
  await page.waitForFunction(() => typeof renderAll === 'function' && typeof defaultState === 'function', null, {timeout:120000});

  async function renderRole(role) {
    return await page.evaluate((role) => {
      state = defaultState();
      const plan = state.plans.find(item => item.id === 'tirzepatide');
      if (!plan) throw new Error('Tirzepatide fixture missing');
      plan.stackStatus = 'active';
      plan.enabled = true;
      plan.confirmed = false;
      plan.noCycle = true;
      plan.startDate = '2026-09-01';
      plan.route = 'Subcutaneous (SC/SQ)';
      plan.disposeAfterDays = 90;
      state.ui.onboardingStage = 'profile';
      state.ui.onboardingComplete = false;
      state.ui.onboardingIntroComplete = false;
      state.ui.sectionOpen = {};
      cloudUser = { id:'parity-test-user', email:'parity@example.invalid' };
      cloudAccess = { status:'active', role };
      normaliseState();
      state.ui.onboardingStage = 'profile';
      state.ui.onboardingComplete = false;
      renderAll({preserveView:false});
      applyCloudAccessUi();
      activateTab('planner');

      const card = document.querySelector('[data-simple-plan="tirzepatide"]');
      if (!card) throw new Error('Tirzepatide treatment card did not render');
      const grid = card.querySelector('.peptide-settings-grid');
      const labels = grid ? [...grid.querySelectorAll(':scope > div > label')].map(el => el.textContent.replace(/\s+/g,' ').trim()) : [];
      const controlSignature = [...document.querySelectorAll('button,input,select,textarea,details')]
        .filter(el => !el.closest('#admin') && el.id !== 'adminTabButton')
        .map(el => ({
          tag:el.tagName,
          id:el.id||'',
          type:el.getAttribute('type')||'',
          name:el.getAttribute('name')||'',
          dataSimpleField:el.getAttribute('data-simple-field')||'',
          dataCollapseKey:el.getAttribute('data-collapse-key')||'',
          disabled:!!el.disabled,
          hidden:el.classList.contains('hidden'),
          open:el.tagName==='DETAILS'?!!el.open:undefined,
          text:el.tagName==='BUTTON'?el.textContent.replace(/\s+/g,' ').trim():undefined
        }));
      const plannerHtml = document.getElementById('planner')?.innerHTML || '';
      const roleBadge = document.getElementById('plannerRoleBadge')?.textContent?.trim() || document.querySelector('[data-planner-role]')?.textContent?.trim() || '';
      return {
        labels,
        controlSignature,
        plannerHtml,
        addTreatmentDisabled:!!document.getElementById('simpleAddTreatment')?.disabled,
        onboardingStage:plannerOnboardingStage(),
        adminButtonHidden:document.getElementById('adminTabButton')?.classList.contains('hidden') ?? true,
        roleBadge
      };
    }, role);
  }

  const owner = await renderRole('owner');
  const user = await renderRole('user');

  assert.deepEqual(user.labels, owner.labels, `${name}: Peptide Settings labels differ by role`);
  assert.deepEqual(user.labels, ['Status','Route','Dispose by','Cycles/Year'], `${name}: continuous Peptide Settings layout is not the required four-field layout`);
  assert.equal(user.plannerHtml, owner.plannerHtml, `${name}: #planner markup differs between owner and user`);
  assert.deepEqual(user.controlSignature, owner.controlSignature, `${name}: non-admin controls/disabled states differ between owner and user`);
  assert.equal(owner.addTreatmentDisabled, false, `${name}: owner Add Treatment is disabled`);
  assert.equal(user.addTreatmentDisabled, false, `${name}: user Add Treatment is disabled`);
  assert.equal(owner.onboardingStage, 'complete', `${name}: owner onboarding still changes normal planner behavior`);
  assert.equal(user.onboardingStage, 'complete', `${name}: user onboarding still changes normal planner behavior`);
  assert.equal(owner.roleBadge, user.roleBadge, `${name}: account role badge differs outside Admin Dashboard`);
  assert.equal(user.adminButtonHidden, true, `${name}: Admin Dashboard button is visible to user`);
  assert.equal(owner.adminButtonHidden, false, `${name}: Admin Dashboard button is hidden from owner`);

  async function mutateStatus(role) {
    return await page.evaluate((role) => {
      state = defaultState();
      const plan = state.plans.find(item => item.id === 'tirzepatide');
      plan.stackStatus='active'; plan.enabled=true; plan.noCycle=true; plan.startDate='2026-09-01';
      state.ui.onboardingStage='profile'; state.ui.onboardingComplete=false; state.ui.sectionOpen={};
      cloudUser={id:'parity-test-user'}; cloudAccess={status:'active',role};
      renderAll({preserveView:false}); applyCloudAccessUi(); activateTab('planner');
      const select=document.querySelector('[data-simple-plan="tirzepatide"] [data-simple-field="stackStatus"]');
      if(!select)throw new Error('Status control missing');
      select.value='soon'; select.dispatchEvent(new Event('change',{bubbles:true}));
      const updated=state.plans.find(item=>item.id==='tirzepatide');
      return {stackStatus:updated.stackStatus,enabled:updated.enabled,onboarding:plannerOnboardingStage(),buttonDisabled:!!document.getElementById('simpleAddTreatment')?.disabled};
    }, role);
  }
  assert.deepEqual(await mutateStatus('user'), await mutateStatus('owner'), `${name}: treatment-setting change behaves differently by role`);

  const adminAccess = await page.evaluate(() => {
    cloudUser={id:'parity-test-user'};
    cloudAccess={status:'active',role:'user'}; applyCloudAccessUi(); activateTab('admin');
    const userAdminActive=document.getElementById('admin')?.classList.contains('active')||false;
    const userDashboardActive=document.getElementById('dashboard')?.classList.contains('active')||false;
    cloudAccess={status:'active',role:'owner'}; applyCloudAccessUi(); activateTab('admin');
    const ownerAdminActive=document.getElementById('admin')?.classList.contains('active')||false;
    return {userAdminActive,userDashboardActive,ownerAdminActive};
  });
  assert.equal(adminAccess.userAdminActive,false,`${name}: user can activate Admin Dashboard`);
  assert.equal(adminAccess.userDashboardActive,true,`${name}: user is not redirected away from Admin Dashboard`);
  assert.equal(adminAccess.ownerAdminActive,true,`${name}: owner cannot activate Admin Dashboard`);

  console.log(`PASS ${name}: owner/user planner parity verified; Admin Dashboard is the only role exception.`);
  await page.close();
}

try {
  await runViewport('desktop',{width:1440,height:1000});
  await runViewport('mobile',{width:390,height:844});
  console.log('PASS ALL: v2026.0609.02 browser parity suite');
} finally {
  await browser.close();
}
