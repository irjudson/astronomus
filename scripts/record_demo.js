/**
 * Astronomus demo screen recorder
 * Usage: node scripts/record_demo.js
 * Output: astronomus-demo.mp4
 */

const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const os = require('os');

const BASE_URL = 'http://localhost:9247/app/';
const VIDEO_DIR = os.tmpdir();
const OUT_MP4 = path.join(process.cwd(), 'astronomus-demo.mp4');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: ['--window-size=1440,900', '--window-position=0,0'],
  });

  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1440, height: 900 } },
  });

  const page = await ctx.newPage();
  page.on('dialog', (d) => d.accept().catch(() => {}));

  // Pre-warm the slow visibility endpoint in background so Solar System loads fast later
  page.evaluate(() =>
    fetch('/api/solar-system/objects?lat=45.9183&lon=-111.5433').catch(() => {})
  ).catch(() => {});

  // ─── SHOT 1: Tonight dashboard ───────────────────────────────────────────
  console.log('Shot 1: Tonight dashboard');
  await page.goto(BASE_URL);
  await page.waitForSelector('text=7-DAY FORECAST', { timeout: 15000 }).catch(() => {});
  await sleep(5000);
  // Mouse across the weather strip
  for (const x of [240, 360, 475, 590, 705, 820, 855]) {
    await page.mouse.move(x, 280);
    await sleep(350);
  }
  await sleep(1000);

  // ─── SHOT 2: Sky → Deep Sky catalog ──────────────────────────────────────
  console.log('Shot 2: Deep Sky catalog');
  // Navigate directly to sky route
  await page.click('a[href="/app/sky"]');
  await page.waitForSelector('button:has-text("Deep Sky")', { timeout: 8000 });

  // Uncheck "Visible tonight" so the full catalog (12,394 items) loads in 27ms
  // instead of the filtered version (529 items, 8s calculation)
  const visCheckbox = page.locator('#visible-now');
  if (await visCheckbox.isChecked().catch(() => false)) {
    await visCheckbox.uncheck();
  }
  await sleep(500);

  // Wait for catalog cards to appear
  await page.waitForSelector('.catalog-card', { timeout: 10000 });
  await sleep(1200);

  // Hover first card to show score/details
  const firstCard = page.locator('.catalog-card').first();
  await firstCard.hover();
  await sleep(1800);
  await page.mouse.move(900, 500); // move away
  await sleep(600);

  // Star 3 targets that are in the wishlist (already seeded)
  // Find the ☆ star buttons and click them
  const starBtns = await page.locator('button[title="Add to wishlist"]').all();
  for (let i = 0; i < Math.min(3, starBtns.length); i++) {
    try {
      if (await starBtns[i].isVisible({ timeout: 500 })) {
        await starBtns[i].scrollIntoViewIfNeeded();
        await starBtns[i].click();
        await sleep(500);
      }
    } catch {}
  }
  await sleep(800);

  // Now enable "Visible tonight" filter to show filtering live
  if (!await visCheckbox.isChecked().catch(() => true)) {
    await visCheckbox.check();
    await sleep(400);
  }

  // ─── SHOT 3: Solar System tab ─────────────────────────────────────────────
  console.log('Shot 3: Solar System tab');
  await page.locator('button:has-text("Solar System")').click();
  // Wait for loading to finish — this endpoint takes ~8s on first call
  await page.waitForSelector('text=Loading solar system', { state: 'hidden', timeout: 25000 }).catch(() => {});
  await page.waitForSelector('text=Jupiter', { timeout: 5000 }).catch(() => {});
  await sleep(2000);

  // Scroll down to show moons section then back up
  await page.mouse.wheel(0, 350);
  await sleep(1800);
  await page.mouse.wheel(0, -350);
  await sleep(800);

  // ─── SHOT 3.5: Satellites tab ────────────────────────────────────────────
  console.log('Shot 3.5: Satellites tab');
  await page.locator('button:has-text("Satellites")').click();
  // Wait for ISS passes to load (fetches from backend)
  await page.waitForSelector('text=ISS Passes', { timeout: 10000 }).catch(() => {});
  await sleep(500);
  // Wait for loading spinner to clear
  await page.waitForSelector('text=Loading satellite passes', { state: 'hidden', timeout: 12000 }).catch(() => {});
  await sleep(2000);
  // Scroll to show pass list
  await page.mouse.wheel(0, 300);
  await sleep(1200);
  await page.mouse.wheel(0, -300);
  await sleep(800);

  // ─── SHOT 4: Plan view → Generate ────────────────────────────────────────
  console.log('Shot 4: Plan → Generate');
  await page.click('a[href="/app/plan"]');
  await page.waitForSelector('button:has-text("Generate")', { timeout: 10000 });
  await sleep(800);
  await page.locator('button:has-text("Generate Plan"), button:has-text("Generate")').first().click();
  console.log('  Waiting for plan generation...');
  await page.waitForSelector('text=Scheduled Targets', { timeout: 35000 }).catch(() => {});
  await sleep(2500);

  // ─── SHOT 5: Timeline hover ───────────────────────────────────────────────
  console.log('Shot 5: Timeline');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(800);

  const svg = page.locator('svg').first();
  const box = await svg.boundingBox().catch(() => null);
  if (box) {
    const y = box.y + box.height * 0.38;
    for (let x = box.x + 80; x < box.x + box.width - 60; x += 80) {
      await page.mouse.move(x, y);
      await sleep(220);
    }
    await page.mouse.move(0, 0);
  }
  await sleep(1200);

  // ─── SHOT 6: Scroll through each scheduled target card ───────────────────
  console.log('Shot 6: Target cards');
  // Scroll past the timeline to reach the target list
  await page.mouse.wheel(0, 600);
  await sleep(1000);

  // Scroll through scheduled target cards only (exclude near-miss cards which have opacity-60)
  const targetCards = await page.locator('.border-l-4.rounded-lg:not(.opacity-60)').all();
  console.log(`  Found ${targetCards.length} scheduled target cards`);
  for (let i = 0; i < targetCards.length; i++) {
    try {
      await targetCards[i].scrollIntoViewIfNeeded();
      await sleep(1400);
    } catch {}
  }

  // ─── SHOT 7: Near misses — brief scroll-by only ───────────────────────────
  console.log('Shot 7: Near misses');
  await page.mouse.wheel(0, 500);
  await sleep(1200);

  // ─── SHOT 8: Scroll back, name plan, save ────────────────────────────────
  console.log('Shot 8: Save and Send to Scope');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(1000);

  // Name the plan (the input is visible once a plan exists)
  const nameInput2 = page.locator('input[placeholder*="Name"], input[placeholder*="name"]').first();
  if (await nameInput2.isVisible({ timeout: 2000 }).catch(() => false)) {
    await nameInput2.click({ clickCount: 3 });
    await nameInput2.fill('Bozeman Session — May 24');
    await sleep(600);
  }

  const saveBtn = page.locator('button:has-text("Save Plan")').first();
  if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await saveBtn.click();
    await sleep(2500);
  }

  // End on "Send to Scope" button hover
  const sendBtn = page.locator('button:has-text("Send to Scope")').first();
  if (await sendBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await sendBtn.hover();
    await sleep(2200);
  }

  await sleep(1500);
  console.log('Recording complete.');

  await ctx.close();
  await browser.close();

  // Find newest webm and convert to mp4
  const { readdirSync, statSync } = require('fs');
  const files = readdirSync(VIDEO_DIR)
    .filter((f) => f.endsWith('.webm'))
    .map((f) => ({ f, t: statSync(path.join(VIDEO_DIR, f)).mtimeMs }))
    .sort((a, b) => b.t - a.t);

  if (!files.length) { console.error('No webm found'); process.exit(1); }

  const webm = path.join(VIDEO_DIR, files[0].f);
  console.log(`Converting ${webm} → ${OUT_MP4}`);
  execSync(
    `ffmpeg -y -i "${webm}" -vf "scale=1440:900,format=yuv420p" -c:v libx264 -preset slow -crf 18 -movflags +faststart "${OUT_MP4}"`,
    { stdio: 'inherit' }
  );
  console.log(`\nDone! → ${OUT_MP4}`);
})();
