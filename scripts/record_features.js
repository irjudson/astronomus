/**
 * Astronomus feature highlight recorder — two focused segments:
 *   0–14s  : Local Weather + Observability score on Tonight home page
 *   14–26s : Satellite Avoidance checkbox in Plan constraints panel
 * Usage: node scripts/record_features.js
 * Output: astronomus-features-raw.mp4
 */

const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const os = require('os');

const BASE_URL = 'http://localhost:9247/app/';
const VIDEO_DIR = os.tmpdir();
const OUT_MP4 = path.join(process.cwd(), 'astronomus-features-raw.mp4');

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

  // ─── SEGMENT 1: Local Weather + Observability on Tonight page (0–14s) ─────
  console.log('Segment 1: Local Weather on Tonight home page');
  await page.goto(BASE_URL);
  await page.waitForSelector('text=Conditions', { timeout: 8000 }).catch(() => {});
  await sleep(1000);

  // Hover slowly over the temperature / humidity row
  await page.mouse.move(220, 210);
  await sleep(800);
  await page.mouse.move(310, 210);
  await sleep(600);
  await page.mouse.move(400, 210);
  await sleep(600);

  // Move to the suitability badge
  await page.mouse.move(200, 240);
  await sleep(1500);

  // Pan slowly up to the "Conditions" header
  await page.mouse.move(200, 195);
  await sleep(800);

  // Sweep across the 7-day forecast strip
  await page.mouse.move(160, 370);
  await sleep(500);
  for (const x of [200, 300, 400, 500, 600, 700, 800, 870]) {
    await page.mouse.move(x, 375);
    await sleep(350);
  }
  await sleep(1200);

  // Return to conditions card and linger on suitability badge
  await page.mouse.move(200, 240);
  await sleep(1500);
  await page.mouse.move(700, 500); // move off
  await sleep(500);
  // End of segment 1 at ~14s

  // ─── SEGMENT 2: Satellite Avoidance in Plan view (14–26s) ─────────────────
  console.log('Segment 2: Satellite Avoidance in Plan view');
  await page.click('a[href="/app/plan"]');
  await page.waitForSelector('text=Avoid Satellites', { timeout: 8000 }).catch(() => {});
  await sleep(800);

  // Find and highlight the Avoid Satellites row clearly
  const satRow = page.locator('label:has-text("Avoid Satellites")');
  if (await satRow.isVisible({ timeout: 2000 }).catch(() => false)) {
    await satRow.scrollIntoViewIfNeeded();
    await sleep(500);

    const box = await satRow.boundingBox().catch(() => null);
    if (box) {
      // Approach from left, sweep across label to checkbox
      await page.mouse.move(box.x + 10, box.y + box.height / 2);
      await sleep(600);
      await page.mouse.move(box.x + box.width * 0.4, box.y + box.height / 2);
      await sleep(800);
      await page.mouse.move(box.x + box.width * 0.85, box.y + box.height / 2);
      await sleep(1200); // linger near the checkbox
      await page.mouse.move(box.x + box.width * 0.4, box.y + box.height / 2);
      await sleep(600);
    }
    // Hover the full row a couple of times for emphasis
    await satRow.hover();
    await sleep(2000);
  }

  // Show context: also hover "Avoid moonlit targets" row briefly
  const moonRow = page.locator('label:has-text("Avoid moonlit targets")');
  if (await moonRow.isVisible({ timeout: 1000 }).catch(() => false)) {
    await moonRow.hover();
    await sleep(700);
  }

  // Return to satellite row for final emphasis
  if (await satRow.isVisible({ timeout: 1000 }).catch(() => false)) {
    await satRow.hover();
    await sleep(1800);
  }

  await sleep(500);
  console.log('All segments recorded.');

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
